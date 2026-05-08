from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from quizbank_common import (  # noqa: E402
    CANONICAL_LEVELS,
    EXPECTED_HEADER,
    ITEM_STATUSES,
    NORMAL_DELIVERY_STATUSES,
    PARSER_PROFILE_ID,
    THEME_TITLES,
    file_sha256,
)


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def read_csv_dicts(relative_path: str) -> list[dict[str, str]]:
    with (ROOT / relative_path).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def parse_import_manifest_sources() -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    current_source: dict[str, str] | None = None
    manifest_path = ROOT / "data" / "manifests" / "import_manifest.yml"

    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  - source_id: "):
            if current_source is not None:
                sources.append(current_source)
            current_source = {"source_id": line.split(": ", 1)[1]}
        elif current_source is not None and line.startswith("    "):
            key, value = line.strip().split(": ", 1)
            current_source[key] = value

    if current_source is not None:
        sources.append(current_source)
    return sources


def file_texts(relative_paths: list[str]) -> dict[str, str]:
    return {
        relative_path: (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in relative_paths
    }
