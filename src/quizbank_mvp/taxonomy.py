"""Canonical taxonomy projections for the MVP API."""

from __future__ import annotations


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
