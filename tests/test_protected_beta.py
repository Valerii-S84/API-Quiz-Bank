from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_control_fixture,
)
from quizbank_mvp.protected_beta import (  # noqa: E402
    CORE_DEUTSCH_IST_EINFACH_CHANNEL,
    DEUTSCH_IST_EINFACH_CHANNEL,
    due_slots,
    run_protected_beta_batch,
    run_protected_beta_slot,
    seed_protected_beta_channels,
)
from quizbank_mvp.telegram_delivery import TelegramDeliveryError, TelegramSendResult  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class FakeTelegramAdapter:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def send_quiz_poll(self, payload: dict[str, object]) -> TelegramSendResult:
        self.payloads.append(payload)
        return TelegramSendResult(message_id=f"msg_{len(self.payloads)}")


class FailSecondTelegramAdapter(FakeTelegramAdapter):
    def send_quiz_poll(self, payload: dict[str, object]) -> TelegramSendResult:
        self.payloads.append(payload)
        if len(self.payloads) == 2:
            raise TelegramDeliveryError("simulated_send_failure")
        return TelegramSendResult(message_id=f"msg_{len(self.payloads)}")


class ProtectedBetaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        self.environment_patch = patch.dict(
            os.environ,
            {"CORE_DEUTSCH_IST_EINFACH_CHANNEL_API_KEY": "unit_core_channel_key"},
        )
        self.environment_patch.start()

    def tearDown(self) -> None:
        self.environment_patch.stop()
        self.temp_directory.cleanup()

    def seed_slot_items(self, level: str, theme_id: str, count: int) -> None:
        source = APPROVED_FIXTURE.read_text(encoding="utf-8").splitlines()[0]
        base_item = json.loads(source)
        rows = [
            json.dumps(self.slot_item(base_item, level, theme_id, index), ensure_ascii=False)
            for index in range(1, count + 1)
        ]
        fixture_path = Path(self.temp_directory.name) / f"{level}_{theme_id}.jsonl"
        fixture_path.write_text("\n".join(rows), encoding="utf-8")
        seed_control_fixture(
            self.db_path,
            fixture_path,
            "approved",
            source_id=f"src_{level}_{theme_id}",
        )

    def slot_item(
        self,
        base_item: dict[str, str],
        level: str,
        theme_id: str,
        index: int,
    ) -> dict[str, str]:
        return {
            **base_item,
            "item_id": f"beta_{level.lower()}_{theme_id.lower()}_{index}",
            "sublevel": level,
            "theme_id": theme_id,
            "coverage_cell_id": f"{level}::{theme_id}::O02::P01",
            "tags": f"theme:{theme_id.lower()};level:{level.lower()};objective:o02;pattern:p01",
        }

    def core_slot_rows_and_delivery_count(self):
        with connect(self.db_path) as connection:
            slot_rows = connection.execute(
                """
                SELECT slot_id, cefr_level, theme_id, status
                FROM scheduled_delivery_slots
                WHERE consumer_id = ?
                ORDER BY slot_id
                """,
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchall()
            delivery_count = connection.execute(
                "SELECT COUNT(*) AS count FROM deliveries WHERE consumer_id = ?",
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()
        return slot_rows, int(delivery_count["count"])


class ProtectedBetaTests(ProtectedBetaTestCase):
    def test_channel_seed_and_schedule_are_configured(self) -> None:
        seed_protected_beta_channels(self.db_path)

        with connect(self.db_path) as connection:
            consumer = connection.execute(
                "SELECT * FROM consumers WHERE consumer_id = ?",
                (DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()
            profile = connection.execute(
                "SELECT * FROM consumer_admin_profiles WHERE consumer_id = ?",
                (DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()

        self.assertEqual(consumer["daily_quota_limit"], 9)
        self.assertEqual(profile["display_name"], "🇩🇪 Deutsch ist einfach! – Quiz")
        self.assertEqual(profile["consumer_kind"], "telegram_channel")
        self.assertEqual(
            [(slot.local_time, slot.cefr_level, slot.theme_id, slot.quiz_count)
             for slot in DEUTSCH_IST_EINFACH_CHANNEL.schedule_slots],
            [
                ("08:22", "A2", "T11", 3),
                ("12:47", "B1", "T03", 3),
                ("20:15", "B2", "T10", 3),
            ],
        )

    def test_core_channel_seed_and_schedule_are_scoped_to_a2_t01_t04(self) -> None:
        seed_protected_beta_channels(self.db_path)

        with connect(self.db_path) as connection:
            consumer = connection.execute(
                "SELECT * FROM consumers WHERE consumer_id = ?",
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()
            entitlement = connection.execute(
                "SELECT * FROM entitlements WHERE consumer_id = ?",
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()
            credential = connection.execute(
                "SELECT status, LENGTH(key_hash) AS hash_len FROM api_credentials WHERE consumer_id = ?",
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchone()

        self.assertEqual(CORE_DEUTSCH_IST_EINFACH_CHANNEL.chat_id, "-1002987612505")
        self.assertEqual(consumer["daily_quota_limit"], 2)
        self.assertEqual(json.loads(consumer["allowed_cefr_levels_json"]), ["A2"])
        self.assertEqual(json.loads(consumer["allowed_theme_ids_json"]), ["T01", "T04"])
        self.assertEqual(json.loads(entitlement["allowed_cefr_levels_json"]), ["A2"])
        self.assertEqual(json.loads(entitlement["allowed_theme_ids_json"]), ["T01", "T04"])
        self.assertEqual(credential["status"], "active")
        self.assertEqual(credential["hash_len"], 64)
        self.assertEqual(
            [
                (slot.local_time, slot.cefr_level, slot.theme_id, slot.quiz_count, slot.slot_id)
                for slot in CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_slots
            ],
            [
                (
                    "12:07",
                    "A2",
                    "T01",
                    1,
                    "core_deutsch_ist_einfach_channel:T01:12_07",
                ),
                (
                    "12:07",
                    "A2",
                    "T04",
                    1,
                    "core_deutsch_ist_einfach_channel:T04:12_07",
                ),
            ],
        )

    def test_due_slots_use_berlin_time(self) -> None:
        slots = due_slots(DEUTSCH_IST_EINFACH_CHANNEL, datetime(2026, 5, 12, 6, 22, tzinfo=UTC))

        self.assertEqual(
            [(slot.cefr_level, slot.theme_id, slot.quiz_count) for slot in slots],
            [("A2", "T11", 3)],
        )

    def test_core_channel_due_slots_use_berlin_1207_time(self) -> None:
        slots = due_slots(
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
        )

        self.assertEqual(
            [(slot.cefr_level, slot.theme_id, slot.quiz_count) for slot in slots],
            [("A2", "T01", 1), ("A2", "T04", 1)],
        )

    def test_slot_sends_three_unique_quizzes(self) -> None:
        self.seed_slot_items("A2", "T11", count=3)
        seed_protected_beta_channels(self.db_path)
        adapter = FakeTelegramAdapter()

        results = run_protected_beta_slot(
            self.db_path,
            DEUTSCH_IST_EINFACH_CHANNEL,
            DEUTSCH_IST_EINFACH_CHANNEL.schedule_slots[0],
            "real",
            adapter,
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(len({result.quiz_item_id for result in results}), 3)
        self.assertEqual(len(adapter.payloads), 3)

    def test_core_batch_retry_does_not_duplicate_sent_slot(self) -> None:
        self.seed_slot_items("A2", "T01", count=2)
        self.seed_slot_items("A2", "T04", count=2)
        seed_protected_beta_channels(self.db_path)
        batch = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_batches[0]
        first_adapter = FakeTelegramAdapter()

        first_results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            first_adapter,
            datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
        )
        retry_adapter = FakeTelegramAdapter()
        retry_results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            retry_adapter,
            datetime(2026, 5, 13, 10, 8, tzinfo=UTC),
        )

        self.assertEqual([result.status for result in first_results], ["sent", "sent"])
        self.assertEqual(len(first_adapter.payloads), 2)
        self.assertEqual(len(retry_adapter.payloads), 0)
        self.assertEqual(
            [result.delivery_id for result in retry_results],
            [result.delivery_id for result in first_results],
        )
        slot_rows, delivery_count = self.core_slot_rows_and_delivery_count()

        self.assertEqual(delivery_count, 2)
        self.assertEqual(
            [(row["slot_id"], row["cefr_level"], row["theme_id"], row["status"])
             for row in slot_rows],
            [
                ("core_deutsch_ist_einfach_channel:T01:12_07", "A2", "T01", "sent"),
                ("core_deutsch_ist_einfach_channel:T04:12_07", "A2", "T04", "sent"),
            ],
        )

    def test_core_batch_retry_only_resends_failed_slot(self) -> None:
        self.seed_slot_items("A2", "T01", count=2)
        self.seed_slot_items("A2", "T04", count=2)
        seed_protected_beta_channels(self.db_path)
        batch = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_batches[0]
        adapter = FailSecondTelegramAdapter()

        first_results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            adapter,
            datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
        )
        retry_adapter = FakeTelegramAdapter()
        retry_results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            retry_adapter,
            datetime(2026, 5, 13, 10, 8, tzinfo=UTC),
        )

        self.assertEqual([result.status for result in first_results], ["sent", "failed"])
        self.assertEqual(len(adapter.payloads), 2)
        self.assertEqual(len(retry_adapter.payloads), 1)
        self.assertEqual(retry_results[0].status, "sent")
        self.assertEqual(retry_results[1].status, "sent")

    def test_core_batch_logs_no_item_without_empty_post(self) -> None:
        self.seed_slot_items("A2", "T01", count=1)
        seed_protected_beta_channels(self.db_path)
        batch = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_batches[0]
        adapter = FakeTelegramAdapter()

        results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            adapter,
            datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
        )

        self.assertEqual([result.status for result in results], ["sent", "no_item"])
        self.assertEqual(len(adapter.payloads), 1)
        with connect(self.db_path) as connection:
            no_item = connection.execute(
                """
                SELECT status, delivery_id, failure_reason
                FROM scheduled_delivery_slots
                WHERE theme_id = 'T04'
                """
            ).fetchone()
        self.assertEqual(no_item["status"], "no_item")
        self.assertIsNone(no_item["delivery_id"])
        self.assertEqual(no_item["failure_reason"], "SELECTION_NO_ELIGIBLE_ITEM")

if __name__ == "__main__":
    unittest.main()
