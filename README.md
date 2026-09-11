# pg-researcher

Research skill and evidence pipeline for **Prince' Gutt**.

The repository exists to turn public, authorized and verifiable information about Prince' Gutt into reusable research artifacts for the **PG Influencer RESEARCH** project. It is not a generic social-media scraper: every output must preserve provenance, distinguish fact from interpretation, and serve the artist's actual editorial universe.

## Core doctrine

Prince' Gutt is treated as an artist-platform: music, production, image, territory, fashion, community and future IP. Research should strengthen recognizability and repertoire rather than fill a calendar.

Primary editorial lenses:

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

## Repository map

```text
.
├── SKILL.md
├── config/
│   └── sources.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── RESEARCH_POLICY.md
│   └── RIGHTS_AND_ASSETS.md
├── schemas/
│   ├── evidence.schema.json
│   └── research-report.schema.json
└── specs/
    └── 001-foundation.md
```

## Status

Foundation phase. The next implementation layer will add executable collectors, normalization, deduplication, claim/evidence indexing, report generation and validation tests.
