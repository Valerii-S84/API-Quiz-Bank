from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database_connection import PostgreSQLConnection  # noqa: E402
from quizbank_mvp.problems import QuizBankProblem  # noqa: E402
from quizbank_mvp.selection_models import ContentScope, SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_queue_selector import select_next_item_from_queue  # noqa: E402
from tests.test_database_backend_contract import FakePostgreSQLRuntimeConnection  # noqa: E402


class PostgreSQLQueueFastPathConcurrencyTests(unittest.TestCase):
    def test_queue_claim_uses_skip_locked_and_claim_status_guard(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection()

        with mock.patch(
            "quizbank_mvp.selection_queue_selector.connect",
            return_value=PostgreSQLConnection(raw_connection),
        ):
            select_next_item_from_queue(None, request())

        claim_sql = raw_connection.sql_matching("WITH candidate AS")
        self.assertIn("FOR UPDATE OF sqi SKIP LOCKED", claim_sql)
        self.assertIn("AND sqi.claim_status = 'available'", claim_sql)
        self.assertIn("LIMIT 1", claim_sql)
        self.assertIn("JOIN quiz_items qi ON qi.item_id = updated.item_id", claim_sql)

    def test_delivery_finalize_does_not_update_parent_queue_hot_row(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection()

        with mock.patch(
            "quizbank_mvp.selection_queue_selector.connect",
            return_value=PostgreSQLConnection(raw_connection),
        ):
            select_next_item_from_queue(None, request())

        finalize_sql = raw_connection.sql_matching("WITH inserted_delivery AS")
        self.assertIn("UPDATE selection_queue_items", finalize_sql)
        self.assertIn("delivered_queue_item", finalize_sql)
        self.assertIn("SELECT queue_id", finalize_sql)
        self.assertNotIn("UPDATE selection_queues", finalize_sql)

    def test_queue_selector_returns_503_if_delivery_is_not_queue_linked(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection(finalize_delivery_link=False)

        with mock.patch(
            "quizbank_mvp.selection_queue_selector.connect",
            return_value=PostgreSQLConnection(raw_connection),
        ):
            with self.assertRaises(QuizBankProblem) as error:
                select_next_item_from_queue(None, request())

        self.assertEqual(error.exception.status, 503)
        self.assertEqual(error.exception.reason_code, "SELECTION_QUEUE_NOT_READY")
        self.assertIn("RETURNING queue_id", raw_connection.sql_matching("WITH inserted_delivery AS"))


def request() -> SelectionRequest:
    return SelectionRequest(
        "consumer_pg",
        filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
        content_scope=ContentScope(
            language_code="de",
            content_bank_id="german-core",
            bank_version_id="german-core:2026-06-12-baseline",
        ),
    )
