#!/usr/bin/env python3
"""Run the reproducible MVP API demo against an isolated SQLite database."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from quizbank_mvp.app import create_app
from quizbank_mvp.database import initialize_database, seed_demo_state


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


def prepare_client(directory: str) -> TestClient:
    db_path = Path(directory) / "mvp_demo.sqlite3"
    fixture = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
    initialize_database(db_path)
    seed_demo_state(db_path, fixture)
    return TestClient(create_app(db_path))


def post_next_item(client: TestClient, consumer_id: str, payload: dict[str, object]):
    return client.post(
        "/v1/quiz-items/next",
        json={**payload, "consumer_id": consumer_id},
        headers={"X-Consumer-Id": consumer_id, "X-API-Key": DEMO_API_KEYS[consumer_id]},
    )


def run_demo_steps(client: TestClient) -> None:
    print_step("health", client.get("/health").json())
    print_step("ready", client.get("/ready").json())

    first = post_next_item(client, "consumer_demo", DEMO_REQUEST)
    print_step("next_item", first.json())

    delivery_id = first.json()["delivery_id"]
    delivery = client.get(
        f"/v1/deliveries/{delivery_id}",
        headers={
            "X-Consumer-Id": "consumer_demo",
            "X-API-Key": DEMO_API_KEYS["consumer_demo"],
        },
    )
    print_step("delivery_log", delivery.json())
    print_step("repeat_denial", post_next_item(client, "consumer_demo", DEMO_REQUEST).json())
    print_step(
        "quota_denial",
        post_next_item(client, "consumer_quota_blocked", DEMO_REQUEST).json(),
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        run_demo_steps(prepare_client(directory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
