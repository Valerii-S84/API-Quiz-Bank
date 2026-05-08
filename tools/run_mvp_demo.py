#!/usr/bin/env python3
"""Run the reproducible MVP API demo against an isolated SQLite database."""

from __future__ import annotations

import json
import sys
import tempfile
from csv import DictReader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from quizbank_mvp.app import create_app
from quizbank_mvp.database import connect, initialize_database, seed_demo_state


DEMO_REQUEST = {
    "consumer_id": "consumer_demo",
    "cefr_level": "A2",
    "theme_ids": ["T10"],
}
DEMO_API_KEYS = {
    "consumer_demo": "demo_consumer_api_key",
    "consumer_quota_blocked": "quota_blocked_api_key",
}


def print_step(name: str, payload: object) -> None:
    print(f"\n{name}")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(DictReader(file))


def inventory_summary() -> dict[str, object]:
    rows = read_csv_rows(ROOT / "data" / "manifests" / "file_inventory.csv")
    active_rows = [row for row in rows if row["source_state"] == "active"]
    return {
        "active_sources": len(active_rows),
        "active_rows": sum(int(row["row_count_detected"]) for row in active_rows),
        "manifest": "data/manifests/import_manifest.yml",
    }


def artifact_backed_proof() -> None:
    import_report = read_json(ROOT / "reports" / "imports" / "control_sample_import.json")
    coverage_report = read_json(ROOT / "reports" / "coverage" / "corpus_coverage.json")
    plan_catalog = read_json(ROOT / "data" / "billing" / "plan_catalog.json")
    print_step("source_governance", inventory_summary())
    print_step("canonical_validation", canonical_validation_summary(import_report))
    print_step("analytics_snapshot", analytics_summary(coverage_report))
    print_step("billing_plan_catalog", billing_plan_summary(plan_catalog))


def canonical_validation_summary(report: dict[str, object]) -> dict[str, object]:
    validation = report["validation_summary"]
    if not isinstance(validation, dict):
        raise TypeError("validation_summary must be a dictionary")
    return {
        "import_mode": report["import_mode"],
        "source_id": report["source_id"],
        "row_count_detected": report["row_count_detected"],
        "canonical_item_count": validation["canonical_item_count"],
        "validation_errors": validation["validation_errors"],
    }


def analytics_summary(report: dict[str, object]) -> dict[str, object]:
    return {
        "active_rows": report["source"]["active_rows"],
        "status_counts": report["status_counts"],
        "level_theme_cells": report["gap_summary"]["level_theme_total_cells"],
        "coverage_cell_count": len(report["coverage_cells"]),
    }


def billing_plan_summary(catalog: dict[str, object]) -> dict[str, object]:
    plans = catalog["plans"]
    if not isinstance(plans, list):
        raise TypeError("plans must be a list")
    return {
        "catalog_id": catalog["catalog_id"],
        "plan_codes": [plan["plan_code"] for plan in plans],
        "access_truth": "internal_entitlement",
    }


def prepare_context(directory: str) -> tuple[TestClient, Path]:
    db_path = Path(directory) / "mvp_demo.sqlite3"
    fixture = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
    initialize_database(db_path)
    seed_demo_state(db_path, fixture)
    return TestClient(create_app(db_path)), db_path


def post_next_item(client: TestClient, consumer_id: str, payload: dict[str, object]):
    return client.post(
        "/v1/quiz-items/next",
        json={**payload, "consumer_id": consumer_id},
        headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": DEMO_API_KEYS[consumer_id]},
    )


def run_demo_steps(client: TestClient, db_path: Path) -> None:
    artifact_backed_proof()
    print_step("health", client.get("/health").json())
    print_step("ready", client.get("/ready").json())

    first = post_next_item(client, "consumer_demo", DEMO_REQUEST)
    print_step("next_item", first.json())

    delivery_id = first.json()["delivery_id"]
    delivery = client.get(
        f"/v1/deliveries/{delivery_id}",
        headers={
            "X-Consumer-Id": "consumer_demo",
            "X-QuizBank-API-Key": DEMO_API_KEYS["consumer_demo"],
        },
    )
    print_step("delivery_log", delivery.json())
    print_step("repeat_denial", post_next_item(client, "consumer_demo", DEMO_REQUEST).json())
    print_step(
        "quota_denial",
        post_next_item(client, "consumer_quota_blocked", DEMO_REQUEST).json(),
    )
    print_step("billing_usage_audit", billing_usage_audit(db_path))


def billing_usage_audit(db_path: Path) -> dict[str, object]:
    with connect(db_path) as connection:
        entitlement_count = connection.execute(
            "SELECT COUNT(*) AS count FROM entitlements WHERE status = 'active'"
        ).fetchone()
        grant_audit_count = connection.execute(
            """
            SELECT COUNT(*) AS count FROM audit_log
            WHERE action = 'entitlement_grant'
            """
        ).fetchone()
        quota_count = connection.execute("SELECT COUNT(*) AS count FROM quota_usage").fetchone()
    return {
        "active_entitlements": entitlement_count["count"],
        "entitlement_grant_audits": grant_audit_count["count"],
        "quota_usage_rows": quota_count["count"],
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        client, db_path = prepare_context(directory)
        run_demo_steps(client, db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
