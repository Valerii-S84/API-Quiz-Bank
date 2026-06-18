from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.repository_test_support import ROOT

sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import database_seed  # noqa: E402
from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools  # noqa: E402
from quizbank_mvp.database import connect, initialize_database, seed_demo_state  # noqa: E402
from quizbank_mvp.selection_models import SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_queue_filler import refill_selection_queue_for_request  # noqa: E402
from quizbank_mvp.selection_queue_selector import select_next_item_from_queue  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class StartupDemoResetTests(unittest.TestCase):
    def test_container_startup_initializes_database_without_demo_seed(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        startup_line = next(line for line in dockerfile.splitlines() if line.startswith("CMD "))

        self.assertIn("quizbank_mvp.cli init-db", startup_line)
        self.assertIn("uvicorn quizbank_mvp.app:app", startup_line)
        self.assertNotIn("seed-demo", startup_line)

    def test_startup_init_does_not_crash_existing_queue_linked_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            self.create_queue_linked_demo_delivery(db_path)

            initialize_database(db_path)

            self.assertEqual(self.count_rows(db_path, "deliveries"), 1)
            self.assertEqual(self.count_linked_queue_rows(db_path), 1)

    def test_demo_reset_clears_queue_linked_demo_deliveries_locally(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.sqlite3"
            self.create_queue_linked_demo_delivery(db_path)

            with mock.patch.dict(os.environ, self.demo_environment()):
                seed_demo_state(db_path, APPROVED_FIXTURE)

            self.assertEqual(self.count_rows(db_path, "deliveries"), 0)
            self.assertEqual(self.count_linked_queue_rows(db_path), 0)
            self.assertEqual(self.count_rows(db_path, "quota_reservations"), 0)

    def test_demo_reset_refuses_postgresql_runtime_database(self) -> None:
        with mock.patch.dict(os.environ, {"QUIZBANK_DATABASE_URL": "postgresql://quizbank"}):
            with mock.patch.object(database_seed, "connect") as connect:
                with self.assertRaisesRegex(RuntimeError, "PostgreSQL runtime database"):
                    database_seed.reset_demo_delivery_state(None)

        connect.assert_not_called()

    def test_demo_reset_refuses_explicit_production_environment(self) -> None:
        with mock.patch.dict(os.environ, {"APP_ENV": "production"}):
            with mock.patch.object(database_seed, "connect") as connect:
                with self.assertRaisesRegex(RuntimeError, "APP_ENV is production"):
                    database_seed.reset_demo_delivery_state(Path("demo.sqlite3"))

        connect.assert_not_called()

    def create_queue_linked_demo_delivery(self, db_path: Path) -> None:
        with mock.patch.dict(os.environ, self.demo_environment()):
            initialize_database(db_path)
            seed_demo_state(db_path, APPROVED_FIXTURE)
            rebuild_candidate_pools(db_path)
            request = SelectionRequest(
                consumer_id="consumer_demo",
                filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
                deterministic=True,
            )
            refill_selection_queue_for_request(db_path, request)
            select_next_item_from_queue(db_path, request)
        self.assertEqual(self.count_rows(db_path, "deliveries"), 1)
        self.assertEqual(self.count_linked_queue_rows(db_path), 1)

    def demo_environment(self) -> dict[str, str]:
        return {
            "APP_ENV": "",
            "QUIZBANK_ENV": "test",
            "ENVIRONMENT": "",
            "QUIZBANK_DATABASE_URL": "",
        }

    def count_rows(self, db_path: Path, table_name: str) -> int:
        with connect(db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])

    def count_linked_queue_rows(self, db_path: Path) -> int:
        with connect(db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM selection_queue_items
                WHERE delivery_id IS NOT NULL
                """
            ).fetchone()
        return int(row["count"])


if __name__ == "__main__":
    unittest.main()
