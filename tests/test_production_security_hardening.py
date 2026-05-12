from __future__ import annotations

import unittest

from tests.repository_test_support import ROOT, run_command


SECURITY_REVIEW_PATH = ROOT / "reports" / "security" / "production_hardening_review_2026-05-10.md"


class ProductionSecurityHardeningTests(unittest.TestCase):
    def test_security_review_records_all_section_one_gates(self) -> None:
        review = SECURITY_REVIEW_PATH.read_text(encoding="utf-8")
        required_gates = [
            "formal server hardening review",
            "secret rotation policy",
            "dependency and container scan",
            "firewall, SSH and Docker exposure audit",
            "rate-limit and abuse controls",
            "production security review record",
        ]

        self.assertIn("Decision: GO for repository security hardening package", review)
        for gate in required_gates:
            self.assertIn(gate, review)
            self.assertIn(f"| {gate} | repo-closed |", review)

    def test_docker_runtime_has_committed_hardening_controls(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "docker-compose.api-quiz-bank.yml").read_text(encoding="utf-8")
        postgres_compose = (ROOT / "docker-compose.api-quiz-bank.postgres.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("cgr.dev/chainguard/python:latest-dev@sha256:", dockerfile)
        self.assertIn("ENTRYPOINT []", dockerfile)
        self.assertIn("USER nonroot", dockerfile)
        self.assertIn('"127.0.0.1:8010:8000"', compose)
        self.assertIn("/data:uid=65532,gid=65532,mode=700", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn("cap_drop:", compose)
        self.assertIn("mem_limit: 512m", compose)
        self.assertIn("cpus: 1.0", compose)
        self.assertIn("no-new-privileges:true", postgres_compose)
        self.assertIn("mem_limit: 512m", postgres_compose)

    def test_security_policy_matches_protected_production_scope(self) -> None:
        security_policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

        self.assertIn("owner-operated protected production API runtime", security_policy)
        self.assertIn("private owner channel", security_policy)
        self.assertNotIn("does not contain or claim a production runtime service", security_policy)
        self.assertIn("Do not open public issues containing secrets", security_policy)

    def test_local_no_secrets_scan_remains_clean(self) -> None:
        result = run_command("python3", "tools/no_secrets_scan.py")

        self.assertIn("No committed secrets detected.", result.stdout)


if __name__ == "__main__":
    unittest.main()
