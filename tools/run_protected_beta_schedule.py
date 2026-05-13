#!/usr/bin/env python3
"""Run configured protected beta Telegram schedule slots."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp.protected_beta import (  # noqa: E402
    PROTECTED_BETA_TELEGRAM_CHANNELS,
    due_batches,
    run_protected_beta_batch,
    seed_protected_beta_channels,
)
from quizbank_mvp.telegram_delivery import TelegramBotApiAdapter  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run protected beta Telegram schedule slots.")
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--mode", choices=["dry_run", "real"], default="dry_run")
    parser.add_argument("--approve-real-send", action="store_true")
    parser.add_argument("--token-file", type=Path, default=None)
    parser.add_argument("--token-env", default="TELEGRAM_BOT_TOKEN")
    parser.add_argument("--seed-access", action="store_true")
    parser.add_argument("--slot-time", default=None, help="Berlin HH:MM slot to run.")
    parser.add_argument("--now", default=None, help="ISO datetime used to resolve due slots.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.seed_access:
        seed_protected_beta_channels(args.db_path)
    adapter = telegram_adapter(args)
    report = []
    for channel in PROTECTED_BETA_TELEGRAM_CHANNELS:
        for batch in selected_batches(channel, args):
            results = run_protected_beta_batch(
                args.db_path,
                channel,
                batch,
                args.mode,
                adapter,
                schedule_now(channel.timezone, args.now),
            )
            report.append(
                {
                    "consumer_id": channel.consumer_id,
                    "telegram_target_ref": results[0].telegram_target_ref if results else None,
                    "local_time": batch.local_time,
                    "slots": [
                        {
                            "slot_id": slot.stable_slot_id(channel.consumer_id),
                            "cefr_level": slot.cefr_level,
                            "theme_id": slot.theme_id,
                            "requested_count": slot.quiz_count,
                        }
                        for slot in batch.slots
                    ],
                    "results": [result.to_public_dict() for result in results],
                }
            )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def telegram_adapter(args: argparse.Namespace):
    if args.mode == "dry_run":
        return None
    if not args.approve_real_send:
        raise SystemExit("real mode requires --approve-real-send")
    return TelegramBotApiAdapter(read_bot_token(args))


def selected_batches(channel, args: argparse.Namespace):
    if args.slot_time is not None:
        return tuple(
            batch for batch in channel.schedule_batches
            if batch.local_time == args.slot_time
        )
    return due_batches(channel, schedule_now(channel.timezone, args.now))


def schedule_now(timezone: str, raw_now: str | None) -> datetime:
    if raw_now is None:
        return datetime.now(ZoneInfo(timezone))
    parsed = datetime.fromisoformat(raw_now)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ZoneInfo(timezone))
    return parsed


def read_bot_token(args: argparse.Namespace) -> str:
    if args.token_file is not None:
        return args.token_file.read_text(encoding="utf-8").strip()
    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise SystemExit("real mode requires --token-file or TELEGRAM_BOT_TOKEN")
    return token


if __name__ == "__main__":
    raise SystemExit(main())
