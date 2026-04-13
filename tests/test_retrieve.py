
def test_retrieve_canonical_examples(memory):
    memory.save("users", "David is going to dinner tonight")
    memory.save("users", "David does not want spelling corrections called out")
    memory.save("world", "Canvas is the LMS used by UWM")

    dinner = memory.retrieve("dinner plans", "now", limit=3)
    assert dinner.matches
    assert "dinner" in dinner.matches[0].idea.lower()

    spelling = memory.retrieve("spelling correction preference", "now", limit=3)
    assert spelling.matches
    assert "spelling" in spelling.matches[0].idea.lower()

    canvas = memory.retrieve("Canvas at UWM", "now", limit=3)
    assert canvas.matches
    assert "canvas" in canvas.matches[0].idea.lower()


def test_stale_item_can_surface(memory):
    save = memory.save("world", "Canvas is the LMS used by UWM")
    memory.storage.update_strength_and_stale(save.idea_id, 0.05, True, "2026-01-01T00:00:00+00:00")
    memory.storage.commit()
    result = memory.retrieve("Canvas UWM", "now", limit=5)
    assert any(match.idea_id == save.idea_id for match in result.matches)
