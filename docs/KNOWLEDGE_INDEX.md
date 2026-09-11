# Knowledge Index

## Purpose

The knowledge index is the deterministic layer between captured evidence and narrative/report synthesis.

It does **not** infer claims from prose. A claim must be authored explicitly and point to evidence IDs. This keeps heuristics, strategy and factual research from collapsing into one opaque step.

## Claim contract

A claim records:

- `claim_id`;
- subject + predicate + JSON value;
- epistemic class and confidence;
- supporting and contradicting evidence IDs;
- optional temporal scope;
- knowledge domain and optional entity ID;
- lifecycle status.

`fact`, `inference` and `editorial_hypothesis` remain distinct classes.

## Evidence deduplication

Evidence is fingerprinted from normalized subject, observation and excerpt. Exact-content duplicates are grouped even when their URLs differ.

The canonical record is chosen deterministically by source authority:

1. official;
2. platform/partner;
3. reputable press;
4. secondary catalog;
5. community.

Ties use capture time and then evidence ID. Claims are rewritten in the generated index to canonical evidence IDs, so syndicated copies do not inflate corroboration.

## Conflict detection

Active claims conflict when they share the same normalized subject, predicate and temporal scope but have different normalized values.

The index never silently picks a winner. Every conflicting claim remains present and receives `status: conflicted`. Retracted claims are excluded from conflict calculation.

## Timeline

Claims with `effective_at` are projected into a chronological timeline. `effective_until` is retained when known. Capture time is not substituted for event time.

## Catalog index

Claims in `catalog`, `release`, `track`, `collaboration` or `production` domains are projected into a dedicated catalog view. This is an index, not a separate source of truth.

## CLI

```bash
pg-researcher claim validate examples/claims/minimal.json
pg-researcher knowledge build \
  --evidence-dir examples/evidence \
  --claims-dir examples/claims \
  --output data/index/knowledge.json
pg-researcher knowledge inspect data/index/knowledge.json
```

## Invariant

The minimum trustworthy path remains:

```text
claim -> canonical evidence -> confidence -> implication
```

Spec 005 reporting will consume this index; it must not bypass it for material factual statements.
