"""Lightweight semantic parsing utilities."""

from __future__ import annotations

import re

from .models import Anchor
from .utils import normalize_idea_text, normalize_token


_TIME_WORDS = {"today", "tonight", "tomorrow", "yesterday", "morning", "evening", "afternoon"}
_COMMON_VERBS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "being",
    "am",
    "go",
    "going",
    "want",
    "wants",
    "used",
    "use",
    "uses",
    "plan",
    "plans",
    "doing",
    "do",
    "does",
    "called",
}
_NEGATIONS = {"no", "not", "never", "don't", "doesn't", "cannot", "can't"}
_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_STOPWORDS = {"to", "the", "a", "an", "by", "of", "at", "in", "on", "for"}


def extract_anchors(idea: str) -> list[Anchor]:
    """Extract deterministic, lightweight semantic anchors from idea text."""
    normalized = normalize_idea_text(idea)
    tokens = _WORD_RE.findall(normalized)
    anchors: list[Anchor] = []

    if not tokens:
        return anchors

    # Subject heuristic: first token if title-cased or pronoun-like noun.
    first = tokens[0]
    if first and (first[0].isupper() or normalize_token(first) in {"user", "system", "canvas", "uwm", "david"}):
        anchors.append(Anchor("subject", first, normalize_token(first), 0))

    for idx, token in enumerate(tokens):
        norm = normalize_token(token)
        if not norm:
            continue
        if norm in _NEGATIONS:
            anchors.append(Anchor("negation", token, norm, idx))
        if norm in _TIME_WORDS:
            anchors.append(Anchor("time", token, norm, idx))
        if token[0].isupper() and idx > 0:
            anchors.append(Anchor("entity", token, norm, idx))
        if norm in _COMMON_VERBS:
            anchors.append(Anchor("verb", token, norm, idx))

    # Object heuristic: first non-stop content word after first verb.
    verb_positions = [a.position for a in anchors if a.anchor_type == "verb" and a.position is not None]
    if verb_positions:
        start = verb_positions[0] + 1
        for idx in range(start, len(tokens)):
            norm = normalize_token(tokens[idx])
            if norm and norm not in _COMMON_VERBS and norm not in _NEGATIONS and norm not in _STOPWORDS:
                anchors.append(Anchor("object", tokens[idx], norm, idx))
                break

    return _dedupe(anchors)


def _dedupe(anchors: list[Anchor]) -> list[Anchor]:
    seen: set[tuple[str, str, int | None]] = set()
    out: list[Anchor] = []
    for anchor in anchors:
        key = (anchor.anchor_type, anchor.anchor_norm, anchor.position)
        if key in seen:
            continue
        seen.add(key)
        out.append(anchor)
    return out
