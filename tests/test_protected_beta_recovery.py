from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect, initialize_database  # noqa: E402
from quizbank_mvp.protected_beta import (  # noqa: E402
    CORE_DEUTSCH_IST_EINFACH_CHANNEL,
    DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
    seed_protected_beta_channels,
    upsert_pending_slot_run,
)
from quizbank_mvp.protected_beta_recovery import recover_slots  # noqa: E402
from quizbank_mvp.protected_beta_slot_runs import scheduled_slot_id  # noqa: E402


class ProtectedBetaRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        self.environment_patch = patch.dict(
            os.environ,
            {"CORE_DEUTSCH_IST_EINFACH_CHANNEL_API_KEY": "unit_core_channel_key"},
        )
        self.environment_patch.start()
        seed_protected_beta_channels(self.db_path)

    def tearDown(self) -> None:
        self.environment_patch.stop()
        self.temp_directory.cleanup()

    def test_dry_run_recovery_does_not_change_database(self) -> None:
        slot = CORE_DEUTSCH_IST_EINFACH_CHANNEL.schedule_slots[0]
        slot_id = scheduled_slot_id(
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            slot,
            DEFAULT_PROTECTED_BETA_DELIVERY_OPTIONS,
        )
        upsert_pending_slot_run(
            self.db_path,
            CORE_DEUTSCH_IST_EINFACH_CHANNEL,
            slot,
            "2026-05-26",
            slot_id,
        )
        before = self.table_counts()

        actions = recover_slots(
            self.db_path,
            "2026-05-26",
            CORE_DEUTSCH_IST_EINFACH_CHANNEL.chat_id,
            ("T01", "T04"),
            "dry_run",
            True,
            True,
            True,
        )

        self.assertEqual(before, self.table_counts())
        self.assertEqual(
            [action.action for action in actions],
            ["would_retry_slot", "would_create_missing_slot"],
        )

    def table_counts(self) -> dict[str, int]:
        with connect(self.db_path) as connection:
            return {
                table: int(
                    connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
                )
                for table in (
                    "scheduled_delivery_slots",
                    "deliveries",
                    "telegram_delivery_results",
                    "visual_delivery_results",
                    "visual_assets",
                )
            }


if __name__ == "__main__":
    unittest.main()
