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

from quizbank_mvp import database_connection, database_runtime, selection as selection_module  # noqa: E402
from quizbank_mvp.database_connection import (  # noqa: E402
    PostgreSQLConnection,
    PostgreSQLUnsupportedSQLError,
    connect_postgresql,
    decode_json_field,
    translate_sqlite_placeholders,
)
from quizbank_mvp.selection_decision_log import (  # noqa: E402
    insert_selection_decision,
    success_decision,
)
from quizbank_mvp.selection_delivery import create_delivery  # noqa: E402
from quizbank_mvp.selection_diagnostics import candidate_count  # noqa: E402
from quizbank_mvp.selection_eligibility import find_eligible_item  # noqa: E402
from quizbank_mvp.selection_models import ContentScope, SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection_quota import reserve_quota  # noqa: E402
from quizbank_mvp.selection_queue_filler import refill_prepared_selection_queues  # noqa: E402
from quizbank_mvp.selection_scope_enforcement import (  # noqa: E402
    load_active_consumer,
    load_active_entitlement,
)
from quizbank_mvp import telegram_result_repository  # noqa: E402
from quizbank_mvp.telegram_models import TelegramDeliveryResult  # noqa: E402


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

    def test_postgresql_adapter_rejects_sqlite_only_sql(self) -> None:
        with PostgreSQLConnection(FakeRawConnection()) as connection:
            for sql in [
                "PRAGMA foreign_keys = ON",
                "SELECT name FROM sqlite_master WHERE type = 'table'",
                "INSERT OR REPLACE INTO consumers (consumer_id) VALUES (?)",
                "SELECT last_insert_rowid()",
            ]:
                with self.subTest(sql=sql):
                    with self.assertRaises(PostgreSQLUnsupportedSQLError):
                        connection.execute(sql, ("value",))

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
                {"name": "languages"},
                {"name": "content_banks"},
                {"name": "content_bank_versions"},
                {"name": "content_bank_activation_events"},
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

    def test_postgresql_selection_runtime_paths_use_supported_sql(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection()
        request = SelectionRequest(
            "consumer_pg",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            selection_strategy="first_eligible",
        )

        with PostgreSQLConnection(raw_connection) as connection:
            consumer = load_active_consumer(connection, request.consumer_id)
            entitlement = load_active_entitlement(connection, request)
            quota_usage = reserve_quota(connection, consumer, request)
            total = candidate_count(connection, request)
            item, eligible_count = find_eligible_item(connection, request)
            delivery = create_delivery(connection, request, item, entitlement, quota_usage)
            decision = success_decision("selreq_pg", request, delivery, item, total, eligible_count, {})
            insert_selection_decision(connection, decision)

        executed_sql = raw_connection.executed_sql()
        self.assertNotIn("?", executed_sql)
        self.assertNotIn(":selection_request_id", executed_sql)
        self.assertIn("%(selection_request_id)s", executed_sql)
        self.assertIn("LEFT JOIN consumer_delivery_state state_repeat", executed_sql)
        self.assertNotIn("LEFT JOIN deliveries d_repeat", executed_sql)
        self.assertIn("LIMIT %s", executed_sql)
        self.assertNotIn("GROUP BY quiz_item_id", executed_sql)
        self.assertNotIn("d_all", executed_sql)
        self.assertNotIn("d_last", executed_sql)
        self.assertNotIn("d_cell", executed_sql)
        self.assertPostgreSQLBoundary(executed_sql)

    def test_postgresql_next_item_keeps_state_reads_out_of_quota_write_scope(self) -> None:
        read_connection = FakePostgreSQLRuntimeConnection()
        write_connection = FakePostgreSQLRuntimeConnection()
        connections = iter(
            [
                PostgreSQLConnection(read_connection),
                PostgreSQLConnection(write_connection),
            ]
        )
        request = SelectionRequest(
            "consumer_pg",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
        )

        with mock.patch.object(selection_module, "connect", side_effect=lambda _db_path: next(connections)):
            result = selection_module.select_next_item(None, request)

        read_sql = read_connection.executed_sql()
        write_sql = write_connection.executed_sql()
        self.assertEqual(result["delivery"]["consumer_id"], "consumer_pg")
        self.assertIn("FROM consumer_delivery_state", read_sql)
        self.assertNotIn("FROM deliveries", read_sql)
        self.assertNotIn("INSERT INTO quota_usage", read_sql)
        self.assertIn("INSERT INTO quota_usage", write_sql)
        self.assertIn("INSERT INTO consumer_delivery_state", write_sql)
        self.assertNotIn("FROM deliveries", write_sql)
        self.assertPostgreSQLBoundary(read_sql + "\n" + write_sql)

    def test_postgresql_telegram_result_runtime_path_uses_supported_sql(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection()
        result = TelegramDeliveryResult(
            delivery_id="deliv_pg",
            consumer_id="consumer_pg",
            quiz_item_id="item_pg",
            mode="dry_run",
            status="sent",
            telegram_target_ref="***1234",
            telegram_message_id="msg_pg",
            telegram_poll_id="poll_pg",
        )

        with mock.patch.object(
            telegram_result_repository,
            "connect",
            return_value=PostgreSQLConnection(raw_connection),
        ):
            telegram_result_repository.record_telegram_result(None, result)

        executed_sql = raw_connection.executed_sql()
        self.assertNotIn("?", executed_sql)
        self.assertIn("ON CONFLICT(delivery_id) DO UPDATE SET", executed_sql)
        self.assertPostgreSQLBoundary(executed_sql)

    def assertPostgreSQLBoundary(self, executed_sql: str) -> None:
        self.assertNotIn("sqlite_master", executed_sql)
        self.assertNotIn("PRAGMA", executed_sql)
        self.assertNotIn("INSERT OR REPLACE", executed_sql)
        self.assertNotIn("last_insert_rowid", executed_sql)


class QueueFillerDatabaseBackendContractTests(unittest.TestCase):
    def test_postgresql_queue_filler_runtime_path_uses_supported_sql(self) -> None:
        raw_connection = FakePostgreSQLRuntimeConnection()
        request = SelectionRequest(
            "consumer_pg",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            content_scope=ContentScope(
                language_code="de",
                content_bank_id="german-core",
                bank_version_id="german-core:2026-06-12-baseline",
            ),
        )

        with PostgreSQLConnection(raw_connection) as connection:
            results = refill_prepared_selection_queues(connection, request)

        executed_sql = raw_connection.executed_sql()
        self.assertEqual(len(results), 1)
        self.assertNotIn("?", executed_sql)
        self.assertIn("FROM candidate_pool_items cpi", executed_sql)
        self.assertIn("LEFT JOIN consumer_delivery_state state", executed_sql)
        self.assertIn("INSERT INTO selection_queue_items", executed_sql)
        self.assertNotIn("GROUP BY", executed_sql)
        self.assertPostgreSQLBoundary(executed_sql)

    def assertPostgreSQLBoundary(self, executed_sql: str) -> None:
        self.assertNotIn("sqlite_master", executed_sql)
        self.assertNotIn("PRAGMA", executed_sql)
        self.assertNotIn("INSERT OR REPLACE", executed_sql)
        self.assertNotIn("last_insert_rowid", executed_sql)


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


class FakePostgreSQLRuntimeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, object]] = []
        self.closed = False
        self.inserted_queue_items = 0

    def __enter__(self) -> "FakePostgreSQLRuntimeConnection":
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        return None

    def close(self) -> None:
        self.closed = True

    def execute(self, sql: str, parameters: object = None) -> FakeResult:
        self.executed.append((sql, parameters))
        if "SELECT * FROM selection_queues WHERE queue_id = %s" in sql:
            return FakeResult()
        if "SELECT COUNT(*) AS count" in sql and "FROM selection_queue_items" in sql:
            return FakeResult(row={"count": self.inserted_queue_items})
        if "FROM candidate_pool_items cpi" in sql:
            return FakeResult(rows=[postgresql_queue_candidate_row()])
        if "SELECT COALESCE(MAX(position), -1) + 1 AS next_position" in sql:
            return FakeResult(row={"next_position": self.inserted_queue_items})
        if "INSERT INTO selection_queue_items" in sql:
            self.inserted_queue_items += 1
            return FakeResult()
        if "FROM consumers WHERE consumer_id = %s" in sql:
            return FakeResult(row=postgresql_consumer_row())
        if "FROM entitlements" in sql:
            return FakeResult(row=postgresql_entitlement_row())
        if "FROM languages WHERE code = %s" in sql:
            return FakeResult(row={"code": "de", "is_active": True})
        if "FROM content_banks cb" in sql:
            return FakeResult(row=postgresql_content_scope_row())
        if "INSERT INTO quota_usage" in sql:
            return FakeResult(row={"quota_usage_id": "quota_pg", "used_count": 1, "quota_limit": 10})
        if "SELECT COUNT(*) AS count" in sql:
            return FakeResult(row={"count": 1})
        if "SELECT qi.*" in sql:
            return FakeResult(rows=[postgresql_quiz_item_row()])
        if "SELECT * FROM deliveries WHERE delivery_id = %s" in sql:
            return FakeResult(row=postgresql_delivery_row())
        return FakeResult()

    def executed_sql(self) -> str:
        return "\n".join(sql for sql, _parameters in self.executed)


