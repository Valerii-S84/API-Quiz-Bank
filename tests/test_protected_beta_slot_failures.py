from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect  # noqa: E402
from quizbank_mvp.protected_beta import (  # noqa: E402
    CORE_DEUTSCH_IST_EINFACH_CHANNEL,
    run_protected_beta_batch,
    seed_protected_beta_channels,
)
from quizbank_mvp.visual_cache import (  # noqa: E402
    VisualAssetStorageError,
    store_visual_asset_candidate,
)

from tests.test_protected_beta import FakeTelegramAdapter, ProtectedBetaTestCase  # noqa: E402


class ProtectedBetaSlotFailureTests(ProtectedBetaTestCase):
    def test_core_batch_marks_failed_slot_and_continues_after_visual_cache_error(self) -> None:
        self.seed_slot_items("A2", "T01", count=1)
        self.seed_slot_items("A2", "T04", count=1)
        seed_protected_beta_channels(self.db_path)
        batch = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_batches[0]
        adapter = FakeTelegramAdapter()
        store_calls = []

        def flaky_store(*args, **kwargs):
            store_calls.append(args)
            if len(store_calls) == 1:
                raise VisualAssetStorageError(
                    "VISUAL_ASSET_PERMISSION_DENIED",
                    self.asset_root,
                    "Permission denied",
                )
            return store_visual_asset_candidate(*args, **kwargs)

        with patch("quizbank_mvp.visual_delivery.store_visual_asset_candidate", flaky_store):
            results = run_protected_beta_batch(
                self.db_path,
                CORE_DEUTSCH_IST_EINFACH_CHANNEL,
                batch,
                "real",
                adapter,
                datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
                self.core_visual_delivery_options(),
            )

        self.assertEqual([result.status for result in results], ["failed", "sent"])
        self.assertEqual(len(adapter.payloads), 1)
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT theme_id, delivery_id, status, failure_reason
                FROM scheduled_delivery_slots
                WHERE consumer_id = ?
                ORDER BY theme_id
                """,
                (CORE_DEUTSCH_IST_EINFACH_CHANNEL.consumer_id,),
            ).fetchall()
        self.assertEqual([row["theme_id"] for row in rows], ["T01", "T04"])
        self.assertEqual(rows[0]["status"], "failed")
        self.assertIsNotNone(rows[0]["delivery_id"])
        self.assertIn("VISUAL_ASSET_PERMISSION_DENIED", rows[0]["failure_reason"])
        self.assertEqual(rows[1]["status"], "sent")

    def test_core_batch_retry_reuses_delivery_after_slot_exception(self) -> None:
        self.seed_slot_items("A2", "T01", count=1)
        self.seed_slot_items("A2", "T04", count=1)
        seed_protected_beta_channels(self.db_path)
        batch = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_batches[0]

        def fail_store(*args, **kwargs):
            raise VisualAssetStorageError(
                "VISUAL_ASSET_PERMISSION_DENIED",
                self.asset_root,
                "Permission denied",
            )

        with patch("quizbank_mvp.visual_delivery.store_visual_asset_candidate", fail_store):
            first_results = run_protected_beta_batch(
                self.db_path,
                CORE_DEUTSCH_IST_EINFACH_CHANNEL,
                batch,
                "real",
                FakeTelegramAdapter(),
                datetime(2026, 5, 13, 10, 7, tzinfo=UTC),
                self.core_visual_delivery_options(),
            )
        retry_adapter = FakeTelegramAdapter()
        retry_results = run_protected_beta_batch(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            batch,
            "real",
            retry_adapter,
            datetime(2026, 5, 13, 10, 8, tzinfo=UTC),
            self.core_visual_delivery_options(),
        )

        self.assertEqual([result.status for result in first_results], ["failed", "failed"])
        self.assertEqual([result.status for result in retry_results], ["sent", "sent"])
        self.assertEqual(len(retry_adapter.payloads), 2)
        slot_rows, delivery_count = self.core_slot_rows_and_delivery_count()

        self.assertEqual(delivery_count, 2)
        self.assertEqual([row["status"] for row in slot_rows], ["sent", "sent"])
