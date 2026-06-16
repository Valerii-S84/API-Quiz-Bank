from __future__ import annotations

import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import app as app_module  # noqa: E402
from quizbank_mvp import database_connection  # noqa: E402
from quizbank_mvp.credential_hashing import api_key_prefix, hash_api_key  # noqa: E402
from quizbank_mvp.database_connection import PostgreSQLConnection  # noqa: E402
from tests.test_database_backend_contract import (  # noqa: E402
    FakeResult,
    FakePostgreSQLRuntimeConnection,
)

POSTGRESQL_TEST_API_KEY = "postgresql_route_test_api_key"


class NextRoutePostgreSQLConnectionTests(unittest.TestCase):
    def test_next_route_reuses_one_connection_for_auth_and_queue(self) -> None:
        raw_connection = RoutePostgreSQLRuntimeConnection()
        environment = {
            "QUIZBANK_DATABASE_URL": "postgresql://quizbank",
            "QUIZBANK_NEXT_SELECTION_MODE": "",
        }

        with mock.patch.dict(os.environ, environment):
            with mock.patch.object(
                app_module,
                "connect",
                return_value=PostgreSQLConnection(raw_connection),
            ) as connect_mock:
                with mock.patch.object(
                    app_module,
                    "select_next_item",
                    side_effect=AssertionError("live selector should not run"),
                ):
                    response = TestClient(app_module.create_app()).post(
                        "/v1/quiz-items/next",
                        json={
                            "consumer_id": "consumer_pg",
                            "cefr_level": "A2",
                            "theme_ids": ["T10"],
                        },
                        headers={
                            "X-Consumer-Id": "consumer_pg",
                            "X-QuizBank-API-Key": POSTGRESQL_TEST_API_KEY,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(connect_mock.call_count, 1)
        self.assertTrue(raw_connection.closed)
        executed_sql = raw_connection.executed_sql()
        self.assertLess(
            executed_sql.index("FROM api_credentials ac"),
            executed_sql.index("WITH active_consumer AS"),
        )
        self.assertIn("queue_candidates AS MATERIALIZED", executed_sql)


class PostgreSQLPoolConnectionTests(unittest.TestCase):
    def tearDown(self) -> None:
        database_connection.close_postgresql_pools()

    def test_pool_default_max_size_matches_twenty_request_gate(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(database_connection.postgresql_pool_max_size(), 20)

    def test_connect_postgresql_uses_pool_context_when_available(self) -> None:
        fake_psycopg = types.ModuleType("psycopg")
        fake_rows = types.ModuleType("psycopg.rows")
        fake_pool_module = types.ModuleType("psycopg_pool")
        raw_connection = FakePostgreSQLRuntimeConnection()
        fake_rows.dict_row = object()
        fake_pool_module.ConnectionPool = fake_connection_pool(raw_connection)

        with mock.patch.dict(
            sys.modules,
            {"psycopg": fake_psycopg, "psycopg.rows": fake_rows, "psycopg_pool": fake_pool_module},
        ):
            with mock.patch.dict(os.environ, {"QUIZBANK_POSTGRES_POOL_ENABLED": "1"}):
                with database_connection.connect_postgresql("postgresql://pooled") as connection:
                    connection.execute("SELECT 1")

        self.assertFalse(raw_connection.closed)
        self.assertEqual(raw_connection.pool_kwargs["max_size"], 20)
        self.assertEqual(raw_connection.pool_enter_count, 1)
        self.assertEqual(raw_connection.pool_exit_count, 1)
        database_connection.close_postgresql_pools()
        self.assertEqual(raw_connection.pool_close_count, 1)


class RoutePostgreSQLRuntimeConnection(FakePostgreSQLRuntimeConnection):
    def execute(self, sql: str, parameters: object = None) -> FakeResult:
        if "FROM api_credentials ac" in sql:
            self.executed.append((sql, parameters))
            return FakeResult(rows=[postgresql_api_credential_row()])
        return super().execute(sql, parameters)


def postgresql_api_credential_row() -> dict[str, object]:
    return {
        "credential_id": "credential_pg",
        "consumer_id": "consumer_pg",
        "key_prefix": api_key_prefix(POSTGRESQL_TEST_API_KEY),
        "key_hash": hash_api_key(POSTGRESQL_TEST_API_KEY),
        "credential_status": "active",
        "consumer_status": "active",
    }


def fake_connection_pool(raw_connection):
    class FakeConnectionPool:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            raw_connection.pool_kwargs = kwargs

        def connection(self):
            return FakePoolContext(raw_connection)

        def close(self) -> None:
            raw_connection.pool_close_count = getattr(raw_connection, "pool_close_count", 0) + 1

    return FakeConnectionPool


class FakePoolContext:
    def __init__(self, raw_connection: FakePostgreSQLRuntimeConnection) -> None:
        self.raw_connection = raw_connection

    def __enter__(self):
        self.raw_connection.pool_enter_count = getattr(self.raw_connection, "pool_enter_count", 0) + 1
        return self.raw_connection

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.raw_connection.pool_exit_count = getattr(self.raw_connection, "pool_exit_count", 0) + 1


if __name__ == "__main__":
    unittest.main()
