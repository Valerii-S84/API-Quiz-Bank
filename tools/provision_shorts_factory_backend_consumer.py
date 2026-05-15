#!/usr/bin/env python3
"""Provision shorts_factory_backend without printing raw credentials."""

from __future__ import annotations

import argparse
import os
import secrets
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_entitlement,
    utc_now,
)
from quizbank_mvp.trusted_delivery import SHORTS_FACTORY_BACKEND_CONSUMER_ID  # noqa: E402


CONSUMER_ID = SHORTS_FACTORY_BACKEND_CONSUMER_ID
DISPLAY_NAME = "Shorts Factory Backend"
CONSUMER_KIND = "api_client"
DAILY_QUOTA_LIMIT = 100
ALLOWED_CEFR_LEVELS = ("A2",)
ALLOWED_THEME_IDS = ("T05",)
DB_PATH = ROOT / "var" / "quizbank_mvp.sqlite3"
SECRET_ENV_PATH = ROOT / "var" / "deployment_env" / "shorts_factory_backend.env"
API_BASE_URL = "http://127.0.0.1:8000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision shorts_factory_backend consumer access.")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--secret-env-out", type=Path, default=SECRET_ENV_PATH)
    parser.add_argument("--api-base-url", default=API_BASE_URL)
    parser.add_argument("--consumer-api-key-env", default="QUIZ_BANK_CONSUMER_API_KEY")
    parser.add_argument("--daily-quota-limit", type=int, default=DAILY_QUOTA_LIMIT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = provision_shorts_factory_backend(args)
    write_secret_env(args.secret_env_out, evidence["env_handoff"]["raw"])
    print(
        "shorts_factory_backend provisioned: "
        f"consumer={CONSUMER_ID}, credential={evidence['credential_masked']}, "
        f"env={args.secret_env_out}"
    )
    return 0


def provision_shorts_factory_backend(args: argparse.Namespace) -> dict[str, Any]:
    raw_api_key = os.environ.get(args.consumer_api_key_env) or generate_secret()
    initialize_database(args.db_path)
    seed_consumer(
        args.db_path,
        CONSUMER_ID,
        int(args.daily_quota_limit),
        ALLOWED_CEFR_LEVELS,
        ALLOWED_THEME_IDS,
    )
    credential_id = seed_api_credential(args.db_path, CONSUMER_ID, raw_api_key)
    entitlement_id = seed_entitlement(
        args.db_path,
        CONSUMER_ID,
        ALLOWED_CEFR_LEVELS,
        ALLOWED_THEME_IDS,
        actor="owner",
        reason="Trusted Shorts Factory backend A2/T05 approved/published quiz delivery",
    )
    upsert_consumer_profile(args.db_path)
    return {
        "consumer_id": CONSUMER_ID,
        "credential_id": credential_id,
        "credential_masked": mask_value(raw_api_key),
        "entitlement_id": entitlement_id,
        "env_handoff": env_handoff(args.api_base_url, raw_api_key),
    }


def upsert_consumer_profile(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO consumer_admin_profiles (
                consumer_id, display_name, consumer_kind, created_by, created_at
            ) VALUES (?, ?, ?, 'owner', ?)
            ON CONFLICT(consumer_id) DO UPDATE SET
                display_name = excluded.display_name,
                consumer_kind = excluded.consumer_kind
            """,
            (CONSUMER_ID, DISPLAY_NAME, CONSUMER_KIND, utc_now()),
        )


def env_handoff(api_base_url: str, raw_api_key: str) -> dict[str, dict[str, str]]:
    raw = {
        "QUIZ_BANK_API_BASE_URL": api_base_url,
        "QUIZ_BANK_CONSUMER_ID": CONSUMER_ID,
        "QUIZ_BANK_CONSUMER_API_KEY": raw_api_key,
    }
    return {"raw": raw, "masked": {key: mask_value(value) for key, value in raw.items()}}


def write_secret_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")


def generate_secret() -> str:
    return f"qb_{secrets.token_urlsafe(24)}_shorts_factory"


def mask_value(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


if __name__ == "__main__":
    raise SystemExit(main())
