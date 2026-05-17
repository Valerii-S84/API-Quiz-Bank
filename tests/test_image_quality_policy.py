from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from quizbank_common import CANONICAL_LEVELS, load_inventory  # noqa: E402
from quizbank_mvp.image_quality_policy import (  # noqa: E402
    ImageQualityPolicyError,
    load_theme_groups,
    medium_share_for,
    normalize_level,
    resolve_image_quality,
    validate_theme_group_coverage,
)


class ImageQualityPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        load_theme_groups.cache_clear()
        self.theme_groups = load_theme_groups(ROOT / "config" / "image_quality_theme_groups.yaml")

    def test_deterministic_item_quality_is_stable(self) -> None:
        first = resolve_image_quality("stable_item_001", "B1", "T10")
        second = resolve_image_quality("stable_item_001", "B1", "T10")

        self.assertEqual(first, second)
        self.assertIn(first, {"low", "medium"})

    def test_override_wins_over_policy(self) -> None:
        self.assertEqual(resolve_image_quality("override_item", "C2", "T18", "low"), "low")
        self.assertEqual(resolve_image_quality("override_item", "A1", "T01", "medium"), "medium")

    def test_level_normalization_accepts_sublevels(self) -> None:
        self.assertEqual(normalize_level("A1.1"), "A1")
        self.assertEqual(normalize_level("A1.2"), "A1")
        self.assertEqual(normalize_level("B2.1"), "B2")
        self.assertEqual(normalize_level("C1.2"), "C1")

    def test_theme_config_covers_all_current_corpus_themes(self) -> None:
        inventory = load_inventory(ROOT / "QuizBank")
        theme_ids = {row["theme_id"].strip() for row in inventory.rows}

        validate_theme_group_coverage(theme_ids, self.theme_groups)

        self.assertEqual(len(theme_ids), 18)
        self.assertEqual(set(self.theme_groups), theme_ids)

    def test_unknown_theme_fails_validation(self) -> None:
        with self.assertRaisesRegex(ImageQualityPolicyError, "themes missing"):
            validate_theme_group_coverage({"T99"}, self.theme_groups)

    def test_policy_never_returns_high(self) -> None:
        for level in CANONICAL_LEVELS:
            for theme_id in sorted(self.theme_groups):
                quality = resolve_image_quality(f"no_high_{level}_{theme_id}", level, theme_id)
                self.assertIn(quality, {"low", "medium"})
                self.assertNotEqual(quality, "high")

    def test_distribution_sanity_tracks_medium_share(self) -> None:
        share = medium_share_for("C2", "abstract_complex")
        item_ids = [f"distribution_item_{index:05d}" for index in range(10000)]
        medium_count = sum(
            resolve_image_quality(item_id, "C2", "T18") == "medium"
            for item_id in item_ids
        )
        actual_share = medium_count / len(item_ids) * 100

        self.assertLessEqual(abs(actual_share - share), 2.0)


if __name__ == "__main__":
    unittest.main()
