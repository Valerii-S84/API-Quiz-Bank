from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect, initialize_database  # noqa: E402


PRECOMPUTED_SELECTION_TABLES = {
    "candidate_pools",
    "candidate_pool_items",
    "consumer_delivery_state",
    "selection_queues",
    "selection_queue_items",
    "selection_diagnostic_events",
    "selection_diagnostic_outbox",
}
CONTENT_SCOPE_COLUMNS = {"language_code", "content_bank_id", "bank_version_id"}


class PrecomputedSelectionSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_precomputed_selection_tables_are_created(self) -> None:
        with connect(self.db_path) as connection:
            table_names = sqlite_table_names(connection)

        self.assertTrue(PRECOMPUTED_SELECTION_TABLES.issubset(table_names))

    def test_precomputed_selection_tables_carry_content_scope(self) -> None:
        scoped_tables = PRECOMPUTED_SELECTION_TABLES - {
            "candidate_pool_items",
            "selection_queue_items",
            "selection_diagnostic_outbox",
        }
        with connect(self.db_path) as connection:
            columns_by_table = {
                table_name: sqlite_columns(connection, table_name)
                for table_name in scoped_tables
            }

        for table_name, columns in columns_by_table.items():
            with self.subTest(table_name=table_name):
                self.assertTrue(CONTENT_SCOPE_COLUMNS.issubset(columns))

    def test_queue_claim_and_outbox_indexes_are_created(self) -> None:
        with connect(self.db_path) as connection:
            queue_claim_columns = sqlite_index_columns(
                connection,
                "idx_selection_queue_items_claim",
            )
            outbox_columns = sqlite_index_columns(
                connection,
                "idx_selection_diagnostic_outbox_pending",
            )

        self.assertEqual(
            queue_claim_columns,
            ["queue_id", "claim_status", "position", "queue_item_id"],
        )
        self.assertEqual(outbox_columns, ["status", "next_attempt_at", "created_at"])

    def test_queue_items_keep_unique_position_and_item_per_queue(self) -> None:
        with connect(self.db_path) as connection:
            index_columns = {
                tuple(sqlite_index_columns(connection, row["name"]))
                for row in sqlite_indexes(connection, "selection_queue_items")
                if row["unique"]
            }

        self.assertIn(("queue_id", "position"), index_columns)
        self.assertIn(("queue_id", "item_id"), index_columns)


def sqlite_table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row["name"] for row in rows}


def sqlite_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def sqlite_index_columns(connection: sqlite3.Connection, index_name: str) -> list[str]:
    rows = connection.execute(f"PRAGMA index_info({index_name})").fetchall()
    return [row["name"] for row in rows]


def sqlite_indexes(connection: sqlite3.Connection, table_name: str):
    return connection.execute(f"PRAGMA index_list({table_name})").fetchall()


if __name__ == "__main__":
    unittest.main()
