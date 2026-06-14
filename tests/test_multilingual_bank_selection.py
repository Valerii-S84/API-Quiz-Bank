from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection import QuizBankProblem, SelectionFilters, SelectionRequest, select_next_item  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
DEFAULT_BANK_VERSION_ID = "german-core:2026-06-12-baseline"


class MultilingualBankSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        self.client = TestClient(create_app(self.db_path))

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_next_item_defaults_to_german_scope_and_returns_it(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access(with_api_key=True)

        response = self.client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": "consumer_allowed", "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={
                "X-Consumer-Id": "consumer_allowed",
                "X-QuizBank-API-Key": "consumer_allowed_key",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assert_response_scope(payload)
        decision = self.single_decision()
        self.assertEqual(decision["language_code"], "de")
        self.assertEqual(decision["content_bank_id"], "german-core")
        self.assertEqual(decision["bank_version_id"], DEFAULT_BANK_VERSION_ID)
        self.assertEqual(json.loads(decision["filters_json"])["language_code"], "de")

    def test_default_german_selection_ignores_draft_english_bank(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()
        self.insert_english_draft_bank_item()
        self.block_german_item()

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(self.db_path, self.selection_request())

        self.assertEqual(error.exception.reason_code, "SELECTION_NO_ELIGIBLE_ITEM")
        self.assertEqual(error.exception.extra["selection_context"]["decision"]["candidate_count"], 0)

    def test_explicit_archived_bank_version_is_not_used_for_new_delivery(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()
        self.insert_archived_german_version()

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(
                self.db_path,
                self.selection_request(bank_version_id="german-core:archived"),
            )

        self.assertEqual(error.exception.status, 404)
        self.assertEqual(error.exception.reason_code, "BANK_VERSION_NOT_AVAILABLE")

    def test_explicit_inactive_language_is_rejected_before_selection(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(self.db_path, self.selection_request(language_code="en"))

        self.assertEqual(error.exception.status, 403)
        self.assertEqual(error.exception.reason_code, "LANGUAGE_NOT_ACTIVE")

    def test_inactive_english_draft_bank_cannot_be_selected_even_if_allowed(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.insert_english_draft_bank_item()
        self.seed_access(
            content_scope={
                "allowed_language_codes": ["de", "en"],
                "allowed_content_bank_ids": ["german-core", "english-core"],
                "allowed_bank_version_ids": ["english-core:stage6-draft"],
            },
        )

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(
                self.db_path,
                self.selection_request(
                    language_code="en",
                    content_bank_id="english-core",
                    bank_version_id="english-core:stage6-draft",
                ),
            )

        self.assertEqual(error.exception.status, 403)
        self.assertEqual(error.exception.reason_code, "LANGUAGE_NOT_ACTIVE")

    def test_explicit_unsupported_language_is_controlled_error(self) -> None:
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        self.seed_access()

        with self.assertRaises(QuizBankProblem) as error:
            select_next_item(self.db_path, self.selection_request(language_code="it"))

        self.assertEqual(error.exception.status, 400)
        self.assertEqual(error.exception.reason_code, "LANGUAGE_UNSUPPORTED")

    def seed_access(
        self,
        with_api_key: bool = False,
        content_scope: dict[str, object] | None = None,
    ) -> None:
        seed_consumer(self.db_path, "consumer_allowed", 5, ["A2"], ["T10"], content_scope)
        seed_entitlement(self.db_path, "consumer_allowed", ["A2"], ["T10"], content_scope=content_scope)
        if with_api_key:
            seed_api_credential(self.db_path, "consumer_allowed", "consumer_allowed_key")

    def selection_request(
        self,
        language_code: str | None = None,
        content_bank_id: str | None = None,
        bank_version_id: str | None = None,
    ) -> SelectionRequest:
        return SelectionRequest(
            consumer_id="consumer_allowed",
            filters=SelectionFilters(cefr_level="A2", theme_ids=("T10",)),
            language_code=language_code,
            content_bank_id=content_bank_id,
            bank_version_id=bank_version_id,
            deterministic=True,
        )

    def assert_response_scope(self, payload: dict[str, object]) -> None:
        for projection_key in ["delivery", "quiz_item"]:
            projection = payload[projection_key]
            self.assertEqual(projection["language_code"], "de")
            self.assertEqual(projection["content_bank_id"], "german-core")
            self.assertEqual(projection["bank_version_id"], DEFAULT_BANK_VERSION_ID)
        self.assertEqual(payload["language_code"], "de")
        self.assertEqual(payload["content_bank_id"], "german-core")
        self.assertEqual(payload["bank_version_id"], DEFAULT_BANK_VERSION_ID)

    def insert_english_draft_bank_item(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(insert_english_bank_sql())
            connection.execute(insert_english_version_sql())
            connection.execute(insert_english_source_sql())
            connection.execute(clone_item_sql("english_draft_001", "en", "english-core:stage6-draft"))

    def insert_archived_german_version(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO content_bank_versions (
                    id, content_bank_id, version, status, activated_at, created_at
                ) VALUES (
                    'german-core:archived',
                    'german-core',
                    'archived',
                    'archived',
                    '2026-06-12T00:00:00Z',
                    '2026-06-12T00:00:00Z'
                )
                """
            )

    def block_german_item(self) -> None:
        with connect(self.db_path) as connection:
            connection.execute(
                "UPDATE quiz_items SET status = 'blocked' WHERE item_id = 'approved_traceable_001'"
            )

    def single_decision(self):
        with connect(self.db_path) as connection:
            return connection.execute("SELECT * FROM selection_decisions").fetchone()


def insert_english_bank_sql() -> str:
    return """
        INSERT INTO content_banks (
            id, slug, language_code, name, status, created_at
        ) VALUES (
            'english-core', 'english-core', 'en', 'English Core', 'draft',
            '2026-06-12T00:00:00Z'
        )
    """


def insert_english_version_sql() -> str:
    return """
        INSERT INTO content_bank_versions (
            id, content_bank_id, version, status, activated_at, created_at
        ) VALUES (
            'english-core:stage6-draft', 'english-core', 'stage6-draft', 'draft',
            NULL, '2026-06-12T00:00:00Z'
        )
    """


def insert_english_source_sql() -> str:
    return """
        INSERT INTO sources (
            source_id, source_type, provenance_note, checksum_sha256, status,
            created_at, language_code, content_bank_id, bank_version_id
        ) VALUES (
            'src_stage6_english_draft', 'fixture', 'stage6 english draft',
            '0000000000000000000000000000000000000000000000000000000000000000',
            'active', '2026-06-12T00:00:00Z', 'en', 'english-core',
            'english-core:stage6-draft'
        )
    """


def clone_item_sql(item_id: str, language_code: str, bank_version_id: str) -> str:
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
            '{item_id}', 'src_stage6_english_draft', '{language_code}', '{language_code}',
            'english-core', '{bank_version_id}', level_band, sublevel, theme_id,
            subtheme_id, objective_id, pattern_id, difficulty_band, register,
            prompt, stem_text, options_json, answer_key, explanation, tags,
            coverage_cell_id || '::en', status, version, created_at, updated_at,
            reviewed_at, level_locked, locked_at
        FROM quiz_items
        WHERE item_id = 'approved_traceable_001'
    """


if __name__ == "__main__":
    unittest.main()
