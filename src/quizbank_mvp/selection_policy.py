"""Selection policy model for the MVP runtime."""

from __future__ import annotations

from dataclasses import dataclass, field


DEFAULT_HARD_FILTERS = (
    "status",
    "cefr_level",
    "theme_id",
    "objective_id",
    "pattern_id",
    "source_traceability",
    "repeat_policy",
    "explicit_exclusion",
    "entitlement",
    "quota",
)
DEFAULT_REPEAT_BLOCK_STATUSES = ("created", "delivered", "reserved", "sent", "failed")


@dataclass(frozen=True)
class RepeatPolicy:
    enabled: bool = True
    scope: str = "consumer"
    repeat_window_days: int | None = None
    blocked_delivery_statuses: tuple[str, ...] = DEFAULT_REPEAT_BLOCK_STATUSES
    fallback_reason_code: str = "SELECTION_REPEAT_POLICY_EXHAUSTED"

    def __post_init__(self) -> None:
        if self.repeat_window_days is not None and self.repeat_window_days < 0:
            raise ValueError("repeat_window_days must be non-negative")

    def to_context(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "scope": self.scope,
            "repeat_window_days": self.repeat_window_days,
            "blocked_delivery_statuses": list(self.blocked_delivery_statuses),
            "fallback_reason_code": self.fallback_reason_code,
        }


@dataclass(frozen=True)
class ChannelCyclePolicy:
    enabled: bool = True
    scope: str = "consumer_channel"
    exhaustion_rule: str = "deny_when_cycle_exhausted"
    fallback_reason_code: str = "SELECTION_CHANNEL_CYCLE_EXHAUSTED"

    def to_context(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "scope": self.scope,
            "exhaustion_rule": self.exhaustion_rule,
            "fallback_reason_code": self.fallback_reason_code,
        }


@dataclass(frozen=True)
class TargetDistributionPolicy:
    enabled: bool = True
    scope: str = "consumer_channel"
    fallback_reason_code: str = "SELECTION_TARGET_DISTRIBUTION_UNAVAILABLE"

    def to_context(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "scope": self.scope,
            "fallback_reason_code": self.fallback_reason_code,
        }


@dataclass(frozen=True)
class SelectionPolicy:
    hard_filters: tuple[str, ...] = DEFAULT_HARD_FILTERS
    repeat_policy: RepeatPolicy = field(default_factory=RepeatPolicy)
    channel_cycle_policy: ChannelCyclePolicy = field(default_factory=ChannelCyclePolicy)
    target_distribution_policy: TargetDistributionPolicy = field(
        default_factory=TargetDistributionPolicy
    )
    no_candidate_reason_code: str = "SELECTION_NO_ELIGIBLE_ITEM"

    def to_context(self) -> dict[str, object]:
        return {
            "hard_filters": list(self.hard_filters),
            "repeat_policy": self.repeat_policy.to_context(),
            "channel_cycle_policy": self.channel_cycle_policy.to_context(),
            "target_distribution_policy": self.target_distribution_policy.to_context(),
            "fallback_reason_codes": self.fallback_reason_codes(),
            "no_candidate_reason_code": self.no_candidate_reason_code,
        }

    def fallback_reason_codes(self) -> list[str]:
        return [
            self.no_candidate_reason_code,
            self.repeat_policy.fallback_reason_code,
            self.channel_cycle_policy.fallback_reason_code,
            self.target_distribution_policy.fallback_reason_code,
        ]

    def selection_reason_summary(self) -> str:
        return "eligible_by_" + "_".join(self.hard_filters)
