from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import selection_async_diagnostics  # noqa: E402
from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)


CONTROL_FIXTURE = ROOT / "data" / "imports" / "control_sample_items.jsonl"


class SelectionAsyncDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_no_candidate_route_enqueues_diagnostics_without_live_counts(self) -> None:
        seed_control_fixture(self.db_path, CONTROL_FIXTURE, "draft")
        seed_consumer(self.db_path, "consumer_allowed", 500, ["A2"], ["T10"])
        seed_api_credential(self.db_path, "consumer_allowed", "async_diagnostic_test_key")
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])

        with mock.patch.object(
            selection_async_diagnostics,
            "candidate_count",
            side_effect=AssertionError("candidate diagnostics must be async"),
        ):
            with mock.patch.object(
                selection_async_diagnostics,
                "blocked_reason_counts",
                side_effect=AssertionError("blocked diagnostics must be async"),
            ):
                response = TestClient(create_app(self.db_path)).post(
                    "/v1/quiz-items/next",
                    json={
                        "consumer_id": "consumer_allowed",
                        "cefr_level": "A2",
                        "theme_ids": ["T10"],
                    },
                    headers={
                        "X-Consumer-Id": "consumer_allowed",
                        "X-QuizBank-API-Key": "async_diagnostic_test_key",
                    },
                )

        decision = response.json()["selection_context"]["decision"]
        self.assertEqual(response.status_code, 404)
        self.assertEqual(decision["candidate_count"], 0)
        self.assertEqual(decision["blocked_reason_counts"], {})
        self.assertEqual(self.scalar_count("selection_diagnostic_outbox"), 1)

    def scalar_count(self, table_name: str) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return int(row["count"])


if __name__ == "__main__":
    unittest.main()
