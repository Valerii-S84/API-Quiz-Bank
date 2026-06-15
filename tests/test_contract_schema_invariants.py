from __future__ import annotations

import json
import unittest

from tests.repository_test_support import (
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    NORMAL_DELIVERY_STATUSES,
    ROOT,
    SUPPORTED_LANGUAGE_CODES,
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
    ".github/branch_protection_main.json",
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
    "schemas/runtime_canonical_quiz_item.schema.json",
    "api/openapi.yaml",
    "database/migrations/001_create_mvp_runtime.sql",
    "database/migrations/002_add_api_credentials.sql",
    "database/migrations/004_add_selection_decisions.sql",
    "database/postgresql/001_create_runtime.sql",
    "database/postgresql/002_add_import_contract.sql",
    "database/postgresql/003_add_runtime_delivery_evidence.sql",
    "database/postgresql/README.md",
    "docs/observability_contract.md",
    "data/parser_profiles/parser_profiles.yml",
    "data/billing/plan_catalog.json",
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
    "tools/quizbank_legal_privacy_gate.py",
    "tools/run_postgresql_contract_smoke.py",
    "tools/run_mvp_load_smoke.py",
    "tools/quizbank_gap_map.py",
    "tools/quizbank_production_corpus_gate.py",
    "tools/promote_verified_corpus_to_production.py",
    "tools/run_production_corpus_postgresql_smoke.py",
    "tools/quizbank_release_governance_gate.py",
    "tools/quizbank_selection_smoke.py",
    "tools/no_secrets_scan.py",
    "CHANGELOG.md",
    "scripts/api_quiz_bank_postgres_backup.sh",
    "scripts/api_quiz_bank_postgres_restore_drill.sh",
    "tests/test_postgresql_load_plan.py",
    "tests/test_postgresql_smoke_report.py",
    "tools/run_pre_pilot_dry_run.py",
    "runbooks/backup_restore.md",
    "runbooks/backup_restore_operational_runbook.md",
    "runbooks/incident_response.md",
    "runbooks/monitoring_alerts_runbook.md",
    "runbooks/migration_approval_checklist.md",
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
    "reports/compliance/legal_privacy_gate_2026-05-10.json",
    "reports/publication/beta_launch_subset_2026-05-08.md",
    "reports/publication/production_corpus_gate_2026-05-10.json",
    "reports/publication/owner_corpus_approval_2026-05-11.json",
    "reports/publication/owner_corpus_approval_2026-05-11.md",
    "reports/publication/verified_corpus_promotion_2026-05-11.json",
    "reports/publication/production_corpus_gate_2026-05-11.json",
    "reports/imports/production_corpus_postgresql_smoke_2026-05-11.json",
    "reports/release/local_beta_release_rollback_2026-05-08.md",
    "reports/release/release_governance_gate_2026-05-10.json",
    "reports/scale/protected_runtime_load_smoke_2026-05-10.json",
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
        self.assertEqual(schema["title"], "API Quiz Bank Raw Canonical CSV Row")
        self.assertIn("Raw source CSV row contract", schema["description"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["required"], EXPECTED_HEADER)
        self.assertEqual(list(schema["properties"].keys()), EXPECTED_HEADER)
        self.assertEqual(
            schema["properties"]["language"],
            {"type": "string", "enum": list(SUPPORTED_LANGUAGE_CODES)},
        )
        self.assertEqual(schema["properties"]["sublevel"]["enum"], list(CANONICAL_LEVELS))
        self.assertEqual(schema["properties"]["status"]["enum"], list(ITEM_STATUSES))

    def test_runtime_json_schema_carries_explicit_content_scope(self) -> None:
        schema = json.loads((ROOT / "schemas/runtime_canonical_quiz_item.schema.json").read_text())

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["title"], "API Quiz Bank Runtime Canonical Quiz Item")
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("source_id", schema["required"])
        self.assertIn("options_json", schema["required"])
        self.assertIn("language_code", schema["required"])
        self.assertIn("content_bank_id", schema["required"])
        self.assertIn("bank_version_id", schema["required"])
        self.assertNotIn("options", schema["properties"])
        self.assertNotIn("source_type", schema["properties"])
        self.assertEqual(schema["properties"]["language_code"]["default"], "de")
        self.assertEqual(schema["properties"]["content_bank_id"]["default"], "german-core")
        self.assertEqual(
            schema["properties"]["bank_version_id"]["default"],
            "german-core:2026-06-12-baseline",
        )

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
            "QuizItemAnswerFeedback:", 1
        )[0]
        self.assertIn("/v1/levels:", openapi)
        self.assertIn("/v1/topics:", openapi)
        self.assertIn("operationId: listTopics", openapi)
        self.assertIn("theme_code:", openapi)
        self.assertIn("language_code:", openapi)
        self.assertIn("/v1/quiz-items/next:", openapi)
        next_route_contract = openapi.split("  /v1/quiz-items/next:", 1)[1].split(
            "  /v1/quiz-items/{item_id}:",
            1,
        )[0]
        self.assertIn("        '503':", next_route_contract)
        self.assertIn("Selection queue is warming", next_route_contract)
        self.assertIn("NextQuizRequest:", openapi)
        self.assertIn("QuizItemPublicProjection:", openapi)
        self.assertIn("ProblemDetails:", openapi)
        self.assertIn("X-QuizBank-API-Key", openapi)
        self.assertIn("options:", public_projection)
        self.assertIn("question:", public_projection)
        self.assertNotIn("answer_key", public_projection)
        self.assertNotIn("explanation", public_projection)
        self.assertNotIn("source_traceability", public_projection)

    def test_openapi_uses_committed_status_and_error_contracts(self) -> None:
        openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("openapi: 3.1.0", openapi)
        self.assertIn("application/problem+json", openapi)
        self.assertIn(
            f"enum: [{', '.join(NORMAL_DELIVERY_STATUSES)}]",
            openapi,
        )
        self.assertIn("  /v1/admin/consumers/{consumer_id}/visual-settings:", openapi)
        self.assertIn("AdminVisualSettingsPatchRequest", openapi)
        self.assertIn("enum: [text_only, image_standard, image_branded]", openapi)
        self.assertNotIn("  /v1/visual-assets/generate:", openapi)

    def test_openapi_does_not_expose_raw_csv_access_path(self) -> None:
        openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        route_lines = [
            line.strip().lower()
            for line in openapi.splitlines()
            if line.startswith("  /")
        ]

        self.assertFalse(any("csv" in route or "raw" in route for route in route_lines))
        self.assertNotIn("text/csv", openapi.lower())
        self.assertNotIn("QuizBank/", openapi)

    def test_mvp_plan_catalog_defines_manual_entitlement_seed(self) -> None:
        catalog = json.loads((ROOT / "data/billing/plan_catalog.json").read_text())
        plan_codes = {plan["plan_code"] for plan in catalog["plans"]}
        feature_codes = {
            feature["feature_code"]
            for plan in catalog["plans"]
            for feature in plan["features"]
        }
        self.assertEqual(catalog["status"], "seed")
        self.assertIn("manual_mvp_demo", plan_codes)
        self.assertIn("api_pilot", plan_codes)
        self.assertIn("manual_visual_demo", plan_codes)
        self.assertIn("visual_pilot", plan_codes)
        self.assertIn("pro_visual_pilot", plan_codes)
        self.assertTrue(
            {
                "visual_delivery.standard",
                "visual_delivery.branded",
                "visual_generation.standard",
                "visual_generation.branded",
            }.issubset(feature_codes)
        )
        for plan in catalog["plans"]:
            self.assertTrue(plan["features"])
            self.assertEqual(plan["features"][0]["feature_code"], "quiz_delivery")
            self.assertIn(plan["features"][0]["limit_period"], {"day", "month", "manual"})

    def test_taxonomy_and_contract_artifacts_exist(self) -> None:
        for relative_path in REQUIRED_CONTRACT_PATHS:
            self.assertTrue((ROOT / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
