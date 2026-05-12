from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.repository_test_support import EXPECTED_HEADER, ROOT


class ProductionPromotionTests(unittest.TestCase):
    def test_promotion_tool_changes_only_status_and_production_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            quizbank_dir = workspace / "QuizBank"
            quizbank_dir.mkdir()
            shutil.copy(
                ROOT / "tests" / "fixtures" / "quizbank_public_smoke" / "public_smoke.csv",
                quizbank_dir / "public_smoke.csv",
            )

            before_rows = read_rows(quizbank_dir / "public_smoke.csv")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "promote_verified_corpus_to_production.py"),
                    "--quizbank-dir",
                    str(quizbank_dir),
                    "--owner-approval-json",
                    str(workspace / "owner.json"),
                    "--owner-approval-md",
                    str(workspace / "owner.md"),
                    "--promotion-report",
                    str(workspace / "promotion.json"),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            after_rows = read_rows(quizbank_dir / "public_smoke.csv")
            report = json.loads((workspace / "promotion.json").read_text(encoding="utf-8"))

            self.assertIn("published_items=2", result.stdout)
            self.assertEqual(report["status_counts_before"]["draft"], 2)
            self.assertEqual(report["status_counts_after"]["published"], 2)
            self.assertFalse(report["content_fields_changed"])
            self.assertEqual([row["status"] for row in after_rows], ["published", "published"])
            for before, after in zip(before_rows, after_rows, strict=True):
                self.assert_content_fields_unchanged(before, after)

    def assert_content_fields_unchanged(
        self,
        before: dict[str, str],
        after: dict[str, str],
    ) -> None:
        production_metadata = {"status", "updated_at", "reviewed_at", "level_locked", "locked_at"}
        for field in EXPECTED_HEADER:
            if field not in production_metadata:
                self.assertEqual(after[field], before[field], field)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


if __name__ == "__main__":
    unittest.main()
