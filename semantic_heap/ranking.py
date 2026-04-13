"""Explainable ranking model for semantic retrieval."""

from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher

from .models import Anchor


def text_similarity(query: str, candidate: str) -> float:
    """Simple normalized text similarity."""
    return SequenceMatcher(None, query.lower(), candidate.lower()).ratio()


def anchor_overlap(query_anchors: list[Anchor], candidate_anchors: list[Anchor]) -> tuple[float, dict[str, int]]:
    """Compute overlap score and anchor-type debugging details."""
    q = Counter((a.anchor_type, a.anchor_norm) for a in query_anchors)
    c = Counter((a.anchor_type, a.anchor_norm) for a in candidate_anchors)
    common = q & c

    type_counts: dict[str, int] = {}
    for (anchor_type, _), count in common.items():
        type_counts[anchor_type] = type_counts.get(anchor_type, 0) + count

    overlap = sum(common.values())
    denom = max(len(q), 1)
    return overlap / denom, type_counts


def weighted_score(text_score: float, anchor_score: float, temporal_score: float, strength_score: float, stale_penalty: float) -> float:
    """Combine core scores in an explicit weighted model."""
    return (
        text_score * 0.25
        + anchor_score * 0.30
        + temporal_score * 0.30
        + strength_score * 0.15
        - stale_penalty
    )
