from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import connect, seed_control_fixture

from tests.test_mvp_admin import (
    APPROVED_FIXTURE,
    BASELINE_VERSION_ID,
    MvpAdminCase,
    insert_bank_version,
)


class MvpAdminContentScopeTests(MvpAdminCase):
    def test_admin_item_list_and_dashboard_filter_by_bank_version(self) -> None:
        key = self.seed_admin("reviewer", "read_only_reviewer")
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        draft_version_id = "german-core:stage4-filter-draft"
        insert_bank_version(self, draft_version_id, "stage4-filter-draft", "draft")
        clone_quiz_item_to_bank_version(self, "stage4_filter_item", draft_version_id)

        baseline_items = self.client.get(
            f"/v1/admin/quiz-items?bank_version_id={BASELINE_VERSION_ID}",
            headers=self.admin_headers(key),
        )
        draft_items = self.client.get(
            f"/v1/admin/quiz-items?bank_version_id={draft_version_id}",
            headers=self.admin_headers(key),
        )
        draft_dashboard = self.client.get(
            f"/v1/admin/dashboard?bank_version_id={draft_version_id}",
            headers=self.admin_headers(key),
        )

        self.assertEqual(baseline_items.status_code, 200)
        self.assertEqual(draft_items.status_code, 200)
        self.assertEqual(draft_dashboard.status_code, 200)
        self.assertEqual(
            [item["item_id"] for item in baseline_items.json()["data"]],
            ["approved_traceable_001"],
        )
        self.assertEqual(
            [item["item_id"] for item in draft_items.json()["data"]],
            ["stage4_filter_item"],
        )
        self.assertEqual(draft_dashboard.json()["items_by_language"], {"de": 1})
        self.assertEqual(
            draft_dashboard.json()["items_by_bank_version"][0]["bank_version_id"],
            draft_version_id,
        )


def clone_quiz_item_to_bank_version(
    case: MvpAdminCase,
    item_id: str,
    bank_version_id: str,
    source_item_id: str = "approved_traceable_001",
) -> None:
    with connect(case.db_path) as connection:
        connection.execute(
            """
            INSERT INTO quiz_items (
                item_id, source_id, language, language_code, content_bank_id,
                bank_version_id, level_band, sublevel, theme_id, subtheme_id,
                objective_id, pattern_id, difficulty_band, register, prompt,
                stem_text, options_json, answer_key, explanation, tags,
                coverage_cell_id, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            )
            SELECT
                ?, source_id, language, language_code, content_bank_id,
                ?, level_band, sublevel, theme_id, subtheme_id, objective_id,
                pattern_id, difficulty_band, register, prompt, stem_text,
                options_json, answer_key, explanation, tags,
                coverage_cell_id || ?, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            FROM quiz_items
            WHERE item_id = ?
            """,
            (item_id, bank_version_id, f"::{item_id}", source_item_id),
        )
