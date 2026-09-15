# pg-researcher

Research skill and evidence pipeline for **Prince' Gutt**.

The repository turns public, authorized and verifiable information into reusable Prince' Gutt research artifacts. Every output must preserve provenance, distinguish fact from interpretation, and serve the artist's actual editorial universe.

## Research domains

### PG Influencer RESEARCH

Public-source research around Prince' Gutt as an artist-platform: music, production, image, territory, fashion, community and future IP.

Primary editorial formats:

- **Prince no Beat** — production as spectacle.
- **Do Arquivo** — catalog, history and memory as living inventory.
- **O Corre por Trás** — process, discipline and backstage.
- **Director's Note** — aesthetic decisions with authorship and authority.
- **Prince Responde** — community and live feedback loops.

### PG RELIGION RESEARCH

Evidence-backed research and publishing across religious, philosophical, esoteric and popular-wisdom sources, with Hermetic and Pythagorean traditions as primary comparative lenses.

The religion domain is universalist in method but must not flatten traditions into false equivalence. Source statements, historical context, tradition claims, scholarly interpretations, comparative parallels and Prince' Gutt editorial synthesis remain explicitly distinct.

See `docs/RELIGION_RESEARCH.md`, `config/religion-corpus.yaml` and `specs/006-religion-research-foundation.md`.

## Core doctrine

Prince' Gutt is treated as an artist-platform. Research should strengthen recognizability, repertoire and original IP rather than fill a calendar or mechanically rewrite source material.

## Research contract

Every material claim should carry:

1. source URL;
2. source class;
3. capture timestamp;
4. evidence excerpt or structured fact;
5. confidence;
6. an explicit claim/interpretation type appropriate to its research domain.

Official/primary and authoritative sources outrank aggregators. Conflicting claims are preserved and flagged instead of silently resolved.

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
```

Collectors normalize provenance into typed evidence; they do not synthesize claims. Claims are explicit artifacts. The knowledge index canonicalizes duplicate evidence, preserves conflicts and projects views without silently deciding which conflicting value is true.

Reporting consumes that knowledge layer. Findings are projected from claims; strategic/editorial synthesis only enters through explicit, traceable planning artifacts.

## Repository map

```text
.
├── .github/workflows/ci.yml
├── SKILL.md
├── config/
│   ├── fetch-policy.yaml
│   ├── religion-corpus.yaml
│   └── sources.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── COLLECTORS.md
│   ├── KNOWLEDGE_INDEX.md
│   ├── RELIGION_RESEARCH.md
│   ├── REPORTING.md
│   ├── RESEARCH_POLICY.md
│   └── RIGHTS_AND_ASSETS.md
├── examples/
│   ├── claims/minimal.json
│   ├── evidence/minimal.json
│   ├── reporting/plan.json
│   └── reports/minimal.json
├── schemas/
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
│   └── 006-religion-research-foundation.md
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
6. **PG Religion Research foundation** — comparative doctrine, source/claim taxonomy, rights/publication rules and e-book contract. ✅
7. **Assets** — provenance manifest, authorized acquisition/derivatives and publication gates.
8. **Religion corpus runtime** — typed models/validation for religious-source, rights, parallel and manuscript artifacts.
9. **E-book production** — deterministic manuscript/package generation, PDF/ePub export and publication QA.
