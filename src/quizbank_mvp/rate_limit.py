"""In-process abuse throttling for protected MVP delivery endpoints."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field

from .problems import QuizBankProblem


DEFAULT_WINDOW_SECONDS = 60
DEFAULT_DELIVERY_REQUESTS = 120


@dataclass
class RateLimitBucket:
    window_started_at: float
    request_count: int = 0


@dataclass
class FixedWindowRateLimiter:
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    delivery_requests: int = DEFAULT_DELIVERY_REQUESTS
    buckets: dict[str, RateLimitBucket] = field(default_factory=dict)

    @classmethod
    def from_environment(cls) -> "FixedWindowRateLimiter":
        return cls(
            window_seconds=positive_int_env(
                "QUIZBANK_RATE_LIMIT_WINDOW_SECONDS",
                DEFAULT_WINDOW_SECONDS,
            ),
            delivery_requests=positive_int_env(
                "QUIZBANK_RATE_LIMIT_DELIVERY_REQUESTS",
                DEFAULT_DELIVERY_REQUESTS,
            ),
        )

    def check_delivery(self, key: str) -> None:
        now = time.monotonic()
        bucket = self.buckets.get(key)
        if bucket is None or now - bucket.window_started_at >= self.window_seconds:
            self.buckets[key] = RateLimitBucket(window_started_at=now, request_count=1)
            return

        bucket.request_count += 1
        if bucket.request_count > self.delivery_requests:
            raise QuizBankProblem(
                429,
                "RATE_LIMIT_EXCEEDED",
                "Rate limit exceeded",
                "Reduce request volume and retry after the current rate-limit window.",
                "https://api.quizbank.example/problems/rate-limit-exceeded",
            )


def positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def delivery_rate_limit_key(
    client_host: str | None,
    consumer_id: str | None,
    api_key: str | None,
) -> str:
    host_part = client_host or "unknown"
    consumer_part = consumer_id or "missing-consumer"
    key_part = "missing-key"
    if api_key:
        key_part = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    return f"delivery:{host_part}:{consumer_part}:{key_part}"
