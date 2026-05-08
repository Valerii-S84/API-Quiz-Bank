#!/usr/bin/env python3
"""Run a Telegram delivery dry-run or controlled real-send smoke."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.telegram_delivery import (  # noqa: E402
    TelegramBotApiAdapter,
    TelegramDeliveryRequest,
    run_telegram_delivery,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Quiz Bank Telegram delivery smoke.")
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--consumer-id", required=True)
    parser.add_argument("--chat-id", required=True)
    parser.add_argument("--cefr-level", default=None)
    parser.add_argument("--theme-id", action="append", default=[])
    parser.add_argument("--objective-id", action="append", default=[])
    parser.add_argument("--pattern-id", action="append", default=[])
    parser.add_argument("--mode", choices=["dry_run", "real"], default="dry_run")
    parser.add_argument("--approve-real-send", action="store_true")
    parser.add_argument("--token-file", type=Path, default=None)
    parser.add_argument("--token-env", default="TELEGRAM_BOT_TOKEN")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    adapter = None
    if args.mode == "real":
        if not args.approve_real_send:
            raise SystemExit("real mode requires --approve-real-send")
        adapter = TelegramBotApiAdapter(read_bot_token(args))
    result = run_telegram_delivery(
        args.db_path,
        TelegramDeliveryRequest(
            consumer_id=args.consumer_id,
            chat_id=args.chat_id,
            mode=args.mode,
            cefr_level=args.cefr_level,
            theme_ids=tuple(args.theme_id),
            objective_ids=tuple(args.objective_id),
            pattern_ids=tuple(args.pattern_id),
        ),
        adapter=adapter,
    )
    print(json.dumps(result.to_public_dict(), ensure_ascii=False, indent=2))
    return 0


def read_bot_token(args: argparse.Namespace) -> str:
    if args.token_file is not None:
        return args.token_file.read_text(encoding="utf-8").strip()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise SystemExit("real mode requires --token-file or TELEGRAM_BOT_TOKEN")
    return token


if __name__ == "__main__":
    raise SystemExit(main())
