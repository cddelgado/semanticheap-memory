from datetime import UTC, datetime


def test_decay_reduces_strength_and_marks_stale(memory):
    saved = memory.save("users", "David is going to dinner tonight")
    memory.storage.conn.execute(
        "UPDATE ideas SET created_at = ?, strength = ?, decay = ? WHERE id = ?",
        ("2020-01-01T00:00:00+00:00", 0.5, 0.05, saved.idea_id),
    )
    memory.storage.commit()

    changed = memory.decay(now=datetime(2026, 4, 13, tzinfo=UTC))
    assert changed >= 1

    inspected = memory.inspect_idea(saved.idea_id)
    assert inspected is not None
    assert inspected["idea"]["is_stale"] == 1
    assert inspected["idea"]["strength"] <= 0.5
