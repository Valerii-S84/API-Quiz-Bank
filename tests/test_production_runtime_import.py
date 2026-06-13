from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.repository_test_support import ROOT


DEFAULT_SCOPE_ARGS = [
    "--language-code",
    "de",
    "--content-bank-id",
    "german-core",
    "--bank-version-id",
    "german-core:2026-06-12-baseline",
    "--target-version-status",
    "active",
]


class ProductionRuntimeImportTests(unittest.TestCase):
    def test_runtime_import_repair_is_idempotent_and_retires_non_corpus_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            quizbank_dir = workspace / "QuizBank"
            quizbank_dir.mkdir()
            shutil.copy(
                ROOT / "tests" / "fixtures" / "quizbank_public_smoke" / "public_smoke.csv",
                quizbank_dir / "public_smoke.csv",
            )
            db_path = workspace / "runtime.sqlite3"
            report_path = workspace / "import.json"
            self.run_cli(db_path, "init-db")
            self.run_cli(db_path, "seed-items")
            self.run_promotion_tool(quizbank_dir, workspace)

            first = self.run_import_tool(quizbank_dir, db_path, report_path)
            second = self.run_import_tool(quizbank_dir, db_path, report_path)
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(first["after_counts"]["published_items"], 2)
        self.assertEqual(first["after_counts"]["active_sources"], 1)
        self.assertEqual(first["after_counts"]["retired_items"], 1)
        self.assertEqual(first["after_counts"]["image_quality_policy_rows"], 2)
        self.assertEqual(
            first["after_counts"]["image_quality_low_items"]
            + first["after_counts"]["image_quality_medium_items"],
            2,
        )
        self.assertEqual(second["after_counts"], first["after_counts"])
        self.assertEqual(report["decision"], "production_corpus_import_committed")
        self.assertTrue(report["approved_active_repair"])
        self.assertEqual(report["content_scope"]["language_code"], "de")
        self.assertEqual(report["content_scope"]["content_bank_id"], "german-core")
        self.assertEqual(
            report["content_scope"]["bank_version_id"],
            "german-core:2026-06-12-baseline",
        )
        self.assertTrue(report["seed_smoke_consumers"])

    def test_runtime_import_refuses_active_target_without_repair_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            quizbank_dir = workspace / "QuizBank"
            quizbank_dir.mkdir()
            shutil.copy(
                ROOT / "tests" / "fixtures" / "quizbank_public_smoke" / "public_smoke.csv",
                quizbank_dir / "public_smoke.csv",
            )
            db_path = workspace / "runtime.sqlite3"
            report_path = workspace / "import.json"
            self.run_promotion_tool(quizbank_dir, workspace)

            result = self.run_import_tool_raw(quizbank_dir, db_path, report_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active_import_requires_approved_repair_mode", result.stdout)

    def test_protected_production_smoke_script_is_valid_shell(self) -> None:
        result = subprocess.run(
            ["sh", "-n", "scripts/api_quiz_bank_protected_production_smoke.sh"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def run_cli(self, db_path: Path, command: str) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "quizbank_mvp.cli",
                "--db-path",
                str(db_path),
                command,
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )

    def run_promotion_tool(self, quizbank_dir: Path, workspace: Path) -> None:
        subprocess.run(
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

    def run_import_tool(
        self,
        quizbank_dir: Path,
        db_path: Path,
        report_path: Path,
    ) -> dict[str, object]:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "import_production_corpus_to_runtime.py"),
                "--quizbank-dir",
                str(quizbank_dir),
                "--db-path",
                str(db_path),
                "--report-out",
                str(report_path),
                "--expected-published-items",
                "2",
                "--expected-active-sources",
                "1",
                *DEFAULT_SCOPE_ARGS,
                "--commit",
                "--approved-active-repair",
                "--retire-non-corpus-items",
                "--seed-smoke-consumers",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(result.stdout)

    def run_import_tool_raw(
        self,
        quizbank_dir: Path,
        db_path: Path,
        report_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "import_production_corpus_to_runtime.py"),
                "--quizbank-dir",
                str(quizbank_dir),
                "--db-path",
                str(db_path),
                "--report-out",
                str(report_path),
                "--expected-published-items",
                "2",
                "--expected-active-sources",
                "1",
                *DEFAULT_SCOPE_ARGS,
                "--commit",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )


if __name__ == "__main__":
    unittest.main()
