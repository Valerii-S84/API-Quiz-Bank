from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests.repository_test_support import ROOT


PRODUCTION_MODULE_LIMIT = 600
TEST_MODULE_LIMIT = 650
CLASS_LIMIT = 220
PRODUCTION_FUNCTION_HARD_LIMIT = 60
TEST_FUNCTION_HARD_LIMIT = 50
NAMED_FUNCTION_LIMITS = {
    ("tools/quizbank_gap_map.py", "coverage_cells"): 40,
    ("tools/quizbank_import_sample.py", "validate_source"): 40,
    ("tools/quizbank_import_sample.py", "build_report"): 40,
    ("tools/quizbank_readme.py", "build_readme"): 40,
    ("tools/quizbank_selection_smoke.py", "build_report"): 40,
    ("tests/test_reports_selection_invariants.py", "test_repeat_policy_report_is_current"): 35,
}


def python_paths() -> list[Path]:
    return [
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "tools").glob("*.py")),
        *sorted((ROOT / "tests").glob("*.py")),
    ]


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def node_span(node: ast.AST) -> int:
    return int(getattr(node, "end_lineno")) - int(getattr(node, "lineno")) + 1


class StyleNumericLimitTests(unittest.TestCase):
    def test_python_sources_keep_basic_whitespace_style(self) -> None:
        failures = []
        for path in python_paths():
            text = path.read_text(encoding="utf-8")
            if text and not text.endswith("\n"):
                failures.append(f"{relative_path(path)}:missing-final-newline")
            for line_number, line in enumerate(text.splitlines(), 1):
                if line.rstrip(" \t") != line:
                    failures.append(f"{relative_path(path)}:{line_number}:trailing-whitespace")
                if line.startswith("\t"):
                    failures.append(f"{relative_path(path)}:{line_number}:tab-indentation")
        self.assertEqual(failures, [])

    def test_python_modules_stay_below_hard_line_limits(self) -> None:
        failures = []
        for path in python_paths():
            limit = TEST_MODULE_LIMIT if relative_path(path).startswith("tests/") else PRODUCTION_MODULE_LIMIT
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > limit:
                failures.append(f"{relative_path(path)}:{line_count}>{limit}")
        self.assertEqual(failures, [])

    def test_classes_and_functions_stay_below_hard_limits(self) -> None:
        failures = []
        for path in python_paths():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            is_test = relative_path(path).startswith("tests/")
            function_limit = TEST_FUNCTION_HARD_LIMIT if is_test else PRODUCTION_FUNCTION_HARD_LIMIT
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node_span(node) > CLASS_LIMIT:
                    failures.append(f"{relative_path(path)}:{node.name}:{node_span(node)}>{CLASS_LIMIT}")
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node_span(node) > function_limit:
                        failures.append(
                            f"{relative_path(path)}:{node.name}:{node_span(node)}>{function_limit}"
                        )
        self.assertEqual(failures, [])

    def test_named_previous_hotspots_stay_under_normal_limits(self) -> None:
        spans: dict[tuple[str, str], int] = {}
        for path in python_paths():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    spans[(relative_path(path), node.name)] = node_span(node)

        failures = [
            f"{path}:{name}:{spans[(path, name)]}>{limit}"
            for (path, name), limit in NAMED_FUNCTION_LIMITS.items()
            if spans[(path, name)] > limit
        ]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
