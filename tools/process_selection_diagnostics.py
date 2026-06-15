#!/usr/bin/env python3
"""Process pending async selection diagnostics outbox events."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.selection_async_diagnostics import (  # noqa: E402
    DEFAULT_WORKER_ID,
    process_pending_selection_diagnostics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--worker-id", default=DEFAULT_WORKER_ID)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = process_pending_selection_diagnostics(
        args.db_path,
        limit=args.limit,
        worker_id=args.worker_id,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
