from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    row_to_dict,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection import select_next_item  # noqa: E402
from quizbank_mvp.visual_delivery import resolve_visual_delivery  # noqa: E402
from quizbank_mvp.visual_provider import FakeImageProvider  # noqa: E402
from tests.test_visual_delivery import (  # noqa: E402
    APPROVED_FIXTURE,
    enable_standard_visual,
    grant_feature,
    load_delivery,
    load_quiz_item,
    selection_request,
)


class VisualRuntimeMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "quizbank.sqlite3"
        self.asset_root = Path(self.temp_directory.name) / "visual-assets"
        initialize_database(self.db_path)
        seed_control_fixture(self.db_path, APPROVED_FIXTURE, "approved")
        seed_consumer(self.db_path, "consumer_visual", 5, ["A2"], ["T10"])
        seed_entitlement(self.db_path, "consumer_visual", ["A2"], ["T10"])
        select_next_item(self.db_path, selection_request())
        self.delivery = load_delivery(self)
        self.quiz_item = load_quiz_item(self)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_generated_asset_and_prompt_audit_store_visual_metadata(self) -> None:
        enable_standard_visual(self)
        grant_feature(self, "visual_delivery.standard")
        grant_feature(self, "visual_generation.standard")

        resolution = resolve_visual_delivery(
            self.db_path,
            self.delivery,
            self.quiz_item,
            "consumer_visual",
            FakeImageProvider(),
            self.asset_root,
        )

        self.assertEqual(resolution.state, "generated_approved")
        for row in [visual_asset_metadata(self.db_path), prompt_audit_metadata(self.db_path)]:
            with self.subTest(row=row):
                self.assertTrue(row["visual_mode"])
                self.assertTrue(row["visual_target"])
                self.assertTrue(row["visual_context_hint"])
                self.assertEqual(row["visual_prompt_policy_version"], "visual_prompt_policy_v4_visual_modes")


def visual_asset_metadata(db_path: Path) -> dict[str, str]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT visual_mode, visual_target, visual_context_hint, visual_prompt_policy_version
            FROM visual_assets
            LIMIT 1
            """
        ).fetchone()
    return row_to_dict(row)


def prompt_audit_metadata(db_path: Path) -> dict[str, str]:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT visual_mode, visual_target, visual_context_hint, visual_prompt_policy_version
            FROM visual_prompt_audit
            LIMIT 1
            """
        ).fetchone()
    return row_to_dict(row)


if __name__ == "__main__":
    unittest.main()
