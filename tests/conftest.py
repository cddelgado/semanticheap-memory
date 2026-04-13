from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from semantic_heap import SemanticHeapMemory


@pytest.fixture()
def memory(tmp_path: Path) -> SemanticHeapMemory:
    mem = SemanticHeapMemory(str(tmp_path / "test.db"))
    yield mem
    mem.close()