def postgresql_consumer_row() -> dict[str, object]:
    return {
        "consumer_id": "consumer_pg",
        "status": "active",
        "daily_quota_limit": 10,
        "allowed_cefr_levels_json": '["A2"]',
        "allowed_theme_ids_json": '["T10"]',
    }


def postgresql_entitlement_row() -> dict[str, object]:
    return {
        "entitlement_id": "entitlement_pg",
        "consumer_id": "consumer_pg",
        "feature": "quiz_delivery",
        "status": "active",
        "allowed_cefr_levels_json": '["A2"]',
        "allowed_theme_ids_json": '["T10"]',
    }


def postgresql_quiz_item_row() -> dict[str, object]:
    return {
        "item_id": "item_pg",
        "language": "de",
        "language_code": "de",
        "content_bank_id": "german-core",
        "bank_version_id": "german-core:2026-06-12-baseline",
        "status": "approved",
        "source_id": "source_pg",
        "resolved_source_type": "fixture",
        "resolved_provenance_note": "contract path",
        "sublevel": "A2",
        "theme_id": "T10",
        "objective_id": "O02",
        "pattern_id": "P01",
        "prompt": "",
        "stem_text": "Contract projection stem.",
        "options_json": '["eins", "zwei"]',
        "answer_key": "0",
        "explanation": "Because.",
        "delivery_count": 0,
        "last_delivered_at": "",
        "cell_delivery_count": 0,
        "quality_score": 1.0,
    }


def postgresql_content_scope_row() -> dict[str, object]:
    return {
        "language_code": "de",
        "content_bank_id": "german-core",
        "bank_version_id": "german-core:2026-06-12-baseline",
    }


def postgresql_delivery_row() -> dict[str, object]:
    return {
        "delivery_id": "deliv_pg",
        "consumer_id": "consumer_pg",
        "quiz_item_id": "item_pg",
        "item_status": "approved",
        "language_code": "de",
        "content_bank_id": "german-core",
        "bank_version_id": "german-core:2026-06-12-baseline",
        "delivery_status": "created",
        "selected_at": "2026-05-25T00:00:00Z",
        "selection_reason_summary": "eligible_by_status",
    }


def postgresql_queue_candidate_row() -> dict[str, object]:
    return {
        "pool_id": "pool_pg",
        "item_id": "item_pg",
        "rank_position": 0,
        "sublevel": "A2",
        "theme_id": "T10",
        "objective_id": "O02",
        "pattern_id": "P01",
        "delivery_count": 0,
        "last_delivered_at": "",
    }


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
