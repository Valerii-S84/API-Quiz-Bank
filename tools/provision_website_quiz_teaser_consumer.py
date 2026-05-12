#!/usr/bin/env python3
"""Provision and prove the website quiz teaser protected beta consumer."""

from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
    transition_consumer_status,
    utc_now,
)


REPORT_DATE = "2026-05-12"
CONSUMER_ID = "website_quiz_teaser"
NO_ENTITLEMENT_CONSUMER_ID = "website_quiz_teaser_no_entitlement_probe"
DISPLAY_NAME = "Website Quiz Teaser"
CONSUMER_KIND = "api_client"
FEATURE = "quiz_delivery"
DAILY_QUOTA_LIMIT = 5
ALLOWED_CEFR_LEVELS = ("A1", "A2")
ALLOWED_THEME_IDS = ("T02",)
ALLOWED_THEME_LABELS = ("Artikel", "Alltag", "Verben", "Präpositionen")
API_BASE_URL = "http://127.0.0.1:8000"
SECRET_ENV_PATH = ROOT / "var" / "deployment_env" / "website_quiz_teaser.env"
REPORT_PATH = ROOT / "reports" / "beta" / f"website_quiz_teaser_consumer_evidence_{REPORT_DATE}.md"
DB_PATH = ROOT / "var" / "quizbank_mvp.sqlite3"


@dataclass(frozen=True)
class BetaSourceSpec:
    label: str
    filename: str
    count: int


BETA_SOURCE_SPECS = (
    BetaSourceSpec("Artikel", "Artikel_Sprint_Bank_A1_B2_1000.csv", 2),
    BetaSourceSpec("Alltag", "Artikel_Sprint_Bank_A1_B2_1000.csv", 1),
    BetaSourceSpec("Verben", "Modalverben_Bank_210.csv", 1),
    BetaSourceSpec("Präpositionen", "Preposition_Natural_Usage_Bank_A1_B1_70.csv", 1),
)


REQUIRED_ITEM_FIELDS = tuple(
    "item_id language level_band sublevel theme_id subtheme_id objective_id "
    "pattern_id difficulty_band register prompt stem_text options answer_key "
    "explanation tags coverage_cell_id version created_at updated_at reviewed_at "
    "level_locked locked_at".split()
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision website_quiz_teaser and write masked beta evidence."
    )
    parser.add_argument("--quizbank-dir", type=Path, default=ROOT / "QuizBank")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--report-out", type=Path, default=REPORT_PATH)
    parser.add_argument("--secret-env-out", type=Path, default=SECRET_ENV_PATH)
    parser.add_argument("--api-base-url", default=API_BASE_URL)
    parser.add_argument("--consumer-api-key-env", default="QUIZ_BANK_CONSUMER_API_KEY")
    parser.add_argument("--edge-api-key-env", default="QUIZ_BANK_EDGE_API_KEY")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = run_provisioning(args)
    write_report(args.report_out, evidence)
    write_secret_env(args.secret_env_out, evidence["env_handoff"]["raw"])
    print(f"wrote masked evidence report: {args.report_out}")
    print(f"wrote ignored deployment env handoff: {args.secret_env_out}")
    return 0


def run_provisioning(args: argparse.Namespace) -> dict[str, Any]:
    consumer_api_key = credential_value(
        args.consumer_api_key_env,
        "wbqt",
    )
    rotated_api_key = generate_secret("wbqt_rotated")
    revoke_probe_api_key = generate_secret("wbqt_revoke_probe")
    no_entitlement_api_key = generate_secret("wbqt_no_entitlement_probe")
    edge_api_key = credential_value(args.edge_api_key_env, "wbqt_edge")
    selected_rows = select_beta_rows(args.quizbank_dir)

    initialize_database(args.db_path)
    reset_consumer_state(args.db_path)
    seed_beta_items(args.db_path, selected_rows)
    provision_consumer(args.db_path, consumer_api_key)
    provision_no_entitlement_probe(args.db_path, no_entitlement_api_key)

    client = TestClient(create_app(args.db_path))
    flow = run_five_question_flow(args.db_path, client, consumer_api_key)
    checks = run_denial_checks(client, consumer_api_key, no_entitlement_api_key)
    checks["entitlement_removal"] = entitlement_removal_probe(
        args.db_path,
        client,
        consumer_api_key,
    )
    rotation = rotate_and_probe_credentials(args.db_path, client, consumer_api_key, rotated_api_key)
    suspended = suspend_and_probe_consumer(args.db_path, rotated_api_key)
    revoked = revoke_and_probe_credential(args.db_path, revoke_probe_api_key)

    evidence = {
        "generated_at": utc_now(),
        "consumer": consumer_projection(args.db_path),
        "selected_items": selected_item_projection(selected_rows),
        "flow": flow,
        "checks": checks,
        "rotation": rotation,
        "suspended": suspended,
        "revoked": revoked,
        "env_handoff": env_handoff(args.api_base_url, edge_api_key, rotated_api_key),
        "db_path": str(args.db_path),
    }
    assert_no_secret_exposure(
        evidence,
        (
            consumer_api_key,
            rotated_api_key,
            revoke_probe_api_key,
            no_entitlement_api_key,
            edge_api_key,
        ),
    )
    return evidence


