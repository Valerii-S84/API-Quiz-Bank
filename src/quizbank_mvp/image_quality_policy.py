"""Deterministic image quality policy for generated quiz visuals."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_THEME_GROUP_CONFIG_PATH = ROOT / "config" / "image_quality_theme_groups.yaml"
ALLOWED_IMAGE_QUALITIES = frozenset({"low", "medium"})
IMAGE_QUALITY_SOURCES = frozenset({"policy", "override"})
THEME_GROUPS = frozenset({"simple_visual", "situational", "abstract_complex"})
BASE_LEVEL_MEDIUM_SHARE = {
    "A1": 5,
    "A2": 10,
    "B1": 20,
    "B2": 30,
    "C1": 40,
    "C2": 50,
}
THEME_GROUP_ADJUSTMENT = {
    "simple_visual": -5,
    "situational": 0,
    "abstract_complex": 10,
}
LEVEL_PATTERN = re.compile(r"^([ABC][12])(?:\.\d+)?$")


class ImageQualityPolicyError(ValueError):
    """Raised when image quality policy inputs or config are invalid."""


@dataclass(frozen=True)
class ImageQualityDecision:
    theme_group: str
    image_quality_policy_share: int
    image_quality_recommended: str
    image_quality_source: str
    image_quality_override: str | None

    def as_fields(self) -> dict[str, object]:
        return {
            "theme_group": self.theme_group,
            "image_quality_recommended": self.image_quality_recommended,
            "image_quality_source": self.image_quality_source,
            "image_quality_policy_share": self.image_quality_policy_share,
            "image_quality_override": self.image_quality_override,
        }


def resolve_image_quality(
    item_id: str,
    level: str,
    theme_id: str,
    image_quality_override: str | None = None,
) -> str:
    override = normalized_override(image_quality_override)
    if override is not None:
        return override
    return resolve_image_quality_decision(item_id, level, theme_id).image_quality_recommended


def resolve_image_quality_decision(
    item_id: str,
    level: str,
    theme_id: str,
    image_quality_override: str | None = None,
    theme_groups: Mapping[str, str] | None = None,
) -> ImageQualityDecision:
    override = normalized_override(image_quality_override)
    groups = load_theme_groups() if theme_groups is None else dict(theme_groups)
    theme_group = group_for_theme(theme_id, groups)
    share = medium_share_for(level, theme_group)
    recommended = override or policy_quality_for(item_id, share)
    source = "override" if override is not None else "policy"
    return ImageQualityDecision(theme_group, share, recommended, source, override)


def enriched_image_quality_fields(
    row: Mapping[str, str],
    theme_groups: Mapping[str, str] | None = None,
) -> dict[str, object]:
    decision = resolve_image_quality_decision(
        str(row.get("item_id", "")),
        str(row.get("sublevel", "")),
        str(row.get("theme_id", "")),
        nullable_text(row.get("image_quality_override")),
        theme_groups,
    )
    return decision.as_fields()


def policy_quality_for(item_id: str, medium_share: int) -> str:
    if not str(item_id).strip():
        raise ImageQualityPolicyError("item_id must not be empty")
    if medium_share < 0 or medium_share > 100:
        raise ImageQualityPolicyError(f"medium_share out of range: {medium_share}")
    bucket = stable_hash_bucket(item_id)
    if bucket < medium_share:
        return "medium"
    return "low"


def stable_hash_bucket(item_id: str) -> int:
    digest = hashlib.sha256(item_id.encode("utf-8")).hexdigest()
    return int(digest, 16) % 100


def medium_share_for(level: str, theme_group: str) -> int:
    normalized = normalize_level(level)
    if theme_group not in THEME_GROUP_ADJUSTMENT:
        raise ImageQualityPolicyError(f"unknown theme group: {theme_group}")
    raw_share = BASE_LEVEL_MEDIUM_SHARE[normalized] + THEME_GROUP_ADJUSTMENT[theme_group]
    return min(max(raw_share, 0), 70)


def normalize_level(level: str) -> str:
    text = str(level).strip().upper()
    match = LEVEL_PATTERN.fullmatch(text)
    if match is None:
        raise ImageQualityPolicyError(f"invalid CEFR level: {level}")
    return match.group(1)


def group_for_theme(theme_id: str, theme_groups: Mapping[str, str]) -> str:
    normalized_theme = str(theme_id).strip()
    if normalized_theme not in theme_groups:
        raise ImageQualityPolicyError(f"theme is not configured: {normalized_theme}")
    group = str(theme_groups[normalized_theme]).strip()
    if group not in THEME_GROUPS:
        raise ImageQualityPolicyError(f"invalid theme group for {normalized_theme}: {group}")
    return group


def normalized_override(value: str | None) -> str | None:
    text = nullable_text(value)
    if text is None:
        return None
    if text not in ALLOWED_IMAGE_QUALITIES:
        raise ImageQualityPolicyError(f"invalid image quality override: {text}")
    return text


def nullable_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_theme_group_coverage(
    theme_ids: set[str],
    theme_groups: Mapping[str, str],
) -> None:
    missing = sorted(theme_id for theme_id in theme_ids if theme_id not in theme_groups)
    if missing:
        raise ImageQualityPolicyError(f"themes missing from image quality config: {', '.join(missing)}")
    for theme_id, group in sorted(theme_groups.items()):
        if group not in THEME_GROUPS:
            raise ImageQualityPolicyError(f"invalid theme group for {theme_id}: {group}")


def validate_policy_fields(fields: Mapping[str, object]) -> None:
    group_for_theme(str(fields.get("theme_id", "")), {str(fields.get("theme_id", "")): str(fields.get("theme_group", ""))})
    recommended = str(fields.get("image_quality_recommended", "")).strip()
    source = str(fields.get("image_quality_source", "")).strip()
    if recommended not in ALLOWED_IMAGE_QUALITIES:
        raise ImageQualityPolicyError(f"invalid recommended image quality: {recommended}")
    if source not in IMAGE_QUALITY_SOURCES:
        raise ImageQualityPolicyError(f"invalid image quality source: {source}")
    override = normalized_override(nullable_text(fields.get("image_quality_override")))
    share = int(fields.get("image_quality_policy_share", -1))
    if share < 0 or share > 70:
        raise ImageQualityPolicyError(f"invalid image quality policy share: {share}")
    if source == "override" and override is None:
        raise ImageQualityPolicyError("override source requires image_quality_override")


@lru_cache(maxsize=1)
def load_theme_groups(config_path: Path = DEFAULT_THEME_GROUP_CONFIG_PATH) -> dict[str, str]:
    return parse_theme_group_config(config_path.read_text(encoding="utf-8"))


def parse_theme_group_config(content: str) -> dict[str, str]:
    groups: dict[str, str] = {}
    in_theme_groups = False
    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line == "theme_groups:":
            in_theme_groups = True
            continue
        if not in_theme_groups or not line.startswith("  ") or ":" not in line:
            raise ImageQualityPolicyError("invalid image quality theme group config")
        theme_id, group = line.strip().split(":", 1)
        if theme_id in groups:
            raise ImageQualityPolicyError(f"duplicate theme group config: {theme_id}")
        groups[theme_id.strip()] = group.strip()
    if not groups:
        raise ImageQualityPolicyError("image quality theme group config is empty")
    validate_theme_group_coverage(set(groups), groups)
    return groups
