"""Selection request and context models."""

from __future__ import annotations

from dataclasses import dataclass, field

from .selection_policy import SelectionPolicy


@dataclass(frozen=True)
class SelectionFilters:
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()

    def to_context(self) -> dict[str, object]:
        return {
            "cefr_level": self.cefr_level,
            "theme_ids": list(self.theme_ids),
            "objective_ids": list(self.objective_ids),
            "pattern_ids": list(self.pattern_ids),
            "excluded_item_ids": list(self.excluded_item_ids),
        }


@dataclass(frozen=True)
class ConsumerProfile:
    consumer_id: str
    delivery_channel: str

    def to_context(self) -> dict[str, str]:
        return {
            "consumer_id": self.consumer_id,
            "delivery_channel": self.delivery_channel,
        }


@dataclass(frozen=True)
class SelectionTargetMix:
    level_weights: dict[str, float] = field(default_factory=dict)
    theme_weights: dict[str, float] = field(default_factory=dict)
    objective_weights: dict[str, float] = field(default_factory=dict)
    pattern_weights: dict[str, float] = field(default_factory=dict)

    def to_context(self) -> dict[str, dict[str, float]]:
        return {
            "level_weights": dict(self.level_weights),
            "theme_weights": dict(self.theme_weights),
            "objective_weights": dict(self.objective_weights),
            "pattern_weights": dict(self.pattern_weights),
        }


@dataclass(frozen=True)
class SelectionRequest:
    consumer_id: str
    filters: SelectionFilters | None = None
    delivery_mode: str = "api"
    deterministic: bool = False
    selection_strategy: str = "weighted_policy"
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    consumer_profile: ConsumerProfile | None = None
    target_mix: SelectionTargetMix = field(default_factory=SelectionTargetMix)
    cefr_level: str | None = None
    theme_ids: tuple[str, ...] = ()
    objective_ids: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    excluded_item_ids: tuple[str, ...] = ()
    quota_scope_key: str | None = None

    def __post_init__(self) -> None:
        filters = self.normalized_filters(self.filters or self.legacy_filters())
        self.validate_filter_contract(filters)
        object.__setattr__(self, "filters", filters)
        object.__setattr__(self, "consumer_profile", self.normalized_consumer_profile())
        object.__setattr__(self, "cefr_level", filters.cefr_level)
        object.__setattr__(self, "theme_ids", filters.theme_ids)
        object.__setattr__(self, "objective_ids", filters.objective_ids)
        object.__setattr__(self, "pattern_ids", filters.pattern_ids)
        object.__setattr__(self, "excluded_item_ids", filters.excluded_item_ids)

    def legacy_filters(self) -> SelectionFilters:
        return SelectionFilters(
            cefr_level=self.cefr_level,
            theme_ids=self.theme_ids,
            objective_ids=self.objective_ids,
            pattern_ids=self.pattern_ids,
            excluded_item_ids=self.excluded_item_ids,
        )

    def normalized_filters(self, filters: SelectionFilters) -> SelectionFilters:
        return SelectionFilters(
            cefr_level=filters.cefr_level,
            theme_ids=tuple(filters.theme_ids),
            objective_ids=tuple(filters.objective_ids),
            pattern_ids=tuple(filters.pattern_ids),
            excluded_item_ids=tuple(filters.excluded_item_ids),
        )

    def validate_filter_contract(self, filters: SelectionFilters) -> None:
        if self.filters is None:
            return
        if self.legacy_filters() != SelectionFilters():
            raise ValueError("SelectionRequest must use filters or legacy filter fields, not both")

    def normalized_consumer_profile(self) -> ConsumerProfile:
        if self.consumer_profile is not None:
            return self.consumer_profile
        return ConsumerProfile(
            consumer_id=self.consumer_id,
            delivery_channel=self.delivery_mode,
        )
