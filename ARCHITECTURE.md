# Architecture

## Overview

Semantic Heap Memory is a compact, local-first memory engine for LLM applications.

It is designed around a very small public mental model:

* save a normalized idea
* retrieve related ideas with temporal bias

Everything else in the system exists to support those two operations.

This project is intentionally small. It is not a full agent framework, not a vector database, not an ontology platform, and not a permanent archival system. It is a semantic memory substrate that stores useful ideas, lets them lose relevance over time, and returns compact semantic scaffolds that a language model can interpret.

---

## Design Goals

The architecture is shaped by a few deliberate choices.

### 1. Local-first and inspectable

The system should run locally, store its data in SQLite, and remain easy to inspect with ordinary tools.

### 2. Small interface

The conceptual interface is intentionally tiny:

* `save(domain, idea)`
* `retrieve(idea, temporal_relevance)`

This keeps the memory model understandable for students and easy to wrap for automation.

### 3. Human-shaped memory

The system is designed to behave more like relevance-based memory than archival storage.

That means:

* memory is selective
* memory is terse
* memory loses relevance naturally
* retrieval is shaped by present need
* stale items may still be found when strongly relevant

### 4. Explainable internals

The ranking and parsing logic should be understandable. The system should not depend on hidden black-box behavior for its core operations.

### 5. Retrieval returns scaffolds, not prose

The memory engine returns semantic maps and matched ideas. The calling language model interprets those results into user-facing language.

---

## High-Level Mental Model

The system stores **normalized ideas** rather than raw utterances.

A normalized idea is a short, direct statement worth remembering.

Examples:

* `David is going to dinner tonight`
* `Canvas is the LMS used by UWM`
* `David does not want spelling corrections called out`

These are memory traces, not transcripts.

Each saved idea is assigned to a broad top-level domain:

* `self`
* `users`
* `people`
* `home`
* `world`

These domains are not a full ontology. They are broad search anchors that help narrow retrieval.

The engine extracts lightweight semantic structure from each idea and stores:

* the idea itself
* semantic anchors
* one or more semantic paths in dot notation
* directed links where useful
* relevance metadata such as strength and decay

When retrieval is requested, the engine finds semantically related candidates, applies temporal bias, ranks the results, and returns semantic maps plus matched ideas.

---

## System Boundaries

The architecture deliberately separates responsibilities.

### The calling LLM or app is responsible for:

* deciding whether something is worth remembering
* rewriting memory into direct language
* reducing pronouns and indirectness when possible
* interpreting retrieval results into human-facing answers

### The memory engine is responsible for:

* storing normalized ideas
* extracting lightweight semantic anchors
* indexing ideas and anchors
* applying temporal bias and decay
* returning compact semantic maps and matched ideas

This boundary is important.

The memory engine should not become a full rewriting engine or a full conversational response engine.

---

## Why SQLite

SQLite is the primary backend because it fits the goals of the project.

It provides:

* local storage with no server requirement
* portability
* inspectability
* transactional safety
* indexing
* full-text search support
* low operational overhead

The first version of this project does not need a graph database or a distributed search system. SQLite is sufficient for a serious prototype and keeps the project approachable.

---

## Core Components

The architecture can be thought of as six layers.

### 1. Public API layer

This is the Python-facing interface.

Primary entry point:

* `SemanticHeapMemory`

Core methods:

* `save(domain, idea)`
* `retrieve(idea, temporal_relevance="now", limit=10)`

Support methods may include:

* `close()`
* `decay()`
* `inspect_idea()`
* `delete_idea()`
* `vacuum()`
* `rebuild_indexes()`

### 2. Storage layer

This layer manages SQLite connections, schema creation, inserts, updates, deletes, and query execution.

This layer should remain isolated from parsing and ranking logic.

### 3. Parsing layer

This layer performs lightweight NLP and heuristic extraction.

Its role is to identify likely semantic anchors such as:

* subject-like components
* verbs/actions
* object-like components
* time expressions
* place expressions when obvious
* named entities when obvious
* negation when obvious

This parser should be practical and inspectable, not academically maximal.

### 4. Path generation layer

This layer turns ideas and anchors into broad-to-specific semantic paths in dot notation.

Examples:

* `users.david.plans.dinner.tonight`
* `users.david.preferences.spelling.no_callout`
* `world.uwm.platforms.canvas`

These paths are semantic scaffolds for retrieval and interpretation.

### 5. Ranking layer

This layer scores and orders retrieval candidates.

It should combine simple, explainable signals such as:

* text similarity
* semantic anchor overlap
* subject/object/verb overlap
* domain fit
* temporal relevance fit
* current strength
* decay-adjusted relevance

### 6. CLI layer

This layer exposes the memory engine for local use, testing, and automation.

It should remain thin and call into the public API rather than reimplementing memory logic.

---

## Data Flow

### Save flow

1. The calling LLM or application decides a statement is worth remembering.
2. The calling side rewrites it into direct language.
3. `save(domain, idea)` is called.
4. The engine validates the domain.
5. The idea is minimally normalized.
6. The parser extracts semantic anchors.
7. The path generator produces one or more dot-notation semantic maps.
8. The storage layer writes the idea and derived structures into SQLite.
9. Initial strength and decay values are assigned.
10. A structured result is returned.

### Retrieve flow

1. The caller provides an idea and a temporal relevance expression.
2. The parser decomposes the query into likely anchors.
3. The temporal parser interprets the time bias.
4. The storage layer finds candidate ideas using text search and semantic matches.
5. The ranking layer scores those candidates.
6. The engine returns ranked matched ideas and semantic maps.
7. The calling LLM interprets the result into user-facing language if needed.

---

## Database Schema

The system stores structured memory data in SQLite.

### `ideas`

Stores primary memory ideas.

Suggested columns:

* `id`
* `domain`
* `idea`
* `normalized_idea`
* `created_at`
* `updated_at`
* `strength`
* `decay`
* `is_stale`

Purpose:

* holds the canonical memory idea text
* tracks current memory relevance state

### `semantic_anchors`

Stores extracted semantic units associated with an idea.

Suggested columns:

* `id`
* `idea_id`
* `anchor_type`
* `anchor_value`
* `anchor_norm`
* `position`

Possible anchor types:

* `subject`
* `verb`
* `object`
* `time`
* `place`
* `entity`
* `negation`

Purpose:

* supports semantic retrieval beyond raw text search
* provides inspectable intermediate structure

### `semantic_paths`

Stores generated broad-to-specific semantic paths.

Suggested columns:

* `id`
* `idea_id`
* `path`
* `depth`

Purpose:

* provides compact semantic maps
* supports path-based inspection and retrieval

### `links`

Stores directed relationships between ideas.

Suggested columns:

* `id`
* `source_idea_id`
* `target_idea_id`
* `relation`
* `weight`

Purpose:

* supports traversal and semantic association
* allows broader-to-specific or related-idea exploration

### `fts_ideas`

SQLite FTS5 table for text search.

Indexed content should include at least:

* `idea`
* `normalized_idea`

Purpose:

* supports lexical retrieval
* forms one input to the ranking model

---

## Semantic Anchors

Semantic anchors are the bridge between raw text and structured retrieval.

They should be lightweight and heuristic.

The goal is not perfect parsing. The goal is to create enough structure that semantically related ideas can be grouped, scored, and inspected.

For example:

Input:
`David is going to dinner tonight`

Possible anchors:

* subject: `David`
* verb: `going`
* object: `dinner`
* time: `tonight`
* entity: `David`

These anchors can then support retrieval by related phrases such as:

* `dinner plans`
* `what David is doing`
* `tonight`

---

## Semantic Paths

Semantic paths are compact broad-to-specific maps that summarize the meaning of an idea.

They are generated heuristically from the domain and extracted anchors.

Examples:

* `users.david.plans.dinner.tonight`
* `world.uwm.platforms.canvas`
* `users.david.preferences.spelling.no_callout`

These paths are important because they let retrieval return a compact semantic scaffold instead of a full narrative answer.

The path generator should be deterministic enough that canonical examples can be unit tested.

---

## Temporal Model

Time in this architecture is not treated as a large tree or archival ledger.

Instead, time is handled through:

* a remembered timestamp on each idea
* a temporal relevance expression at retrieval time
* strength and decay over time

Supported temporal relevance expressions should include:

* `now`
* positive offsets such as `+1d`, `+3w`, `+2m`
* negative offsets such as `-2d`, `-1w`, `-3m`

Meaning:

* positive values bias toward future-relevant material
* negative values bias toward past-relevant material
* `now` biases toward currently active or recently relevant material

This model is intentionally human-shaped.
It is meant to approximate salience and drift, not preserve a perfect history.

---

## Strength, Decay, and Staleness

Each memory idea should have a current strength and a decay profile.

### Strength

Represents how much the idea currently presses on retrieval.

### Decay

Represents how quickly that relevance fades over time.

### Staleness

