from __future__ import annotations

import json
import unittest

from tests.repository_test_support import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    NORMAL_DELIVERY_STATUSES,
    ROOT,
    THEME_TITLES,
    read_csv_dicts,
)


REQUIRED_CONTRACT_PATHS = [
    "README.md",
    "LICENSE",
    "policies/license_policy.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/docs_change.md",
    ".github/ISSUE_TEMPLATE/corpus_change.md",
    ".github/ISSUE_TEMPLATE/tooling_change.md",
    ".github/ISSUE_TEMPLATE/security_change.md",
    ".github/ISSUE_TEMPLATE/support_abuse.md",
    "data/taxonomy/cefr_levels.csv",
    "data/taxonomy/themes.csv",
    "data/taxonomy/objectives.csv",
    "data/taxonomy/patterns.csv",
    "schemas/canonical_quiz_item.schema.json",
    "api/openapi.yaml",
    "database/migrations/001_create_mvp_runtime.sql",
    "database/migrations/002_add_api_credentials.sql",
    "database/postgresql/001_create_runtime.sql",
    "database/postgresql/002_add_import_contract.sql",
    "database/postgresql/README.md",
    "docs/observability_contract.md",
    "data/parser_profiles/parser_profiles.yml",
    "data/manifests/import_manifest.yml",
    "data/imports/control_sample_items.jsonl",
    "data/registry/source_registry.csv",
    "reports/coverage/corpus_coverage.json",
    "reports/delivery/control_approved_selection_report.json",
    "reports/delivery/control_repeat_policy_report.json",
    "reports/delivery/control_selection_report.json",
    "reports/imports/control_sample_import.json",
    "reports/imports/control_sample_postgresql_load_plan.json",
    "reports/imports/control_sample_postgresql_smoke.json",
    "tests/fixtures/control_source/control_sample.csv",
    "tests/fixtures/selection/approved_traceable_items.jsonl",
    "tools/quizbank_import_sample.py",
    "tools/quizbank_postgresql_load_plan.py",
    "tools/run_postgresql_contract_smoke.py",
    "tools/quizbank_gap_map.py",
    "tools/quizbank_selection_smoke.py",
    "tools/no_secrets_scan.py",
    "tests/test_postgresql_load_plan.py",
    "tests/test_postgresql_smoke_report.py",
    "tools/run_pre_pilot_dry_run.py",
    "runbooks/backup_restore.md",
    "runbooks/backup_restore_operational_runbook.md",
    "runbooks/incident_response.md",
    "runbooks/monitoring_alerts_runbook.md",
    "runbooks/rollback.md",
    "runbooks/release_rollback.md",
    "runbooks/support_triage.md",
    "reports/pre_pilot/local_pre_pilot_dry_run_2026-05-08.md",
    "reports/beta/local_beta_security_smoke_2026-05-08.md",
    "reports/beta/app_level_public_smoke_2026-05-08.md",
    "reports/beta/backup_timer_evidence_2026-05-08.md",
    "reports/beta/edge_app_header_split_smoke_2026-05-08.md",
    "reports/beta/public_route_smoke_2026-05-08.md",
    "reports/beta/vps_live_ops_evidence_2026-05-08.md",
    "reports/observability/beta_alert_review_2026-05-08.md",
    "reports/publication/beta_launch_subset_2026-05-08.md",
    "reports/release/local_beta_release_rollback_2026-05-08.md",
    "reports/pre_pilot/telegram_controlled_send_2026-05-08.md",
    "reports/rollback/local_rollback_tabletop_2026-05-08.md",
    "reports/restore/mvp_sqlite_restore_drill_2026-05-08.md",
    "reports/roadmap/external_evidence_blockers.md",
    "reports/roadmap/phase_7_9_gate_matrix.md",
    "reports/roadmap/roadmap_evidence_register.md",
]


class ContractSchemaInvariantTests(unittest.TestCase):
    def test_json_schema_matches_canonical_header_contract(self) -> None:
        schema = json.loads((ROOT / "schemas/canonical_quiz_item.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], EXPECTED_HEADER)
        self.assertEqual(list(schema["properties"].keys()), EXPECTED_HEADER)
        self.assertEqual(schema["properties"]["language"], {"type": "string", "const": "de"})
        self.assertEqual(schema["properties"]["sublevel"]["enum"], list(CANONICAL_LEVELS))
        self.assertEqual(schema["properties"]["status"]["enum"], list(ITEM_STATUSES))

    def test_theme_taxonomy_uses_canonical_titles(self) -> None:
        theme_rows = read_csv_dicts("data/taxonomy/themes.csv")
        self.assertEqual(len(theme_rows), len(THEME_TITLES))
        for row in theme_rows:
            self.assertEqual(row["title"], THEME_TITLES[row["theme_id"]])
            self.assertEqual(row["status"], "active")
            self.assertEqual(row["label_status"], "canonical")

    def test_openapi_seed_preserves_public_delivery_boundary(self) -> None:
        openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        public_projection = openapi.split("QuizItemPublicProjection:", 1)[1].split(
            "ProblemDetails:", 1
        )[0]
        self.assertIn("/v1/quiz-items/next:", openapi)
        self.assertIn("NextQuizRequest:", openapi)
        self.assertIn("QuizItemPublicProjection:", openapi)
        self.assertIn("ProblemDetails:", openapi)
        self.assertIn("X-QuizBank-API-Key", openapi)
        self.assertIn("options:", public_projection)
        self.assertNotIn("answer_key", public_projection)
        self.assertNotIn("explanation", public_projection)

    def test_openapi_uses_committed_status_and_error_contracts(self) -> None:
        openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("openapi: 3.1.0", openapi)
        self.assertIn("application/problem+json", openapi)
        self.assertIn(
            f"enum: [{', '.join(NORMAL_DELIVERY_STATUSES)}]",
            openapi,
        )

    def test_taxonomy_and_contract_artifacts_exist(self) -> None:
        for relative_path in REQUIRED_CONTRACT_PATHS:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
