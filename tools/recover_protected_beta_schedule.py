#!/usr/bin/env python3
"""Recover protected beta Telegram schedule slots without duplicate sends."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.protected_beta_recovery import recover_slots  # noqa: E402
from quizbank_mvp.telegram_delivery import TelegramBotApiAdapter  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--date", required=True)
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--slot-code", action="append", required=True)
    parser.add_argument("--mode", choices=["dry_run", "real"], default="dry_run")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-duplicate-send", action="store_true")
    parser.add_argument("--resume-created-delivery", action="store_true")
    parser.add_argument("--approve-real-send", action="store_true")
    parser.add_argument("--token-file", type=Path, default=None)
    parser.add_argument("--token-env", default="TELEGRAM_BOT_TOKEN")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = args.dry_run or args.mode == "dry_run"
    adapter = None if dry_run else telegram_adapter(args)
    actions = recover_slots(
        args.db_path,
        args.date,
        args.channel_id,
        parse_slot_codes(args.slot_code),
        args.mode,
        dry_run,
        args.no_duplicate_send,
        args.resume_created_delivery,
        adapter,
    )
    print(json.dumps([action.to_dict() for action in actions], ensure_ascii=False, indent=2))
    return 0


def parse_slot_codes(raw_values: list[str]) -> tuple[str, ...]:
    codes: list[str] = []
    for raw_value in raw_values:
        codes.extend(part.strip() for part in raw_value.split(",") if part.strip())
    if not codes:
        raise SystemExit("--slot-code must not be empty")
    return tuple(dict.fromkeys(codes))


def telegram_adapter(args: argparse.Namespace) -> TelegramBotApiAdapter:
    if not args.approve_real_send:
        raise SystemExit("real mode requires --approve-real-send")
    return TelegramBotApiAdapter(read_bot_token(args))


def read_bot_token(args: argparse.Namespace) -> str:
    if args.token_file is not None:
        return args.token_file.read_text(encoding="utf-8").strip()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise SystemExit("real mode requires --token-file or TELEGRAM_BOT_TOKEN")
    return token


if __name__ == "__main__":
    raise SystemExit(main())
