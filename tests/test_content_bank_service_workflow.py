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
    create_content_bank,
    create_content_bank_version,
    list_content_bank_versions,
    list_content_banks,
    list_import_batches,
    list_languages,
    mark_bank_version_for_audit,
    rollback_bank_version,
)
from quizbank_mvp.database import connect, initialize_database  # noqa: E402

BASELINE_VERSION_ID = "german-core:2026-06-12-baseline"


class ContentBankServiceWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_language_listing_marks_only_german_active(self) -> None:
        languages = list_languages(self.db_path)["data"]

        self.assertEqual([row["code"] for row in languages], ["de", "en", "fr", "es", "nl"])
        self.assertEqual(
            {row["code"]: row["is_active"] for row in languages},
            {"de": True, "en": False, "fr": False, "es": False, "nl": False},
        )

    def test_content_bank_lifecycle_activates_english_version(self) -> None:
        created_bank = create_content_bank(self.db_path, english_bank_payload(), "operator")
        created_version = create_content_bank_version(
            self.db_path,
            "english-core",
            version_payload("stage6-draft"),
            "operator",
        )
        listed_english = list_content_banks(self.db_path, "en")["data"][0]
        listed_versions = list_content_bank_versions(self.db_path, "english-core")["data"]

        self.assertEqual(created_bank["active_bank_version_id"], None)
        self.assertEqual(created_version["status"], "draft")
        self.assertEqual(listed_english["version_count"], 1)
        self.assertEqual(listed_versions[0]["bank_version_id"], "english-core:stage6-draft")

        audit = mark_bank_version_for_audit(
            self.db_path,
            "english-core:stage6-draft",
            "operator",
            "ready for isolated audit",
        )
        activated = activate_bank_version(
            self.db_path,
            "english-core:stage6-draft",
            "operator",
            "activate scoped English draft",
        )

        self.assertEqual(audit["to_status"], "audit")
        self.assertEqual(activated["from_bank_version_id"], None)
        self.assertEqual(activated["to_bank_version_id"], "english-core:stage6-draft")
        self.assertEqual(active_version_id(self.db_path, "english-core"), "english-core:stage6-draft")

    def test_content_bank_lifecycle_rolls_back_german_version(self) -> None:
        create_german_candidate_version(self.db_path)
        activate_bank_version(
            self.db_path,
            "german-core:rollback-candidate",
            "operator",
            "activate candidate",
        )
        rolled_back = rollback_bank_version(
            self.db_path,
            BASELINE_VERSION_ID,
            "operator",
            "restore baseline",
        )

        self.assertEqual(rolled_back["from_bank_version_id"], "german-core:rollback-candidate")
        self.assertEqual(active_version_id(self.db_path, "german-core"), BASELINE_VERSION_ID)
        self.assertEqual(version_status(self.db_path, "german-core:rollback-candidate"), "archived")
        self.assertEqual(audit_action_count(self.db_path, "content_bank_version_rollback"), 1)

    def test_content_bank_errors_are_controlled(self) -> None:
        with self.assertRaisesRegex(ContentBankVersionError, "unknown_language:it"):
            create_content_bank(
                self.db_path,
                {**english_bank_payload(), "content_bank_id": "italian-core", "language_code": "it"},
                "operator",
            )

        create_content_bank(self.db_path, english_bank_payload(), "operator")
        with self.assertRaisesRegex(ContentBankVersionError, "content_bank_create_conflict"):
            create_content_bank(self.db_path, english_bank_payload(), "operator")
        with self.assertRaisesRegex(ContentBankVersionError, "unknown_content_bank:missing"):
            list_content_bank_versions(self.db_path, "missing")
        with self.assertRaisesRegex(ContentBankVersionError, "unknown_bank_version:missing"):
            mark_bank_version_for_audit(self.db_path, "missing", "operator", "missing")
        with self.assertRaisesRegex(ContentBankVersionError, "invalid_bank_version_status:active"):
            activate_bank_version(self.db_path, BASELINE_VERSION_ID, "operator", "already active")

    def test_import_batch_listing_filters_by_content_scope(self) -> None:
        create_import_batch_table(self.db_path)
        insert_import_batch(self.db_path, "import_de", BASELINE_VERSION_ID, "dry_run_passed")
        insert_import_batch(self.db_path, "import_en", "english-core:stage6-draft", "rejected")

        filtered = list_import_batches(
            self.db_path,
            {"language_code": "de", "bank_version_id": BASELINE_VERSION_ID},
            10,
        )["data"]
        empty_from_missing_table = list_import_batches(db_without_import_table(), {}, 5)["data"]

        self.assertEqual([row["import_batch_id"] for row in filtered], ["import_de"])
        self.assertEqual(filtered[0]["bank_version_status"], "active")
        self.assertEqual(empty_from_missing_table, [])


def english_bank_payload() -> dict[str, str]:
    return {
        "content_bank_id": "english-core",
        "language_code": "en",
        "name": "English Core",
        "reason": "stage language bank",
    }


def version_payload(version: str) -> dict[str, str]:
    return {"version": version, "reason": f"create {version}"}


def create_german_candidate_version(db_path: Path) -> None:
    create_content_bank_version(db_path, "german-core", version_payload("rollback-candidate"), "operator")
    mark_bank_version_for_audit(db_path, "german-core:rollback-candidate", "operator", "candidate ready")


def active_version_id(db_path: Path, content_bank_id: str) -> str:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT id FROM content_bank_versions WHERE content_bank_id = ? AND status = 'active'",
            (content_bank_id,),
        ).fetchone()
    return str(row["id"])


def version_status(db_path: Path, bank_version_id: str) -> str:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT status FROM content_bank_versions WHERE id = ?",
            (bank_version_id,),
        ).fetchone()
    return str(row["status"])


def audit_action_count(db_path: Path, action: str) -> int:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM audit_log WHERE action = ?",
            (action,),
        ).fetchone()
    return int(row["count"])


def create_import_batch_table(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE import_batches (
                import_batch_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
                parser_profile_id TEXT NOT NULL, import_mode TEXT NOT NULL,
                import_status TEXT NOT NULL, default_item_status TEXT NOT NULL,
                row_count_detected INTEGER NOT NULL, accepted_candidate_count INTEGER NOT NULL,
                rejected_candidate_count INTEGER NOT NULL, report_uri TEXT NOT NULL,
                started_at TEXT NOT NULL, completed_at TEXT, created_by TEXT NOT NULL,
                language_code TEXT NOT NULL, content_bank_id TEXT NOT NULL,
                bank_version_id TEXT NOT NULL
            )
            """
        )


def insert_import_batch(db_path: Path, batch_id: str, bank_version_id: str, status: str) -> None:
    language_code = "de" if bank_version_id == BASELINE_VERSION_ID else "en"
    content_bank_id = "german-core" if language_code == "de" else "english-core"
    if language_code == "en":
        create_content_bank(db_path, english_bank_payload(), "operator")
        create_content_bank_version(db_path, "english-core", version_payload("stage6-draft"), "operator")
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO import_batches VALUES (?, 'source', 'profile', 'dry_run', ?, 'draft',
            2, 1, 1, 'reports/imports/control.json', '2026-06-14T00:00:00Z',
            NULL, 'test', ?, ?, ?)
            """,
            (batch_id, status, language_code, content_bank_id, bank_version_id),
        )


def db_without_import_table() -> Path:
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "empty.sqlite3"
    initialize_database(path)
    db_without_import_table._temp_dir = temp_dir
    return path
