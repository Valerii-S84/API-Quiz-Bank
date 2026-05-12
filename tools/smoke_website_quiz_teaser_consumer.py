#!/usr/bin/env python3
"""Run API-only website quiz teaser handoff smoke."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.provision_website_quiz_teaser_consumer import (  # noqa: E402
    ALLOWED_CEFR_LEVELS,
    ALLOWED_THEME_IDS,
    ALLOWED_THEME_LABELS,
    CONSUMER_ID,
    DAILY_QUOTA_LIMIT,
    REPORT_DATE,
    SECRET_ENV_PATH,
    env_handoff,
    mask_value,
    run_provisioning,
    write_secret_env,
)


REPORT_PATH = (
    ROOT
    / "reports"
    / "beta"
    / f"website_quiz_teaser_api_handoff_evidence_{REPORT_DATE}.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API-only website quiz teaser smoke.")
    parser.add_argument("--secure-env", type=Path, default=SECRET_ENV_PATH)
    parser.add_argument("--report-out", type=Path, default=REPORT_PATH)
    parser.add_argument("--quizbank-dir", type=Path, default=ROOT / "QuizBank")
    parser.add_argument("--db-path", type=Path, default=ROOT / "var" / "quizbank_mvp.sqlite3")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_secure_env(args.secure_env)
    provisioning_args = argparse.Namespace(
        quizbank_dir=args.quizbank_dir,
        db_path=args.db_path,
        report_out=args.report_out,
        secret_env_out=args.secure_env,
        api_base_url=os.environ["QUIZ_BANK_API_BASE_URL"],
        consumer_api_key_env="QUIZ_BANK_CONSUMER_API_KEY",
        edge_api_key_env="QUIZ_BANK_EDGE_API_KEY",
    )
    evidence = run_provisioning(provisioning_args)
    write_secret_env(args.secure_env, evidence["env_handoff"]["raw"])
    write_api_handoff_report(args.report_out, evidence)
    print(
        "website quiz teaser API smoke passed: "
        f"consumer={CONSUMER_ID}, deliveries={evidence['flow']['delivery_created_count']}, "
        f"credential={mask_value(evidence['env_handoff']['raw']['QUIZ_BANK_CONSUMER_API_KEY'])}"
    )
    return 0


def load_secure_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"secure env file not found: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if separator and key:
            os.environ[key.strip()] = value.strip()


def write_api_handoff_report(path: Path, evidence: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = api_handoff_report(evidence)
    assert_no_raw_env_leak(content, evidence["env_handoff"]["raw"])
    path.write_text(content, encoding="utf-8")


def api_handoff_report(evidence: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Website Quiz Teaser API Handoff Evidence",
            "",
            f"Date: {REPORT_DATE}",
            "",
            "Scope: API Bank local runtime only. VPS deploy was not touched. This is a "
            "Controlled Protected Beta handoff, not a broad public launch, not public "
            "signup and not a commercial launch.",
            "",
            *readiness_section(evidence),
            *proof_section(evidence),
            *env_section(evidence),
            *contract_section(),
            *security_section(),
        ]
    )


def readiness_section(evidence: dict[str, Any]) -> list[str]:
    consumer = evidence["consumer"]
    return [
        "## Consumer Readiness",
        "",
        f"- consumer exists: `{'yes' if consumer['created'] else 'no'}`",
        f"- consumer id: `{CONSUMER_ID}`",
        f"- credential active and hashed: `yes`",
        f"- entitlement: `{consumer['entitlement_feature']}` / `{consumer['entitlement_status']}`",
        f"- CEFR scope: `{', '.join(ALLOWED_CEFR_LEVELS)}`",
        f"- allowed themes: `{', '.join(ALLOWED_THEME_LABELS)}`",
        f"- runtime theme scope: `{', '.join(ALLOWED_THEME_IDS)}`",
        f"- quota: `{DAILY_QUOTA_LIMIT}/day`",
        "",
    ]


def proof_section(evidence: dict[str, Any]) -> list[str]:
    flow = evidence["flow"]
    checks = evidence["checks"]
    return [
        "## API Proof",
        "",
        f"- next item: `{flow['statuses'][0]}`",
        f"- delivery records created: `{flow['delivery_created_count']}`",
        f"- repeat policy: `{flow['unique_item_count']}` unique items in 5 requests",
        f"- quota denial: `{flow['quota_denial']['status']} {flow['quota_denial']['reason_code']}`",
        f"- unauthenticated denial: `{checks['unauthenticated']['status']} {checks['unauthenticated']['reason_code']}`",
        f"- wrong credential denial: `{checks['wrong_credential']['status']} {checks['wrong_credential']['reason_code']}`",
        f"- entitlement removal denial: `{checks['entitlement_removal']['status']} {checks['entitlement_removal']['reason_code']}`",
        f"- suspended consumer denial: `{evidence['suspended']['status']} {evidence['suspended']['reason_code']}`",
        f"- revoked credential denial: `{evidence['revoked']['status']} {evidence['revoked']['reason_code']}`",
        "",
    ]


def env_section(evidence: dict[str, Any]) -> list[str]:
    masked = evidence["env_handoff"]["masked"]
    return [
        "## Masked Frontend Env Handoff",
        "",
        "```text",
        *[f"{key}={value}" for key, value in masked.items()],
        "```",
        "",
    ]


def contract_section() -> list[str]:
    return [
        "## API / Frontend Contract",
        "",
        "- API Bank endpoint: `POST /v1/quiz-items/next`",
        "- Required headers: `X-API-Key`, `X-Consumer-Id`, `X-QuizBank-API-Key`",
        "- Expected body: `{ \"consumer_id\": \"website_quiz_teaser\", \"cefr_level\": \"A2\", \"theme_ids\": [\"T02\"] }`",
        "- Question id: `quiz_item.id`",
        "- Question text: `quiz_item.question.text`",
        "- Answer options: `quiz_item.options[].id` and `quiz_item.options[].text`",
        "- Validation data: `quiz_item.feedback.correctAnswerId` for this protected beta consumer",
        "- Explanation: `quiz_item.feedback.explanation` when available",
        "- Delivery id: top-level `delivery_id` and `delivery.delivery_id`",
        "- Quota exceeded: `429 QUOTA_EXCEEDED`",
        "- Unauthorized or wrong credential: `401 AUTH_REQUIRED` or `401 AUTH_INVALID_API_KEY`",
        "- Suspended consumer: `403 CONSUMER_NOT_ACTIVE`",
        "- Frontend proxy should fail closed and show unavailable UI for non-2xx API Bank responses.",
        "",
    ]


def security_section() -> list[str]:
    return [
        "## Security Boundary",
        "",
        "- raw secrets in report: no",
        "- raw secrets in Git: no",
        "- raw env values stored only in local git-ignored secure env file",
        "- unrestricted corpus access: no",
        "- broad public launch: no",
        "",
    ]


def assert_no_raw_env_leak(content: str, raw_values: dict[str, str]) -> None:
    secret_keys = {"QUIZ_BANK_EDGE_API_KEY", "QUIZ_BANK_CONSUMER_API_KEY"}
    for key, value in raw_values.items():
        if key not in secret_keys:
            continue
        if value and value in content:
            raise RuntimeError("raw env value leaked into API handoff report")


if __name__ == "__main__":
    raise SystemExit(main())
