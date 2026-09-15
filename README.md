# pg-researcher

Research skill and evidence pipeline for **Prince' Gutt**.

The repository turns public, authorized and verifiable information about Prince' Gutt into reusable research artifacts for **PG Influencer RESEARCH**. It is not a generic social-media scraper: every output must preserve provenance, distinguish fact from interpretation, and serve the artist's actual editorial universe.

## Core doctrine

Prince' Gutt is treated as an artist-platform: music, production, image, territory, fashion, community and future IP. Research should strengthen recognizability and repertoire rather than fill a calendar.

Primary editorial formats:

- **Prince no Beat** — production as spectacle.
- **Do Arquivo** — catalog, history and memory as living inventory.
- **O Corre por Trás** — process, discipline and backstage.
- **Director's Note** — aesthetic decisions with authorship and authority.
- **Prince Responde** — community and live feedback loops.

## Research contract

Every material claim should carry:

1. source URL;
2. source class;
3. capture timestamp;
4. evidence excerpt or structured fact;
5. confidence;
6. explicit separation between `fact`, `inference` and `editorial_hypothesis`.

Official/first-party sources outrank aggregators. Conflicting claims are preserved and flagged instead of silently resolved.

## Install for development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Requires Python 3.12+.

## CLI

```bash
pg-researcher version
pg-researcher sources validate
pg-researcher sources list
pg-researcher evidence validate examples/evidence/minimal.json
pg-researcher claim validate examples/claims/minimal.json

# Controlled public-source capture
pg-researcher collect source x_princeguttreal --output data/evidence/x-profile.json

# Deterministic knowledge index
pg-researcher knowledge build \
  --evidence-dir examples/evidence \
  --claims-dir examples/claims \
  --output data/index/knowledge.json
pg-researcher knowledge inspect data/index/knowledge.json

# Evidence-backed reporting
pg-researcher report plan-validate examples/reporting/plan.json
pg-researcher report build \
  --knowledge data/index/knowledge.json \
  --evidence-dir examples/evidence \
  --plan examples/reporting/plan.json \
  --output-json data/reports/identity.json \
  --output-markdown data/reports/identity.md
pg-researcher report validate data/reports/identity.json

# Rights-aware asset inventory
pg-researcher asset record-validate examples/assets/record.json
pg-researcher asset manifest-build \
  --records-dir data/assets/records \
  --output data/assets/manifest.json
pg-researcher asset verify data/assets/manifest.json --root .
pg-researcher asset gate data/assets/manifest.json --root . --require-approved
```

Collectors normalize provenance into typed evidence; they do not synthesize claims. Claims are explicit artifacts. The knowledge index canonicalizes duplicate evidence, preserves conflicts and projects timeline/catalog views without silently deciding which conflicting value is true.

Reporting consumes that knowledge layer. Findings are projected from claims; strategic implications and editorial opportunities only enter through an explicit `ReportPlan` anchored to claim IDs.

Assets preserve a separate publication boundary: public discovery is not reuse clearance. Local files are content-addressed, derivatives remain traceable to a parent and the publication gate distinguishes `approved`, `research_only` and `blocked`.

## Repository map

```text
.
├── .github/workflows/ci.yml
├── SKILL.md
├── config/
│   ├── asset-policy.yaml
│   ├── fetch-policy.yaml
│   └── sources.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ASSETS.md
│   ├── COLLECTORS.md
│   ├── KNOWLEDGE_INDEX.md
│   ├── REPORTING.md
│   ├── RESEARCH_POLICY.md
│   └── RIGHTS_AND_ASSETS.md
├── examples/
│   ├── assets/record.json
│   ├── claims/minimal.json
│   ├── evidence/minimal.json
│   ├── reporting/plan.json
│   └── reports/minimal.json
├── schemas/
│   ├── asset-manifest.schema.json
│   ├── asset-record.schema.json
│   ├── claim.schema.json
│   ├── evidence.schema.json
│   ├── knowledge-index.schema.json
│   ├── report-plan.schema.json
│   └── research-report.schema.json
├── specs/
│   ├── 001-foundation.md
│   ├── 002-executable-core.md
│   ├── 003-collectors.md
│   ├── 004-knowledge-index.md
│   ├── 005-reporting.md
│   └── 006-assets.md
├── src/pg_researcher/
└── tests/
```

## Development gates

```bash
ruff check .
pytest
python -m build --wheel
```

## Roadmap

1. **Foundation** — evidence doctrine, source hierarchy, rights/provenance, schemas. ✅
2. **Executable core** — typed models, registry loader, validation CLI and CI. ✅
3. **Collectors** — controlled web/DSP/social acquisition, cache and fetch policy. ✅
4. **Knowledge index** — explicit claims, evidence dedupe, conflicts, catalog/timeline indexes. ✅
5. **Reporting** — briefs, source ledger and explicit editorial-opportunity bridges. ✅
6. **Assets** — provenance manifest, authorized acquisition/derivatives and publication gates. ✅

The six-stage foundation is complete. The next work should populate the system with a real Prince' Gutt research/asset corpus and release it as an operational skill rather than add another foundational abstraction.
