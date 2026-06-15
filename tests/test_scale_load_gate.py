from __future__ import annotations

import json
import sys
import unittest

from tests.repository_test_support import ROOT, file_texts, run_command


REPORT_PATH = "reports/scale/protected_runtime_load_smoke_2026-05-10.json"
BUSINESS_ROUTE_LOAD_REPORT_PATH = "reports/scale/protected_business_route_load_smoke_2026-06-11.json"
CREATION_REPORT_PATH = "reports/scale/isolated_test_consumer_creation_2026-06-11.json"
SCALE_LOAD_DOC_PATHS = [
    "reports/roadmap/external_evidence_blockers.md",
    "reports/roadmap/roadmap_evidence_register.md",
]


class ScaleLoadGateTests(unittest.TestCase):
    def test_scale_load_smoke_report_is_current(self) -> None:
        before = file_texts([REPORT_PATH])
        run_command(sys.executable, "tools/run_mvp_load_smoke.py")
        self.assertEqual(before, file_texts([REPORT_PATH]))

        report = json.loads((ROOT / REPORT_PATH).read_text(encoding="utf-8"))
        self.assertEqual(report["report_type"], "protected_runtime_load_smoke")
        self.assertEqual(report["concurrent_consumers"], 8)
        self.assertEqual(report["status_counts"], {"200": 8})
        self.assertEqual(report["ready_status"], 200)
        self.assertEqual(report["auth_no_key_status"], 401)
        self.assertEqual(report["repeat_selection_status"], 503)
        self.assertEqual(report["quota_denial_status"], 429)
        self.assertTrue(all(report["resource_limits"].values()))
        self.assertIn("external concurrent traffic test is not executed", report["scale_blockers"])

    def test_protected_business_route_load_smoke_report_schema(self) -> None:
        report = json.loads((ROOT / BUSINESS_ROUTE_LOAD_REPORT_PATH).read_text(encoding="utf-8"))
        self.assertEqual(report["report_type"], "protected_business_route_load_smoke")
        self.assertIn(report["stop_condition_status"], {
            "stopped_missing_required_env",
            "stopped_invalid_config",
            "stopped_auth_gate_unexpected",
            "stopped_5xx_detected",
            "stopped_p95_threshold_exceeded",
            "stopped_latency_instability",
            "stopped_unexpected_status",
            "stopped_timeout",
            "completed",
        })
        self.assertEqual(report["endpoint_list"][0]["path"], "/health")
        self.assertEqual(report["endpoint_list"][1]["path"], "/health")
        self.assertEqual(report["endpoint_list"][2]["path"], "/ready")
        self.assertEqual(report["endpoint_list"][3]["path"], "/v1/quiz-items/next")
        self.assertIn("concurrency", report)
        self.assertIn("total_requests_executed", report)
        self.assertIn("p50_ms", report)
        self.assertIn("p95_ms", report)
        self.assertIn("p99_ms", report)
        self.assertIn("local_git_commit_sha", report)
        self.assertIn("server_git_commit_sha", report)
        self.assertNotIn("git_commit_sha", report)
        self.assertIn("route_profile", report)
        self.assertIn(report["route_profile"], {"health_ready_only", "business_route_with_test_tenant"})
        self.assertIn("business_route_tested", report)
        self.assertIn("business_route_path", report)
        self.assertIn("test_consumer_id", report)
        self.assertIn("test_key_hash_prefix", report)
        self.assertIn("test_key_fingerprint", report)
        self.assertIn("test_tenant_key_isolation", report)
        self.assertIn("quota_counter_pollution_risk", report)
        self.assertIn("health_result", report)
        self.assertIn("ready_result", report)
        self.assertIn("business_route_result", report)
        self.assertIn("auth_gate_result", report)
        self.assertIn("status_counts", report)
        self.assertIn("five_xx_count", report)
        self.assertIn("timeout_count", report)
        self.assertIn("state_changing_route_used", report)
        self.assertIn("negative_controls", report)
        self.assertIn("quota_entitlement_control_result", report)
        self.assertIn("explicit_non_claims", report)
        self.assertIn(report["quota_counter_pollution_risk"], {"none", "isolated", "unknown"})

    def test_business_route_go_requires_actual_business_route_test(self) -> None:
        report = json.loads((ROOT / BUSINESS_ROUTE_LOAD_REPORT_PATH).read_text(encoding="utf-8"))
        conclusion = report["conclusion"]
        if conclusion == "GO protected business-route load evidence for tested threshold":
            self.assertTrue(report["business_route_tested"])
            self.assertTrue(report["test_tenant_key_isolation"])
            self.assertEqual(report["quota_counter_pollution_risk"], "isolated")
            self.assertEqual(report["five_xx_count"], 0)
            self.assertEqual(report["timeout_count"], 0)
            self.assertEqual(report["error_count"], 0)
        if not report["business_route_tested"]:
            docs = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in SCALE_LOAD_DOC_PATHS)
            self.assertNotIn("Scale/load closed", docs)
            self.assertNotIn("protected business-route tested threshold", docs)

    def test_business_route_report_has_no_secret_or_launch_claims(self) -> None:
        report = json.loads((ROOT / BUSINESS_ROUTE_LOAD_REPORT_PATH).read_text(encoding="utf-8"))
        non_claims = report["explicit_non_claims"]
        self.assertTrue(non_claims.get("not_paid_launch_approval"))
        self.assertTrue(non_claims.get("not_legal_privacy_approval"))
        self.assertTrue(non_claims.get("not_support_sla_approval"))
        self.assertTrue(non_claims.get("not_school_launch_approval"))
        self.assertTrue(non_claims.get("not_unlimited_broad_scale_proof"))
        serialized = json.dumps(report).lower()
        self.assertNotIn("x-api-key", serialized)
        self.assertNotIn("x-quizbank-api-key", serialized)
        self.assertNotIn("x-consumer-id", serialized)
        self.assertNotIn("invalid-load-smoke-key", serialized)
        self.assertNotIn("demo_consumer_api_key", serialized)
        self.assertNotIn("test_api_key_for_", serialized)
        self.assertNotIn("quiz_item", serialized)
        self.assertNotIn("stem_text", serialized)
        self.assertNotIn("answer_key", serialized)
        self.assertNotIn("options_json", serialized)
        self.assertNotIn("source_traceability", serialized)
        conclusion = str(report["conclusion"]).lower()
        self.assertNotIn("paid launch approval", conclusion)
        self.assertNotIn("legal/privacy approval", conclusion)
        self.assertNotIn("school launch approval", conclusion)

    def test_isolated_test_consumer_creation_report_is_sanitized(self) -> None:
        report = json.loads((ROOT / CREATION_REPORT_PATH).read_text(encoding="utf-8"))
        self.assertEqual(report["report_type"], "isolated_test_consumer_creation")
        self.assertEqual(report["consumer_id"], "load-smoke-test-2026-06-11")
        self.assertFalse(report["secret_printed"])
        if report["creation_status"] == "created":
            self.assertTrue(report["test_tenant_key_isolation"])
            self.assertEqual(report["write_scope"], ["consumers", "api_credentials", "entitlements"])
            self.assertFalse(report["non_test_customer_rows_changed"])
            self.assertIsNotNone(report["key_hash_prefix"])
            self.assertIsNotNone(report["key_fingerprint"])
        serialized = json.dumps(report).lower()
        self.assertNotIn("x-api-key", serialized)
        self.assertNotIn("x-quizbank-api-key", serialized)
        self.assertNotIn("qb_", serialized)


if __name__ == "__main__":
    unittest.main()
