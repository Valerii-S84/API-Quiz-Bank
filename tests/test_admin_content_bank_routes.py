from __future__ import annotations

from quizbank_mvp.database import seed_control_fixture

from tests.test_mvp_admin import APPROVED_FIXTURE, BASELINE_VERSION_ID, MvpAdminCase


class AdminContentBankRouteTests(MvpAdminCase):
    def test_owner_manages_language_bank_and_english_version_activation(self) -> None:
        key = self.seed_admin("owner", "owner")

        languages = self.client.get("/v1/admin/languages", headers=self.admin_headers(key))
        default_banks = self.client.get("/v1/admin/content-banks", headers=self.admin_headers(key))
        created_bank = self.client.post(
            "/v1/admin/content-banks",
            json=bank_payload(),
            headers=self.admin_headers(key),
        )
        duplicate_bank = self.client.post(
            "/v1/admin/content-banks",
            json=bank_payload(),
            headers=self.admin_headers(key),
        )
        created_version = self.client.post(
            "/v1/admin/content-banks/english-core/versions",
            json=version_payload("stage6-draft"),
            headers=self.admin_headers(key),
        )
        listed_versions = self.client.get(
            "/v1/admin/content-banks/english-core/versions",
            headers=self.admin_headers(key),
        )
        mark_audit = self.client.post(
            "/v1/admin/content-bank-versions/english-core:stage6-draft/mark-audit",
            json={"reason": "ready for audit"},
            headers=self.admin_headers(key),
        )
        activate = self.client.post(
            "/v1/admin/content-bank-versions/english-core:stage6-draft/activate",
            json={"reason": "activate English bank"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(languages.status_code, 200)
        self.assertEqual(
            {row["code"]: row["is_active"] for row in languages.json()["data"]},
            {"de": True, "en": False, "fr": False, "es": False, "nl": False},
        )
        self.assertEqual(default_banks.json()["data"][0]["active_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(created_bank.status_code, 200)
        self.assertEqual(duplicate_bank.status_code, 409)
        self.assertEqual(duplicate_bank.json()["reason_code"], "ADMIN_CONTENT_BANK_WORKFLOW_CONFLICT")
        self.assertEqual(created_version.json()["status"], "draft")
        self.assertEqual(listed_versions.json()["data"][0]["bank_version_id"], "english-core:stage6-draft")
        self.assertEqual(mark_audit.status_code, 200)
        self.assertEqual(activate.json()["to_bank_version_id"], "english-core:stage6-draft")

    def test_owner_rolls_back_active_german_bank_version(self) -> None:
        key = self.seed_admin("owner", "owner")
        create_german_candidate(self, key)
        activated_candidate = self.client.post(
            "/v1/admin/content-bank-versions/german-core:rollback-candidate/activate",
            json={"reason": "activate candidate"},
            headers=self.admin_headers(key),
        )
        rollback = self.client.post(
            f"/v1/admin/content-bank-versions/{BASELINE_VERSION_ID}/rollback",
            json={"reason": "restore baseline"},
            headers=self.admin_headers(key),
        )
        active_conflict = self.client.post(
            f"/v1/admin/content-bank-versions/{BASELINE_VERSION_ID}/activate",
            json={"reason": "already active"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(activated_candidate.status_code, 200)
        self.assertEqual(rollback.status_code, 200)
        self.assertEqual(rollback.json()["from_bank_version_id"], "german-core:rollback-candidate")
        self.assertEqual(active_conflict.status_code, 409)

    def test_admin_content_bank_read_routes_return_controlled_results(self) -> None:
        key = self.seed_admin("reviewer", "read_only_reviewer")
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

        item = self.client.get(
            "/v1/admin/quiz-items/approved_traceable_001",
            headers=self.admin_headers(key),
        )
        audit_log = self.client.get("/v1/admin/audit-log", headers=self.admin_headers(key))
        import_batches = self.client.get("/v1/admin/import-batches", headers=self.admin_headers(key))
        missing_versions = self.client.get(
            "/v1/admin/content-banks/missing/versions",
            headers=self.admin_headers(key),
        )

        self.assertEqual(item.status_code, 200)
        self.assertEqual(item.json()["item_id"], "approved_traceable_001")
        self.assertEqual(audit_log.status_code, 200)
        self.assertEqual(import_batches.status_code, 200)
        self.assertEqual(import_batches.json()["data"], [])
        self.assertEqual(missing_versions.status_code, 404)
        self.assertEqual(missing_versions.json()["reason_code"], "ADMIN_CONTENT_BANK_NOT_FOUND")


def bank_payload() -> dict[str, str]:
    return {
        "content_bank_id": "english-core",
        "language_code": "en",
        "name": "English Core",
        "reason": "stage language bank",
    }


def version_payload(version: str, status: str = "draft") -> dict[str, str]:
    return {"version": version, "status": status, "reason": f"create {version}"}


def create_german_candidate(case: MvpAdminCase, key: str) -> None:
    response = case.client.post(
        "/v1/admin/content-banks/german-core/versions",
        json=version_payload("rollback-candidate", "audit"),
        headers=case.admin_headers(key),
    )
    case.assertEqual(response.status_code, 200)
