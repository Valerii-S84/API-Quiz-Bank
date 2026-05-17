"""Deterministic visual mode routing for quiz image generation."""

from __future__ import annotations

import re

from .visual_target_extractor import (
    DOCUMENT_KEYWORDS,
    NOUN_TARGET_SKIP_TOKENS,
    non_visual_answer_token,
    normalize_token,
    text_tokens,
)


VISUAL_MODES = frozenset(
    {
        "target_action",
        "target_object",
        "context_only",
        "document_form",
        "symbolic_abstract",
    }
)
SIMPLE_CONCRETE_THEME_IDS = frozenset({"T01", "T03", "T04", "T05", "T08", "T11"})
MIXED_SITUATIONAL_THEME_IDS = frozenset({"T02", "T06", "T07", "T09", "T10", "T12", "T15"})
ABSTRACT_HIGH_RISK_THEME_IDS = frozenset({"T13", "T14", "T16", "T17", "T18"})
DOCUMENT_THEME_IDS = frozenset({"T03", "T09", "T10", "T15"})
VISIBLE_ACTION_VERBS = frozenset(
    {
        "abgeben",
        "ausfuellen",
        "ausfüllen",
        "ausraeumen",
        "ausräumen",
        "bezahlen",
        "bringen",
        "buchen",
        "fahren",
        "kaufen",
        "kochen",
        "lesen",
        "machen",
        "nehmen",
        "oeffnen",
        "öffnen",
        "putzen",
        "schliessen",
        "schließen",
        "schreiben",
        "tragen",
        "trinken",
        "unterschreiben",
        "vorbereiten",
    }
)
ABSTRACT_VERBS = frozenset(
    {
        "analysieren",
        "argumentieren",
        "begruenden",
        "begründen",
        "bewerten",
        "deuten",
        "interpretieren",
        "meinen",
        "schliessen",
        "schließen",
        "vermuten",
    }
)


def resolve_visual_mode(
    item_id: str,
    theme_id: str,
    level: str,
    question_text: str,
    correct_answer: str,
    options: list[str] | None = None,
) -> str:
    del item_id, level
    if non_visual_answer_token(correct_answer) or grammar_form_answer(correct_answer, question_text):
        return "context_only"
    del options
    combined_text = " ".join([question_text, correct_answer])
    if document_form_candidate(theme_id, combined_text):
        return "document_form"
    if normalized_theme(theme_id) in ABSTRACT_HIGH_RISK_THEME_IDS:
        return "symbolic_abstract"
    if visible_action_answer(correct_answer):
        return "target_action"
    return "target_object"


def document_form_candidate(theme_id: str, text: str) -> bool:
    normalized_theme_id = normalized_theme(theme_id)
    if not contains_document_keyword(text):
        return False
    return normalized_theme_id in DOCUMENT_THEME_IDS or strong_document_text(text)


def contains_document_keyword(text: str) -> bool:
    return any(document_keyword_token(token) for token in text_tokens(text))


def strong_document_text(text: str) -> bool:
    normalized_tokens = {normalize_token(token) for token in text_tokens(text)}
    return bool(normalized_tokens & DOCUMENT_KEYWORDS)


def document_keyword_token(token: str) -> bool:
    normalized = normalize_token(token)
    return normalized in DOCUMENT_KEYWORDS or any(normalized.endswith(keyword) for keyword in DOCUMENT_KEYWORDS)


def visible_action_answer(correct_answer: str) -> bool:
    tokens = text_tokens(correct_answer)
    if not tokens:
        return False
    verb = normalize_token(tokens[-1])
    if verb in ABSTRACT_VERBS:
        return False
    if verb in VISIBLE_ACTION_VERBS:
        return True
    if len(tokens) == 1:
        return correct_answer[:1].islower() and verb.endswith(("en", "eln", "ern"))
    return verb.endswith(("en", "eln", "ern"))


def grammar_form_answer(correct_answer: str, question_text: str) -> bool:
    tokens = text_tokens(correct_answer)
    if len(tokens) != 1 or not correct_answer[:1].islower():
        return False
    if normalize_token(tokens[0]) in VISIBLE_ACTION_VERBS:
        return False
    return blank_is_followed_by_noun(question_text)


def blank_is_followed_by_noun(question_text: str) -> bool:
    blank = re.search(r"_{3,}", question_text)
    if blank is None:
        return False
    for token in text_tokens(question_text[blank.end() :]):
        if normalize_token(token) in NOUN_TARGET_SKIP_TOKENS:
            continue
        return token[:1].isupper()
    return False


def normalized_theme(theme_id: str) -> str:
    return theme_id.strip().upper()
