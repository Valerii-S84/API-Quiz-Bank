#!/usr/bin/env python3
"""Run the local pre-pilot readiness dry run."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from quizbank_mvp.app import create_app
from quizbank_mvp.candidate_pool_builder import rebuild_candidate_pools
from quizbank_mvp.database import (
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    transition_consumer_status,
)
from quizbank_mvp.selection_models import SelectionFilters, SelectionRequest
from quizbank_mvp.selection_queue_filler import refill_selection_queue_for_request


REPORT_PATH = ROOT / "reports" / "pre_pilot" / "local_pre_pilot_dry_run_2026-05-08.md"
FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
REQUEST = {"consumer_id": "consumer_lifecycle", "cefr_level": "A2", "theme_ids": ["T10"]}
API_KEYS = {
    "consumer_lifecycle": "lifecycle_api_key",
    "consumer_quota_blocked": "quota_blocked_api_key",
}


def post_next_item(client: TestClient, consumer_id: str) -> dict[str, Any]:
    response = client.post(
        "/v1/quiz-items/next",
        json={**REQUEST, "consumer_id": consumer_id},
        headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": API_KEYS[consumer_id]},
    )
    payload = response.json()
    return {
        "status_code": response.status_code,
        "reason_code": payload.get("reason_code"),
        "delivery_created": "delivery_id" in payload,
    }


def post_invalid_key(client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/v1/quiz-items/next",
        json=REQUEST,
        headers={"X-Consumer-Id": "consumer_lifecycle", "X-QuizBank-API-Key": "invalid_key"},
    )
    payload = response.json()
    return {"status_code": response.status_code, "reason_code": payload.get("reason_code")}


def consumer_status(db_path: Path, consumer_id: str) -> str:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT status FROM consumers WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
    if row is None:
        raise AssertionError(f"consumer missing: {consumer_id}")
    return str(row["status"])


def prepare_database(db_path: Path) -> None:
    initialize_database(db_path)
    seed_control_fixture(db_path, FIXTURE, "approved")
    seed_consumer(db_path, "consumer_lifecycle", 2, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_lifecycle", API_KEYS["consumer_lifecycle"])
    seed_entitlement(db_path, "consumer_lifecycle", ["A2"], ["T10"])
    seed_consumer(db_path, "consumer_quota_blocked", 0, ["A2"], ["T10"])
    seed_api_credential(db_path, "consumer_quota_blocked", API_KEYS["consumer_quota_blocked"])
    seed_entitlement(db_path, "consumer_quota_blocked", ["A2"], ["T10"])
    warm_queue(db_path, "consumer_lifecycle")


def warm_queue(db_path: Path, consumer_id: str) -> None:
    rebuild_candidate_pools(db_path)
    refill_selection_queue_for_request(
        db_path,
        SelectionRequest(
            consumer_id=consumer_id,
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
        ),
    )


def run_lifecycle(db_path: Path, client: TestClient) -> dict[str, Any]:
    states = [consumer_status(db_path, "consumer_lifecycle")]
    transition_consumer_status(db_path, "consumer_lifecycle", "suspended", "local_admin", "dry run")
    states.append(consumer_status(db_path, "consumer_lifecycle"))
    suspended = post_next_item(client, "consumer_lifecycle")
    transition_consumer_status(db_path, "consumer_lifecycle", "blocked", "local_admin", "dry run")
    states.append(consumer_status(db_path, "consumer_lifecycle"))
    blocked = post_next_item(client, "consumer_lifecycle")
    transition_consumer_status(db_path, "consumer_lifecycle", "active", "local_admin", "dry run")
    states.append(consumer_status(db_path, "consumer_lifecycle"))
    allowed = post_next_item(client, "consumer_lifecycle")
    return {
        "states": states,
        "suspended_denial": suspended,
        "blocked_denial": blocked,
        "reactivated_allowed": allowed,
    }


def audit_summary(db_path: Path) -> dict[str, Any]:
    with connect(db_path) as connection:
        transitions = connection.execute(
            """
            SELECT from_status, to_status FROM audit_log
            WHERE entity_type = 'consumer'
            ORDER BY rowid
            """
        ).fetchall()
        delivery_count = connection.execute("SELECT COUNT(*) AS count FROM deliveries").fetchone()
    return {
        "consumer_transitions": [f"{row['from_status']}->{row['to_status']}" for row in transitions],
        "delivery_count": int(delivery_count["count"]),
    }


def run_dry_run(report_path: Path | None = REPORT_PATH) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        db_path = Path(directory) / "pre_pilot.sqlite3"
        prepare_database(db_path)
        client = TestClient(create_app(db_path))
        report = {
            "health": client.get("/health").json()["status"],
            "ready": client.get("/ready").json()["status"],
            "consumer_lifecycle": run_lifecycle(db_path, client),
            "auth_behavior": post_invalid_key(client),
            "repeat_behavior": post_next_item(client, "consumer_lifecycle"),
            "quota_behavior": post_next_item(client, "consumer_quota_blocked"),
            "audit_summary": audit_summary(db_path),
            "observability_events": [
                "health",
                "ready",
                "consumer_status_transition",
                "delivery_created",
                "auth_denial",
                "selection_denial",
                "quota_denial",
            ],
        }
    if report_path is not None:
        write_report(report_path, report)
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(report), encoding="utf-8")


def render_report(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Local Pre-Pilot Dry Run Evidence",
            "",
            "Date: 2026-05-08",
            "",
            "Scope: local only; no pilot, beta, production or external send.",
            "",
            "## Result",
            "",
            "```json",
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Limitation",
            "",
            "This proves local pre-pilot behavior only. It is not external pilot,",
            "public beta or production readiness evidence.",
            "",
        ]
    )


def main() -> int:
    report = run_dry_run()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
