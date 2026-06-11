#!/usr/bin/env python3
"""Create one isolated load-smoke test consumer without printing secrets."""
from __future__ import annotations
import argparse
import json
import os
import secrets
import stat
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.credential_hashing import api_key_prefix, hash_api_key  # noqa: E402
from quizbank_mvp.database_connection import connect, new_id, utc_now  # noqa: E402

REPORT_PATH = ROOT / "reports" / "scale" / "isolated_test_consumer_creation_2026-06-11.json"
DEFAULT_CONSUMER_ID = "load-smoke-test-2026-06-11"
ALLOWED_LEVELS = ("A2",)
ALLOWED_THEMES = ("T10",)
FEATURE = "quiz_delivery"


@dataclass(frozen=True)
class CreationConfig:
    consumer_id: str
    quota_limit: int
    key_out: Path | None
    output: Path
    apply: bool
    valid_days: int


def main() -> int:
    args = parse_args()
    config = CreationConfig(
        consumer_id=args.consumer_id,
        quota_limit=args.daily_quota_limit,
        key_out=args.key_out,
        output=args.output,
        apply=args.apply,
        valid_days=args.valid_days,
    )
    issues = validate_config(config)
    if issues:
        report = preflight_report(config, "stopped_invalid_config", issues)
        emit_report(config.output, report)
        return 1
    if not database_configured():
        report = preflight_report(
            config,
            "stopped_missing_database_connection",
            ["missing:QUIZBANK_DATABASE_URL_OR_DATABASE_URL"],
        )
        emit_report(config.output, report)
        return 1
    report = apply_creation(config) if config.apply else dry_run(config)
    emit_report(config.output, report)
    return 0 if report["creation_status"] in {"created", "dry_run_ready"} else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create isolated load-smoke test consumer.")
    parser.add_argument("--consumer-id", default=DEFAULT_CONSUMER_ID)
    parser.add_argument("--daily-quota-limit", type=int, default=200)
    parser.add_argument("--valid-days", type=int, default=2)
    parser.add_argument("--key-out", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def validate_config(config: CreationConfig) -> list[str]:
    issues: list[str] = []
    if not config.consumer_id.startswith("load-smoke-test-"):
        issues.append("consumer id must start with load-smoke-test-")
    if config.quota_limit < 100:
        issues.append("daily quota limit must be at least 100")
    if config.valid_days < 1 or config.valid_days > 14:
        issues.append("valid-days must be between 1 and 14")
    if config.apply and config.key_out is None:
        issues.append("--key-out is required with --apply")
    if config.apply and not postgresql_database_configured():
        issues.append("--apply requires QUIZBANK_DATABASE_URL or DATABASE_URL")
    if config.key_out is not None and config.key_out.exists():
        issues.append("--key-out target already exists")
    return issues


def database_configured() -> bool:
    return bool(os.getenv("QUIZBANK_DATABASE_URL") or os.getenv("DATABASE_URL") or os.getenv("QUIZBANK_DB_PATH"))
def postgresql_database_configured() -> bool:
    return bool(os.getenv("QUIZBANK_DATABASE_URL") or os.getenv("DATABASE_URL"))


def dry_run(config: CreationConfig) -> dict[str, object]:
    existing = read_existing_state(config.consumer_id)
    status = "blocked_existing_consumer" if existing["consumer_exists"] else "dry_run_ready"
    return report_payload(config, status, existing, None)


def apply_creation(config: CreationConfig) -> dict[str, object]:
    existing = read_existing_state(config.consumer_id)
    if existing["consumer_exists"]:
        return report_payload(config, "blocked_existing_consumer", existing, None)
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    created = write_consumer_rows(config, raw_key)
    write_key_file(config.key_out, raw_key)
    verified = read_existing_state(config.consumer_id)
    return report_payload(config, "created", verified, key_hash, created)


def read_existing_state(consumer_id: str) -> dict[str, object]:
    with connect(None) as connection:
        consumer = connection.execute(
            "SELECT consumer_id, status, daily_quota_limit FROM consumers WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        credential_count = scalar(
            connection,
            "SELECT COUNT(*) AS count FROM api_credentials WHERE consumer_id = ?",
            (consumer_id,),
        )
        entitlement_count = scalar(
            connection,
            "SELECT COUNT(*) AS count FROM entitlements WHERE consumer_id = ? AND feature = ?",
            (consumer_id, FEATURE),
        )
        non_test_count = scalar(
            connection,
            "SELECT COUNT(*) AS count FROM consumers WHERE consumer_id <> ?",
            (consumer_id,),
        )
    return {
        "consumer_exists": consumer is not None,
        "consumer_id": None if consumer is None else str(consumer["consumer_id"]),
        "consumer_status": None if consumer is None else str(consumer["status"]),
        "daily_quota_limit": None if consumer is None else int(consumer["daily_quota_limit"]),
        "credential_count": credential_count,
        "entitlement_count": entitlement_count,
        "non_test_consumer_count": non_test_count,
    }


def write_consumer_rows(config: CreationConfig, raw_key: str) -> dict[str, object]:
    valid_until = (datetime.now(UTC) + timedelta(days=config.valid_days)).replace(microsecond=0).isoformat()
    before = read_existing_state(config.consumer_id)["non_test_consumer_count"]
    with connect(None) as connection:
        connection.execute(
            """
            INSERT INTO consumers (
                consumer_id, status, allowed_cefr_levels_json, allowed_theme_ids_json,
                daily_quota_limit, created_at
            ) VALUES (?, 'active', ?::jsonb, ?::jsonb, ?, ?)
            """,
            (config.consumer_id, json.dumps(ALLOWED_LEVELS), json.dumps(ALLOWED_THEMES), config.quota_limit, utc_now()),
        )
        connection.execute(
            """
            INSERT INTO api_credentials (
                credential_id, consumer_id, key_prefix, key_hash, status, created_at, revoked_at
            ) VALUES (?, ?, ?, ?, 'active', ?, NULL)
            """,
            (f"cred_{config.consumer_id}", config.consumer_id, api_key_prefix(raw_key), hash_api_key(raw_key), utc_now()),
        )
        connection.execute(
            """
            INSERT INTO entitlements (
                entitlement_id, consumer_id, feature, status, allowed_cefr_levels_json,
                allowed_theme_ids_json, valid_until, created_at
            ) VALUES (?, ?, ?, 'active', ?::jsonb, ?::jsonb, ?, ?)
            """,
            (
                f"ent_{config.consumer_id}",
                config.consumer_id,
                FEATURE,
                json.dumps(ALLOWED_LEVELS),
                json.dumps(ALLOWED_THEMES),
                valid_until,
                utc_now(),
            ),
        )
    after = read_existing_state(config.consumer_id)["non_test_consumer_count"]
    return {"non_test_consumer_count_before": before, "non_test_consumer_count_after": after}


def scalar(connection, sql: str, parameters: tuple[object, ...]) -> int:
    row = connection.execute(sql, parameters).fetchone()
    return int(row["count"])


def write_key_file(path: Path | None, raw_key: str) -> None:
    if path is None:
        raise RuntimeError("key output path is required")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw_key, encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def report_payload(
    config: CreationConfig,
    status: str,
    state: dict[str, object],
    key_hash: str | None,
    created: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "report_type": "isolated_test_consumer_creation",
        "generated_at": now_utc_iso(),
        "consumer_id": config.consumer_id,
        "creation_status": status,
        "test_tenant_key_isolation": status == "created",
        "feature": FEATURE,
        "allowed_cefr_levels": list(ALLOWED_LEVELS),
        "allowed_theme_ids": list(ALLOWED_THEMES),
        "daily_quota_limit": config.quota_limit,
        "key_hash_prefix": None if key_hash is None else key_hash[:16],
        "key_fingerprint": None if key_hash is None else key_hash[:24],
        "key_output_mode": "chmod_600_file" if config.key_out else "none",
        "secret_printed": False,
        "existing_state": state,
        "write_scope": ["consumers", "api_credentials", "entitlements"] if status == "created" else [],
        "non_test_customer_rows_changed": None if created is None else changed_non_test_count(created),
        "created_counts": created or {},
    }


def preflight_report(config: CreationConfig, status: str, issues: list[str]) -> dict[str, object]:
    report = report_payload(config, status, {}, None)
    report["stop_condition_reasons"] = issues
    return report


def changed_non_test_count(created: dict[str, object]) -> bool:
    return created["non_test_consumer_count_before"] != created["non_test_consumer_count_after"]


def generate_api_key() -> str:
    return f"qb_{secrets.token_urlsafe(32)}_load_smoke"


def emit_report(path: Path, report: dict[str, object]) -> None:
    if str(path) == "-":
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(path), "creation_status": report["creation_status"]}))


def now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
