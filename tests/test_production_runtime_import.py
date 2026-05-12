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


class ProductionRuntimeImportTests(unittest.TestCase):
    def test_runtime_import_is_idempotent_and_retires_non_corpus_fixture(self) -> None:
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
        self.assertEqual(second["after_counts"], first["after_counts"])
        self.assertEqual(report["decision"], "production_corpus_import_committed")
        self.assertTrue(report["seed_smoke_consumers"])

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
                "--retire-non-corpus-items",
                "--seed-smoke-consumers",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
