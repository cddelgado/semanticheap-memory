# AGENTS.md

## Project

Semantic Heap Memory for LLM Apps

This repository builds a compact, local-first semantic memory engine for LLM applications.

The project is intended to be understandable, inspectable, testable, and useful in educational settings. The implementation should remain simple enough for students to study directly, while still being solid enough for developers and agent systems to build upon.

---

## Mission

Build a small semantic memory system with only two core conceptual operations:

* `save(domain, idea)`
* `retrieve(idea, temporal_relevance)`

The system stores normalized memory ideas, extracts lightweight semantic structure, retrieves semantically related ideas with temporal bias, and returns compact semantic maps rather than fully written answers.

The implementation should be suitable for:

* local Python use
* CLI use
* automated testing by systems such as OpenClaw
* later wrapping by an HTTP service, MCP server, or browser tool adapter

---

## Product Stance

This project is intentionally **not** trying to become a full agent framework, full ontology engine, or production-scale memory cloud.

It is a compact semantic memory substrate.

The system should feel:

* local-first
* lightweight
* explainable
* deterministic where practical
* human-shaped rather than archival

The system should preserve useful ideas, not every utterance.

---

## Core Rules

### 1. Keep the interface small

Do not expand the conceptual interface beyond the two main operations unless there is a strong implementation reason.

The public mental model must remain:

* save a normalized idea
* retrieve related ideas with temporal bias

### 2. Prefer clarity over cleverness

When choosing between:

* a more clever but opaque implementation
* a slightly simpler but explainable implementation

choose the explainable one.

This repository is meant to be read and improved by humans.

### 3. Keep storage terse

Do not store large narrative answers as memory.

Memory should remain compact. The engine stores normalized ideas, semantic anchors, generated paths, and lightweight links.

### 4. Let the LLM do language cleanup

Assume the calling LLM or application rewrites input into direct language before calling `save`.

The package may normalize whitespace and perform minimal cleanup, but it should not become a heavy rewriting engine.

### 5. Retrieval returns scaffolds, not essays

The engine returns semantic maps and matched ideas.
It does not generate full conversational responses.
That job belongs to the calling LLM.

### 6. Time is a bias, not a ledger

Implement time as a retrieval bias and decay mechanism.
Do not turn this into a forensic archival system.
Natural relevance loss is a feature.

### 7. SQLite is the default backend

The first-class implementation target is SQLite.
Do not replace it with a heavier database system unless explicitly instructed.

---

## Supported Domains

The system should support these top-level domains:

* `self`
* `users`
* `people`
* `home`
* `world`

Treat these as broad search anchors, not rigid ontology categories.

Validate domain values in the public API.

---

## Public API Expectations

The primary Python entry point should be a class similar to:

`SemanticHeapMemory`

Required methods:

* `save(domain: str, idea: str)`
* `retrieve(idea: str, temporal_relevance: str = "now", limit: int = 10)`

Recommended support methods:

* `close()` - close the database connection
* `vacuum()` - carry out standard database maintenance
* `decay()` - change (e.g. drop) priority of aging nodes
* `inspect_idea(idea_id)`
* `delete_idea(idea_id)` - remove saved ideas, intended for development primarily, no automatic pruning
* `rebuild_indexes()`

Keep return types structured and typed.
Prefer dataclasses unless a stronger dependency is necessary.

---

## Save Behavior

The `save` pathway should:

1. validate the domain
2. normalize trivial formatting
3. store the idea
4. extract lightweight semantic anchors
5. generate semantic paths in dot notation
6. create directed links where useful
7. assign initial strength and decay values
8. return structured metadata

Do not overbuild semantic parsing in v1.
It should be practical, inspectable, and testable.

---

## Retrieve Behavior

The `retrieve` pathway should:

1. parse the query into likely semantic anchors
2. interpret the temporal relevance expression
3. search using text and semantic signals
4. rank results using a simple explainable scoring model
5. reconstruct or return broad-to-specific semantic maps
6. return matched ideas plus scores and minimal debugging metadata

Results should be compact and machine-usable.

---

## Temporal Semantics

Support at least the following temporal relevance expressions:

* `now`
* positive offsets such as `+6h`, `+1d`, `+3w`, `+2m`, `+1y`
* negative offsets such as `-6h`, `-2d`, `-1w`, `-3m`, `-1y`

Interpretation:

* positive values bias toward future-relevant ideas
* negative values bias toward past-relevant ideas
* `now` biases toward currently active or recently relevant ideas

Do not require multiple explicit archival timestamps in v1.
A remembered timestamp plus strength/decay model is sufficient.

---

## Semantic Parsing Guidance

Use lightweight NLP.

The parser should attempt to identify:

* subject-like anchors
* verb/action-like anchors
* object-like anchors
* time expressions
* place expressions when obvious
* simple named entities when obvious
* negation when obvious

This parser does not need to be academically complete.
It needs to be useful and deterministic enough to test.

### Preferred implementation order

1. simple normalization and token heuristics
2. regex/rule-based time parsing
3. deterministic anchor extraction
4. optional spaCy integration only if isolated and optional

Do not make spaCy or a similarly heavy dependency mandatory unless explicitly necessary.