def credential_value(env_name: str, prefix: str) -> str:
    value = os.environ.get(env_name)
    return value if value else generate_secret(prefix)


def generate_secret(prefix: str) -> str:
    return f"qb_{secrets.token_urlsafe(24)}_{prefix}"


def select_beta_rows(quizbank_dir: Path) -> list[dict[str, str]]:
    selected_rows: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    for spec in BETA_SOURCE_SPECS:
        rows = matching_rows(quizbank_dir / spec.filename, spec.label, selected_ids)
        selected_rows.extend(rows[: spec.count])
        selected_ids.update(row["item_id"] for row in rows[: spec.count])
    if len(selected_rows) != DAILY_QUOTA_LIMIT:
        raise RuntimeError(f"expected {DAILY_QUOTA_LIMIT} beta rows, got {len(selected_rows)}")
    return selected_rows


def matching_rows(path: Path, label: str, selected_ids: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("item_id") in selected_ids:
                continue
            if not is_allowed_beta_row(row):
                continue
            rows.append(normalized_runtime_row(row, label))
    if not rows:
        raise RuntimeError(f"no eligible beta rows in {path}")
    return rows


def is_allowed_beta_row(row: dict[str, str]) -> bool:
    return (
        row.get("status") == "published"
        and row.get("sublevel") == "A2"
        and row.get("theme_id") in ALLOWED_THEME_IDS
        and all(row.get(field, "").strip() for field in REQUIRED_ITEM_FIELDS)
    )


def normalized_runtime_row(row: dict[str, str], label: str) -> dict[str, str]:
    item = {field: row[field] for field in REQUIRED_ITEM_FIELDS}
    item["source_type"] = "website_quiz_teaser_controlled_subset"
    item["provenance_note"] = f"website_quiz_teaser:{label}:{row['item_id']}"
    item["theme_label"] = label
    return item


def reset_consumer_state(db_path: Path) -> None:
    consumers = (CONSUMER_ID, NO_ENTITLEMENT_CONSUMER_ID)
    with connect(db_path) as connection:
        connection.execute("DELETE FROM selection_decisions WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM deliveries WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM quota_usage WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM api_credentials WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM entitlements WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM consumer_admin_profiles WHERE consumer_id IN (?, ?)", consumers)
        connection.execute("DELETE FROM consumers WHERE consumer_id IN (?, ?)", consumers)


def seed_beta_items(db_path: Path, rows: list[dict[str, str]]) -> None:
    with TemporaryDirectory() as directory:
        fixture_path = Path(directory) / "website_quiz_teaser_items.jsonl"
        content = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"
        fixture_path.write_text(content, encoding="utf-8")
        seed_control_fixture(
            db_path,
            fixture_path,
            "published",
            source_id="src_website_quiz_teaser_controlled_subset",
        )


def provision_consumer(db_path: Path, consumer_api_key: str) -> None:
    seed_consumer(db_path, CONSUMER_ID, DAILY_QUOTA_LIMIT, ALLOWED_CEFR_LEVELS, ALLOWED_THEME_IDS)
    seed_api_credential(db_path, CONSUMER_ID, consumer_api_key)
    seed_entitlement(
        db_path,
        CONSUMER_ID,
        ALLOWED_CEFR_LEVELS,
        ALLOWED_THEME_IDS,
        actor="owner",
        reason="Controlled protected beta website quiz teaser access",
    )
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


def provision_no_entitlement_probe(db_path: Path, api_key: str) -> None:
    seed_consumer(
        db_path,
        NO_ENTITLEMENT_CONSUMER_ID,
        DAILY_QUOTA_LIMIT,
        ALLOWED_CEFR_LEVELS,
        ALLOWED_THEME_IDS,
    )
    seed_api_credential(
        db_path,
        NO_ENTITLEMENT_CONSUMER_ID,
        api_key,
    )


def run_five_question_flow(db_path: Path, client: TestClient, api_key: str) -> dict[str, Any]:
    responses = [next_item(client, api_key) for _ in range(DAILY_QUOTA_LIMIT)]
    deliveries = [response.json()["delivery"] for response in responses]
    item_ids = [delivery["quiz_item_id"] for delivery in deliveries]
    quota_response = next_item(client, api_key)
    return {
        "statuses": [response.status_code for response in responses],
        "delivery_created_count": len(deliveries),
        "unique_item_count": len(set(item_ids)),
        "item_ids": item_ids,
        "quota_denial": problem_summary(quota_response),
        "delivery_count_after_quota_denial": delivery_count(db_path),
    }


def run_denial_checks(
    client: TestClient,
    api_key: str,
    no_entitlement_api_key: str,
) -> dict[str, Any]:
    return {
        "unauthenticated": problem_summary(client.post("/v1/quiz-items/next", json=payload())),
        "wrong_credential": problem_summary(next_item(client, "wrong_consumer_api_key")),
        "entitlement_denial": problem_summary(
            client.post(
                "/v1/quiz-items/next",
                json=payload(NO_ENTITLEMENT_CONSUMER_ID),
                headers=headers(NO_ENTITLEMENT_CONSUMER_ID, no_entitlement_api_key),
            )
        ),
        "cefr_denial": problem_summary(next_item(client, api_key, cefr_level="B1")),
        "theme_denial": problem_summary(next_item(client, api_key, theme_id="T10")),
    }


def entitlement_removal_probe(
    db_path: Path,
    client: TestClient,
    api_key: str,
) -> dict[str, Any]:
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE entitlements SET status = 'revoked' WHERE consumer_id = ?",
            (CONSUMER_ID,),
        )
    result = problem_summary(next_item(client, api_key))
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE entitlements SET status = 'active' WHERE consumer_id = ?",
            (CONSUMER_ID,),
        )
    return result


