"""Visual target extraction for quiz image prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass


ARTICLES = frozenset(
    {
        "der",
        "die",
        "das",
        "den",
        "dem",
        "des",
        "ein",
        "eine",
        "einen",
        "einem",
        "einer",
        "eines",
        "kein",
        "keine",
        "keinen",
        "keinem",
        "keiner",
        "keines",
    }
)
PREPOSITIONS = frozenset(
    {
        "an",
        "am",
        "auf",
        "aus",
        "bei",
        "bis",
        "durch",
        "fuer",
        "für",
        "gegen",
        "hinter",
        "im",
        "in",
        "ins",
        "mit",
        "nach",
        "neben",
        "ohne",
        "seit",
        "trotz",
        "ueber",
        "über",
        "um",
        "unter",
        "von",
        "vor",
        "waehrend",
        "während",
        "wegen",
        "zwischen",
        "zu",
        "zum",
        "zur",
    }
)
PRONOUNS = frozenset(
    {
        "ich",
        "du",
        "er",
        "sie",
        "es",
        "wir",
        "ihr",
        "mich",
        "dich",
        "ihn",
        "uns",
        "euch",
        "mir",
        "dir",
        "ihm",
        "ihnen",
        "mein",
        "meine",
        "meinen",
        "meinem",
        "meiner",
        "dein",
        "deine",
        "deinen",
        "deinem",
        "deiner",
        "sein",
        "seine",
        "seinen",
        "seinem",
        "seiner",
        "unser",
        "unsere",
        "euren",
        "euer",
    }
)
CONJUNCTIONS = frozenset(
    {
        "aber",
        "als",
        "bevor",
        "bis",
        "da",
        "damit",
        "dass",
        "denn",
        "falls",
        "nachdem",
        "ob",
        "obwohl",
        "oder",
        "sobald",
        "sondern",
        "und",
        "waehrend",
        "während",
        "weil",
        "wenn",
        "wie",
    }
)
PARTICLES_AND_FILLERS = frozenset(
    {
        "auch",
        "bitte",
        "doch",
        "eben",
        "erst",
        "etwa",
        "gar",
        "halt",
        "ja",
        "mal",
        "nicht",
        "noch",
        "nur",
        "schon",
        "sehr",
        "so",
        "vielleicht",
        "wohl",
        "zu",
    }
)
MODAL_WORDS = frozenset(
    {
        "bestimmt",
        "eigentlich",
        "eventuell",
        "jedenfalls",
        "leider",
        "moeglich",
        "möglich",
        "sicher",
        "vermutlich",
        "wahrscheinlich",
    }
)
NON_VISUAL_ANSWER_TOKENS = (
    ARTICLES | PREPOSITIONS | PRONOUNS | CONJUNCTIONS | PARTICLES_AND_FILLERS | MODAL_WORDS
)
NOUN_TARGET_SKIP_TOKENS = NON_VISUAL_ANSWER_TOKENS | frozenset(
    {
        "bin",
        "bist",
        "bleibt",
        "hat",
        "habe",
        "haben",
        "ist",
        "kann",
        "muss",
        "sind",
        "war",
        "waren",
        "werde",
        "werden",
        "wird",
    }
)
DOCUMENT_KEYWORDS = frozenset(
    {
        "akte",
        "antrag",
        "bescheid",
        "bescheinigung",
        "bestaetigung",
        "bestätigung",
        "bewerbung",
        "brief",
        "dokument",
        "e-mail",
        "email",
        "formular",
        "karte",
        "kontoauszug",
        "kuendigung",
        "kündigung",
        "lebenslauf",
        "mahnung",
        "mappe",
        "meldung",
        "mietvertrag",
        "nachricht",
        "protokoll",
        "rechnung",
        "schreiben",
        "unterlage",
        "vertrag",
    }
)


@dataclass(frozen=True)
class VisualTargetResolution:
    visual_target: str
    context_hint: str
    is_answer_directly_visualizable: bool
    reason_code: str


def extract_visual_target(
    question_text: str,
    correct_answer: str,
    visual_mode: str,
    options: list[str] | None = None,
) -> VisualTargetResolution:
    if non_visual_answer_token(correct_answer):
        target = context_anchor(question_text, options) or fallback_context_target(question_text)
        return resolution(target, question_text, False, "non_visual_answer_context_anchor")
    if visual_mode == "document_form":
        target = document_anchor(correct_answer) or document_anchor(question_text)
        return resolution(target or object_target(correct_answer), question_text, True, "document_form_anchor")
    if visual_mode == "context_only":
        target = context_anchor(question_text, options) or object_target(correct_answer)
        return resolution(target, question_text, True, "context_only_anchor")
    if visual_mode == "symbolic_abstract":
        target = symbolic_anchor(correct_answer, question_text)
        return resolution(target, question_text, False, "symbolic_abstract_anchor")
    if visual_mode == "target_action":
        return resolution(correct_answer.strip(), question_text, True, "direct_visual_answer")
    if visual_mode == "target_object":
        return resolution(object_target(correct_answer), question_text, True, "direct_visual_answer")
    return resolution(clean_answer_phrase(correct_answer), question_text, True, "direct_visual_answer")


def non_visual_answer_token(answer: str) -> bool:
    tokens = [normalize_token(token) for token in text_tokens(answer)]
    return bool(tokens) and all(token in NON_VISUAL_ANSWER_TOKENS for token in tokens)


def context_anchor(question_text: str, options: list[str] | None = None) -> str:
    blank = re.search(r"_{3,}", question_text)
    if blank is not None:
        return blank_connected_target(question_text, blank) or option_anchor(options)
    return first_noun_phrase(question_text) or option_anchor(options)


def blank_connected_target(question_text: str, blank: re.Match[str]) -> str:
    right_target = first_noun_phrase(question_text[blank.end() :])
    if right_target:
        return right_target
    return last_noun_phrase(question_text[: blank.start()])


def document_anchor(text: str) -> str:
    tokens = text_tokens(text)
    for index, token in enumerate(tokens):
        if document_keyword_match(token):
            return clean_answer_phrase(" ".join(document_phrase(tokens, index)))
    return ""


def object_target(answer: str) -> str:
    document_target = document_anchor(answer)
    if document_target:
        return document_target
    return clean_answer_phrase(answer)


def symbolic_anchor(correct_answer: str, question_text: str) -> str:
    return object_target(correct_answer) or first_noun_phrase(question_text) or "abstract context"


def option_anchor(options: list[str] | None) -> str:
    for option in options or []:
        if not non_visual_answer_token(option):
            return object_target(option)
    return ""


def first_noun_phrase(text: str) -> str:
    tokens = text_tokens(text)
    for index, token in enumerate(tokens):
        if is_noun_target_candidate(token):
            return clean_answer_phrase(" ".join(noun_phrase(tokens, index)))
    return ""


def last_noun_phrase(text: str) -> str:
    tokens = text_tokens(text)
    for index in range(len(tokens) - 1, -1, -1):
        if is_noun_target_candidate(tokens[index]):
            return clean_answer_phrase(" ".join(noun_phrase(tokens, index)))
    return ""


def noun_phrase(tokens: list[str], noun_index: int) -> list[str]:
    start = noun_index
    while start > 0 and normalize_token(tokens[start - 1]) in ARTICLES:
        start -= 1
    return tokens[start : noun_index + 1]


def document_phrase(tokens: list[str], keyword_index: int) -> list[str]:
    start = keyword_index
    while start > 0 and normalize_token(tokens[start - 1]) in ARTICLES:
        start -= 1
    return tokens[start : keyword_index + 1]


def clean_answer_phrase(answer: str) -> str:
    tokens = text_tokens(answer)
    if tokens and normalize_token(tokens[0]) in ARTICLES:
        tokens = tokens[1:]
    return " ".join(tokens).strip() or answer.strip()


def fallback_context_target(question_text: str) -> str:
    for token in text_tokens(question_text):
        if normalize_token(token) not in NOUN_TARGET_SKIP_TOKENS:
            return token
    return "context"


def context_hint(question_text: str, visual_target: str) -> str:
    tokens = [
        token
        for token in text_tokens(question_text.replace("___", " "))
        if normalize_token(token) not in NON_VISUAL_ANSWER_TOKENS
    ]
    hint = " ".join(tokens[:10]).strip()
    return hint or visual_target


def resolution(
    visual_target: str,
    question_text: str,
    is_answer_directly_visualizable: bool,
    reason_code: str,
) -> VisualTargetResolution:
    target = visual_target.strip() or "context"
    return VisualTargetResolution(
        visual_target=target,
        context_hint=context_hint(question_text, target),
        is_answer_directly_visualizable=is_answer_directly_visualizable,
        reason_code=reason_code,
    )


def is_noun_target_candidate(token: str) -> bool:
    if normalize_token(token) in NOUN_TARGET_SKIP_TOKENS:
        return False
    return token[:1].isupper() and len(token) > 1


def document_keyword_match(token: str) -> bool:
    normalized = normalize_token(token)
    return normalized in DOCUMENT_KEYWORDS or any(normalized.endswith(keyword) for keyword in DOCUMENT_KEYWORDS)


def normalize_token(token: str) -> str:
    return token.strip().strip(".,;:!?()[]{}\"'„“”").lower()


def text_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß-]*", text)
