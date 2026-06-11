#!/usr/bin/env python3
"""Build the release governance gate report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports/release/release_governance_gate_2026-05-10.json"
BRANCH_PROTECTION_PATH = ROOT / ".github/branch_protection_main.json"
CI_PATH = ROOT / ".github/workflows/ci.yml"
PR_TEMPLATE_PATH = ROOT / ".github/pull_request_template.md"
MIGRATION_CHECKLIST_PATH = ROOT / "runbooks/migration_approval_checklist.md"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
GENERATED_AT = "2026-05-10T00:00:00+00:00"
REMOTE_VERIFICATION_ATTEMPTED_AT = "2026-06-11T00:00:00+00:00"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_report() -> dict[str, object]:
    branch_protection = json.loads(read(BRANCH_PROTECTION_PATH))
    ci = read(CI_PATH)
    pr_template = read(PR_TEMPLATE_PATH)
    migration_checklist = read(MIGRATION_CHECKLIST_PATH)
    changelog = read(CHANGELOG_PATH)
    checks = {
        "branch_protection_config_present": BRANCH_PROTECTION_PATH.exists(),
        "direct_push_blocked_in_desired_config": branch_protection["allow_force_pushes"] is False,
        "required_status_check_configured": "repository-invariants" in json.dumps(branch_protection),
        "ci_runs_on_pull_request": "pull_request:" in ci,
        "ci_runs_no_secrets_scan": "tools/no_secrets_scan.py" in ci,
        "pr_template_has_release_notes_prompt": "Changelog / release note" in pr_template,
        "changelog_exists": "## Unreleased" in changelog,
        "migration_approval_checklist_exists": "backup freshness is verified" in migration_checklist,
    }
    blockers = []
    if not all(checks.values()):
        blockers.append("one or more repository-side governance controls are missing")
    blockers.append("actual GitHub branch protection enforcement must be verified on remote")
    blockers.append("release tag must be created only at release time")
    return {
        "report_type": "release_governance_gate",
        "generated_at": GENERATED_AT,
        "decision": "REPO-GO release governance controls; VERIFY remote branch protection",
        "checks": checks,
        "required_ci_check": "repository-invariants",
        "protected_branch": "main",
        "release_tag_policy": "annotated tag after release approval",
        "remote_branch_protection_verification": {
            "attempted_at": REMOTE_VERIFICATION_ATTEMPTED_AT,
            "status": "blocked_by_missing_github_cli_auth",
            "commands": [
                "gh auth status",
                "gh api repos/Valerii-S84/API-Quiz-Bank/branches/main/protection",
            ],
            "observed_results": [
                "gh auth status: not logged into any GitHub hosts",
                "gh api branch protection: requires gh auth login or GH_TOKEN",
            ],
            "conclusion": "remote branch protection is not confirmed or enabled by this report",
        },
        "release_governance_blockers": blockers,
    }


def main() -> int:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
