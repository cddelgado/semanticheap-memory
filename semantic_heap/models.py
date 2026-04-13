"""Datamodels for semantic heap memory results."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Anchor:
    """Extracted semantic anchor."""

    anchor_type: str
    anchor_value: str
    anchor_norm: str
    position: int | None = None


@dataclass(slots=True)
class SaveResult:
    """Return model for save operations."""

    idea_id: int
    normalized_idea: str
    source_text: str
    anchors: list[Anchor] = field(default_factory=list)
    semantic_paths: list[str] = field(default_factory=list)
    linked_idea_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class RetrieveMatch:
    """A ranked match for retrieval."""

    idea_id: int
    idea: str
    source_text: str
    domain: str
    semantic_paths: list[str]
    match_score: float
    temporal_score: float
    strength: float
    is_stale: bool
    debug: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrieveResult:
    """Return model for retrieve operations."""

    query: str
    temporal_relevance: str
    matches: list[RetrieveMatch]
