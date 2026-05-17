#!/usr/bin/env python3
"""Audit deterministic visual mode routing for QuizBank image generation."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_common import THEME_TITLES, load_inventory, print_json  # noqa: E402
from quizbank_mvp.visual_mode_policy import VISUAL_MODES, resolve_visual_mode  # noqa: E402
from quizbank_mvp.visual_prompt_builder import (  # noqa: E402
    PROMPT_POLICY_VERSION,
    answer_text,
    options_from_item,
    question_context,
)
from quizbank_mvp.visual_target_extractor import (  # noqa: E402
    ARTICLES,
    PREPOSITIONS,
    extract_visual_target,
    non_visual_answer_token,
    normalize_token,
    text_tokens,
)


DEFAULT_GENERATED_AT = "2026-05-17"
DEFAULT_AUDIT_PATH = Path("reports/visual_mode/visual_mode_audit.md")
DEFAULT_EXAMPLES_PATH = Path("reports/visual_mode/visual_mode_examples.md")
MODE_ORDER = ("target_action", "target_object", "context_only", "document_form", "symbolic_abstract")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit QuizBank visual mode routing.")
    parser.add_argument("--quizbank-dir", default="QuizBank", type=Path)
    parser.add_argument("--audit-out", default=DEFAULT_AUDIT_PATH, type=Path)
    parser.add_argument("--examples-out", default=DEFAULT_EXAMPLES_PATH, type=Path)
    parser.add_argument("--generated-at", default=DEFAULT_GENERATED_AT)
    parser.add_argument("--write-reports", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def build_decision(row: dict[str, str]) -> dict[str, Any]:
    options = options_from_item(row)
    answer = answer_text(row, options)
    context = question_context(row)
    visual_mode = resolve_visual_mode(
        row["item_id"],
        row["theme_id"],
        row["sublevel"],
        context,
        answer,
        options,
    )
    target = extract_visual_target(context, answer, visual_mode, options)
    return {
        "item_id": row["item_id"],
        "theme_id": row["theme_id"],
        "level": row["sublevel"],
        "prompt": row.get("prompt", ""),
        "stem_text": row.get("stem_text", ""),
        "answer": answer,
        "visual_mode": visual_mode,
        "visual_target": target.visual_target,
        "visual_context_hint": target.context_hint,
        "is_answer_directly_visualizable": target.is_answer_directly_visualizable,
        "reason_code": target.reason_code,
        "grammar_token_answer": non_visual_answer_token(answer),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    inventory = load_inventory(args.quizbank_dir)
    decisions = [build_decision(row) for row in inventory.rows]
    validate_modes(decisions)
    return {
        "report_type": "visual_mode_policy",
        "generated_at": args.generated_at,
        "prompt_policy_version": PROMPT_POLICY_VERSION,
        "total_items": inventory.active_row_count,
        "mode_counts": dict(mode_counts(decisions)),
        "theme_breakdown": theme_breakdown(decisions),
        "level_breakdown": level_breakdown(decisions),
        "high_risk_examples": high_risk_examples(decisions),
        "examples_by_mode": examples_by_mode(decisions),
        "grammar_examples": grammar_examples(decisions),
    }


def validate_modes(decisions: list[dict[str, Any]]) -> None:
    invalid_modes = {decision["visual_mode"] for decision in decisions} - set(VISUAL_MODES)
    if invalid_modes:
        raise ValueError(f"invalid visual modes: {sorted(invalid_modes)}")
    leaked_targets = [
        decision["item_id"]
        for decision in decisions
        if decision["grammar_token_answer"]
        and decision["visual_target"].strip().lower() == decision["answer"].strip().lower()
    ]
    if leaked_targets:
        raise ValueError(f"grammar token leaked as visual target: {leaked_targets[:5]}")


def mode_counts(decisions: list[dict[str, Any]]) -> Counter[str]:
    counts = Counter(decision["visual_mode"] for decision in decisions)
    return Counter({mode: counts.get(mode, 0) for mode in MODE_ORDER})


def theme_breakdown(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_theme: dict[str, Counter[str]] = defaultdict(Counter)
    for decision in decisions:
        by_theme[decision["theme_id"]][decision["visual_mode"]] += 1
    return [
        {"theme_id": theme_id, "theme_title": THEME_TITLES.get(theme_id, ""), **mode_columns(by_theme[theme_id])}
        for theme_id in sorted(by_theme)
    ]


def level_breakdown(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_level: dict[str, Counter[str]] = defaultdict(Counter)
    for decision in decisions:
        by_level[decision["level"]][decision["visual_mode"]] += 1
    return [{"level": level, **mode_columns(by_level[level])} for level in sorted(by_level)]


def mode_columns(counter: Counter[str]) -> dict[str, int]:
    return {mode: counter.get(mode, 0) for mode in MODE_ORDER}


def high_risk_examples(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        decision
        for decision in decisions
        if decision["visual_mode"] in {"context_only", "document_form", "symbolic_abstract"}
    ]
    return candidates[:20]


def examples_by_mode(decisions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    examples: dict[str, list[dict[str, Any]]] = {mode: [] for mode in MODE_ORDER}
    for decision in decisions:
        bucket = examples[decision["visual_mode"]]
        if len(bucket) < 5:
            bucket.append(decision)
    return examples


def grammar_examples(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    articles = [decision for decision in decisions if grammar_answer_kind(decision["answer"]) == "article"]
    prepositions = [decision for decision in decisions if grammar_answer_kind(decision["answer"]) == "preposition"]
    others = [decision for decision in decisions if decision["grammar_token_answer"]]
    selected = unique_decisions(articles[:5] + prepositions[:5])
    return selected if len(selected) >= 10 else unique_decisions(selected + others[: 10 - len(selected)])


def grammar_answer_kind(answer: str) -> str:
    tokens = [normalize_token(token) for token in text_tokens(answer)]
    if tokens and all(token in ARTICLES for token in tokens):
        return "article"
    if tokens and all(token in PREPOSITIONS or token in ARTICLES for token in tokens):
        return "preposition"
    return "other"


def unique_decisions(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique = []
    for decision in decisions:
        if decision["item_id"] not in seen:
            seen.add(decision["item_id"])
            unique.append(decision)
    return unique


def write_audit(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Visual Mode Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "Source: top-level `QuizBank/*.csv`; service template and `QuizBank/staging/` are excluded.",
        f"Prompt policy: `{report['prompt_policy_version']}`",
        "",
        f"Total active items: `{report['total_items']}`",
        "",
        "## Mode Distribution",
        "",
        "| visual_mode | count |",
        "|---|---:|",
    ]
    lines.extend(f"| {mode} | `{count}` |" for mode, count in report["mode_counts"].items())
    lines.extend(["", "## Breakdown By Theme", "", mode_table_header("theme"), mode_table_separator()])
    for row in report["theme_breakdown"]:
        lines.append(mode_table_row(f"{row['theme_id']} - {escape(row['theme_title'])}", row))
    lines.extend(["", "## Breakdown By Level", "", mode_table_header("level"), mode_table_separator()])
    for row in report["level_breakdown"]:
        lines.append(mode_table_row(row["level"], row))
    lines.extend(["", "## High-Risk Examples", "", example_table_header(), example_table_separator()])
    for decision in report["high_risk_examples"]:
        lines.append(example_table_row(decision))
    write_lines(path, lines)


def write_examples(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Visual Mode Examples",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Prompt policy: `{report['prompt_policy_version']}`",
        "",
    ]
    for mode in MODE_ORDER:
        lines.extend([f"## {mode}", "", example_table_header(), example_table_separator()])
        for decision in report["examples_by_mode"][mode]:
            lines.append(example_table_row(decision))
        lines.append("")
    lines.extend(["## Article / Preposition Examples", "", example_table_header(), example_table_separator()])
    for decision in report["grammar_examples"]:
        lines.append(example_table_row(decision))
    write_lines(path, lines)


def mode_table_header(first_column: str) -> str:
    return f"| {first_column} | " + " | ".join(MODE_ORDER) + " |"


def mode_table_separator() -> str:
    return "|---|---:|---:|---:|---:|---:|"


def mode_table_row(first_value: str, row: dict[str, Any]) -> str:
    return "| " + first_value + " | " + " | ".join(f"`{row[mode]}`" for mode in MODE_ORDER) + " |"


def example_table_header() -> str:
    return "| item_id | theme | level | old behavior | new behavior | reason | stem |"


def example_table_separator() -> str:
    return "|---|---|---|---|---|---|---|"


def example_table_row(decision: dict[str, Any]) -> str:
    old_behavior = f"visual_target = {decision['answer']}"
    new_behavior = f"{decision['visual_mode']} / {decision['visual_target']}"
    values = [
        decision["item_id"],
        decision["theme_id"],
        decision["level"],
        old_behavior,
        new_behavior,
        decision["reason_code"],
        short_text(decision["stem_text"]),
    ]
    return "| " + " | ".join(escape(value) for value in values) + " |"


def short_text(value: str, limit: int = 90) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[: limit - 3]}..."


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.write_reports:
        write_audit(args.audit_out, report)
        write_examples(args.examples_out, report)
    if args.format == "json":
        print_json(report)
    else:
        print(f"total_items={report['total_items']}")
        for mode, count in report["mode_counts"].items():
            print(f"{mode}={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
