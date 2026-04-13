import pytest

from semantic_heap.exceptions import InvalidTemporalExpressionError
from semantic_heap.temporal import parse_temporal_expression


def test_temporal_parser_accepts_expected_values():
    assert parse_temporal_expression("now").target_seconds == 0
    assert parse_temporal_expression("+6h").target_seconds > 0
    assert parse_temporal_expression("-2d").target_seconds < 0


def test_invalid_temporal_expression():
    with pytest.raises(InvalidTemporalExpressionError):
        parse_temporal_expression("next week")


def test_temporal_bias_changes_scores(memory):
    recent = memory.save("users", "David is going to dinner tonight")
    old = memory.save("users", "David was doing dinner planning yesterday")

    memory.storage.conn.execute(
        "UPDATE ideas SET created_at = ?, strength = ?, decay = ? WHERE id = ?",
        ("2025-01-01T00:00:00+00:00", 1.0, 0.0, old.idea_id),
    )
    memory.storage.conn.execute(
        "UPDATE ideas SET created_at = ?, strength = ?, decay = ? WHERE id = ?",
        ("2026-04-10T00:00:00+00:00", 1.0, 0.0, recent.idea_id),
    )
    memory.storage.commit()

    past_result = memory.retrieve("dinner", "-1y", limit=2)
    by_id = {m.idea_id: m for m in past_result.matches}
    assert by_id[old.idea_id].temporal_score > by_id[recent.idea_id].temporal_score
