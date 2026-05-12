"""Command line entrypoints for MVP database operations."""

from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path

from .database import (
    connect,
    initialize_database,
    seed_admin_credential,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_demo_state,
    seed_entitlement,
    transition_consumer_status,
    transition_item_status,
)
from .protected_beta import seed_protected_beta_channels


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
OWNER_ACTOR = "owner"
OWNER_ROLE = "owner"
OWNER_CREDENTIAL_ID = "admin_cred_owner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Quiz Bank MVP runtime commands.")
    parser.add_argument("--db-path", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the SQLite MVP schema.")

    seed_items = subparsers.add_parser("seed-items", help="Import a canonical JSONL fixture.")
    seed_items.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    seed_items.add_argument("--status", default="approved")

    seed_consumer_parser = subparsers.add_parser("seed-consumer", help="Create consumer access.")
    seed_consumer_parser.add_argument("--consumer-id", required=True)
    seed_consumer_parser.add_argument("--daily-quota-limit", type=int, default=10)
    seed_consumer_parser.add_argument("--cefr-level", action="append", default=[])
    seed_consumer_parser.add_argument("--theme-id", action="append", default=[])
    seed_consumer_parser.add_argument("--with-entitlement", action="store_true")
    seed_consumer_parser.add_argument("--entitlement-valid-until", default=None)
    seed_consumer_parser.add_argument("--actor", default="local_admin")
    seed_consumer_parser.add_argument("--grant-reason", default="manual MVP entitlement grant")
    seed_consumer_parser.add_argument("--api-key", default=None)

    demo = subparsers.add_parser("seed-demo", help="Seed demo item, consumers and entitlement.")
    demo.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)

    seed_admin = subparsers.add_parser(
        "seed-admin",
        help="Create the single owner admin password.",
    )
    seed_admin.add_argument("--reset", action="store_true")

    seed_beta = subparsers.add_parser(
        "seed-protected-beta",
        help="Create configured protected beta Telegram consumers.",
    )
    seed_beta.add_argument("--actor", default="protected_beta_seed")

    transition = subparsers.add_parser("transition-status", help="Transition item status.")
    transition.add_argument("--item-id", required=True)
    transition.add_argument("--to-status", required=True)
    transition.add_argument("--actor", default="local_admin")
    transition.add_argument("--reason", required=True)

    consumer_transition = subparsers.add_parser(
        "transition-consumer-status",
        help="Suspend or reactivate a consumer.",
    )
    consumer_transition.add_argument("--consumer-id", required=True)
    consumer_transition.add_argument(
        "--to-status",
        choices=["active", "suspended", "blocked"],
        required=True,
    )
    consumer_transition.add_argument("--actor", default="local_admin")
    consumer_transition.add_argument("--reason", required=True)

    subparsers.add_parser("show-audit-log", help="Print audit log as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "init-db":
        path = initialize_database(args.db_path)
        print(f"initialized database: {path}")
        return 0
    if args.command == "seed-items":
        count = seed_control_fixture(args.db_path, args.fixture, args.status)
        print(f"seeded quiz items: {count}")
        return 0
    if args.command == "seed-consumer":
        return seed_consumer_command(args)
    if args.command == "seed-demo":
        seed_demo_state(args.db_path, args.fixture)
        print("seeded MVP demo state")
        return 0
    if args.command == "seed-admin":
        return seed_admin(args)
    if args.command == "seed-protected-beta":
        consumer_ids = seed_protected_beta_channels(args.db_path, actor=args.actor)
        print("seeded protected beta consumers: " + ", ".join(consumer_ids))
        return 0
    if args.command == "transition-status":
        transition_item_status(args.db_path, args.item_id, args.to_status, args.actor, args.reason)
        print(f"transitioned {args.item_id} to {args.to_status}")
        return 0
    if args.command == "transition-consumer-status":
        transition_consumer_status(
            args.db_path,
            args.consumer_id,
            args.to_status,
            args.actor,
            args.reason,
        )
        print(f"transitioned consumer {args.consumer_id} to {args.to_status}")
        return 0
    if args.command == "show-audit-log":
        with connect(args.db_path) as connection:
            rows = connection.execute("SELECT * FROM audit_log ORDER BY created_at").fetchall()
        print(json.dumps([dict(row) for row in rows], ensure_ascii=False, indent=2))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


def seed_consumer_command(args: argparse.Namespace) -> int:
    seed_consumer(
        args.db_path,
        args.consumer_id,
        args.daily_quota_limit,
        args.cefr_level,
        args.theme_id,
    )
    if args.with_entitlement:
        seed_entitlement(
            args.db_path,
            args.consumer_id,
            args.cefr_level,
            args.theme_id,
            valid_until=args.entitlement_valid_until,
            actor=args.actor,
            reason=args.grant_reason,
        )
    if args.api_key:
        seed_api_credential(args.db_path, args.consumer_id, args.api_key)
    print(f"seeded consumer: {args.consumer_id}")
    return 0


def prompt_admin_password() -> str:
    password = getpass.getpass("Owner admin password: ")
    confirmation = getpass.getpass("Confirm owner admin password: ")
    if not password:
        raise SystemExit("admin password cannot be empty")
    if password != confirmation:
        raise SystemExit("admin password confirmation does not match")
    return password


def seed_admin(args: argparse.Namespace) -> int:
    if admin_password_is_configured(args.db_path) and not args.reset:
        raise SystemExit("owner admin password is already configured; use --reset to replace it")
    if args.reset:
        clear_admin_credentials(args.db_path)
    password = prompt_admin_password()
    seed_admin_credential(
        args.db_path,
        OWNER_ACTOR,
        OWNER_ROLE,
        password,
        credential_id=OWNER_CREDENTIAL_ID,
    )
    print("owner admin password configured")
    return 0


def admin_password_is_configured(db_path: Path | None) -> bool:
    with connect(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM admin_credentials").fetchone()
    return int(row["count"]) > 0


def clear_admin_credentials(db_path: Path | None) -> None:
    with connect(db_path) as connection:
        connection.execute("DELETE FROM admin_credentials")


if __name__ == "__main__":
    raise SystemExit(main())
