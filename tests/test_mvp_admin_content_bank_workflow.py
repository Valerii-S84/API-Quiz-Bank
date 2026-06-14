from __future__ import annotations

from quizbank_mvp.database import connect, seed_control_fixture, utc_now

from tests.test_mvp_admin import APPROVED_FIXTURE, BASELINE_VERSION_ID, MvpAdminCase


class MvpAdminContentBankTests(MvpAdminCase):
    def test_admin_dashboard_includes_content_bank_version_aggregates(self) -> None:
        key = self.seed_admin()
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        insert_bank_version(self, "german-core:dashboard-draft", "dashboard-draft", "draft")

        response = self.client.get("/v1/admin/dashboard", headers=self.admin_headers(key))
        payload = response.json()
        baseline = aggregate_for(payload, BASELINE_VERSION_ID)
        draft = aggregate_for(payload, "german-core:dashboard-draft")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["items_by_language"]["de"], 1)
        self.assertEqual(baseline["language_code"], "de")
        self.assertEqual(baseline["content_bank_id"], "german-core")
        self.assertEqual(baseline["bank_version_status"], "active")
        self.assertEqual(baseline["item_count"], 1)
        self.assertEqual(baseline["approved_published_count"], 1)
        self.assertEqual(draft["bank_version_status"], "draft")
        self.assertEqual(draft["item_count"], 0)

    def test_read_only_admin_can_inspect_content_bank_workflow_surface(self) -> None:
        key = self.seed_admin("reviewer", "read_only_reviewer")
        insert_bank_version(self, "german-core:stage4-draft", "stage4-draft", "draft")

        languages = self.client.get("/v1/admin/languages", headers=self.admin_headers(key))
        banks = self.client.get("/v1/admin/content-banks", headers=self.admin_headers(key))
        versions = self.client.get(
            "/v1/admin/content-banks/german-core/versions",
            headers=self.admin_headers(key),
        )
        batches = self.client.get("/v1/admin/import-batches", headers=self.admin_headers(key))

        self.assertEqual(languages.status_code, 200)
        self.assertEqual(languages.json()["data"][0]["code"], "de")
        self.assertTrue(languages.json()["data"][0]["is_active"])
        self.assertEqual(banks.status_code, 200)
        self.assertEqual(banks.json()["data"][0]["language_code"], "de")
        self.assertEqual(banks.json()["data"][0]["active_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(versions.status_code, 200)
        self.assertEqual(versions.json()["data"][0]["status"], "active")
        self.assertEqual(batches.status_code, 200)
        self.assertEqual(batches.json()["data"], [])

    def test_owner_can_create_inactive_english_draft_bank_and_version(self) -> None:
        key = self.seed_admin("owner", "owner")

        bank = self.client.post(
            "/v1/admin/content-banks",
            json=english_bank_payload(),
            headers=self.admin_headers(key),
        )
        version = self.client.post(
            "/v1/admin/content-banks/english-core/versions",
            json={
                "version": "stage6-draft",
                "status": "draft",
                "reason": "create draft English onboarding version",
            },
            headers=self.admin_headers(key),
        )
        languages = self.client.get("/v1/admin/languages", headers=self.admin_headers(key))
        banks = self.client.get(
            "/v1/admin/content-banks?language_code=en",
            headers=self.admin_headers(key),
        )

        self.assertEqual(bank.status_code, 200)
        self.assertEqual(bank.json()["language_code"], "en")
        self.assertEqual(bank.json()["status"], "draft")
        self.assertEqual(version.status_code, 200)
        self.assertEqual(version.json()["bank_version_id"], "english-core:stage6-draft")
        self.assertEqual(version.json()["status"], "draft")
        self.assertFalse(language_by_code(languages.json(), "en")["is_active"])
        self.assertEqual(banks.json()["data"][0]["active_bank_version_id"], None)

    def test_admin_content_bank_actions_use_existing_activation_service(self) -> None:
        content_key = self.seed_admin("content_admin", "content_admin")
        owner_key = self.seed_admin("owner", "owner")
        draft_version_id = "german-core:stage4-draft"
        insert_bank_version(self, draft_version_id, "stage4-draft", "draft")

        mark_audit = self.client.post(
            f"/v1/admin/content-bank-versions/{draft_version_id}/mark-audit",
            json={"reason": "ready for owner activation"},
            headers=self.admin_headers(content_key),
        )
        denied_activate = self.client.post(
            f"/v1/admin/content-bank-versions/{draft_version_id}/activate",
            json={"reason": "content admin cannot activate"},
            headers=self.admin_headers(content_key),
        )
        activate = self.client.post(
            f"/v1/admin/content-bank-versions/{draft_version_id}/activate",
            json={"reason": "owner activates audited bank"},
            headers=self.admin_headers(owner_key),
        )
        rollback = self.client.post(
            f"/v1/admin/content-bank-versions/{BASELINE_VERSION_ID}/rollback",
            json={"reason": "owner rolls back to baseline"},
            headers=self.admin_headers(owner_key),
        )

        self.assertEqual(mark_audit.status_code, 200)
        self.assertEqual(mark_audit.json()["to_status"], "audit")
        self.assertEqual(denied_activate.status_code, 403)
        self.assertEqual(denied_activate.json()["reason_code"], "ADMIN_OWNER_REQUIRED")
        self.assertEqual(activate.status_code, 200)
        self.assertEqual(activate.json()["from_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(rollback.status_code, 200)
        self.assertEqual(rollback.json()["to_bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(bank_version_status(self, BASELINE_VERSION_ID), "active")
        self.assertEqual(bank_version_status(self, draft_version_id), "archived")

    def test_admin_import_batches_surface_filters_default_german_scope(self) -> None:
        key = self.seed_admin("reviewer", "read_only_reviewer")
        create_import_batches_table(self)
        insert_import_batch(self, "stage4_import_batch")

        response = self.client.get(
            "/v1/admin/import-batches?content_bank_id=german-core",
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 200)
        batch = response.json()["data"][0]
        self.assertEqual(batch["import_batch_id"], "stage4_import_batch")
        self.assertEqual(batch["language_code"], "de")
        self.assertEqual(batch["content_bank_id"], "german-core")
        self.assertEqual(batch["bank_version_id"], BASELINE_VERSION_ID)
        self.assertEqual(batch["bank_version_status"], "active")


def english_bank_payload() -> dict[str, str]:
    return {
        "content_bank_id": "english-core",
        "slug": "english-core",
        "language_code": "en",
        "name": "English Core",
        "status": "draft",
        "reason": "create draft English onboarding bank",
    }


def insert_bank_version(case: MvpAdminCase, bank_version_id: str, version: str, status: str) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO content_bank_versions (
                id, content_bank_id, version, status, activated_at, created_at
            ) VALUES (?, 'german-core', ?, ?, NULL, ?)
            """,
            (bank_version_id, version, status, utc_now()),
        )


def bank_version_status(case: MvpAdminCase, bank_version_id: str) -> str:
    with connect(case.db_path) as connection:
        row = connection.execute(
            "SELECT status FROM content_bank_versions WHERE id = ?",
            (bank_version_id,),
        ).fetchone()
    return str(row["status"])


def aggregate_for(payload: dict[str, object], bank_version_id: str) -> dict[str, object]:
    for aggregate in payload["items_by_bank_version"]:
        if aggregate["bank_version_id"] == bank_version_id:
            return aggregate
    raise AssertionError(f"missing aggregate for {bank_version_id}")


def language_by_code(payload: dict[str, object], language_code: str) -> dict[str, object]:
    for language in payload["data"]:
        if language["code"] == language_code:
            return language
    raise AssertionError(f"missing language {language_code}")


def create_import_batches_table(case: MvpAdminCase) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            CREATE TABLE import_batches (
                import_batch_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                parser_profile_id TEXT NOT NULL,
                import_mode TEXT NOT NULL,
                import_status TEXT NOT NULL,
                language_code TEXT NOT NULL,
                content_bank_id TEXT NOT NULL,
                bank_version_id TEXT NOT NULL,
                default_item_status TEXT NOT NULL,
                row_count_detected INTEGER NOT NULL,
                accepted_candidate_count INTEGER NOT NULL,
                rejected_candidate_count INTEGER NOT NULL,
                report_uri TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                created_by TEXT NOT NULL
            )
            """
        )


def insert_import_batch(case: MvpAdminCase, import_batch_id: str) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO import_batches (
                import_batch_id, source_id, parser_profile_id, import_mode,
                import_status, language_code, content_bank_id, bank_version_id,
                default_item_status, row_count_detected, accepted_candidate_count,
                rejected_candidate_count, report_uri, started_at, completed_at,
                created_by
            ) VALUES (?, 'src_control_mvp', 'control_profile', 'dry_run',
                      'dry_run_passed', 'de', 'german-core', ?, 'draft',
                      12, 12, 0, 'reports/imports/stage4.json', ?, ?, 'owner')
            """,
            (import_batch_id, BASELINE_VERSION_ID, utc_now(), utc_now()),
        )
