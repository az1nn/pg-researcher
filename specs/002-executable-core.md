# Spec 002 — Executable Core

## Status

Implemented in PR #2 candidate.

## Objective

Turn the policy-only foundation into a deterministic Python package and CLI that can load curated research sources and validate evidence/report artifacts before network collectors are introduced.

## Decisions

- Python 3.12 baseline.
- Pydantic v2 for typed runtime models and registry validation.
- JSON Schema Draft 2020-12 remains the external artifact contract.
- Typer provides the CLI surface.
- PyYAML loads the human-maintained source registry.
- Network access is intentionally absent in this spec.
- Repository files are preferred during development; canonical config/schemas are force-included as package resources in built wheels.

## Functional requirements

### FR-002-01 Package

The repository SHALL install as `pg-researcher` and expose both `pg-researcher` and `python -m pg_researcher` entry points.

### FR-002-02 Typed registry

`config/sources.yaml` SHALL be parsed into typed models. Duplicate source IDs and source classes without class configuration SHALL fail validation.

### FR-002-03 Source CLI

The executable SHALL support:

```bash
pg-researcher sources list
pg-researcher sources list --json
pg-researcher sources validate
```

### FR-002-04 Evidence validation

The executable SHALL validate JSON evidence documents against `schemas/evidence.schema.json` and return a non-zero exit code on failure.

### FR-002-05 Report validation

The executable SHALL validate JSON research reports against `schemas/research-report.schema.json` and return a non-zero exit code on failure.

### FR-002-06 Offline operation

All validation and registry commands SHALL run without network access.

### FR-002-07 Distribution

The wheel SHALL contain the canonical registry and schemas so installed commands do not depend on the original repository layout.

### FR-002-08 Quality gate

CI SHALL execute Ruff and pytest on Python 3.12 for pushes and pull requests.

## Acceptance criteria

- `pip install -e '.[dev]'` installs successfully;
- `pg-researcher version` prints `0.1.0`;
- `pg-researcher sources validate` succeeds on the committed registry;
- valid example evidence/report files pass schema validation;
- evidence without `source_url` fails validation;
- duplicate source IDs fail registry validation;
- test suite passes without network calls.

## Explicitly deferred to Spec 003

- browser/web search;
- DSP/social collectors;
- HTTP caching;
- retry/rate-limit policy;
- robots/platform policy adapters;
- content extraction;
- asset downloading.
