from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools
from quizbank_mvp.app import create_app
from quizbank_mvp.database import (
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection_models import SelectionFilters, SelectionRequest
from quizbank_mvp.selection_queue_filler import refill_selection_queue_for_request


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class MvpRateLimitTests(unittest.TestCase):
    def test_delivery_endpoint_rate_limit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "quizbank.sqlite3"
            prepare_database(db_path)
            with patch.dict("os.environ", rate_limit_environment()):
                client = TestClient(create_app(db_path))

            first = post_next_item(client)
            second = post_next_item(client)
            limited = post_next_item(client)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 503)
        self.assertEqual(second.json()["reason_code"], "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited.json()["reason_code"], "RATE_LIMIT_EXCEEDED")


def prepare_database(db_path: Path) -> None:
    initialize_database(db_path)
    seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
    seed_consumer(db_path, "consumer_allowed", 5, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_allowed", "test_api_key")
    seed_entitlement(db_path, "consumer_allowed", ["A2"], ["T10"])
    rebuild_candidate_pools(db_path)
    refill_selection_queue_for_request(
        db_path,
        SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
        ),
    )


def rate_limit_environment() -> dict[str, str]:
    return {
        "QUIZBANK_RATE_LIMIT_DELIVERY_REQUESTS": "2",
        "QUIZBANK_RATE_LIMIT_WINDOW_SECONDS": "60",
    }


def post_next_item(client: TestClient):
    return client.post(
        "/v1/quiz-items/next",
        json={"consumer_id": "consumer_allowed", "cefr_level": "A2", "theme_ids": ["T10"]},
        headers={"X-Consumer-Id": "consumer_allowed", "X-QuizBank-API-Key": "test_api_key"},
    )


if __name__ == "__main__":
    unittest.main()
