# Semantic Heap Memory

Semantic Heap Memory is a compact, local-first semantic memory engine for LLM applications.

It focuses on two conceptual operations:

- `save(domain, idea)`
- `retrieve(idea, temporal_relevance)`

## What this is

- A SQLite-backed memory substrate for normalized ideas
- Lightweight semantic anchors and dot-path maps
- Explainable ranking with temporal bias
- Deterministic local CLI + pytest suite

## What this is not

- A full agent framework
- A vector/embedding database
- A cloud memory service
- A permanent archival ledger

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quickstart (Python)

```python
from semantic_heap import SemanticHeapMemory

memory = SemanticHeapMemory("memory.db")
memory.save("users", "David is going to dinner tonight")
result = memory.retrieve("dinner plans", temporal_relevance="now")
for match in result.matches:
    print(match.idea, match.semantic_paths)
memory.close()
```

## CLI usage

```bash
semantic-heap --db memory.db init
semantic-heap --db memory.db save --domain users --idea "David is going to dinner tonight"
semantic-heap --db memory.db retrieve --idea "dinner plans" --time now --json
semantic-heap --db memory.db inspect --id 1 --json
semantic-heap --db memory.db decay
semantic-heap --db memory.db vacuum
```

## Design philosophy

- Keep the interface small and teachable
- Keep storage terse and inspectable
- Return semantic scaffolds, not prose answers
- Model time as retrieval bias + relevance decay

## Development

```bash
pytest
```
