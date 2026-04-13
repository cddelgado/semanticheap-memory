"""Public memory API for Semantic Heap Memory."""

from __future__ import annotations

from datetime import UTC, datetime

from .exceptions import InvalidDomainError
from .models import Anchor, RetrieveMatch, RetrieveResult, SaveResult
from .parser import extract_anchors
from .paths import generate_paths
from .ranking import anchor_overlap, text_similarity, weighted_score
from .storage import SQLiteStorage
from .temporal import decay_strength, now_iso, parse_datetime, parse_temporal_expression, temporal_fit_score
from .utils import normalize_idea_text

SUPPORTED_DOMAINS = {"self", "users", "people", "home", "world"}


class SemanticHeapMemory:
    """Compact semantic memory engine with SQLite persistence."""

    def __init__(self, db_path: str = "semantic_heap.db") -> None:
        self.storage = SQLiteStorage(db_path)
        self.storage.init_schema()

    def save(self, domain: str, idea: str) -> SaveResult:
        """Save a normalized idea into semantic memory."""
        if domain not in SUPPORTED_DOMAINS:
            raise InvalidDomainError(f"Unsupported domain '{domain}'. Allowed: {sorted(SUPPORTED_DOMAINS)}")

        normalized = normalize_idea_text(idea)
        anchors = extract_anchors(normalized)
        paths = generate_paths(domain, normalized, anchors)

        idea_id = self.storage.insert_idea(
            domain=domain,
            idea=idea,
            normalized_idea=normalized.lower(),
            created_at=now_iso(),
            strength=1.0,
            decay=0.02,
        )

        for anchor in anchors:
            self.storage.insert_anchor(idea_id, anchor.anchor_type, anchor.anchor_value, anchor.anchor_norm, anchor.position)
        for path in paths:
            self.storage.insert_path(idea_id, path)

        linked_ids = self.storage.find_related_ids_by_anchor_norms([a.anchor_norm for a in anchors], exclude_idea_id=idea_id)
        for linked_id in linked_ids:
            self.storage.insert_link(idea_id, linked_id, relation="semantic_related", weight=1.0)

        self.storage.commit()

        return SaveResult(
            idea_id=idea_id,
            normalized_idea=normalized,
            anchors=anchors,
            semantic_paths=paths,
            linked_idea_ids=linked_ids,
        )

    def retrieve(self, idea: str, temporal_relevance: str = "now", limit: int = 10) -> RetrieveResult:
        """Retrieve semantically related ideas with temporal bias."""
        query = normalize_idea_text(idea)
        temporal_bias = parse_temporal_expression(temporal_relevance)
        query_anchors = extract_anchors(query)

        tokens = [t.anchor_norm for t in query_anchors if t.anchor_norm]
        fts_query = " OR ".join(tokens) if tokens else query
        candidates = self.storage.candidate_ideas(fts_query, limit=max(50, limit * 5))

        now = datetime.now(UTC)
        ranked: list[RetrieveMatch] = []
        for row in candidates:
            created_at = parse_datetime(row["created_at"])
            effective_strength = decay_strength(row["strength"], row["decay"], created_at, now=now)
            candidate_anchors = [
                Anchor(
                    anchor_type=a["anchor_type"],
                    anchor_value=a["anchor_value"],
                    anchor_norm=a["anchor_norm"],
                    position=a["position"],
                )
                for a in self.storage.fetch_anchors(row["id"])
            ]
            anchor_score, overlap_debug = anchor_overlap(query_anchors, candidate_anchors)
            t_score = temporal_fit_score(temporal_bias, created_at, now=now)
            txt_score = text_similarity(query, row["normalized_idea"])
            stale_penalty = 0.05 if row["is_stale"] else 0.0
            score = weighted_score(
                text_score=txt_score,
                anchor_score=anchor_score,
                temporal_score=t_score,
                strength_score=effective_strength,
                stale_penalty=stale_penalty,
            )
            ranked.append(
                RetrieveMatch(
                    idea_id=row["id"],
                    idea=row["idea"],
                    domain=row["domain"],
                    semantic_paths=self.storage.fetch_paths(row["id"]),
                    match_score=round(score, 6),
                    temporal_score=round(t_score, 6),
                    strength=round(effective_strength, 6),
                    is_stale=bool(row["is_stale"]),
                    debug={"text_score": round(txt_score, 6), "anchor_overlap": overlap_debug},
                )
            )

        ranked.sort(key=lambda x: x.match_score, reverse=True)
        return RetrieveResult(query=query, temporal_relevance=temporal_relevance, matches=ranked[:limit])

    def decay(self, now: datetime | None = None) -> int:
        """Apply decay updates to all ideas and mark stale ones."""
        current = now or datetime.now(UTC)
        changed = 0
        for row in self.storage.all_ideas():
            created_at = parse_datetime(row["created_at"])
            new_strength = decay_strength(row["strength"], row["decay"], created_at, now=current)
            stale = new_strength < 0.20
            if abs(new_strength - row["strength"]) > 1e-9 or stale != bool(row["is_stale"]):
                self.storage.update_strength_and_stale(row["id"], new_strength, stale, current.replace(microsecond=0).isoformat())
                changed += 1
        self.storage.commit()
        return changed

    def inspect_idea(self, idea_id: int) -> dict | None:
        """Inspect a stored idea and its semantic structures."""
        return self.storage.inspect_idea(idea_id)

    def delete_idea(self, idea_id: int) -> bool:
        """Delete a stored idea by id."""
        return self.storage.delete_idea(idea_id)

    def rebuild_indexes(self) -> None:
        """Rebuild FTS indexes."""
        self.storage.rebuild_indexes()

    def vacuum(self) -> None:
        """Run SQLite VACUUM."""
        self.storage.vacuum()

    def close(self) -> None:
        """Close database connection."""
        self.storage.close()
