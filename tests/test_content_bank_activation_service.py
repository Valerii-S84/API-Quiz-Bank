from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.content_bank_service import (  # noqa: E402
    ContentBankVersionError,
    activate_bank_version,
    mark_bank_version_for_audit,
    rollback_bank_version,
)
from quizbank_mvp.database import connect, initialize_database  # noqa: E402


BASELINE_VERSION_ID = "german-core:2026-06-12-baseline"
DRAFT_VERSION_ID = "german-core:stage3-draft"


class ContentBankActivationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_mark_audit_promotes_only_draft_versions(self) -> None:
        self.insert_bank_version(DRAFT_VERSION_ID, "stage3-draft", "draft")

        result = mark_bank_version_for_audit(
            self.db_path,
            DRAFT_VERSION_ID,
            "admin",
            "ready for audit",
        )

        self.assertEqual(result["to_status"], "audit")
        self.assertEqual(self.version_status(DRAFT_VERSION_ID), "audit")
        self.assertEqual(self.latest_audit_action(), "content_bank_version_mark_audit")

    def test_activate_audited_version_archives_previous_active_version(self) -> None:
        self.insert_bank_version(DRAFT_VERSION_ID, "stage3-draft", "draft")
        mark_bank_version_for_audit(self.db_path, DRAFT_VERSION_ID, "admin", "ready")

        result = activate_bank_version(self.db_path, DRAFT_VERSION_ID, "admin", "activate")

        self.assertEqual(result["from_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(result["to_bank_version_id"], DRAFT_VERSION_ID)
        self.assertEqual(self.version_status(BASELINE_VERSION_ID), "archived")
        self.assertEqual(self.version_status(DRAFT_VERSION_ID), "active")
        self.assertEqual(self.latest_activation_event()["to_bank_version_id"], DRAFT_VERSION_ID)

    def test_rollback_reactivates_archived_version(self) -> None:
        self.insert_bank_version(DRAFT_VERSION_ID, "stage3-draft", "audit")
        activate_bank_version(self.db_path, DRAFT_VERSION_ID, "admin", "activate")

        result = rollback_bank_version(self.db_path, BASELINE_VERSION_ID, "admin", "rollback")

        self.assertEqual(result["from_bank_version_id"], DRAFT_VERSION_ID)
        self.assertEqual(result["to_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(self.version_status(BASELINE_VERSION_ID), "active")
        self.assertEqual(self.version_status(DRAFT_VERSION_ID), "archived")
        self.assertEqual(self.latest_audit_action(), "content_bank_version_rollback")

    def test_activate_rejects_draft_version_before_audit(self) -> None:
        self.insert_bank_version(DRAFT_VERSION_ID, "stage3-draft", "draft")

        with self.assertRaises(ContentBankVersionError) as error:
            activate_bank_version(self.db_path, DRAFT_VERSION_ID, "admin", "activate")

        self.assertIn("invalid_bank_version_status:draft", str(error.exception))
        self.assertEqual(self.version_status(BASELINE_VERSION_ID), "active")

    def insert_bank_version(self, version_id: str, version: str, status: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO content_bank_versions (
                    id, content_bank_id, version, status, activated_at, created_at
                ) VALUES (?, 'german-core', ?, ?, NULL, '2026-06-12T01:00:00Z')
                """,
                (version_id, version, status),
            )

    def version_status(self, version_id: str) -> str:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT status FROM content_bank_versions WHERE id = ?",
                (version_id,),
            ).fetchone()
        return str(row["status"])

    def latest_activation_event(self):
        with connect(self.db_path) as connection:
            return connection.execute(
                """
                SELECT *
                FROM content_bank_activation_events
                ORDER BY activated_at DESC, activation_event_id DESC
                LIMIT 1
                """
            ).fetchone()

    def latest_audit_action(self) -> str:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT action FROM audit_log ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        return str(row["action"])


if __name__ == "__main__":
    unittest.main()
