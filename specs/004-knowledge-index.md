# Spec 004 — Knowledge Index

## Status

Implemented in this PR.

## Problem

Collectors produce auditable `Evidence`, but downstream synthesis still needs a deterministic way to represent claims, collapse duplicate evidence, surface contradictions and build catalog/timeline views.

## Decision

Claims are explicit artifacts. The system SHALL NOT extract or promote claims from evidence text implicitly in this phase.

## Functional requirements

### FR-001 Claim contract

The project SHALL define a typed and JSON-Schema-backed claim with epistemic class, confidence, evidence references, temporal scope and domain.

### FR-002 Referential integrity

Index generation SHALL fail when a claim references an unknown evidence ID.

### FR-003 Evidence deduplication

Exact normalized evidence content SHALL map to one canonical evidence record. Source authority SHALL decide the canonical record before capture time and evidence ID.

### FR-004 Independent corroboration

Duplicate/syndicated evidence SHALL collapse to the canonical evidence ID inside indexed claims so duplicates cannot inflate corroboration.

### FR-005 Conflict preservation

Claims sharing subject, predicate and temporal scope with different values SHALL be grouped as conflicts. No winner SHALL be silently selected.

### FR-006 Retractions

Retracted claims SHALL remain queryable but SHALL NOT participate in conflict, timeline or catalog projections.

### FR-007 Timeline

Claims with explicit `effective_at` SHALL produce chronologically sorted timeline entries. Capture timestamps SHALL NOT substitute event dates.

### FR-008 Catalog projection

Catalog/release/track/collaboration/production claims SHALL produce a deterministic catalog projection.

### FR-009 CLI

The executable SHALL support claim validation plus knowledge index build/inspect commands.

## Non-goals

- LLM claim extraction;
- semantic/fuzzy dedupe;
- automatic conflict resolution;
- graph database dependency;
- editorial synthesis;
- live metrics aggregation.

## Acceptance criteria

- duplicate evidence collapses deterministically;
- unknown evidence references fail closed;
- conflicting values are surfaced;
- retractions are excluded from active projections;
- timeline/catalog ordering is deterministic;
- generated index validates against its contract;
- tests and wheel-resource gates pass offline.

## Next

Spec 005 will render evidence-backed research briefs and source ledgers from the knowledge index, then map supported findings into Prince' Gutt editorial opportunities without blurring fact and strategy.
