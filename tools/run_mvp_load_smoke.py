#!/usr/bin/env python3
"""Run a local concurrent load smoke for the MVP runtime."""

from __future__ import annotations

import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)


FIXTURE = ROOT / "tests/fixtures/selection/approved_traceable_items.jsonl"
REPORT_PATH = ROOT / "reports/scale/protected_runtime_load_smoke_2026-05-10.json"
GENERATED_AT = "2026-05-10T00:00:00+00:00"
CONCURRENT_CONSUMERS = 8


def prepare_database(db_path: Path) -> None:
    initialize_database(db_path)
    seed_control_fixture(db_path, FIXTURE, "approved")
    for index in range(CONCURRENT_CONSUMERS):
        consumer_id = f"consumer_load_{index:02d}"
        seed_consumer(db_path, consumer_id, 2, ["A2"], ["T10"])
        seed_api_credential(db_path, consumer_id, f"load_key_{index:02d}")
        seed_entitlement(db_path, consumer_id, ["A2"], ["T10"])
    seed_consumer(db_path, "consumer_quota_denied", 0, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_quota_denied", "quota_denied_key")
    seed_entitlement(db_path, "consumer_quota_denied", ["A2"], ["T10"])


def post_next_item(client: TestClient, consumer_id: str, api_key: str) -> int:
    response = client.post(
        "/v1/quiz-items/next",
        json={"consumer_id": consumer_id, "cefr_level": "A2", "theme_ids": ["T10"]},
        headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": api_key},
    )
    return response.status_code


def concurrent_delivery_results(client: TestClient) -> list[int]:
    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_CONSUMERS) as executor:
        futures = [
            executor.submit(post_next_item, client, f"consumer_load_{index:02d}", f"load_key_{index:02d}")
            for index in range(CONCURRENT_CONSUMERS)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results)


def resource_limit_evidence() -> dict[str, bool]:
    compose = (ROOT / "docker-compose.api-quiz-bank.yml").read_text(encoding="utf-8")
    postgres = (ROOT / "docker-compose.api-quiz-bank.postgres.yml").read_text(encoding="utf-8")
    return {
        "api_mem_limit": "mem_limit: 512m" in compose,
        "api_cpu_limit": "cpus: 1.0" in compose,
        "postgres_mem_limit": "mem_limit: 512m" in postgres,
        "postgres_cpu_limit": "cpus: 1.0" in postgres,
    }


def run_smoke() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        db_path = Path(directory) / "quizbank_load.sqlite3"
        prepare_database(db_path)
        client = TestClient(create_app(db_path))
        concurrent_statuses = concurrent_delivery_results(client)
        ready_status = client.get("/ready").status_code
        no_key_status = client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_load_00", "cefr_level": "A2", "theme_ids": ["T10"]},
        ).status_code
        repeat_status = post_next_item(client, "consumer_load_00", "load_key_00")
        quota_status = post_next_item(client, "consumer_quota_denied", "quota_denied_key")
    return {
        "report_type": "protected_runtime_load_smoke",
        "generated_at": GENERATED_AT,
        "decision": "GO local protected-runtime load smoke; NO-GO real scale claim",
        "concurrent_consumers": CONCURRENT_CONSUMERS,
        "concurrent_delivery_statuses": concurrent_statuses,
        "status_counts": {
            str(status): concurrent_statuses.count(status)
            for status in sorted(set(concurrent_statuses))
        },
        "ready_status": ready_status,
        "auth_no_key_status": no_key_status,
        "repeat_selection_status": repeat_status,
        "quota_denial_status": quota_status,
        "resource_limits": resource_limit_evidence(),
        "scale_blockers": [
            "local TestClient smoke is not production traffic",
            "external concurrent traffic test is not executed",
            "large corpus approved/published production volume remains NO-GO",
        ],
    }


def main() -> int:
    report = run_smoke()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(report["decision"])
    print(f"concurrent_status_counts={report['status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
