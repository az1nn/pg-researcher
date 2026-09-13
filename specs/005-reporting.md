# Spec 005 — Reporting

## Status

Implemented in this PR.

## Problem

The knowledge index now provides explicit claims, evidence deduplication, conflict preservation and deterministic projections. The project still needs a presentation layer that can create concise research briefs without turning strategy into fact or bypassing provenance.

## Decision

Reporting SHALL consume the knowledge index. Strategy SHALL be introduced through an explicit `ReportPlan` whose bridges point to existing claim IDs.

The renderer SHALL NOT invent implications or editorial opportunities.

## Functional requirements

### FR-001 Report plan contract

The project SHALL define a typed and JSON-Schema-backed report plan containing topic, selected finding claim IDs, strategic bridges and open questions.

### FR-002 Claim integrity

Report generation SHALL fail when the plan references an unknown or retracted claim.

### FR-003 Finding preservation

Generated findings SHALL preserve claim ID, epistemic class, confidence, lifecycle status, supporting evidence and contradicting evidence.

### FR-004 Conflict preservation

When selected claims participate in a knowledge-index conflict, the report SHALL surface that conflict and SHALL NOT choose a winner automatically.

### FR-005 Source ledger

Every evidence record used by the report SHALL appear in a source ledger with provenance and claim linkage. Missing referenced evidence SHALL fail report generation.

### FR-006 Strategic bridge

A strategic implication and editorial opportunity SHALL only appear when explicitly declared in a report-plan bridge anchored to one or more valid claims.

### FR-007 Prince' Gutt formats

Editorial opportunities SHALL use one of the approved proprietary formats:

- Prince no Beat;
- Do Arquivo;
- O Corre por Trás;
- Director's Note;
- Prince Responde.

### FR-008 Asset candidates

Evidence containing asset provenance SHALL be projected as asset candidates without changing its usage basis.

### FR-009 Deterministic rendering

The project SHALL support stable JSON and Markdown report output with separate sections for findings, conflicts, strategy, editorial opportunities, sources and open questions.

### FR-010 CLI

The executable SHALL support:

- report-plan validation;
- report build from knowledge + evidence + plan;
- research-report validation;
- Markdown rendering from a generated report.

## Non-goals

- LLM-authored implications inside the deterministic renderer;
- automatic editorial strategy;
- automatic conflict resolution;
- PDF/presentation generation;
- asset download or transformation;
- live metrics dashboards.

## Acceptance criteria

- unknown/retracted claim references fail closed;
- findings preserve epistemic metadata;
- source ledger resolves every used evidence ID;
- strategic bridges retain claim linkage;
- Markdown separates research from strategy visibly;
- report-plan and report schemas validate offline;
- wheel contains all reporting schemas;
- lint, tests and wheel build pass in CI.

## Next

Spec 006 will implement the asset manifest, authorized acquisition/derivatives and publication gates. Reporting will consume that richer asset layer without weakening provenance.
