# Spec 003 — Controlled Collectors

## Status

Implemented in the collectors PR.

## Problem

The executable core can validate artifacts but cannot yet create evidence from public sources. Acquisition must be added without turning the project into an unrestricted scraper or coupling live-network behavior to evidence semantics.

## Goals

- collect registered public HTTP/HTTPS sources;
- normalize URLs and strip trackers;
- enforce a configurable fetch policy;
- cache captures locally;
- retry only transient failures;
- convert captures into typed `Evidence`;
- keep network tests deterministic/offline.

## Non-goals

- browser automation;
- login/session bypass;
- private or undocumented APIs;
- broad crawling/site mirroring;
- automatic source discovery/identity resolution;
- claim synthesis;
- binary asset downloading.

## Functional requirements

### FR-001 Registered-source collection

The CLI SHALL collect by source id from the curated registry. A source with no canonical URL SHALL require an explicit URL override.

### FR-002 Public URL guard

The collector SHALL accept only HTTP/HTTPS and SHALL reject embedded credentials, localhost-style names and non-public literal IP addresses.

### FR-003 Canonicalization

The collector SHALL remove fragments/common tracking parameters and normalize query ordering before cache lookup and capture.

### FR-004 Policy-aware HTTP

Timeout, retries, backoff, host interval, response limit, accepted media types and cache TTL SHALL be configurable in `config/fetch-policy.yaml`.

### FR-005 Retry semantics

Retries SHALL be limited to request errors, HTTP 429 and 5xx. `Retry-After` SHALL be honored when present.

### FR-006 Cache

A successful textual capture SHALL be cacheable by canonical URL. `--refresh` SHALL bypass cache.

### FR-007 Evidence conversion

A capture SHALL produce a typed `Evidence` object containing provenance, capture time, source class, identity status, concise observation and excerpt.

### FR-008 Stable evidence identity

Evidence ID SHALL be derived from source id, final canonical URL and normalized captured text so unchanged content remains addressable across repeated captures.

### FR-009 Offline tests

CI SHALL NOT depend on live network access. HTTP behavior SHALL be exercised through a deterministic mock transport.

## Acceptance criteria

- `pg-researcher collect source <source-id>` exists;
- explicit `--url` supports registry entries whose canonical URL is pending;
- URL safety and tracker stripping have tests;
- cache round-trip and expiry have tests;
- 429 + `Retry-After` retry behavior has a test;
- collector output is a valid typed `Evidence` object;
- repeated identical content generates the same evidence id;
- fetch policy is packaged in the wheel;
- Ruff, pytest, wheel build and resource-verification gates pass.

## Follow-up

Spec 004 will introduce the claim ledger, evidence deduplication, conflict preservation and timeline/catalog indexes. It will consume collector-generated evidence rather than fetch the network itself.
