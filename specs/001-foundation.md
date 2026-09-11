# Spec 001 — Research Foundation

## Status

Implemented in foundation PR.

## Problem

PG Influencer RESEARCH needs a dedicated researcher for Prince' Gutt that can collect public information without turning search results into unsupported biography or generic content suggestions.

The system must preserve evidence, source authority, uncertainty and asset provenance so downstream strategy remains auditable.

## Goals

- define a reusable researcher skill;
- encode the Prince' Gutt editorial doctrine;
- establish source hierarchy and known official/partner sources;
- define evidence and report contracts;
- codify project-specific rights/asset handling;
- create an architecture that can accept executable collectors later without coupling collection to synthesis.

## Non-goals

- bulk scraping every social network;
- bypassing platform access controls;
- downloading every public image by default;
- treating follower/stream counts as permanent facts;
- autonomous publishing;
- fabricating missing biographical details.

## Functional requirements

### FR-001 Source registry

The project SHALL maintain a human-reviewed source registry containing authority class, identity status and capabilities.

### FR-002 Evidence contract

Every material research observation SHALL be serializable to `schemas/evidence.schema.json`.

### FR-003 Epistemic separation

Research findings SHALL use one of `fact`, `inference`, or `editorial_hypothesis`.

### FR-004 Conflict preservation

Contradictory evidence SHALL remain visible and SHALL NOT be silently overwritten.

### FR-005 Asset provenance

Visual asset candidates SHALL carry source URL, rights class and usage basis before downstream publication use.

### FR-006 Editorial mapping

Strategic findings MAY map to Prince' Gutt proprietary formats, but this mapping SHALL be labeled as interpretation/hypothesis unless explicitly factual.

## Acceptance criteria

- `README.md` explains scope and research contract;
- `SKILL.md` contains the complete research workflow;
- source tiers and seed sources exist in `config/sources.yaml`;
- evidence schema rejects unclassified source/evidence types;
- report schema enforces epistemic class and confidence;
- rights policy explicitly separates artist authorization from third-party rights;
- architecture defines collection -> evidence -> claims -> synthesis separation.

## Follow-up specs

- `002-executable-core`: CLI, typed models, schema validation and source registry loader.
- `003-collectors`: web/DSP/social adapters with caching and rate-limit behavior.
- `004-knowledge-index`: claim ledger, dedupe, conflict graph and timeline/catalog indexes.
- `005-reporting`: research briefs, source ledger and editorial opportunity renderer.
- `006-assets`: asset manifest, authorized downloads/derivatives and provenance checks.
