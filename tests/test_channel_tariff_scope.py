from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.protected_beta_config import load_protected_beta_channels  # noqa: E402
from quizbank_mvp.protected_beta_config import parse_protected_beta_channels  # noqa: E402
from quizbank_mvp.protected_beta_slot_runs import scheduled_slot_idempotency_key  # noqa: E402
from quizbank_mvp.selection import QuizBankProblem, SelectionFilters, SelectionRequest  # noqa: E402
from quizbank_mvp.selection import enforce_entitlement_scope  # noqa: E402
from quizbank_mvp.selection import select_next_item  # noqa: E402
from quizbank_mvp.selection_models import ContentScope  # noqa: E402
from quizbank_mvp.telegram_delivery import TelegramDeliveryRequest, run_telegram_delivery  # noqa: E402
from quizbank_mvp.visual_cache import compute_visual_cache_key  # noqa: E402
from quizbank_mvp.visual_models import VisualDeliveryMode, VisualFallbackPolicy  # noqa: E402
from quizbank_mvp.visual_models import VisualSettings  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
DEFAULT_BANK_VERSION_ID = "german-core:2026-06-12-baseline"


class ChannelTariffScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_protected_beta_config_defaults_to_german_scope(self) -> None:
        channels = load_protected_beta_channels()

        self.assertTrue(channels)
        for channel in channels:
            self.assertEqual(channel.default_language_code, "de")
            self.assertEqual(channel.default_content_bank_slug, "german-core")
            self.assertEqual(channel.allowed_language_codes, ("de",))
            self.assertEqual(channel.allowed_content_bank_slugs, ("german-core",))

    def test_channel_allowed_scopes_block_wrong_language_and_bank(self) -> None:
        with self.assertRaisesRegex(ValueError, "language_code.*allowed_language_codes"):
            parse_protected_beta_channels(raw_channel_config(slot_scope={"language_code": "en"}))

        with self.assertRaisesRegex(ValueError, "content_bank_slug.*allowed_content_bank_slugs"):
            parse_protected_beta_channels(raw_channel_config(slot_scope={"content_bank_slug": "english-core"}))

    def test_scheduled_slot_idempotency_differs_by_language_bank_and_version(self) -> None:
        base = self.slot_key(ContentScope("de", "german-core", "german-core:v1"))
        other_language = self.slot_key(ContentScope("en", "english-core", "english-core:v1"))
        other_version = self.slot_key(ContentScope("de", "german-core", "german-core:v2"))

        self.assertEqual(len({base, other_language, other_version}), 3)

    def test_telegram_delivery_uses_resolved_bank_version(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_quiz_access()

        result = run_telegram_delivery(
            self.db_path,
            TelegramDeliveryRequest(
                consumer_id="consumer_allowed",
                chat_id="@unit_test",
                mode="dry_run",
                cefr_level="A2",
                theme_ids=("T10",),
            ),
        )

        self.assertEqual(result.bank_version_id, DEFAULT_BANK_VERSION_ID)
        self.assertEqual(self.single_delivery()["bank_version_id"], DEFAULT_BANK_VERSION_ID)

    def test_plan_catalog_exposes_language_and_bank_scope(self) -> None:
        catalog = json.loads((ROOT / "data" / "billing" / "plan_catalog.json").read_text())

        for plan in catalog["plans"]:
            for feature in plan["features"]:
                with self.subTest(plan=plan["plan_code"], feature=feature["feature_code"]):
                    self.assertEqual(feature["scope"]["language_codes"], ["de"])
                    self.assertEqual(feature["scope"]["content_bank_slugs"], ["german-core"])
                    self.assertTrue(feature["scope"]["content_types"])

    def test_entitlement_blocks_wrong_content_bank(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_quiz_access(allowed_banks=["german-core", "german-alt"])
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"])
        self.insert_alternate_german_bank()
        self.clone_item_to_alternate_bank("alternate_bank_item")

        with self.assertRaises(QuizBankProblem) as raised:
            select_next_item(self.db_path, self.request(content_bank_id="german-alt"))

        self.assertEqual(raised.exception.reason_code, "ENTITLEMENT_CONTENT_BANK_NOT_ALLOWED")

    def test_entitlement_blocks_wrong_language_without_importing_bank(self) -> None:
        entitlement = {
            "allowed_language_codes_json": '["de"]',
            "allowed_content_bank_ids_json": '["german-core"]',
            "allowed_bank_version_ids_json": "[]",
            "allowed_cefr_levels_json": "[]",
            "allowed_theme_ids_json": "[]",
        }
        request = SelectionRequest(
            consumer_id="consumer_allowed",
            language_code="en",
            content_bank_id="german-core",
            bank_version_id=DEFAULT_BANK_VERSION_ID,
        )

        with self.assertRaises(QuizBankProblem) as raised:
            enforce_entitlement_scope(entitlement, request)

        self.assertEqual(raised.exception.reason_code, "ENTITLEMENT_LANGUAGE_NOT_ALLOWED")

    def test_quota_usage_isolated_by_content_bank(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_quiz_access(daily_quota_limit=1, allowed_banks=["german-core", "german-alt"])
        self.insert_alternate_german_bank()
        self.clone_item_to_alternate_bank("alternate_quota_item")

        default_result = select_next_item(self.db_path, self.request())
        alternate_result = select_next_item(self.db_path, self.request(content_bank_id="german-alt"))

        self.assertEqual(default_result["delivery"]["content_bank_id"], "german-core")
        self.assertEqual(alternate_result["delivery"]["content_bank_id"], "german-alt")
        self.assertEqual(self.quota_scopes(), [("german-alt", 1), ("german-core", 1)])

    def test_visual_cache_key_differs_for_different_bank_versions(self) -> None:
        settings = visual_settings()
        first = compute_visual_cache_key(self.visual_item(DEFAULT_BANK_VERSION_ID), settings)
        second = compute_visual_cache_key(self.visual_item("german-core:replacement"), settings)

        self.assertNotEqual(first, second)

    def test_existing_german_selection_without_scope_stays_compatible(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_quiz_access()

        result = select_next_item(self.db_path, self.request())

        self.assertEqual(result["delivery"]["language_code"], "de")
        self.assertEqual(result["delivery"]["content_bank_id"], "german-core")
        self.assertEqual(result["quiz_item"]["bank_version_id"], DEFAULT_BANK_VERSION_ID)

    def slot_key(self, content_scope: ContentScope) -> str:
        return scheduled_slot_idempotency_key(
            "consumer",
            "channel",
            "2026-06-13",
            "slot",
            content_scope,
            "A2",
            "T10",
        )

    def seed_quiz_access(
        self,
        daily_quota_limit: int = 5,
        allowed_banks: list[str] | None = None,
    ) -> None:
        content_scope = {
            "allowed_language_codes": ["de"],
            "allowed_content_bank_ids": allowed_banks or ["german-core"],
        }
        seed_consumer(self.db_path, "consumer_allowed", daily_quota_limit, ["A2"], ["T10"], content_scope)
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"], content_scope=content_scope)

    def request(self, content_bank_id: str | None = None) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            content_bank_id=content_bank_id,
            deterministic=True,
        )

    def insert_alternate_german_bank(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO content_banks (
                    id, slug, language_code, name, status, created_at
                ) VALUES (
                    'german-alt', 'german-alt', 'de', 'German Alt', 'active',
                    '2026-06-13T00:00:00Z'
                )
                """
            )
            connection.execute(
                """
                INSERT INTO content_bank_versions (
                    id, content_bank_id, version, status, activated_at, created_at
                ) VALUES (
                    'german-alt:v1', 'german-alt', 'v1', 'active',
                    '2026-06-13T00:00:00Z', '2026-06-13T00:00:00Z'
                )
                """
            )

    def clone_item_to_alternate_bank(self, item_id: str) -> None:
        with connect(self.db_path) as connection:
            connection.execute(clone_item_sql(item_id))

    def single_delivery(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM deliveries").fetchone()

    def quota_scopes(self) -> list[tuple[str, int]]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT content_bank_id, used_count
                FROM quota_usage
                ORDER BY content_bank_id
                """
            ).fetchall()
        return [(str(row["content_bank_id"]), int(row["used_count"])) for row in rows]

    def visual_item(self, bank_version_id: str) -> dict[str, str]:
        return {
            "item_id": "same_item",
            "language": "de",
            "language_code": "de",
            "content_bank_id": "german-core",
            "bank_version_id": bank_version_id,
        }


def raw_channel_config(slot_scope: dict[str, str]) -> dict[str, object]:
    slot = {
        "local_time": "08:00",
        "cefr_level": "A2",
        "theme_id": "T10",
        "quiz_count": 1,
        **slot_scope,
    }
    return {
        "channels": [
            {
                "consumer_id": "test_channel",
                "chat_id": "@test",
                "display_name": "Test Channel",
                "timezone": "Europe/Berlin",
                "daily_quota_limit": 1,
                "default_language_code": "de",
                "default_content_bank_slug": "german-core",
                "allowed_language_codes": ["de"],
                "allowed_content_bank_slugs": ["german-core"],
                "schedule_batches": [{"local_time": "08:00", "slots": [slot]}],
            }
        ]
    }


def clone_item_sql(item_id: str) -> str:
    return f"""
        INSERT INTO quiz_items (
            item_id, source_id, language, language_code, content_bank_id,
            bank_version_id, level_band, sublevel, theme_id, subtheme_id,
            objective_id, pattern_id, difficulty_band, register, prompt,
            stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id, status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        )
        SELECT
            '{item_id}', source_id, language, language_code,
            'german-alt', 'german-alt:v1', level_band, sublevel,
            theme_id, subtheme_id, objective_id, pattern_id, difficulty_band,
            register, prompt, stem_text, options_json, answer_key, explanation,
            tags, coverage_cell_id || '::german-alt', status, version,
            created_at, updated_at, reviewed_at, level_locked, locked_at
        FROM quiz_items
        WHERE item_id = 'approved_traceable_001'
    """


def visual_settings() -> VisualSettings:
    return VisualSettings(
        consumer_id="consumer_visual",
        delivery_mode=VisualDeliveryMode.IMAGE_STANDARD,
        visual_style="standard_illustration",
        branding_preset="none",
        fallback_policy=VisualFallbackPolicy.TEXT_ONLY,
        daily_visual_delivery_limit=3,
        daily_generation_limit=3,
        monthly_generation_limit=10,
        is_active=True,
    )


if __name__ == "__main__":
    unittest.main()
