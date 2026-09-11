# Rights and Asset Handling

## Project authorization

For the PG Influencer RESEARCH workflow, the project operates with authorization communicated by the Prince' Gutt rights holder to research and reuse the artist's own public materials, including public profile imagery and cover art where the relevant rights are controlled by the artist/project.

This authorization is a project-specific usage basis. It does **not** mean every asset visible on an official profile is automatically owned solely by Prince' Gutt, nor does it relicense third-party rights to downstream users.

## Asset classes

### A — artist-controlled / project-authorized

Examples may include artist-owned portraits, official covers, project-created graphics and other assets whose rights are controlled by the artist/project.

Usage basis: `artist_authorization`.

### B — collaborator / commissioned third-party work

Examples: photography, artwork, styling imagery, video stills or designs where another creator may retain rights.

Usage basis must be recorded. Do not assume artist publication equals unrestricted relicensing.

### C — platform/interface material

Examples: screenshots containing Spotify, Instagram, X, YouTube or other platform UI/trademarks.

Keep usage contextual and minimal. Prefer the underlying artist asset where available rather than a UI screenshot.

### D — press/editorial third-party material

Use as research evidence. Reuse of the image itself requires an explicit basis separate from the article's public availability.

## Asset manifest

Every retained visual asset should record:

```yaml
asset_id: pg_asset_...
source_url: https://...
source_account: princeguttreal
captured_at: 2026-09-11T00:00:00Z
asset_type: portrait|cover|post|video_still|screenshot|other
rights_class: A|B|C|D
usage_basis: artist_authorization|license|permission|research_reference|unknown
creator: null
work_or_release: null
notes: null
```

## Editing and derivatives

Where `usage_basis: artist_authorization` applies, the workflow may prepare research/content derivatives such as crops, cleanup, layout adaptation and art-direction variants consistent with the project's authorization. The original source and transformation history should remain traceable.

Do not erase attribution or rights metadata merely because an asset is being visually cleaned or reformatted.

## Storage rule

Prefer storing:

1. provenance metadata;
2. canonical source URL;
3. authorized working derivative when needed;
4. transformation notes.

Avoid accumulating duplicate downloads with no provenance.

## Publication gate

Before an asset moves from research to public-facing output, confirm:

- identity is correct;
- usage basis is not `unknown`;
- third-party authorship, if present, is handled;
- crop/edit does not create a misleading representation;
- required attribution is preserved;
- the asset still fits the approved Prince' Gutt visual direction.
