from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover - local dependency gate
    psycopg = None
    dict_row = None
    Jsonb = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import database_connection  # noqa: E402
from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.credential_hashing import api_key_prefix, hash_api_key  # noqa: E402
from quizbank_mvp.selection_queue_models import (  # noqa: E402
    QueueScope,
    selection_queue_id,
    selection_queue_item_id,
)


POSTGRES_IMAGE = "postgres:16-alpine"
DATABASE_NAME = "postgres"
LANGUAGE_CODE = "de"
CONTENT_BANK_ID = "german-core"
BANK_VERSION_ID = "german-core:2026-06-12-baseline"
CEFR_LEVEL = "A2"
THEME_ID = "T10"


@unittest.skipUnless(shutil.which("docker"), "Docker is required for PostgreSQL route tests")
@unittest.skipUnless(psycopg is not None, "psycopg is required for PostgreSQL route tests")
class PostgreSQLQuotaReservationRouteTests(unittest.TestCase):
    container_name = ""
    database_url = ""

    @classmethod
    def setUpClass(cls) -> None:
        cls.container_name, cls.database_url = start_postgresql_container()
        apply_schema(cls.container_name)

    @classmethod
    def tearDownClass(cls) -> None:
        database_connection.close_postgresql_pools()
        if cls.container_name:
            subprocess.run(
                ["docker", "stop", cls.container_name],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

    def test_next_route_succeeds_and_records_timestamptz_links_without_fallback(self) -> None:
        consumer_id = unique_id("consumer_success")
        api_key = api_key_for_consumer(consumer_id)
        seed_route_fixture(self.database_url, consumer_id, api_key, quota_limit=5, item_count=1)

        response = next_item_response(self.database_url, consumer_id, api_key)

        self.assertEqual(response.status_code, 200)
        proof = delivery_linkage_proof(self.database_url, consumer_id)
        self.assertEqual(proof["delivery_count"], 1)
        self.assertEqual(proof["queue_linkage_count"], 1)
        self.assertEqual(proof["quota_linkage_count"], 1)
        self.assertEqual(proof["fallback_count"], 0)
        self.assertEqual(proof["claimed_type"], "timestamp with time zone")
        self.assertEqual(proof["finalized_type"], "timestamp with time zone")
        self.assertIsNotNone(proof["claimed_at"])
        self.assertIsNotNone(proof["finalized_at"])
        self.assertIsNotNone(proof["claimed_at"].tzinfo)
        self.assertIsNotNone(proof["finalized_at"].tzinfo)

    def test_quota_exhaustion_returns_429_without_overrunning_hard_limit(self) -> None:
        consumer_id = unique_id("consumer_quota")
        api_key = api_key_for_consumer(consumer_id)
        seed_route_fixture(self.database_url, consumer_id, api_key, quota_limit=1, item_count=2)

        first = next_item_response(self.database_url, consumer_id, api_key)
        second = next_item_response(self.database_url, consumer_id, api_key)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["reason_code"], "QUOTA_EXCEEDED")
        self.assertEqual(delivery_count(self.database_url, consumer_id), 1)
        self.assertLessEqual(used_quota_reservation_count(self.database_url, consumer_id), 1)

    def test_queue_exhaustion_returns_503_without_fallback_or_quota_reservation(self) -> None:
        consumer_id = unique_id("consumer_empty_queue")
        api_key = api_key_for_consumer(consumer_id)
        seed_route_fixture(self.database_url, consumer_id, api_key, quota_limit=5, item_count=0)

        response = next_item_response(self.database_url, consumer_id, api_key)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["reason_code"], "SELECTION_QUEUE_NOT_READY")
        self.assertEqual(delivery_count(self.database_url, consumer_id), 0)
        self.assertEqual(quota_reservation_count(self.database_url, consumer_id), 0)
        self.assertEqual(fallback_count(self.database_url, consumer_id), 0)


