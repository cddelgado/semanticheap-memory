"""SQLite storage layer for Semantic Heap Memory."""

from __future__ import annotations

import sqlite3
from typing import Any


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY,
    domain TEXT NOT NULL,
    idea TEXT NOT NULL,
    source_text TEXT NOT NULL,
    normalized_idea TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    strength REAL NOT NULL,
    decay REAL NOT NULL,
    is_stale INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS semantic_anchors (
    id INTEGER PRIMARY KEY,
    idea_id INTEGER NOT NULL,
    anchor_type TEXT NOT NULL,
    anchor_value TEXT NOT NULL,
    anchor_norm TEXT NOT NULL,
    position INTEGER,
    FOREIGN KEY(idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS semantic_paths (
    id INTEGER PRIMARY KEY,
    idea_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    depth INTEGER NOT NULL,
    FOREIGN KEY(idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    source_idea_id INTEGER NOT NULL,
    target_idea_id INTEGER NOT NULL,
    relation TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY(source_idea_id) REFERENCES ideas(id) ON DELETE CASCADE,
    FOREIGN KEY(target_idea_id) REFERENCES ideas(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS fts_ideas USING fts5(
    idea,
    normalized_idea,
    content='ideas',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS ideas_ai AFTER INSERT ON ideas BEGIN
  INSERT INTO fts_ideas(rowid, idea, normalized_idea)
  VALUES (new.id, new.idea, new.normalized_idea);
END;

CREATE TRIGGER IF NOT EXISTS ideas_ad AFTER DELETE ON ideas BEGIN
  INSERT INTO fts_ideas(fts_ideas, rowid, idea, normalized_idea)
  VALUES('delete', old.id, old.idea, old.normalized_idea);
END;

CREATE TRIGGER IF NOT EXISTS ideas_au AFTER UPDATE ON ideas BEGIN
  INSERT INTO fts_ideas(fts_ideas, rowid, idea, normalized_idea)
  VALUES('delete', old.id, old.idea, old.normalized_idea);
  INSERT INTO fts_ideas(rowid, idea, normalized_idea)
  VALUES (new.id, new.idea, new.normalized_idea);
END;
"""


class SQLiteStorage:
    """Thin SQLite storage helper with explicit queries."""

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def insert_idea(
        self,
        *,
        domain: str,
        idea: str,
        source_text: str,
        normalized_idea: str,
        created_at: str,
        strength: float,
        decay: float,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO ideas (domain, idea, source_text, normalized_idea, created_at, updated_at, strength, decay, is_stale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (domain, idea, source_text, normalized_idea, created_at, created_at, strength, decay),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def insert_anchor(self, idea_id: int, anchor_type: str, anchor_value: str, anchor_norm: str, position: int | None) -> None:
        self.conn.execute(
            """
            INSERT INTO semantic_anchors (idea_id, anchor_type, anchor_value, anchor_norm, position)
            VALUES (?, ?, ?, ?, ?)
            """,
            (idea_id, anchor_type, anchor_value, anchor_norm, position),
        )

    def insert_path(self, idea_id: int, path: str) -> None:
        self.conn.execute(
            "INSERT INTO semantic_paths (idea_id, path, depth) VALUES (?, ?, ?)",
            (idea_id, path, len(path.split("."))),
        )

    def insert_link(self, source_idea_id: int, target_idea_id: int, relation: str, weight: float = 1.0) -> None:
        self.conn.execute(
            "INSERT INTO links (source_idea_id, target_idea_id, relation, weight) VALUES (?, ?, ?, ?)",
            (source_idea_id, target_idea_id, relation, weight),
        )

    def commit(self) -> None:
        self.conn.commit()

    def candidate_ideas(self, query: str, limit: int = 50) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            """
            SELECT i.*
            FROM fts_ideas f
            JOIN ideas i ON i.id = f.rowid
            WHERE fts_ideas MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        if rows:
            return rows
        return self.conn.execute(
            "SELECT * FROM ideas ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def fetch_anchors(self, idea_id: int) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM semantic_anchors WHERE idea_id = ?", (idea_id,)).fetchall()

    def fetch_paths(self, idea_id: int) -> list[str]:
        rows = self.conn.execute("SELECT path FROM semantic_paths WHERE idea_id = ? ORDER BY depth", (idea_id,)).fetchall()
        return [row[0] for row in rows]

    def find_related_ids_by_anchor_norms(self, anchor_norms: list[str], exclude_idea_id: int, limit: int = 5) -> list[int]:
        if not anchor_norms:
            return []
        placeholders = ",".join("?" for _ in anchor_norms)
        rows = self.conn.execute(
            f"""
            SELECT idea_id, COUNT(*) AS c
            FROM semantic_anchors
            WHERE anchor_norm IN ({placeholders}) AND idea_id != ?
            GROUP BY idea_id
            ORDER BY c DESC, idea_id DESC
            LIMIT ?
            """,
            (*anchor_norms, exclude_idea_id, limit),
        ).fetchall()
        return [int(r[0]) for r in rows]

    def update_strength_and_stale(self, idea_id: int, strength: float, is_stale: bool, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE ideas SET strength = ?, is_stale = ?, updated_at = ? WHERE id = ?",
            (strength, 1 if is_stale else 0, updated_at, idea_id),
        )

    def all_ideas(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM ideas ORDER BY id").fetchall()

    def inspect_idea(self, idea_id: int) -> dict[str, Any] | None:
        idea_row = self.conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
        if idea_row is None:
            return None
        anchors = [dict(r) for r in self.fetch_anchors(idea_id)]
        paths = self.fetch_paths(idea_id)
        links = [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM links WHERE source_idea_id = ? OR target_idea_id = ?",
                (idea_id, idea_id),
            ).fetchall()
        ]
        return {"idea": dict(idea_row), "anchors": anchors, "paths": paths, "links": links}

    def delete_idea(self, idea_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def rebuild_indexes(self) -> None:
        self.conn.execute("INSERT INTO fts_ideas(fts_ideas) VALUES('rebuild')")
        self.conn.commit()

    def vacuum(self) -> None:
        self.conn.execute("VACUUM")

    def close(self) -> None:
        self.conn.close()
