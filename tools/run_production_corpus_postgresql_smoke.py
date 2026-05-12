#!/usr/bin/env python3
"""Smoke-test the promoted production corpus in an ephemeral PostgreSQL runtime."""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from fastapi.testclient import TestClient

from quizbank_common import NORMAL_DELIVERY_STATUSES, THEME_TITLES, load_inventory
from quizbank_mvp.auth import hash_api_key, api_key_prefix
from quizbank_mvp.database import (
    connect,
    initialize_database,
    seed_consumer,
    seed_entitlement,
    upsert_quiz_item,
    utc_now,
)


POSTGRES_IMAGE = "postgres:16-alpine"
DATABASE_NAME = "postgres"
DEFAULT_REPORT_PATH = Path("reports/imports/production_corpus_postgresql_smoke_2026-05-11.json")
DEFAULT_EXECUTED_AT = "2026-05-11T00:00:00Z"
SMOKE_CONSUMER_ID = "production_corpus_smoke"
SMOKE_API_KEY = "production_corpus_smoke_api_key"
QUOTA_CONSUMER_ID = "production_corpus_quota_blocked"
QUOTA_API_KEY = "production_corpus_quota_blocked_api_key"


class PostgreSQLProductionSmokeError(RuntimeError):
    """Raised when the production corpus PostgreSQL smoke cannot complete."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the promoted corpus into ephemeral PostgreSQL and exercise the API."
    )
    parser.add_argument("--quizbank-dir", default="QuizBank", type=Path)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--executed-at", default=DEFAULT_EXECUTED_AT)
    return parser.parse_args()


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)


def start_container() -> str:
    if shutil.which("docker") is None:
        raise PostgreSQLProductionSmokeError("docker_not_available")
    container_name = f"api-quiz-bank-production-corpus-{uuid.uuid4().hex[:12]}"
    run_command(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            container_name,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-p",
            "127.0.0.1::5432",
            POSTGRES_IMAGE,
        ]
    )
    return container_name


def wait_for_database(container_name: str) -> None:
    for _ in range(30):
        result = subprocess.run(
            ["docker", "exec", container_name, "pg_isready", "-U", "postgres", "-d", DATABASE_NAME],
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise PostgreSQLProductionSmokeError("postgres_not_ready")


def mapped_port(container_name: str) -> str:
    output = run_command(["docker", "port", container_name, "5432/tcp"]).stdout.strip()
    if not output:
        raise PostgreSQLProductionSmokeError("postgres_port_not_mapped")
    return output.rsplit(":", 1)[1]


def database_url(port: str) -> str:
    return f"postgresql://postgres:postgres@127.0.0.1:{port}/{DATABASE_NAME}"


def validate_promoted_inventory(inventory) -> None:
    status_counts = Counter(row.get("status", "").strip() for row in inventory.rows)
    if inventory.active_row_count == 0:
        raise PostgreSQLProductionSmokeError("empty_corpus")
    if status_counts.get("published", 0) != inventory.active_row_count:
        raise PostgreSQLProductionSmokeError(f"corpus_not_fully_published:{dict(status_counts)}")


def seed_sources_and_items(inventory) -> None:
    source_ids_by_filename = {
        source.filename: source.source_id
        for source in inventory.active_sources
    }
    with connect(None) as connection:
        for source in inventory.active_sources:
            connection.execute(
                """
                INSERT INTO sources (
                    source_id, source_type, provenance_note, checksum_sha256, status, created_at
                ) VALUES (?, ?, ?, ?, 'active', ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    source_type = excluded.source_type,
                    provenance_note = excluded.provenance_note,
                    checksum_sha256 = excluded.checksum_sha256,
                    status = excluded.status
                """,
                (
                    source.source_id,
                    "quizbank_csv",
                    f"production_promotion:QuizBank/{source.filename}",
                    source.checksum_sha256,
                    utc_now(),
                ),
            )
        for filename, rows in inventory.rows_by_file.items():
            source_id = source_ids_by_filename[filename]
            for row in rows:
                upsert_quiz_item(connection, runtime_item(row), row["status"], source_id)


def runtime_item(row: dict[str, str]) -> dict[str, str]:
    item = dict(row)
    item["options"] = json.dumps(parse_options(row["options"]), ensure_ascii=False)
    return item


def parse_options(raw_options: str) -> list[object]:
    try:
        parsed = json.loads(raw_options)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_options)
    if not isinstance(parsed, list):
        raise ValueError("options_not_list")
    return parsed


def seed_smoke_consumers() -> None:
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    themes = list(THEME_TITLES)
    seed_consumer(None, SMOKE_CONSUMER_ID, 2, levels, themes)
    seed_api_credential(SMOKE_CONSUMER_ID, SMOKE_API_KEY)
    seed_entitlement(None, SMOKE_CONSUMER_ID, levels, themes, reason="production corpus smoke")
    seed_consumer(None, QUOTA_CONSUMER_ID, 0, levels, themes)
    seed_api_credential(QUOTA_CONSUMER_ID, QUOTA_API_KEY)
    seed_entitlement(None, QUOTA_CONSUMER_ID, levels, themes, reason="production corpus quota smoke")


def seed_api_credential(consumer_id: str, raw_api_key: str) -> None:
    with connect(None) as connection:
        connection.execute(
            """
            INSERT INTO api_credentials (
                credential_id, consumer_id, key_prefix, key_hash, status,
                created_at, revoked_at
            ) VALUES (?, ?, ?, ?, 'active', ?, NULL)
            ON CONFLICT(credential_id) DO UPDATE SET
                key_prefix = excluded.key_prefix,
                key_hash = excluded.key_hash,
                status = excluded.status,
                revoked_at = NULL
            """,
            (
                f"cred_{consumer_id}",
                consumer_id,
                api_key_prefix(raw_api_key),
                hash_api_key(raw_api_key),
                utc_now(),
            ),
        )


def post_next_item(client: TestClient, consumer_id: str, api_key: str):
    return client.post(
        "/v1/quiz-items/next",
        json={"consumer_id": consumer_id},
        headers={
            "X-Consumer-Id": consumer_id,
            "X-QuizBank-API-Key": api_key,
        },
    )


def status_counts_query() -> dict[str, int]:
    with connect(None) as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM quiz_items GROUP BY status ORDER BY status"
        ).fetchall()
    return {row["status"]: int(row["count"]) for row in rows}


def scalar_count(sql: str) -> int:
    with connect(None) as connection:
        row = connection.execute(sql).fetchone()
    return int(row["count"])


def run_api_smoke() -> dict[str, object]:
    from quizbank_mvp.app import create_app

    client = TestClient(create_app(None))
    health = client.get("/health")
    ready = client.get("/ready")
    no_key = client.post("/v1/quiz-items/next", json={"consumer_id": SMOKE_CONSUMER_ID})
    first = post_next_item(client, SMOKE_CONSUMER_ID, SMOKE_API_KEY)
    if first.status_code != 200:
        raise PostgreSQLProductionSmokeError(f"next_item_failed:{first.status_code}:{first.text}")
    first_payload = first.json()
    selected_item_id = first_payload["quiz_item"]["id"]
    delivery_id = first_payload["delivery_id"]
    delivery = client.get(
        f"/v1/deliveries/{delivery_id}",
        headers={
            "X-Consumer-Id": SMOKE_CONSUMER_ID,
            "X-QuizBank-API-Key": SMOKE_API_KEY,
        },
    )
    second = post_next_item(client, SMOKE_CONSUMER_ID, SMOKE_API_KEY)
    second_payload = second.json()
    quota = post_next_item(client, QUOTA_CONSUMER_ID, QUOTA_API_KEY)
    mismatch = client.get(
        f"/v1/deliveries/{delivery_id}",
        headers={
            "X-Consumer-Id": QUOTA_CONSUMER_ID,
            "X-QuizBank-API-Key": QUOTA_API_KEY,
        },
    )
    return {
        "health_status": health.status_code,
        "ready_status": ready.status_code,
        "no_key_status": no_key.status_code,
        "next_item_status": first.status_code,
        "selected_item_id": selected_item_id,
        "selected_item_status": first_payload["delivery"]["item_status"],
        "delivery_read_status": delivery.status_code,
        "repeat_control_status": second.status_code,
        "repeat_control_repeated_same_item": (
            second.status_code == 200 and second_payload["quiz_item"]["id"] == selected_item_id
        ),
        "quota_status": quota.status_code,
        "quota_reason_code": quota.json().get("reason_code"),
        "cross_consumer_delivery_status": mismatch.status_code,
        "cross_consumer_reason_code": mismatch.json().get("reason_code"),
    }


def build_report(inventory, executed_at: str, api_smoke: dict[str, object]) -> dict[str, object]:
    status_counts = status_counts_query()
    published_items = status_counts.get("published", 0)
    checks = {
        "quiz_items": scalar_count("SELECT COUNT(*) AS count FROM quiz_items"),
        "published_items": published_items,
        "sources": scalar_count("SELECT COUNT(*) AS count FROM sources"),
        "deliveries": scalar_count("SELECT COUNT(*) AS count FROM deliveries"),
        "selection_decisions": scalar_count("SELECT COUNT(*) AS count FROM selection_decisions"),
        "status_counts": status_counts,
    }
    ok = (
        checks["quiz_items"] == inventory.active_row_count
        and checks["published_items"] == inventory.active_row_count
        and api_smoke["health_status"] == 200
        and api_smoke["ready_status"] == 200
        and api_smoke["no_key_status"] == 401
        and api_smoke["next_item_status"] == 200
        and api_smoke["selected_item_status"] in NORMAL_DELIVERY_STATUSES
        and api_smoke["delivery_read_status"] == 200
        and api_smoke["repeat_control_repeated_same_item"] is False
        and api_smoke["quota_status"] == 429
        and api_smoke["cross_consumer_delivery_status"] in {403, 404}
    )
    return {
        "report_type": "production_corpus_postgresql_smoke",
        "executed_at": executed_at,
        "database": "postgresql",
        "docker_image": POSTGRES_IMAGE,
        "source": {
            "quizbank_dir": "QuizBank",
            "active_bank_files": len(inventory.active_sources),
            "active_rows": inventory.active_row_count,
        },
        "checks": checks,
        "api_smoke": api_smoke,
        "decision": (
            "GO PostgreSQL production corpus smoke"
            if ok
            else "NO-GO PostgreSQL production corpus smoke"
        ),
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    output_path = ROOT / path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_smoke(quizbank_dir: Path, report_out: Path, executed_at: str) -> None:
    inventory = load_inventory(quizbank_dir)
    validate_promoted_inventory(inventory)
    container_name = start_container()
    previous_url = os.environ.get("QUIZBANK_DATABASE_URL")
    try:
        wait_for_database(container_name)
        os.environ["QUIZBANK_DATABASE_URL"] = database_url(mapped_port(container_name))
        initialize_database(None)
        seed_sources_and_items(inventory)
        seed_smoke_consumers()
        api_smoke = run_api_smoke()
        report = build_report(inventory, executed_at, api_smoke)
    finally:
        if previous_url is None:
            os.environ.pop("QUIZBANK_DATABASE_URL", None)
        else:
            os.environ["QUIZBANK_DATABASE_URL"] = previous_url
        subprocess.run(["docker", "stop", container_name], text=True, capture_output=True)
    write_report(report_out, report)


def main() -> int:
    args = parse_args()
    try:
        run_smoke(args.quizbank_dir, args.report_out, args.executed_at)
    except (PostgreSQLProductionSmokeError, subprocess.CalledProcessError) as error:
        print(f"PostgreSQL production corpus smoke failed: {error}")
        return 1
    print(f"PostgreSQL production corpus smoke report written: {args.report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
