#!/usr/bin/env python3
"""Refill precomputed selection queues for entitled consumers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.selection_queue_filler import refill_selection_queues  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--channel-id", action="append", default=[])
    parser.add_argument("--target-size", type=int, default=50)
    parser.add_argument("--language-code", default="de")
    parser.add_argument("--content-bank-id", default=None)
    parser.add_argument("--bank-version-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = refill_selection_queues(
        args.db_path,
        channel_ids=tuple(args.channel_id) or ("api",),
        target_size=args.target_size,
        language_code=args.language_code,
        content_bank_id=args.content_bank_id,
        bank_version_id=args.bank_version_id,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