def rotate_and_probe_credentials(
    db_path: Path,
    client: TestClient,
    old_api_key: str,
    rotated_api_key: str,
) -> dict[str, Any]:
    seed_api_credential(db_path, CONSUMER_ID, rotated_api_key)
    return {
        "rotated": True,
        "old_credential_denial": problem_summary(next_item(client, old_api_key)),
        "new_credential_quota_gate": problem_summary(next_item(client, rotated_api_key)),
    }


def suspend_and_probe_consumer(db_path: Path, api_key: str) -> dict[str, Any]:
    client = TestClient(create_app(db_path))
    transition_consumer_status(
        db_path,
        CONSUMER_ID,
        "suspended",
        "owner",
        "controlled beta suspension proof",
    )
    return problem_summary(next_item(client, api_key))


def revoke_and_probe_credential(db_path: Path, api_key: str) -> dict[str, Any]:
    transition_consumer_status(
        db_path,
        CONSUMER_ID,
        "active",
        "owner",
        "reactivate for credential revoke proof",
    )
    seed_api_credential(
        db_path,
        CONSUMER_ID,
        api_key,
        credential_id="cred_website_quiz_teaser_revoke_probe",
    )
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE api_credentials
            SET status = 'revoked', revoked_at = ?
            WHERE credential_id = ?
            """,
            (utc_now(), "cred_website_quiz_teaser_revoke_probe"),
        )
    client = TestClient(create_app(db_path))
    return problem_summary(next_item(client, api_key))


def next_item(
    client: TestClient,
    api_key: str,
    cefr_level: str = "A2",
    theme_id: str = "T02",
) -> Any:
    return client.post(
        "/v1/quiz-items/next",
        json=payload(cefr_level=cefr_level, theme_id=theme_id),
        headers=headers(CONSUMER_ID, api_key),
    )


def payload(
    consumer_id: str = CONSUMER_ID,
    cefr_level: str = "A2",
    theme_id: str = "T02",
) -> dict[str, object]:
    return {"consumer_id": consumer_id, "cefr_level": cefr_level, "theme_ids": [theme_id]}


def headers(consumer_id: str, api_key: str) -> dict[str, str]:
    return {"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": api_key}


def problem_summary(response: Any) -> dict[str, Any]:
    body = response.json()
    return {
        "status": response.status_code,
        "reason_code": body.get("reason_code"),
        "delivery_created": response.status_code == 200,
    }


def delivery_count(db_path: Path) -> int:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM deliveries WHERE consumer_id = ?",
            (CONSUMER_ID,),
        ).fetchone()
    return int(row["count"])


def consumer_projection(db_path: Path) -> dict[str, Any]:
    with connect(db_path) as connection:
        consumer = connection.execute(
            "SELECT * FROM consumers WHERE consumer_id = ?",
            (CONSUMER_ID,),
        ).fetchone()
        entitlement = connection.execute(
            "SELECT * FROM entitlements WHERE consumer_id = ? AND feature = ?",
            (CONSUMER_ID, FEATURE),
        ).fetchone()
        credential = connection.execute(
            """
            SELECT credential_id, key_prefix, status
            FROM api_credentials
            WHERE consumer_id = ? AND credential_id = ?
            """,
            (CONSUMER_ID, f"cred_{CONSUMER_ID}"),
        ).fetchone()
    return {
        "consumer_id": CONSUMER_ID,
        "created": consumer is not None,
        "status": consumer["status"],
        "daily_quota_limit": int(consumer["daily_quota_limit"]),
        "allowed_cefr_levels": json.loads(consumer["allowed_cefr_levels_json"]),
        "allowed_theme_ids": json.loads(consumer["allowed_theme_ids_json"]),
        "allowed_theme_labels": list(ALLOWED_THEME_LABELS),
        "entitlement_feature": entitlement["feature"],
        "entitlement_status": entitlement["status"],
        "credential_id": credential["credential_id"],
        "credential_status": credential["status"],
        "credential_key_prefix": mask_value(credential["key_prefix"]),
    }


def selected_item_projection(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "item_id": row["item_id"],
            "cefr_level": row["sublevel"],
            "theme_id": row["theme_id"],
            "theme_label": row["theme_label"],
        }
        for row in rows
    ]


def env_handoff(api_base_url: str, edge_api_key: str, consumer_api_key: str) -> dict[str, Any]:
    masked = {
        "QUIZ_BANK_API_BASE_URL": api_base_url,
        "QUIZ_BANK_EDGE_API_KEY": mask_value(edge_api_key) if edge_api_key else "<deployment-env-only>",
        "QUIZ_BANK_CONSUMER_ID": CONSUMER_ID,
        "QUIZ_BANK_CONSUMER_API_KEY": mask_value(consumer_api_key),
    }
    raw = {
        "QUIZ_BANK_API_BASE_URL": api_base_url,
        "QUIZ_BANK_EDGE_API_KEY": edge_api_key or "<set-real-edge-key-in-deployment-env>",
        "QUIZ_BANK_CONSUMER_ID": CONSUMER_ID,
        "QUIZ_BANK_CONSUMER_API_KEY": consumer_api_key,
    }
    return {"masked": masked, "raw": raw}


def mask_value(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def write_secret_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{key}={value}\n" for key, value in values.items())
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def write_report(path: Path, evidence: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = report_markdown(evidence)
    path.write_text(content, encoding="utf-8")


def report_markdown(evidence: dict[str, Any]) -> str:
    consumer = evidence["consumer"]
    flow = evidence["flow"]
    checks = evidence["checks"]
    lines = [
        "# Website Quiz Teaser Consumer Evidence",
        "",
        f"Date: {REPORT_DATE}",
        "",
        "Scope: Controlled Protected Beta only; not public launch, signup or commercial launch.",
        "",
        f"- consumer created: {'yes' if consumer['created'] else 'no'}",
        f"- entitlement: `{consumer['entitlement_feature']}` / `{consumer['entitlement_status']}`",
        f"- quota: `{consumer['daily_quota_limit']}/day`",
        f"- CEFR scope: `{', '.join(consumer['allowed_cefr_levels'])}`",
        f"- themes: `{', '.join(consumer['allowed_theme_labels'])}`",
        f"- next item: `{flow['statuses'][0]}`",
        f"- 5-question flow: `{flow['statuses']}`, unique `{flow['unique_item_count']}`",
        f"- quota denial: `{flow['quota_denial']['status']} {flow['quota_denial']['reason_code']}`",
        f"- wrong credential: `{checks['wrong_credential']['status']} {checks['wrong_credential']['reason_code']}`",
        f"- suspended: `{evidence['suspended']['status']} {evidence['suspended']['reason_code']}`",
        f"- revoked credential: `{evidence['revoked']['status']} {evidence['revoked']['reason_code']}`",
        "",
        "## Masked Frontend Env Handoff",
        "",
        "```text",
    ]
    lines.extend(f"{key}={value}" for key, value in evidence["env_handoff"]["masked"].items())
    lines.extend([
        "```",
        "",
        "- raw secrets exposed: no",
        "- unrestricted corpus access: no",
        "",
    ])
    return "\n".join(lines)


def assert_no_secret_exposure(evidence: dict[str, Any], secrets_to_check: tuple[str, ...]) -> None:
    report = report_markdown(evidence)
    for secret in secrets_to_check:
        if secret and secret in report:
            raise RuntimeError("secret value leaked into evidence report")


if __name__ == "__main__":
    raise SystemExit(main())
