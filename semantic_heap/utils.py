"""Utility helpers."""

from __future__ import annotations

import re


_WHITESPACE = re.compile(r"\s+")
_TRAILING_NOISE = re.compile(r"[\s\.,;:!?]+$")
_TOKEN_SANITIZE = re.compile(r"[^a-z0-9_]+")


def normalize_idea_text(idea: str) -> str:
    """Normalize user-provided idea text with minimal rewriting."""
    text = _WHITESPACE.sub(" ", idea.strip())
    text = _TRAILING_NOISE.sub("", text)
    return text


def normalize_token(value: str) -> str:
    """Normalize a token for indexing and path generation."""
    token = value.strip().lower().replace("-", "_")
    token = _TOKEN_SANITIZE.sub("", token)
    return token
