# Research Policy

## Purpose

This policy defines how `pg-researcher` evaluates sources and converts public material into evidence-backed research.

## Source hierarchy

### Tier 1 — official / first-party

Examples: Prince' Gutt's official profiles, direct statements, official release announcements and authorized materials.

Use for identity, intent, announcements and artist-authored context. Still distinguish between a teaser, joke, opinion, future plan and confirmed fact.

### Tier 2 — authoritative platform / partner

Examples: DSP release pages, distributor/publisher information, platform metadata and formal partner pages.

Use for catalog metadata, release availability and business/distribution context when the platform exposes the relevant field directly.

### Tier 3 — reputable press

Use for interviews, reported context, event coverage and production credits when sourced transparently.

### Tier 4 — secondary catalog / index

Useful for discovery and corroboration. Do not prefer an aggregator over first-party/platform metadata when both exist.

### Tier 5 — community / UGC

Use as a lead generator or audience-signal source. It cannot independently close a material biographical, contractual or catalog claim.

## Evidence rules

Every evidence record needs:

- stable evidence ID;
- source class and source ID where configured;
- URL;
- capture timestamp;
- published/event date when available;
- source title/account;
- concise excerpt or structured observation;
- content type;
- identity-match status;
- optional asset metadata;
- notes about ambiguity or contradiction.

## Fact vs inference

`fact` means directly supported by evidence.

`inference` means a reasoned conclusion built from facts but not explicitly stated by a source.

`editorial_hypothesis` means a strategic/content possibility worth testing.

A report may contain all three, but must never blur the labels.

## Corroboration

Two syndicated copies of the same press release count as one evidentiary origin. Corroboration requires genuinely independent sourcing or a separate first-party confirmation.

## Conflict handling

Do not choose the more convenient version. Preserve:

- each conflicting value;
- supporting evidence IDs;
- source authority;
- date/context;
- unresolved status.

Only resolve when stronger evidence is obtained.

## Temporal claims

Music catalogs, bios, affiliations, metrics and platform metadata change over time. Store `observed_at` and avoid turning a time-bound observation into a permanent claim.

## Metrics

Follower counts, streams, views and engagement are snapshots. Reports must include collection date and platform; never present them as timeless facts.

## Copyright-sensitive material

Prefer short evidence excerpts and paraphrase. Store metadata and provenance instead of reproducing full articles, lyrics, transcripts or other third-party works unless separately authorized.

## Identity matching

A search result with a matching name is not sufficient. Match using one or more of:

- official handle/linkage;
- known collaborators/releases;
- cross-linked official profile;
- platform verification;
- direct project confirmation.

Ambiguous matches remain `unresolved`.
