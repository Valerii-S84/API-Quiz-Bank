#!/usr/bin/env python3
"""Shared corpus inventory helpers for API Quiz Bank."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


EXPECTED_HEADER = [
    "item_id",
    "language",
    "level_band",
    "sublevel",
    "theme_id",
    "subtheme_id",
    "objective_id",
    "pattern_id",
    "difficulty_band",
    "register",
    "prompt",
    "stem_text",
    "options",
    "answer_key",
    "explanation",
    "tags",
    "coverage_cell_id",
    "status",
    "version",
    "source_type",
    "provenance_note",
    "created_at",
    "updated_at",
    "reviewed_at",
    "level_locked",
    "locked_at",
]

CANONICAL_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
OBJECTIVE_IDS = tuple(f"O{index:02d}" for index in range(1, 17))
PATTERN_IDS = tuple(f"P{index:02d}" for index in range(1, 13))
THEME_TITLES = {
    "T01": "Person / Identität / Familie",
    "T02": "Alltag / Zeit / Organisation",
    "T03": "Wohnen / Haushalt / Verträge",
    "T04": "Einkaufen / Geld / Konsum",
    "T05": "Essen / Gesundheit / Pflege",
    "T06": "Arbeit / Beruf / Karriere",
    "T07": "Schule / Bildung / Weiterbildung",
    "T08": "Verkehr / Reise / Orientierung",
    "T09": "Kommunikation / Telefon / Nachricht / E-Mail",
    "T10": "Termine / Formulare / Behörden / Recht",
    "T11": "Freizeit / Kultur / Service / soziale Kontakte",
    "T12": "Medien / Digitales / Nachrichten",
    "T13": "Gesellschaft / Integration / Werte",
    "T14": "Umwelt / Nachhaltigkeit / Alltagssysteme",
    "T15": "Wirtschaft / Finanzen / Arbeitswelt",
    "T16": "Wissenschaft / Technik / Forschung",
    "T17": "Politik / Öffentlichkeit / Debatte",
    "T18": "Analyse / Interpretation / Argumentation",
}
ITEM_STATUSES = (
    "draft",
    "imported",
    "normalized",
    "needs_review",
    "approved",
    "published",
    "monitored",
    "retired",
    "blocked",
)
TEMPLATE_FILENAMES = {"logik_luecke_sheet_template.csv"}
PARSER_PROFILE_ID = "csv_quiz_bank_v1"


@dataclass(frozen=True)
class SourceFile:
    source_id: str
    path: Path
    filename: str
    is_template: bool
    source_state: str
    row_count: int
    size_bytes: int
    checksum_sha256: str
    header: list[str]
    header_hash_sha256: str


@dataclass
class CorpusInventory:
    quizbank_dir: Path
    source_files: list[SourceFile]
    rows: list[dict[str, str]]
    rows_by_file: dict[str, list[dict[str, str]]]

    @property
    def active_sources(self) -> list[SourceFile]:
        return [source for source in self.source_files if not source.is_template]

    @property
    def template_sources(self) -> list[SourceFile]:
        return [source for source in self.source_files if source.is_template]

    @property
    def active_row_count(self) -> int:
        return sum(source.row_count for source in self.active_sources)


def build_arg_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--quizbank-dir",
        default="QuizBank",
        type=Path,
        help="Path to the top-level QuizBank directory.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def header_hash(header: Iterable[str]) -> str:
    joined = ",".join(header).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def top_level_csv_files(quizbank_dir: Path) -> list[Path]:
    return sorted(path for path in quizbank_dir.glob("*.csv") if path.is_file())


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        header = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return header, rows


def load_inventory(quizbank_dir: Path) -> CorpusInventory:
    quizbank_dir = quizbank_dir.resolve()
    source_files: list[SourceFile] = []
    rows: list[dict[str, str]] = []
    rows_by_file: dict[str, list[dict[str, str]]] = {}

    for index, path in enumerate(top_level_csv_files(quizbank_dir), start=1):
        header, file_rows = read_csv_rows(path)
        is_template = path.name in TEMPLATE_FILENAMES
        source_id = f"src_{index:06d}"
        source_state = "template" if is_template else "active"
        source = SourceFile(
            source_id=source_id,
            path=path,
            filename=path.name,
            is_template=is_template,
            source_state=source_state,
            row_count=0 if is_template else len(file_rows),
            size_bytes=path.stat().st_size,
            checksum_sha256=file_sha256(path),
            header=header,
            header_hash_sha256=header_hash(header),
        )
        source_files.append(source)
        if not is_template:
            rows_by_file[path.name] = file_rows
            rows.extend(file_rows)

    return CorpusInventory(
        quizbank_dir=quizbank_dir,
        source_files=source_files,
        rows=rows,
        rows_by_file=rows_by_file,
    )


def counter_for(rows: Iterable[dict[str, str]], field: str) -> Counter[str]:
    values = [row.get(field, "").strip() or "(missing)" for row in rows]
    return Counter(values)


def nested_level_counts(rows: Iterable[dict[str, str]], key_field: str) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        key = row.get(key_field, "").strip() or "(missing)"
        level = row.get("sublevel", "").strip() or "(missing)"
        nested[key][level] += 1
    return {
        key: dict(sorted(counter.items()))
        for key, counter in sorted(
            nested.items(), key=lambda item: (-sum(item[1].values()), item[0])
        )
    }


def inventory_summary(inventory: CorpusInventory) -> dict[str, object]:
    return {
        "snapshot_date": date.today().isoformat(),
        "top_level_file_count": len([p for p in inventory.quizbank_dir.iterdir() if p.is_file()]),
        "top_level_directory_count": len([p for p in inventory.quizbank_dir.iterdir() if p.is_dir()]),
        "top_level_csv_count": len(inventory.source_files),
        "active_bank_files": len(inventory.active_sources),
        "template_files": [source.filename for source in inventory.template_sources],
        "active_rows": inventory.active_row_count,
        "by_status": dict(counter_for(inventory.rows, "status").most_common()),
        "by_level": dict(sorted(counter_for(inventory.rows, "sublevel").items())),
        "by_theme": nested_level_counts(inventory.rows, "theme_id"),
        "by_objective": dict(counter_for(inventory.rows, "objective_id").most_common()),
        "by_pattern": dict(counter_for(inventory.rows, "pattern_id").most_common()),
    }


def print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
