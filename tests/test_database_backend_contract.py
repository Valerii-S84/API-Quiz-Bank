from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import database_connection, database_runtime  # noqa: E402
from quizbank_mvp.database_connection import (  # noqa: E402
    PostgreSQLConnection,
    connect_postgresql,
    decode_json_field,
    translate_sqlite_placeholders,
)


class DatabaseBackendContractTests(unittest.TestCase):
    def test_postgresql_adapter_translates_positional_placeholders(self) -> None:
        sql = "SELECT * FROM consumers WHERE consumer_id = ? AND status = ?"

        translated = translate_sqlite_placeholders(sql, ("consumer", "active"))

        self.assertEqual(
            translated,
            "SELECT * FROM consumers WHERE consumer_id = %s AND status = %s",
        )

    def test_postgresql_adapter_translates_named_placeholders(self) -> None:
        sql = "INSERT INTO consumers (consumer_id, status) VALUES (:consumer_id, :status)"

        translated = translate_sqlite_placeholders(
            sql,
            {"consumer_id": "consumer", "status": "active"},
        )

        self.assertEqual(
            translated,
            "INSERT INTO consumers (consumer_id, status) VALUES (%(consumer_id)s, %(status)s)",
        )

    def test_postgresql_adapter_leaves_sql_without_parameters_unchanged(self) -> None:
        self.assertEqual(translate_sqlite_placeholders("SELECT 1"), "SELECT 1")

    def test_postgresql_connect_wraps_psycopg_connection(self) -> None:
        raw_connection = FakeRawConnection()
        fake_psycopg = types.ModuleType("psycopg")
        fake_rows = types.ModuleType("psycopg.rows")
        fake_rows.dict_row = object()

        def connect(database_url: str, row_factory: object) -> FakeRawConnection:
            raw_connection.connect_args = (database_url, row_factory)
            return raw_connection

        fake_psycopg.connect = connect
        with mock.patch.dict(sys.modules, {"psycopg": fake_psycopg, "psycopg.rows": fake_rows}):
            wrapped = connect_postgresql("postgresql://quizbank")

        self.assertIsInstance(wrapped, PostgreSQLConnection)
        self.assertEqual(raw_connection.connect_args[0], "postgresql://quizbank")

    def test_postgresql_connection_wrapper_translates_and_closes(self) -> None:
        raw_connection = FakeRawConnection()

        with PostgreSQLConnection(raw_connection) as connection:
            connection.execute("SELECT * FROM consumers WHERE consumer_id = ?", ("consumer",))
            connection.executescript("SELECT 1")
            connection.rollback()

        self.assertTrue(raw_connection.entered)
        self.assertTrue(raw_connection.closed)
        self.assertTrue(raw_connection.rolled_back)
        self.assertEqual(raw_connection.executed[0][0], "SELECT * FROM consumers WHERE consumer_id = %s")
        self.assertEqual(raw_connection.executed[1][0], "SELECT 1")

    def test_environment_database_url_uses_postgresql_runtime_paths(self) -> None:
        with mock.patch.dict(os.environ, {"QUIZBANK_DATABASE_URL": "postgresql://quizbank"}):
            with mock.patch.object(
                database_connection,
                "connect_postgresql",
                return_value="postgresql_connection",
            ):
                self.assertEqual(database_connection.connect(), "postgresql_connection")
            with mock.patch.object(database_runtime, "initialize_postgresql_database") as initialize_postgresql:
                self.assertEqual(database_runtime.initialize_database(), "postgresql")
            with mock.patch.object(database_runtime, "postgresql_is_ready", return_value=True):
                self.assertTrue(database_runtime.database_is_ready())
        initialize_postgresql.assert_called_once_with()

    def test_initialize_postgresql_database_applies_only_missing_migrations(self) -> None:
        connection = FakeMigrationConnection(applied_migrations={"001_seen.sql"})
        with tempfile.TemporaryDirectory() as directory:
            migration_directory = Path(directory)
            (migration_directory / "001_seen.sql").write_text("SELECT 'seen';", encoding="utf-8")
            (migration_directory / "002_new.sql").write_text("SELECT 'new';", encoding="utf-8")

            with mock.patch.object(database_runtime, "POSTGRESQL_MIGRATIONS_DIRECTORY", migration_directory):
                with mock.patch.object(database_runtime, "connect", return_value=connection):
                    database_runtime.initialize_postgresql_database()

        self.assertEqual(connection.scripts, ["SELECT 'new';"])
        self.assertIn(("insert_migration", "002_new.sql"), connection.events)

    def test_postgresql_readiness_reports_success_and_connection_failure(self) -> None:
        ready_connection = FakeReadyConnection(
            [
                {"name": "quiz_items"},
                {"name": "consumers"},
                {"name": "api_credentials"},
                {"name": "admin_credentials"},
                {"name": "consumer_admin_profiles"},
                {"name": "deliveries"},
                {"name": "selection_decisions"},
                {"name": "quiz_item_image_quality_policy"},
            ]
        )
        with mock.patch.object(database_runtime, "connect", return_value=ready_connection):
            self.assertTrue(database_runtime.postgresql_is_ready())
        with mock.patch.object(database_runtime, "connect", return_value=FailingContext()):
            self.assertFalse(database_runtime.postgresql_is_ready())

    def test_decode_json_field_accepts_already_decoded_values(self) -> None:
        self.assertEqual(decode_json_field({"status": "ready"}), {"status": "ready"})
        self.assertEqual(decode_json_field(["A2"]), ["A2"])


class FakeRawConnection:
    def __init__(self) -> None:
        self.connect_args: tuple[object, ...] = ()
        self.executed: list[tuple[str, object]] = []
        self.entered = False
        self.closed = False
        self.rolled_back = False

    def __enter__(self) -> "FakeRawConnection":
        self.entered = True
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    def execute(self, sql: str, parameters: object = None) -> None:
        self.executed.append((sql, parameters))

    def rollback(self) -> None:
        self.rolled_back = True


class FakeResult:
    def __init__(self, row: dict[str, str] | None = None, rows: list[dict[str, str]] | None = None) -> None:
        self.row = row
        self.rows = rows or []

    def fetchone(self) -> dict[str, str] | None:
        return self.row

    def fetchall(self) -> list[dict[str, str]]:
        return self.rows


class FakeMigrationConnection:
    def __init__(self, applied_migrations: set[str]) -> None:
        self.applied_migrations = applied_migrations
        self.scripts: list[str] = []
        self.events: list[tuple[str, str]] = []

    def __enter__(self) -> "FakeMigrationConnection":
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        return None

    def execute(self, sql: str, parameters: object = None) -> FakeResult:
        if "SELECT migration_id" in sql:
            migration_id = parameters[0]
            row = {"migration_id": migration_id} if migration_id in self.applied_migrations else None
            return FakeResult(row=row)
        if "INSERT INTO schema_migrations" in sql:
            self.events.append(("insert_migration", parameters[0]))
        return FakeResult()

    def executescript(self, script: str) -> None:
        self.scripts.append(script)


class FakeReadyConnection:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def __enter__(self) -> "FakeReadyConnection":
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        return None

    def execute(self, _sql: str) -> FakeResult:
        return FakeResult(rows=self.rows)


class FailingContext:
    def __enter__(self) -> object:
        raise RuntimeError("connection failed")

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
