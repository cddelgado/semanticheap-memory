import pytest

from semantic_heap.exceptions import InvalidDomainError


def test_save_valid_domain(memory):
    result = memory.save("users", "David is going to dinner tonight")
    assert result.idea_id > 0
    assert result.normalized_idea == "David is going to dinner tonight"
    assert result.source_text == "David is going to dinner tonight"
    assert any(a.anchor_type == "subject" for a in result.anchors)
    assert any(a.anchor_type == "time" for a in result.anchors)
    assert result.semantic_paths[0].startswith("users.david")


def test_save_with_source_text(memory):
    result = memory.save("world", "Cancer survival improves in Europe", source_text="Cancer survival increases in Europe, but international differences remain wide.")
    assert result.normalized_idea == "Cancer survival improves in Europe"
    assert result.source_text == "Cancer survival increases in Europe, but international differences remain wide."


def test_save_invalid_domain(memory):
    with pytest.raises(InvalidDomainError):
        memory.save("invalid", "Hello")
