from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualModeAuditCliTests(unittest.TestCase):
    def test_audit_cli_reports_all_modes_for_minimal_fixture_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_dir = Path(directory)
            write_fixture_corpus(fixture_dir / "mini.csv")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "quizbank_visual_mode_audit.py"),
                    "--quizbank-dir",
                    str(fixture_dir),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )

        report = json.loads(completed.stdout)
        self.assertEqual(report["total_items"], 5)
        self.assertEqual(set(report["mode_counts"]), expected_modes())
        self.assertTrue(all(report["mode_counts"][mode] == 1 for mode in expected_modes()))


def expected_modes() -> set[str]:
    return {"target_action", "target_object", "context_only", "document_form", "symbolic_abstract"}


def write_fixture_corpus(path: Path) -> None:
    rows = [
        row("mini_action", "T02", "A2", "Ich muss ___.", ["das Fenster öffnen"]),
        row("mini_object", "T02", "A1", "Was ist wichtig?", ["der Schlüssel"]),
        row("mini_context", "T06", "A1", "Heute ist ___ Auftrag wichtig.", ["der"]),
        row("mini_document", "T10", "B1", "Im Amt liegt ein Formular.", ["das Formular"]),
        row("mini_abstract", "T17", "C1", "Welche Folgerung passt?", ["die Debatte analysieren"]),
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def row(item_id: str, theme_id: str, level: str, stem: str, options: list[str]) -> dict[str, str]:
    return {
        "item_id": item_id,
        "language": "de",
        "level_band": level,
        "sublevel": level,
        "theme_id": theme_id,
        "subtheme_id": "fixture",
        "objective_id": "O01",
        "pattern_id": "P01",
        "difficulty_band": level,
        "register": "standard_neutral",
        "prompt": "Welche Antwort passt?",
        "stem_text": stem,
        "options": json.dumps(options, ensure_ascii=False),
        "answer_key": "0",
        "explanation": "fixture",
        "tags": "fixture",
        "coverage_cell_id": f"{level}::{theme_id}::O01::P01",
        "status": "published",
        "version": "1.0",
        "source_type": "fixture",
        "provenance_note": "visual_mode_audit_cli",
        "created_at": "2026-05-17T00:00:00Z",
        "updated_at": "2026-05-17T00:00:00Z",
        "reviewed_at": "2026-05-17T00:00:00Z",
        "level_locked": "true",
        "locked_at": "2026-05-17T00:00:00Z",
    }


if __name__ == "__main__":
    unittest.main()