---

## Semantic Paths

Generating semantic maps in dot notation is a core requirement.

Examples of desired outputs:

* `users.david.plans.dinner.tonight`
* `users.david.preferences.spelling.no_callout`
* `world.work.platforms.microsoft365`

These paths should move from broad to specific.

Path generation should be heuristic but deterministic enough for unit tests.

---

## Ranking Guidance

Ranking should be understandable.

Prefer a simple weighted model using factors such as:

* text similarity
* semantic anchor overlap
* subject/object/verb overlap
* domain fit
* temporal fit
* current strength
* decay-adjusted relevance

Do not hide ranking behavior behind opaque logic unless there is a very strong reason.
Students and other developers should be able to understand why a result surfaced.

---

## Data Model Guidance

SQLite schema should remain easy to inspect.

Expected core tables:

* `ideas`
* `semantic_anchors`
* `semantic_paths`
* `links`
* FTS table for idea text

Keep schema names readable.
Keep columns typed and obvious.

Do not over-normalize prematurely.
The database should support inspection in a standard SQLite browser.

---

## Decay Guidance

Memory should naturally lose relevance over time.

In v1:

* reduce effective strength over time
* allow items to become stale
* do not hard-delete memories automatically
* still allow stale items to surface when strongly matched

This should simulate human relevance drift, not permanent archival retention.

---

## CLI Requirements

The repository should include a small CLI for local use and automation.

Suggested commands:

* `semantic-heap init --db path/to/db.sqlite`
* `semantic-heap save --domain users --idea "David is going to dinner tonight"`
* `semantic-heap retrieve --idea "dinner plans" --time now`
* `semantic-heap inspect --id 1`
* `semantic-heap decay`
* `semantic-heap vacuum`

CLI behavior should be:

* deterministic
* non-interactive by default
* automation-friendly

Add a `--json` mode if practical.

---

## Testing Requirements

Use `pytest`.

Tests must be deterministic and local.

At minimum, cover:

* valid and invalid saves
* retrieval quality for canonical examples
* temporal relevance behavior
* semantic path generation
* decay behavior
* CLI flows

Canonical examples should include at least:

* `David is going to dinner tonight`
* `David does not want spelling corrections called out`
* `Canvas is the LMS used by UWM`

Do not ship the project without a functioning test suite.

---

## OpenClaw Compatibility

This project should be easy for automation systems to drive.

That means:

* stable CLI exit codes
* no interactive prompts for normal operations
* clean command-line behavior
* ideally a machine-readable output mode
* test suite invocable from the command line

Design with automation in mind.

---

## Browser Integration Guidance

Do not tightly couple core logic to a browser UI.

The core package should be usable later from:

* a local HTTP wrapper
* a local MCP server
* a subprocess bridge
* a browser-based LLM tool that calls into Python indirectly

Keep boundaries clean so the core package remains reusable.

---

## Code Quality Standards

Use modern Python practices.

Required:

* Python 3.11+
* type hints throughout
* docstrings on public APIs
* isolated database layer
* no hidden global state
* clear exceptions for invalid input
* deterministic tests

Preferred:

* `ruff`
* `mypy` or type-clean code
* small focused modules

Avoid sprawling files when responsibilities can be separated cleanly.

---

## Project Structure Guidance

A suggested structure is:

```text
semantic_heap/
  __init__.py
  memory.py
  models.py
  storage.py
  parser.py
  ranking.py
  temporal.py
  paths.py
  cli.py
  exceptions.py
  utils.py
tests/
  test_save.py
  test_retrieve.py
  test_temporal.py
  test_paths.py
  test_decay.py
  test_cli.py
```

This may be adjusted, but keep responsibilities clearly separated.

---

## Documentation Expectations

The repository should include:

### README

Explain:

* what the project is
* what it is not
* install instructions
* Python examples
* CLI examples
* design philosophy

### Architecture notes

Explain:

* why there are only two conceptual operations
* how semantic anchors work
* how temporal bias works
* how path generation works
* why SQLite is used

### Contributing notes

Keep them small but clear.

---

## Constraints and Anti-Patterns

Avoid the following unless explicitly requested:

* embeddings in core v1
* external services as a requirement
* mandatory cloud infrastructure
* graph database migration in v1
* excessive abstraction layers
* opaque ranking logic
* overcomplicated ontologies
* turning the package into a full chat framework
* storing full conversational prose as memory records

Do not let the project lose its small, teachable shape.

---

## Implementation Style

When building features:

* start with the smallest complete implementation
* keep algorithms inspectable
* make defaults sensible
* preserve local-first behavior
* expose enough internals for teaching and debugging

When uncertain, ask:

1. does this make the memory system easier to understand?
2. does this make it easier to test?
3. does this preserve the two-operation mental model?
4. does this keep the project useful for students?

If the answer is no, reconsider the change.

---

## Final Instruction to the Agent

Build a serious, compact prototype.

Not a toy demo.
Not an overengineered platform.

The best implementation is the one that:

* works locally
* is easy to inspect
* is easy to test
* returns useful semantic maps
* stays true to the project’s human-shaped memory philosophy

Everything in this repository should serve that goal.
