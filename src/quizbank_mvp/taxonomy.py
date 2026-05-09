"""Canonical taxonomy projections for the MVP API."""

from __future__ import annotations

import re


CANONICAL_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
TOPIC_TITLES = {
    "T01": "Person / Identität / Familie",
    "T02": "Alltag / Zeit / Organisation",
    "T03": "Wohnen / Haushalt / Verträge",
    "T04": "Einkaufen / Geld / Konsum",
    "T05": "Essen / Gesundheit / Pflege",
    "T06": "Arbeit / Beruf / Karriere",
    "T07": "Schule / Bildung / Weiterbildung",
    "T08": "Verkehr / Reise / Orientierung",
    "T09": "Kommunikation / Telefon / Nachricht / E-Mail",
    "T10": "Termine / Formulare / Behörden / Recht",
    "T11": "Freizeit / Kultur / Service / soziale Kontakte",
    "T12": "Medien / Digitales / Nachrichten",
    "T13": "Gesellschaft / Integration / Werte",
    "T14": "Umwelt / Nachhaltigkeit / Alltagssysteme",
    "T15": "Wirtschaft / Finanzen / Arbeitswelt",
    "T16": "Wissenschaft / Technik / Forschung",
    "T17": "Politik / Öffentlichkeit / Debatte",
    "T18": "Analyse / Interpretation / Argumentation",
}
OBJECTIVE_TITLES = {f"O{index:02d}": f"Objective O{index:02d}" for index in range(1, 17)}
PATTERN_TITLES = {f"P{index:02d}": f"Pattern P{index:02d}" for index in range(1, 13)}


def theme_label(theme_id: str) -> dict[str, str]:
    title = TOPIC_TITLES.get(theme_id, "Unknown theme")
    return {"title": title, "slug": slugify_title(title)}


def objective_label(objective_id: str) -> dict[str, str]:
    return {"title": OBJECTIVE_TITLES.get(objective_id, "Unknown objective")}


def pattern_label(pattern_id: str) -> dict[str, str]:
    return {"title": PATTERN_TITLES.get(pattern_id, "Unknown pattern")}


def slugify_title(title: str) -> str:
    normalized = (
        title.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "theme"


def level_catalog() -> list[dict[str, object]]:
    return [
        {"cefr_level": level, "order_index": index, "status": "active"}
        for index, level in enumerate(CANONICAL_LEVELS, start=1)
    ]


def topic_catalog() -> list[dict[str, str]]:
    return [
        {
            "topic_id": topic_id,
            "theme_id": topic_id,
            "title": title,
            "status": "active",
        }
        for topic_id, title in TOPIC_TITLES.items()
    ]
