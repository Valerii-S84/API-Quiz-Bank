"""Time and identifier primitives shared by runtime modules."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_usage_date() -> str:
    return date.today().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"
