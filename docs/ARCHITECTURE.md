# Architecture

## Goal

`pg-researcher` is an evidence-first research system for Prince' Gutt. The architecture keeps acquisition, evidence, claims and editorial synthesis separate so that strategy can evolve without corrupting source truth.

## Logical pipeline

```text
Research Request
      |
      v
Question Planner
      |
      v
Source Registry -> Discovery / Collectors
                         |
                         v
                   Raw Evidence
                         |
                         v
                 Normalization Layer
                         |
                         v
                    Claim Ledger
                    /        \
                   v          v
             Conflict Check  Timeline/Catalog Index
                    \        /
                     v      v
                  Synthesis Engine
                         |
                         v
                 Research Report
                         |
                         v
               Editorial Opportunities
```

## Layers

### Source registry

Human-reviewed registry in `config/sources.yaml`. It stores source class, authority prior, identity status and supported research capabilities.

### Collectors

Collectors will be adapters, not business logic. A collector returns normalized capture metadata plus raw/structured evidence. It must not decide the strategic meaning of a source.

Planned adapters:

- generic web page;
- public social/profile page;
- DSP release/catalog page;
- press article;
- manually supplied/private authorized source;
- visual-asset manifest entry.

### Evidence store

Evidence is immutable in meaning. Corrections create a new record or supersession link rather than silently rewriting what was captured.

### Claim ledger

Claims are independent objects backed by evidence IDs. Multiple claims may share one evidence item; one claim may require several evidence items.

Important claim dimensions:

- subject;
- predicate;
- value;
- temporal scope;
- epistemic class;
- confidence;
- supporting and contradicting evidence;
- status (`open`, `supported`, `conflicted`, `retracted`).

### Synthesis

Synthesis consumes the claim ledger, never untracked raw browsing output. It produces strategic implications and labels them as interpretation/hypothesis instead of presenting them as sourced facts.

## Storage strategy

Phase 1 uses repository-native JSON/Markdown artifacts to keep research inspectable and diffable. A database/search index can be introduced only when volume justifies it; source truth remains exportable and versioned.

Proposed runtime paths:

```text
data/
├── evidence/
├── claims/
├── reports/
├── assets/
│   └── manifest.jsonl
└── indexes/
```

Generated data should not be mixed with hand-authored policy/configuration.

## Quality gates

A report is valid only when:

- all factual findings resolve to evidence IDs;
- evidence validates against schema;
- material conflicts are surfaced;
- unsupported inference is not labeled as fact;
- visual assets have provenance and usage basis;
- source URLs and capture timestamps are present;
- identity ambiguity is not silently resolved.

## Future execution layer

The first executable implementation should expose a CLI with deterministic commands such as:

```bash
pg-researcher sources list
pg-researcher evidence validate <path>
pg-researcher report validate <path>
pg-researcher research "question"
```

Network collectors, caching and rate-limit handling belong behind interfaces so tests can run without live network access.
