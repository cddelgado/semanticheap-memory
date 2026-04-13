import pytest

from semantic_heap.exceptions import InvalidDomainError


def test_save_valid_domain(memory):
    result = memory.save("users", "David is going to dinner tonight")
    assert result.idea_id > 0
    assert result.normalized_idea == "David is going to dinner tonight"
    assert any(a.anchor_type == "subject" for a in result.anchors)
    assert any(a.anchor_type == "time" for a in result.anchors)
    assert result.semantic_paths[0].startswith("users.david")


def test_save_invalid_domain(memory):
    with pytest.raises(InvalidDomainError):
        memory.save("invalid", "Hello")
