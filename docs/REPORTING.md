# Reporting

## Purpose

Reporting is the deterministic presentation layer on top of the knowledge index. It converts selected claims into auditable research briefs without allowing narrative convenience to overwrite epistemic status, confidence, conflicts or provenance.

## Boundary

The reporting layer does not extract claims from prose and does not invent strategic implications.

The flow is:

```text
Evidence -> KnowledgeClaim -> KnowledgeIndex -> ReportPlan -> ResearchReport -> Markdown
```

The `ReportPlan` is the explicit bridge between research and strategy. A human or authorized agent chooses the claims to surface and, when strategy is desired, authors a bridge containing:

- supporting `claim_ids`;
- a strategic implication;
- one proprietary editorial format;
- one editorial lens;
- an editorial opportunity/concept;
- an optional objective.

This keeps `fact`, `inference`, `editorial_hypothesis` and strategy from collapsing into one generated paragraph.

## Findings

Findings are deterministic projections of selected claims. They retain:

- the source `claim_id`;
- epistemic class;
- confidence;
- lifecycle status;
- supporting evidence IDs;
- contradicting evidence IDs;
- editorial lenses attached by explicit report bridges.

A retracted claim cannot enter a report plan. Unknown claims fail closed.

## Conflict behavior

A conflicted claim remains conflicted in the report. The builder surfaces matching knowledge-index conflict groups and never selects a winner automatically.

## Source ledger

Every evidence ID used by included claims is resolved against the supplied evidence directory. Missing evidence fails report generation.

The ledger records:

- evidence ID;
- source class;
- URL/title/account;
- capture and publication timestamps;
- claims supported;
- claims contradicted.

This makes the rendered brief traceable back to acquisition artifacts.

## Strategic implications and editorial opportunities

These are copied from the `ReportPlan`; they are not inferred by the renderer.

Supported proprietary formats:

- `prince_no_beat`;
- `do_arquivo`;
- `o_corre_por_tras`;
- `directors_note`;
- `prince_responde`.

Supported strategic lenses:

- identity;
- catalog;
- territory;
- collaboration;
- production;
- fashion/visual;
- business/IP;
- community.

## Markdown renderer

The Markdown renderer produces stable sections:

1. Executive findings;
2. Conflicts, when present;
3. Strategic implications;
4. Editorial opportunities;
5. Asset candidates, when present;
6. Source ledger;
7. Open questions.

The footer explicitly states that strategy is plan-authored and not automatically inferred fact.

## CLI

```bash
pg-researcher report plan-validate examples/reporting/plan.json

pg-researcher report build \
  --knowledge data/index/knowledge.json \
  --evidence-dir data/evidence \
  --plan examples/reporting/plan.json \
  --output-json data/reports/identity.json \
  --output-markdown data/reports/identity.md

pg-researcher report validate data/reports/identity.json
pg-researcher report render data/reports/identity.json --output data/reports/identity.md
```

## Core invariant

A strategic recommendation is publishable only when its bridge points to existing, non-retracted claims. The report can format knowledge; it cannot manufacture evidentiary support.
