from __future__ import annotations

import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp import admin_service  # noqa: E402
from quizbank_mvp.cli import seed_admin as seed_owner_password  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_admin_credential,
    seed_consumer,
    seed_control_fixture,
    utc_now,
)
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy, VisualSettings  # noqa: E402
from quizbank_mvp.visual_settings import save_visual_settings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"


class MvpAdminCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        self.client = TestClient(create_app(self.db_path))

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def seed_admin(self, actor: str = "admin_owner", role: str = "owner") -> str:
        key = f"{actor}_admin_key"
        seed_admin_credential(self.db_path, actor, role, key)
        return key

    def admin_headers(self, key: str) -> dict[str, str]:
        return {"X-QuizBank-Admin-Key": key}


class MvpAdminEndpointTests(MvpAdminCase):
    def test_admin_routes_are_reflected_in_committed_openapi_seed(self) -> None:
        committed_openapi = (ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
        app_paths = set(create_app(self.db_path).openapi()["paths"])

        for path in [
            "/admin",
            "/v1/admin/dashboard",
            "/v1/admin/quiz-items",
            "/v1/admin/quiz-items/{item_id}",
            "/v1/admin/quiz-items/{item_id}/approve",
            "/v1/admin/quiz-items/{item_id}/publish",
            "/v1/admin/quiz-items/{item_id}/retire",
            "/v1/admin/quiz-items/{item_id}/block",
            "/v1/admin/audit-log",
            "/v1/admin/consumers",
            "/v1/admin/consumers/{consumer_id}/visual-settings",
            "/v1/admin/consumers/{consumer_id}/suspend",
            "/v1/admin/consumers/{consumer_id}/activate",
            "/v1/admin/consumers/{consumer_id}/block",
        ]:
            self.assertIn(path, app_paths)
            self.assertIn(f"  {path}:", committed_openapi)

    def test_admin_panel_shell_is_available_without_data_access(self) -> None:
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn("API Quiz Bank Admin", response.text)
        self.assertIn("Admin password", response.text)

    def test_admin_reads_require_admin_key(self) -> None:
        response = self.client.get("/v1/admin/dashboard")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["reason_code"], "ADMIN_AUTH_REQUIRED")

    def test_admin_key_is_hashed_and_can_read_dashboard(self) -> None:
        key = self.seed_admin()
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

        response = self.client.get("/v1/admin/dashboard", headers=self.admin_headers(key))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["approved_published_count"], 1)
        with connect(self.db_path) as connection:
            credential = connection.execute("SELECT key_prefix, key_hash FROM admin_credentials").fetchone()
        self.assertEqual(credential["key_prefix"], key[:12])
        self.assertNotEqual(credential["key_hash"], key)

    def test_admin_dashboard_includes_visual_metrics_summary(self) -> None:
        key = self.seed_admin()
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        save_visual_settings(self.db_path, visual_settings("consumer_visual"))
        insert_visual_usage_event(self, "vusage_cache", "cache_hit")
        insert_visual_usage_event(self, "vusage_fallback", "fallback_used")
        insert_visual_usage_event(self, "vusage_generation", "generation_requested")

        response = self.client.get("/v1/admin/dashboard", headers=self.admin_headers(key))
        visual = response.json()["visual_metrics"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(visual["settings_by_mode"]["image_standard"], 1)
        self.assertEqual(visual["event_counts"]["cache_hit"], 1)
        self.assertEqual(visual["generation_count_by_consumer"]["consumer_visual"], 1)
        self.assertEqual(visual["cache_hit_rate"], 0.5)
        self.assertEqual(visual["fallback_rate"], 0.5)

    def test_read_only_reviewer_can_list_items_but_cannot_write(self) -> None:
        key = self.seed_admin("reviewer", "read_only_reviewer")
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")

        list_response = self.client.get("/v1/admin/quiz-items", headers=self.admin_headers(key))
        write_response = self.client.post(
            "/v1/admin/quiz-items/approved_traceable_001/approve",
            json={"reason": "reviewer cannot approve"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["data"][0]["status"], "draft")
        self.assertEqual(write_response.status_code, 403)
        self.assertEqual(write_response.json()["reason_code"], "ADMIN_WRITE_DENIED")

    def test_content_admin_can_approve_publish_and_create_audit_evidence(self) -> None:
        key = self.seed_admin("content_admin", "content_admin")
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")

        approve = self.client.post(
            "/v1/admin/quiz-items/approved_traceable_001/approve",
            json={"reason": "metadata checked"},
            headers=self.admin_headers(key),
        )
        publish = self.client.post(
            "/v1/admin/quiz-items/approved_traceable_001/publish",
            json={"reason": "ready for delivery"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(approve.status_code, 200)
        self.assertEqual(publish.status_code, 200)
        self.assertEqual(publish.json()["item"]["status"], "published")
        self.assertEqual(publish.json()["audit"]["actor"], "content_admin")
        self.assertEqual(self.audit_count(), 2)

    def test_invalid_admin_transition_uses_problem_details(self) -> None:
        key = self.seed_admin("content_admin", "content_admin")
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")

        response = self.client.post(
            "/v1/admin/quiz-items/approved_traceable_001/publish",
            json={"reason": "cannot publish draft directly"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["content-type"], "application/problem+json")
        self.assertEqual(response.json()["reason_code"], "ADMIN_INVALID_STATUS_TRANSITION")

    def test_cli_owner_password_setup_allows_only_one_configured_admin(self) -> None:
        first_args = AdminSeedArgs(self.db_path, reset=False)
        with mock.patch("quizbank_mvp.cli.prompt_admin_password", return_value="owner_password"):
            seed_owner_password(first_args)

        response = self.client.get(
            "/v1/admin/dashboard",
            headers=self.admin_headers("owner_password"),
        )
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(SystemExit):
            with mock.patch("quizbank_mvp.cli.prompt_admin_password", return_value="second_password"):
                seed_owner_password(AdminSeedArgs(self.db_path, reset=False))

    def test_cli_owner_password_reset_replaces_existing_admin_credentials(self) -> None:
        seed_admin_credential(self.db_path, "old_admin", "owner", "old_password")

        with mock.patch("quizbank_mvp.cli.prompt_admin_password", return_value="new_password"):
            seed_owner_password(AdminSeedArgs(self.db_path, reset=True))

        old_response = self.client.get("/v1/admin/dashboard", headers=self.admin_headers("old_password"))
        new_response = self.client.get("/v1/admin/dashboard", headers=self.admin_headers("new_password"))
        self.assertEqual(old_response.status_code, 401)
        self.assertEqual(new_response.status_code, 200)

    def test_owner_can_create_list_and_suspend_consumer_access(self) -> None:
        key = self.seed_admin("owner", "owner")

        create_response = self.client.post(
            "/v1/admin/consumers",
            json={
                "consumer_id": "telegram_channel_a2",
                "display_name": "A2 Telegram Channel",
                "consumer_kind": "telegram_channel",
                "daily_quota_limit": 3,
                "allowed_cefr_levels": ["A2"],
                "allowed_theme_ids": ["T10"],
                "api_key": "channel_access_password",
                "reason": "owner created Telegram channel access",
            },
            headers=self.admin_headers(key),
        )
        list_response = self.client.get("/v1/admin/consumers", headers=self.admin_headers(key))
        suspend_response = self.client.post(
            "/v1/admin/consumers/telegram_channel_a2/suspend",
            json={"reason": "pause channel delivery"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.json()["consumer_kind"], "telegram_channel")
        self.assertEqual(list_response.json()["data"][0]["display_name"], "A2 Telegram Channel")
        self.assertEqual(suspend_response.status_code, 200)
        self.assertEqual(suspend_response.json()["status"], "suspended")

    def test_non_owner_admin_cannot_create_consumer_access(self) -> None:
        key = self.seed_admin("content_admin", "content_admin")

        response = self.client.post(
            "/v1/admin/consumers",
            json={
                "consumer_id": "api_client_test",
                "display_name": "API Client",
                "consumer_kind": "api_client",
                "daily_quota_limit": 1,
                "allowed_cefr_levels": ["A2"],
                "allowed_theme_ids": ["T10"],
                "api_key": "api_client_password",
                "reason": "should be owner-only",
            },
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "ADMIN_OWNER_REQUIRED")

    def audit_count(self) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM audit_log WHERE entity_type = 'quiz_item'"
            ).fetchone()
        return int(row["count"])


class MvpAdminVisualSettingsTests(MvpAdminCase):
    def test_owner_can_configure_visual_settings(self) -> None:
        key = self.seed_admin("owner", "owner")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

        patch = self.client.patch(
            "/v1/admin/consumers/consumer_visual/visual-settings",
            json={
                "delivery_mode": "image_standard",
                "visual_style": "standard_illustration",
                "branding_preset": "none",
                "fallback_policy": "text_only",
                "daily_visual_delivery_limit": 3,
                "daily_generation_limit": 2,
                "monthly_generation_limit": 10,
                "is_active": True,
                "reason": "enable standard visual pilot",
            },
            headers=self.admin_headers(key),
        )
        get = self.client.get(
            "/v1/admin/consumers/consumer_visual/visual-settings",
            headers=self.admin_headers(key),
        )

        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["settings"]["delivery_mode"], "image_standard")
        self.assertEqual(patch.json()["audit"]["action"], "visual_settings_update")
        self.assertEqual(get.json()["delivery_mode"], "image_standard")
        self.assertEqual(self.visual_audit_count(), 1)

    def test_invalid_visual_mode_is_rejected(self) -> None:
        key = self.seed_admin("owner", "owner")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

        response = self.client.patch(
            "/v1/admin/consumers/consumer_visual/visual-settings",
            json={"delivery_mode": "video", "reason": "invalid mode"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 422)

    def test_non_owner_cannot_mutate_visual_settings(self) -> None:
        key = self.seed_admin("content_admin", "content_admin")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

        response = self.client.patch(
            "/v1/admin/consumers/consumer_visual/visual-settings",
            json={"delivery_mode": "image_standard", "reason": "not owner"},
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "ADMIN_OWNER_REQUIRED")

    def test_non_owner_cannot_read_visual_settings(self) -> None:
        key = self.seed_admin("content_admin", "content_admin")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])

        response = self.client.get(
            "/v1/admin/consumers/consumer_visual/visual-settings",
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["reason_code"], "ADMIN_OWNER_REQUIRED")

    def test_visual_settings_for_missing_consumer_are_not_exposed(self) -> None:
        key = self.seed_admin("owner", "owner")

        response = self.client.get(
            "/v1/admin/consumers/missing_consumer/visual-settings",
            headers=self.admin_headers(key),
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["reason_code"], "ADMIN_CONSUMER_NOT_FOUND")

    def visual_audit_count(self) -> int:
        with connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM audit_log
                WHERE action = 'visual_settings_update'
                """
            ).fetchone()
        return int(row["count"])


def visual_settings(consumer_id: str) -> VisualSettings:
    return VisualSettings(
        consumer_id=consumer_id,
        delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
        visual_style="standard_illustration",
        branding_preset="none",
        fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
        daily_visual_delivery_limit=5,
        daily_generation_limit=5,
        monthly_generation_limit=20,
        is_active=True,
    )


def insert_visual_usage_event(case: MvpAdminCase, usage_event_id: str, event_type: str) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO visual_usage_events (
                usage_event_id, consumer_id, event_type, feature, quantity,
                estimated_cost_minor, provider_name, created_at
            ) VALUES (?, 'consumer_visual', ?, 'visual_delivery.standard', 1, 0, 'local', ?)
            """,
            (usage_event_id, event_type, utc_now()),
        )


class MvpAdminServiceTests(MvpAdminCase):
    def test_admin_service_reports_missing_quiz_item_as_problem(self) -> None:
        with self.assertRaises(Exception) as error:
            admin_service.get_admin_quiz_item(self.db_path, "missing_item")

        self.assertEqual(error.exception.reason_code, "ADMIN_ITEM_NOT_FOUND")

    def test_admin_service_filters_items_and_lists_audit_rows(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")
        admin_service.change_admin_quiz_item_status(
            self.db_path,
            "approved_traceable_001",
            "approve",
            "content_admin",
            "metadata checked",
        )

        filtered = admin_service.list_admin_quiz_items(
            self.db_path,
            {
                "status": "approved",
                "cefr_level": "A2",
                "theme_id": "T10",
                "source_id": "src_control_mvp",
            },
            10,
        )
        audit_rows = admin_service.list_audit_log(self.db_path, 10)

        self.assertEqual(filtered["data"][0]["item_id"], "approved_traceable_001")
        self.assertEqual(audit_rows["data"][0]["action"], "status_transition")

    def test_admin_service_maps_transition_errors_to_problem_details(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "draft")
        seed_consumer(self.db_path, "consumer_active", 2, ["A2"], ["T10"])

        with self.assertRaises(Exception) as missing_item:
            admin_service.change_admin_quiz_item_status(
                self.db_path,
                "missing_item",
                "approve",
                "content_admin",
                "metadata checked",
            )
        with self.assertRaises(Exception) as invalid_consumer_transition:
            admin_service.change_admin_consumer_status(
                self.db_path,
                "consumer_active",
                "active",
                "owner",
                "invalid no-op",
            )
        with self.assertRaises(Exception) as missing_consumer:
            admin_service.change_admin_consumer_status(
                self.db_path,
                "missing_consumer",
                "blocked",
                "owner",
                "missing consumer",
            )
        with self.assertRaises(Exception) as missing_consumer_read:
            admin_service.get_admin_consumer(self.db_path, "missing_consumer")

        self.assertEqual(missing_item.exception.reason_code, "ADMIN_ITEM_NOT_FOUND")
        self.assertEqual(
            invalid_consumer_transition.exception.reason_code,
            "ADMIN_INVALID_CONSUMER_TRANSITION",
        )
        self.assertEqual(missing_consumer.exception.reason_code, "ADMIN_CONSUMER_NOT_FOUND")
        self.assertEqual(missing_consumer_read.exception.reason_code, "ADMIN_CONSUMER_NOT_FOUND")


class AdminSeedArgs:
    def __init__(self, db_path: Path, reset: bool) -> None:
        self.db_path = db_path
        self.reset = reset


if __name__ == "__main__":
    unittest.main()
