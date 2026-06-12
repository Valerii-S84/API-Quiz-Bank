from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect, initialize_database, seed_control_fixture  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
DEFAULT_BANK_VERSION_ID = "german-core:2026-06-12-baseline"
CRITICAL_SCOPE_TABLES = (
    "sources",
    "quiz_items",
    "deliveries",
    "selection_decisions",
    "scheduled_delivery_slots",
    "visual_assets",
)
CONTENT_SCOPE_COLUMNS = {"language_code", "content_bank_id", "bank_version_id"}


class MultilingualBankSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_default_german_content_bank_version_is_active(self) -> None:
        with connect(self.db_path) as connection:
            language_rows = connection.execute(
                "SELECT code, is_active FROM languages ORDER BY code"
            ).fetchall()
            active_version = connection.execute(active_version_sql()).fetchone()

        self.assertEqual({row["code"] for row in language_rows}, {"de", "en", "es", "fr", "nl"})
        self.assertEqual(active_version["slug"], "german-core")
        self.assertEqual(active_version["language_code"], "de")
        self.assertEqual(active_version["version_id"], DEFAULT_BANK_VERSION_ID)

    def test_critical_runtime_tables_have_content_scope_columns(self) -> None:
        with connect(self.db_path) as connection:
            columns_by_table = {
                table_name: sqlite_columns(connection, table_name)
                for table_name in CRITICAL_SCOPE_TABLES
            }

        for table_name, column_names in columns_by_table.items():
            with self.subTest(table_name=table_name):
                self.assertTrue(CONTENT_SCOPE_COLUMNS.issubset(column_names))

    def test_seeded_german_items_receive_default_content_scope(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

        with connect(self.db_path) as connection:
            item_scope = connection.execute(
                """
                SELECT language_code, content_bank_id, bank_version_id
                FROM quiz_items
                WHERE item_id = 'approved_traceable_001'
                """
            ).fetchone()

        self.assertEqual(item_scope["language_code"], "de")
        self.assertEqual(item_scope["content_bank_id"], "german-core")
        self.assertEqual(item_scope["bank_version_id"], DEFAULT_BANK_VERSION_ID)

    def test_quiz_item_bank_version_fk_is_enforced(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

        with self.assertRaises(sqlite3.IntegrityError), connect(self.db_path) as connection:
            connection.execute(insert_bad_bank_version_item_sql())

    def test_only_one_active_version_is_allowed_per_content_bank(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError), connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO content_bank_versions (
                    id, content_bank_id, version, status, activated_at, created_at
                ) VALUES (
                    'german-core:second-active',
                    'german-core',
                    'second-active',
                    'active',
                    '2026-06-12T01:00:00Z',
                    '2026-06-12T01:00:00Z'
                )
                """
            )

    def test_selection_indexes_include_language_and_bank_version_scope(self) -> None:
        with connect(self.db_path) as connection:
            selection_columns = sqlite_index_columns(connection, "idx_quiz_items_selection_pool")
            decision_columns = sqlite_index_columns(
                connection,
                "idx_selection_decisions_scope_created",
            )

        self.assertEqual(selection_columns[:2], ["language_code", "bank_version_id"])
        self.assertEqual(
            decision_columns,
            ["consumer_id", "language_code", "bank_version_id", "created_at"],
        )


def active_version_sql() -> str:
    return """
        SELECT cb.slug, cb.language_code, cbv.id AS version_id
        FROM content_bank_versions cbv
        JOIN content_banks cb ON cb.id = cbv.content_bank_id
        WHERE cb.slug = 'german-core' AND cbv.status = 'active'
    """


def sqlite_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def sqlite_index_columns(connection: sqlite3.Connection, index_name: str) -> list[str]:
    rows = connection.execute(f"PRAGMA index_info({index_name})").fetchall()
    return [row["name"] for row in rows]


def insert_bad_bank_version_item_sql() -> str:
    return """
        INSERT INTO quiz_items (
            item_id, source_id, language, language_code, content_bank_id,
            bank_version_id, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt,
            stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        )
        SELECT
            'bad_bank_version_item', source_id, language, language_code,
            content_bank_id, 'missing-bank-version', level_band, sublevel,
            theme_id, subtheme_id, objective_id, pattern_id, difficulty_band,
            register, prompt, stem_text, options_json, answer_key, explanation,
            tags, coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        FROM quiz_items
        WHERE item_id = 'approved_traceable_001'
    """


if __name__ == "__main__":
    unittest.main()
