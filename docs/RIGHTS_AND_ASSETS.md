# Rights and Asset Handling

## Project authorization

For the PG Influencer RESEARCH workflow, the project operates with authorization communicated by the Prince' Gutt rights holder to research and reuse the artist's own public materials, including public profile imagery and cover art where the relevant rights are controlled by the artist/project.

This authorization is a project-specific usage basis. It does **not** mean every asset visible on an official profile is automatically owned solely by Prince' Gutt, nor does it relicense third-party rights to downstream users.

## Asset classes

### A — artist-controlled / project-authorized

Examples may include artist-owned portraits, official covers, project-created graphics and other assets whose rights are controlled by the artist/project.

Usage basis may be `artist_authorization`, `license` or `permission` as applicable.

### B — collaborator / commissioned third-party work

Examples: photography, artwork, styling imagery, video stills or designs where another creator may retain rights.

Artist authorization alone is not treated as third-party clearance. Public-facing reuse requires an explicit basis such as `license` or `permission`, and the creator must remain recorded.

### C — platform/interface material

Examples: screenshots containing Spotify, Instagram, X, YouTube or other platform UI/trademarks.

Keep usage contextual and minimal. Prefer the underlying artist asset where available. The deterministic gate keeps class C research-only unless explicit license/permission is recorded.

### D — press/editorial third-party material

Use as research evidence by default. Reuse of the image itself requires an explicit basis separate from the article's public availability and the creator/source authorship must remain recorded.

## Asset records and manifest

The implemented contract is defined by:

- `schemas/asset-record.schema.json`;
- `schemas/asset-manifest.schema.json`;
- `docs/ASSETS.md`.

Every retained asset records source provenance, rights class, usage basis, identity status and optional creator/attribution/restriction fields. Local files add:

- relative path;
- byte size;
- SHA-256;
- media type;
- acquisition URL where relevant;
- parent and transformation history for derivatives.

A manifest is generated deterministically from individual records. It is metadata source of truth, not proof that the underlying rights assertion is legally correct.

## Editing and derivatives

Where the usage basis authorizes transformation, the workflow may prepare crops, cleanup, layout adaptation and art-direction variants. Creative editing happens in the appropriate image workflow; this asset layer records the resulting derivative against its parent file and transformation history.

Do not erase attribution or rights metadata merely because an asset is visually cleaned or reformatted.

## File integrity

Every registered local file is content-addressed by SHA-256. Before publication, `asset verify` checks that files exist, stay inside the declared root, retain their byte size and still match the recorded digest.

A missing or changed file fails integrity and blocks publication.

## Publication gate

The implemented gate produces one of three states:

- `approved` — all blocking and review checks pass;
- `research_only` — the asset remains useful for research but needs publication clearance/review;
- `blocked` — a material safety/provenance/integrity condition failed.

The gate blocks unknown usage basis, identity mismatch, file-integrity failure, missing required attribution and required creator metadata for relevant third-party classes.

It keeps unresolved identity, research-reference-only use, uncleared class B/C/D material, extra restrictions and metadata-only records in `research_only` state.

## Storage rule

Prefer storing:

1. provenance metadata and the canonical/public source URL;
2. artist-supplied or explicitly authorized original when needed;
3. only useful derivatives;
4. transformation history and hashes.

Avoid accumulating duplicate downloads with no provenance. The repository should not become an unbounded media dump.

## CLI

See `docs/ASSETS.md` for registration, acquisition, derivative, manifest, verification and gate commands.
