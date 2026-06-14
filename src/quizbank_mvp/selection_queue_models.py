"""Selection queue identifiers and small transfer models."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib


DEFAULT_QUEUE_CHANNELS = ("api",)
DEFAULT_QUEUE_TARGET_SIZE = 50
MIN_QUEUE_TARGET_SIZE = 50
MAX_QUEUE_TARGET_SIZE = 100


@dataclass(frozen=True)
class QueueScope:
    consumer_id: str
    channel_id: str
    language_code: str
    content_bank_id: str
    bank_version_id: str
    cefr_level: str = ""
    theme_id: str = ""
    objective_id: str = ""
    pattern_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class QueueRefillResult:
    queue_id: str
    scope: QueueScope
    target_size: int
    added_count: int
    available_count: int
    queue_status: str
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "queue_id": self.queue_id,
            "scope": self.scope.to_dict(),
            "target_size": self.target_size,
            "added_count": self.added_count,
            "available_count": self.available_count,
            "queue_status": self.queue_status,
            "skipped_reason": self.skipped_reason,
        }


def selection_queue_id(scope: QueueScope) -> str:
    digest = hashlib.sha256("|".join(scope.to_dict().values()).encode("utf-8")).hexdigest()
    return f"selq_{digest[:24]}"


def selection_queue_item_id(queue_id: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{queue_id}|{item_id}".encode("utf-8")).hexdigest()
    return f"selqi_{digest[:24]}"


def validate_target_size(target_size: int) -> None:
    if target_size < MIN_QUEUE_TARGET_SIZE or target_size > MAX_QUEUE_TARGET_SIZE:
        raise ValueError("target_size must be between 50 and 100")


def normalized_channels(channel_ids: tuple[str, ...]) -> tuple[str, ...]:
    channels = tuple(channel_id.strip() for channel_id in channel_ids if channel_id.strip())
    if not channels:
        raise ValueError("at least one channel_id is required")
    return channels
