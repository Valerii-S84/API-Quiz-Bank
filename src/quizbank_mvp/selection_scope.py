"""Scope-derived selection filters for consumer delivery."""

from __future__ import annotations

from typing import Any

from .database import decode_json_field


SCOPE_CONFLICT_VALUE = "__scope_conflict__"


def effective_scope_replacement(
    request: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> dict[str, Any]:
    return {
        "filters": effective_scope_filters(request.filters, consumer, entitlement),
        "cefr_level": None,
        "theme_ids": (),
        "objective_ids": (),
        "pattern_ids": (),
        "excluded_item_ids": (),
    }


def effective_scope_filters(filters: Any, consumer: dict[str, Any], entitlement: dict[str, Any]):
    return type(filters)(
        cefr_level=effective_cefr_level(filters, consumer, entitlement),
        theme_ids=effective_theme_ids(filters, consumer, entitlement),
        objective_ids=filters.objective_ids,
        pattern_ids=filters.pattern_ids,
        excluded_item_ids=filters.excluded_item_ids,
    )


def effective_cefr_level(
    filters: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> str | None:
    if filters.cefr_level:
        return filters.cefr_level
    allowed_levels = bounded_scope_values(
        decode_json_field(consumer["allowed_cefr_levels_json"]),
        decode_json_field(entitlement["allowed_cefr_levels_json"]),
    )
    if allowed_levels is None:
        return None
    if len(allowed_levels) == 1:
        return allowed_levels[0]
    if not allowed_levels:
        return SCOPE_CONFLICT_VALUE
    return None


def effective_theme_ids(
    filters: Any,
    consumer: dict[str, Any],
    entitlement: dict[str, Any],
) -> tuple[str, ...]:
    if filters.theme_ids:
        return filters.theme_ids
    allowed_themes = bounded_scope_values(
        decode_json_field(consumer["allowed_theme_ids_json"]),
        decode_json_field(entitlement["allowed_theme_ids_json"]),
    )
    if allowed_themes is None:
        return ()
    return allowed_themes or (SCOPE_CONFLICT_VALUE,)


def bounded_scope_values(first: list[str], second: list[str]) -> tuple[str, ...] | None:
    if not first and not second:
        return None
    if not first:
        return tuple(second)
    if not second:
        return tuple(first)
    second_values = set(second)
    return tuple(value for value in first if value in second_values)
