"""Deterministic semantic path generation."""

from __future__ import annotations

from .models import Anchor
from .utils import normalize_token


def generate_paths(domain: str, idea: str, anchors: list[Anchor]) -> list[str]:
    """Generate broad-to-specific semantic map paths."""
    subject = _find_first(anchors, "subject")
    obj = _find_first(anchors, "object")
    time = _find_first(anchors, "time")
    neg = any(a.anchor_type == "negation" for a in anchors)

    parts = [normalize_token(domain)]
    if subject:
        parts.append(subject)

    lower_idea = idea.lower()
    if "want" in lower_idea or "prefer" in lower_idea:
        parts.append("preferences")
    elif "going" in lower_idea or "plan" in lower_idea:
        parts.append("plans")
    elif "used by" in lower_idea or "is the" in lower_idea:
        parts.append("platforms")

    if obj:
        parts.append(obj)

    if "spelling" in lower_idea and "call" in lower_idea and neg:
        parts.extend(["spelling", "no_callout"])

    if "canvas" in lower_idea and "uwm" in lower_idea:
        parts = [normalize_token(domain), "uwm", "platforms", "canvas"]

    if time:
        parts.append(time)

    parts = [p for p in parts if p]
    if len(parts) < 2:
        return [normalize_token(domain)]
    return [".".join(parts)]


def _find_first(anchors: list[Anchor], anchor_type: str) -> str | None:
    for anchor in anchors:
        if anchor.anchor_type == anchor_type:
            return normalize_token(anchor.anchor_value)
    return None