def start_postgresql_container() -> tuple[str, str]:
    container_name = f"api-quiz-bank-pg-quota-{uuid.uuid4().hex[:12]}"
    run_command(
        [
            "docker", "run", "--rm", "-d", "--name", container_name,
            "-e", "POSTGRES_PASSWORD=postgres", "-p", "127.0.0.1::5432",
            "-v", f"{ROOT / 'database' / 'postgresql'}:/schema:ro", POSTGRES_IMAGE,
        ]
    )
    wait_for_database(container_name)
    port = mapped_postgresql_port(container_name)
    return container_name, f"postgresql://postgres:postgres@127.0.0.1:{port}/{DATABASE_NAME}"


def wait_for_database(container_name: str) -> None:
    for _ in range(60):
        result = subprocess.run(
            ["docker", "exec", container_name, "pg_isready", "-U", "postgres", "-d", DATABASE_NAME],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("postgres_not_ready")


def mapped_postgresql_port(container_name: str) -> str:
    result = run_command(["docker", "port", container_name, "5432/tcp"])
    return result.stdout.strip().rsplit(":", 1)[1]


def apply_schema(container_name: str) -> None:
    for schema_path in sorted((ROOT / "database" / "postgresql").glob("*.sql")):
        run_command(
            [
                "docker", "exec", "-i", container_name, "psql",
                "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", DATABASE_NAME,
                "-f", f"/schema/{schema_path.name}",
            ]
        )


def seed_route_fixture(
    database_url: str,
    consumer_id: str,
    api_key: str,
    quota_limit: int,
    item_count: int,
) -> None:
    now = "2026-06-17T00:00:00Z"
    source_id = f"source_{consumer_id}"
    queue_id = queue_id_for_consumer(consumer_id)
    with psycopg.connect(database_url) as connection:
        insert_source(connection, source_id, consumer_id, now)
        for index in range(item_count):
            insert_quiz_item(connection, consumer_id, source_id, index, now)
        insert_consumer_bundle(connection, consumer_id, api_key, quota_limit, now)
        if item_count:
            insert_selection_queue(connection, consumer_id, queue_id, item_count, now)


def insert_source(connection, source_id: str, consumer_id: str, now: str) -> None:
    connection.execute(
        """
        INSERT INTO sources (
            source_id, source_type, provenance_note, checksum_sha256,
            status, created_at, language_code, content_bank_id, bank_version_id
        ) VALUES (%s, 'fixture', 'PostgreSQL quota route test', %s, 'active',
                  %s, %s, %s, %s)
        """,
        (source_id, f"checksum_{consumer_id}", now, LANGUAGE_CODE, CONTENT_BANK_ID, BANK_VERSION_ID),
    )


def insert_quiz_item(connection, consumer_id: str, source_id: str, index: int, now: str) -> None:
    connection.execute(
        """
        INSERT INTO quiz_items (
            item_id, source_id, language, language_code, content_bank_id,
            bank_version_id, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt,
            stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        ) VALUES (
            %s, %s, 'de', %s, %s, %s, 'A1-A2', %s, %s, 'appointments',
            'O02', 'P01', 'A1-A2', 'standard_neutral', '',
            %s, %s, '0', 'Fixture explanation.', 'theme:t10',
            'A2::T10::O02::P01', 'published', '1.0', %s, %s,
            %s, 'false', NULL
        )
        """,
        (
            item_id_for_consumer(consumer_id, index), source_id, LANGUAGE_CODE,
            CONTENT_BANK_ID, BANK_VERSION_ID, CEFR_LEVEL, THEME_ID,
            f"PostgreSQL quota fixture stem {index}.",
            Jsonb(["eins", "zwei", "drei", "vier"]), now, now, now,
        ),
    )


def insert_consumer_bundle(connection, consumer_id: str, api_key: str, quota_limit: int, now: str) -> None:
    insert_consumer_row(connection, consumer_id, quota_limit, now)
    insert_api_credential_row(connection, consumer_id, api_key, now)
    insert_entitlement_row(connection, consumer_id, now)


def insert_consumer_row(connection, consumer_id: str, quota_limit: int, now: str) -> None:
    connection.execute(
        """
        INSERT INTO consumers (
            consumer_id, status, allowed_cefr_levels_json,
            allowed_theme_ids_json, daily_quota_limit, created_at,
            default_language_code, default_content_bank_id, default_bank_version_id,
            allowed_language_codes_json, allowed_content_bank_ids_json,
            allowed_bank_version_ids_json
        ) VALUES (%s, 'active', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            consumer_id, Jsonb([CEFR_LEVEL]), Jsonb([THEME_ID]), quota_limit, now,
            LANGUAGE_CODE, CONTENT_BANK_ID, BANK_VERSION_ID, json_text(LANGUAGE_CODE),
            json_text(CONTENT_BANK_ID), json_text(BANK_VERSION_ID),
        ),
    )


def insert_api_credential_row(connection, consumer_id: str, api_key: str, now: str) -> None:
    connection.execute(
        """
        INSERT INTO api_credentials (
            credential_id, consumer_id, key_prefix, key_hash, status, created_at
        ) VALUES (%s, %s, %s, %s, 'active', %s)
        """,
        (f"cred_{consumer_id}", consumer_id, api_key_prefix(api_key), hash_api_key(api_key), now),
    )


def insert_entitlement_row(connection, consumer_id: str, now: str) -> None:
    connection.execute(
        """
        INSERT INTO entitlements (
            entitlement_id, consumer_id, feature, status,
            allowed_cefr_levels_json, allowed_theme_ids_json,
            valid_until, created_at, allowed_language_codes_json,
            allowed_content_bank_ids_json, allowed_bank_version_ids_json
        ) VALUES (%s, %s, 'quiz_delivery', 'active', %s, %s, NULL, %s, %s, %s, %s)
        """,
        (
            f"entitlement_{consumer_id}", consumer_id, Jsonb([CEFR_LEVEL]),
            Jsonb([THEME_ID]), now, json_text(LANGUAGE_CODE),
            json_text(CONTENT_BANK_ID), json_text(BANK_VERSION_ID),
        ),
    )


def insert_selection_queue(
    connection,
    consumer_id: str,
    queue_id: str,
    item_count: int,
    now: str,
) -> None:
    insert_selection_queue_row(connection, consumer_id, queue_id, item_count, now)
    for index in range(item_count):
        insert_selection_queue_item(connection, consumer_id, queue_id, index, now)


def insert_selection_queue_row(connection, consumer_id: str, queue_id: str, item_count: int, now: str) -> None:
    connection.execute(
        """
        INSERT INTO selection_queues (
            queue_id, consumer_id, channel_id, language_code, content_bank_id,
            bank_version_id, cefr_level, theme_id, objective_id, pattern_id,
            queue_status, target_size, available_count, created_at, updated_at
        ) VALUES (%s, %s, 'api', %s, %s, %s, %s, %s, '', '',
                  'ready', 50, %s, %s, %s)
        """,
        (
            queue_id, consumer_id, LANGUAGE_CODE, CONTENT_BANK_ID, BANK_VERSION_ID,
            CEFR_LEVEL, THEME_ID, item_count, now, now,
        ),
    )


def insert_selection_queue_item(connection, consumer_id: str, queue_id: str, index: int, now: str) -> None:
    item_id = item_id_for_consumer(consumer_id, index)
    connection.execute(
        """
        INSERT INTO selection_queue_items (
            queue_item_id, queue_id, pool_id, item_id, position,
            claim_status, score_snapshot_json, created_at, updated_at
        ) VALUES (%s, %s, NULL, %s, %s, 'available', %s, %s, %s)
        """,
        (
            selection_queue_item_id(queue_id, item_id), queue_id, item_id, index,
            Jsonb({"selection_score": {"fixture": 1.0 - (index * 0.01)}}), now, now,
        ),
    )


def next_item_response(database_url: str, consumer_id: str, api_key: str):
    with mock.patch.dict(os.environ, postgresql_test_environment(database_url)):
        return TestClient(create_app()).post(
            "/v1/quiz-items/next",
            json={"consumer_id": consumer_id, "cefr_level": CEFR_LEVEL, "theme_ids": [THEME_ID]},
            headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": api_key},
        )


def delivery_linkage_proof(database_url: str, consumer_id: str) -> dict[str, object]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        row = connection.execute(
            """
            SELECT COUNT(DISTINCT d.delivery_id) AS delivery_count,
                   COUNT(DISTINCT sqi.queue_item_id) AS queue_linkage_count,
                   COUNT(DISTINCT qr.quota_reservation_id) AS quota_linkage_count,
                   COUNT(DISTINCT sd.selection_request_id)
                       FILTER (WHERE sd.fallback_reason_code IS NOT NULL) AS fallback_count,
                   MAX(pg_typeof(qr.claimed_at)::text) AS claimed_type,
                   MAX(pg_typeof(qr.finalized_at)::text) AS finalized_type,
                   MAX(qr.claimed_at) AS claimed_at,
                   MAX(qr.finalized_at) AS finalized_at
            FROM deliveries d
            LEFT JOIN selection_queue_items sqi ON sqi.delivery_id = d.delivery_id
            LEFT JOIN quota_reservations qr ON qr.quota_reservation_id = d.quota_reservation_id
            LEFT JOIN selection_decisions sd ON sd.delivery_id = d.delivery_id
            WHERE d.consumer_id = %s
            """,
            (consumer_id,),
        ).fetchone()
    return dict(row)


def used_quota_reservation_count(database_url: str, consumer_id: str) -> int:
    return scalar(
        database_url,
        """
        SELECT COUNT(*)
        FROM quota_reservations
        WHERE consumer_id = %s AND reservation_status IN ('claimed', 'finalized')
        """,
        consumer_id,
    )


def delivery_count(database_url: str, consumer_id: str) -> int:
    return count_where(database_url, "deliveries", consumer_id)


def quota_reservation_count(database_url: str, consumer_id: str) -> int:
    return count_where(database_url, "quota_reservations", consumer_id)


def fallback_count(database_url: str, consumer_id: str) -> int:
    return scalar(
        database_url,
        """
        SELECT COUNT(*)
        FROM selection_decisions
        WHERE consumer_id = %s AND fallback_reason_code IS NOT NULL
        """,
        consumer_id,
    )


def count_where(database_url: str, table_name: str, consumer_id: str) -> int:
    return scalar(database_url, f"SELECT COUNT(*) FROM {table_name} WHERE consumer_id = %s", consumer_id)


def scalar(database_url: str, sql: str, consumer_id: str) -> int:
    with psycopg.connect(database_url) as connection:
        row = connection.execute(sql, (consumer_id,)).fetchone()
    return int(row[0])


def postgresql_test_environment(database_url: str) -> dict[str, str]:
    return {
        "QUIZBANK_DATABASE_URL": database_url,
        "QUIZBANK_POSTGRES_POOL_ENABLED": "0",
        "QUIZBANK_NEXT_SELECTION_MODE": "",
    }


def queue_id_for_consumer(consumer_id: str) -> str:
    return selection_queue_id(
        QueueScope(
            consumer_id, "api", LANGUAGE_CODE, CONTENT_BANK_ID,
            BANK_VERSION_ID, CEFR_LEVEL, THEME_ID,
        )
    )


def item_id_for_consumer(consumer_id: str, index: int) -> str:
    return f"item_{consumer_id}_{index}"


def api_key_for_consumer(consumer_id: str) -> str:
    return f"{consumer_id}_api_key"


def unique_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def json_text(value: str) -> str:
    return f'["{value}"]'


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