Marks ideas that have lost enough relevance that they should be deprioritized under ordinary retrieval.

Important:

* stale does not mean deleted
* stale ideas may still surface when the semantic match is strong
* this system models fading, not immediate forgetting

This design supports a memory style closer to human relevance than to archival retention.

---

## Ranking

Retrieval ranking should be understandable.

Candidate results may be scored using a weighted combination of:

* text similarity between query and stored idea
* overlap in semantic anchors
* subject/object/verb alignment
* domain agreement
* temporal relevance alignment
* current strength
* decay-adjusted freshness

The ranking system should remain explainable enough that students and developers can understand why a result surfaced.

Opaque or excessively clever ranking logic should be avoided unless there is a very strong reason.

---

## Links and Traversal

Links between ideas should remain lightweight and directed.

The architecture does not require a fully symmetric or exhaustive graph in v1.
The purpose of links is to support:

* related idea expansion
* narrow semantic traversal
* broad-to-specific pathing when useful

Traversal is especially useful once a small set of strong candidates has already been found. This allows the engine to search closest-out rather than trying to exhaustively walk the entire memory space.

---

## Administrative and Maintenance Operations

These operations exist to support practical use, testing, and maintenance.
They are not part of the core conceptual memory interface.

### `close()`

Closes the SQLite connection cleanly and flushes pending work.

This is purely resource cleanup.

### `decay()`

Recomputes effective relevance over time.

Expected behavior:

* reduce effective strength using elapsed time and decay profile
* mark low-relevance items as stale
* do not automatically delete ideas

This is a cognitive maintenance step, not a pruning step.

### `delete_idea()`

Explicitly removes an idea and associated records.

Expected behavior:

* delete the idea by ID
* delete related anchors
* delete related semantic paths
* delete links to and from it
* update FTS state

This is an administrative/debugging operation, not normal forgetting.

### `vacuum()`

Runs SQLite maintenance.

Expected behavior:

* compact the database file
* reclaim storage after deletes or churn
* optionally refresh planner statistics

This is physical storage maintenance, not semantic maintenance.

---

## CLI Architecture

The CLI should remain thin.

Its job is to expose core engine behavior for:

* local experimentation
* demos
* tests
* automation

Suggested commands:

* `semantic-heap init`
* `semantic-heap save`
* `semantic-heap retrieve`
* `semantic-heap inspect`
* `semantic-heap decay`
* `semantic-heap vacuum`

The CLI should be:

* deterministic
* non-interactive by default
* automation-friendly
* optionally machine-readable with a `--json` mode

---

## Testing Strategy

The architecture is designed to be testable.

Important test areas include:

* save behavior
* invalid domain handling
* semantic anchor extraction
* path generation
* temporal relevance behavior
* ranking behavior on canonical examples
* decay behavior
* CLI behavior

Canonical examples should be built into tests because they anchor the semantic behavior of the system.

Examples:

* `David is going to dinner tonight`
* `David does not want spelling corrections called out`
* `Canvas is the LMS used by UWM`

---

## Automation and OpenClaw

This architecture should be easy for automated systems to drive.

That means:

* no interactive dependency for normal operations
* stable command behavior
* clear exit codes
* deterministic local tests
* ideally machine-readable output when requested

The architecture should support OpenClaw-style automation without requiring OpenClaw-specific logic in the core engine.

---

## Browser Tool Integration

The core engine should remain separate from any browser or UI code.

This makes it easier to wrap later with:

* a local HTTP service
* an MCP server
* a subprocess bridge
* a browser-based LLM tool adapter

The architectural rule is simple:

core memory logic first,
wrappers later.

---

## What This Architecture Avoids

This project deliberately avoids several common patterns in order to remain small and teachable.

It avoids:

* mandatory embeddings in v1
* opaque cloud memory services
* graph databases as a first dependency
* overcomplicated ontologies
* fully archival memory semantics
* storing final prose answers as memory items
* turning the package into a general chat framework

These are not necessarily bad ideas. They are simply outside the scope of this architecture.

---

## Summary

Semantic Heap Memory is a compact semantic memory engine for LLM applications.

Its architecture is built around a tiny public interface, a local SQLite backend, lightweight semantic parsing, heuristic path generation, explainable ranking, and human-shaped relevance decay.

The system stores normalized ideas, not raw transcripts.
It returns semantic scaffolds, not polished prose.
It favors inspectability and extensibility over abstraction.

That is the point of the architecture: small enough to build, real enough to matter, and clear enough that others can improve it.
