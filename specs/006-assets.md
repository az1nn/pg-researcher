# Spec 006 — Assets

## Status

Implemented in this PR.

## Problem

Research and reporting can identify useful visual material, but public availability does not prove ownership, reuse permission, identity, file integrity or transformation provenance. The project needs a deterministic boundary between research reference and publication-ready media.

## Decision

Asset records are explicit artifacts. Every retained asset SHALL preserve source provenance, rights class, usage basis and identity status. Local files SHALL be content-addressed by SHA-256. Derivatives SHALL link to a parent file and transformation history. Publication SHALL be gated deterministically and fail closed when material requirements are unresolved.

## Functional requirements

### FR-001 Asset record

The project SHALL define typed and JSON-Schema-backed asset records with provenance, rights metadata, local files and derivative history.

### FR-002 Manifest

Multiple asset records SHALL build into a stable manifest sorted by asset ID. Duplicate asset IDs or global file IDs SHALL fail.

### FR-003 File integrity

Every registered file SHALL record a relative path, byte size and SHA-256. Verification SHALL detect missing, changed or path-escaping files.

### FR-004 Authorized acquisition

The CLI SHALL support bounded public image acquisition with public-URL validation, redirect revalidation, MIME allowlisting and maximum response size. Acquisition SHALL require explicit rights metadata.

### FR-005 Local originals

The CLI SHALL support registering a local artist/project file without network acquisition.

### FR-006 Derivatives

A derivative SHALL reference a known parent file and SHALL record at least one transformation entry. Cycles and missing parents SHALL fail.

### FR-007 Publication gate

The gate SHALL return `approved`, `research_only` or `blocked` and SHALL preserve reasons/checks.

Blocking conditions include unknown usage basis, identity mismatch, missing required attribution/creator data and failed file integrity.

Review conditions include unresolved identity, research-reference-only usage, platform/interface material without explicit clearance, third-party material without license/permission, additional restrictions and metadata-only records.

### FR-008 Rights boundaries

Artist authorization SHALL NOT automatically clear collaborator, platform/interface or press/editorial rights.

### FR-009 Offline CI

Network behavior SHALL be tested with `httpx.MockTransport`; CI SHALL not acquire live assets.

## Non-goals

- creative image editing;
- automatic rights ownership determination;
- legal advice or automated fair-use adjudication;
- DRM/access-control bypass;
- scraping private or authenticated media;
- binary media warehouse management.

## Acceptance criteria

- artist-authorized class A asset with verified identity and intact file can be approved;
- altered/missing file blocks publication;
- unknown usage basis blocks publication;
- class B/D rights are not cleared by artist authorization alone;
- class C remains research-only without explicit license/permission;
- derivatives preserve parent and transformation history;
- unsafe or unsupported acquisition fails;
- asset schemas ship in the wheel;
- lint, tests and build gates pass offline.

## Completion

With Spec 006 merged, the six-stage foundation is complete: evidence acquisition, deterministic knowledge, auditable reporting and rights-aware asset publication controls.
