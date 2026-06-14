from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.candidate_pool_builder import (  # noqa: E402
    rebuild_candidate_pools,
    rebuild_candidate_pools_after_bank_activation,
    rebuild_candidate_pools_for_item,
)
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_control_fixture,
    transition_item_status,
)


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
BASELINE_VERSION_ID = "german-core:2026-06-12-baseline"
TARGET_VERSION_ID = "german-core:pool-target"


class CandidatePoolBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_rebuild_creates_pool_per_full_scope_cell(self) -> None:
        insert_item_copy(self.db_path, "approved_traceable_002", "O03", "P02")

        summary = rebuild_candidate_pools_for_item(self.db_path, "approved_traceable_001")

        self.assertEqual(summary["pool_count"], 2)
        self.assertEqual(summary["rebuilt_pool_count"], 2)
        with connect(self.db_path) as connection:
            scopes = pool_scope_tuples(connection)
            item_count = pool_item_count(connection)
        self.assertEqual(
            scopes,
            [("A2", "T10", "O02", "P01"), ("A2", "T10", "O03", "P02")],
        )
        self.assertEqual(item_count, 2)

    def test_rebuild_is_idempotent_when_source_fingerprint_is_unchanged(self) -> None:
        first = rebuild_candidate_pools(self.db_path)
        second = rebuild_candidate_pools(self.db_path)

        with connect(self.db_path) as connection:
            pool = connection.execute("SELECT * FROM candidate_pools").fetchone()
            item_count = pool_item_count(connection)

        self.assertEqual(first["rebuilt_pool_count"], 1)
        self.assertEqual(second["rebuilt_pool_count"], 0)
        self.assertEqual(second["unchanged_pool_count"], 1)
        self.assertEqual(pool["pool_version"], 1)
        self.assertEqual(item_count, 1)

    def test_rebuild_after_status_change_clears_pool_items(self) -> None:
        rebuild_candidate_pools(self.db_path)
        transition_item_status(
            self.db_path,
            "approved_traceable_001",
            "blocked",
            "local_test",
            "pool rebuild status test",
        )

        summary = rebuild_candidate_pools(self.db_path)

        with connect(self.db_path) as connection:
            pool = connection.execute("SELECT * FROM candidate_pools").fetchone()
            item_count = pool_item_count(connection)

        self.assertEqual(summary["pool_count"], 1)
        self.assertEqual(summary["rebuilt_pool_count"], 1)
        self.assertEqual(summary["item_count"], 0)
        self.assertEqual(pool["pool_version"], 2)
        self.assertEqual(pool["item_count"], 0)
        self.assertEqual(item_count, 0)

    def test_activation_rebuild_stales_archived_version_and_rebuilds_target(self) -> None:
        rebuild_candidate_pools(self.db_path)
        insert_bank_version(self.db_path, TARGET_VERSION_ID, "pool-target", "audit")
        insert_item_copy(self.db_path, "approved_traceable_target", "O03", "P02", TARGET_VERSION_ID)

        summary = rebuild_candidate_pools_after_bank_activation(
            self.db_path,
            {
                "from_bank_version_id": BASELINE_VERSION_ID,
                "to_bank_version_id": TARGET_VERSION_ID,
            },
        )

        with connect(self.db_path) as connection:
            statuses = pool_statuses_by_version(connection)
        self.assertEqual(summary["pool_count"], 1)
        self.assertEqual(summary["item_count"], 1)
        self.assertEqual(statuses[BASELINE_VERSION_ID], ["stale"])
        self.assertEqual(statuses[TARGET_VERSION_ID], ["ready"])


def insert_item_copy(
    db_path: Path,
    item_id: str,
    objective_id: str,
    pattern_id: str,
    bank_version_id: str = BASELINE_VERSION_ID,
) -> None:
    with connect(db_path) as connection:
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
            SELECT ?, source_id, language, language_code, content_bank_id,
                   ?, level_band, sublevel, theme_id, subtheme_id,
                   ?, ?, difficulty_band, register, prompt, stem_text,
                   options_json, answer_key, explanation, tags,
                   ? || '::copy', status, version, created_at, updated_at,
                   reviewed_at, level_locked, locked_at
            FROM quiz_items
            WHERE item_id = 'approved_traceable_001'
            """,
            (
                item_id,
                bank_version_id,
                objective_id,
                pattern_id,
                f"A2::T10::{objective_id}::{pattern_id}",
            ),
        )


def insert_bank_version(db_path: Path, version_id: str, version: str, status: str) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO content_bank_versions (
                id, content_bank_id, version, status, activated_at, created_at
            ) VALUES (?, 'german-core', ?, ?, NULL, '2026-06-12T01:00:00Z')
            """,
            (version_id, version, status),
        )


def pool_scope_tuples(connection) -> list[tuple[str, str, str, str]]:
    rows = connection.execute(
        """
        SELECT cefr_level, theme_id, objective_id, pattern_id
        FROM candidate_pools
        ORDER BY cefr_level, theme_id, objective_id, pattern_id
        """
    ).fetchall()
    return [
        (row["cefr_level"], row["theme_id"], row["objective_id"], row["pattern_id"])
        for row in rows
    ]


def pool_item_count(connection) -> int:
    row = connection.execute("SELECT COUNT(*) AS count FROM candidate_pool_items").fetchone()
    return int(row["count"])


def pool_statuses_by_version(connection) -> dict[str, list[str]]:
    rows = connection.execute(
        """
        SELECT bank_version_id, pool_status
        FROM candidate_pools
        ORDER BY bank_version_id, pool_status
        """
    ).fetchall()
    statuses: dict[str, list[str]] = {}
    for row in rows:
        statuses.setdefault(str(row["bank_version_id"]), []).append(str(row["pool_status"]))
    return statuses


if __name__ == "__main__":
    unittest.main()
