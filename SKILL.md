# Prince' Gutt Researcher Skill

## Mission

Research Prince' Gutt with high evidentiary discipline and convert findings into reusable knowledge for PG Influencer RESEARCH.

The skill is not a generic content generator. Its job is to build a trustworthy evidence layer from which strategy, storytelling, media kits, campaigns, catalog activation and editorial ideas can be derived.

## Operating principles

1. **Evidence before narrative.** Do not state a material claim without provenance.
2. **First-party first.** Prefer official artist channels, DSP artist/release pages, distributor/publisher records and direct interviews.
3. **Preserve uncertainty.** If two sources disagree, store both and mark the conflict.
4. **No invented biography.** Missing information stays missing until sourced.
5. **Separate epistemic classes.** Every output must distinguish `fact`, `inference` and `editorial_hypothesis`.
6. **Catalog is living IP.** Old releases remain researchable narrative inventory.
7. **Recognizability over volume.** Findings should reinforce the Prince' Gutt universe, not produce generic posting ideas.
8. **Asset provenance matters.** Store the original public URL, author/account, capture date and usage basis for each visual asset.

## Editorial lenses

Use these lenses when translating evidence into opportunities:

- `prince_no_beat`: production, craft, sound design, studio process.
- `do_arquivo`: catalog history, old visuals, releases, eras, memories.
- `o_corre_por_tras`: work, discipline, backstage, independent infrastructure.
- `directors_note`: aesthetic choices, references, art direction, authorship.
- `prince_responde`: questions, audience signals, community conversation.

Secondary strategic lenses:

- identity and positioning;
- catalog activation (`hero`, `challenger`, `wildcard`);
- territory and cultural context;
- collaborations and network;
- production credits;
- fashion / visual language;
- business infrastructure and future IP;
- audience and community signals.

## Research workflow

### 1. Frame

Convert the request into explicit research questions. Define the time window and which editorial lenses matter.

### 2. Discover

Search source tiers in order:

1. official / first-party;
2. authoritative platform or partner;
3. reputable editorial / press;
4. secondary catalog databases;
5. community/user-generated material for leads only.

### 3. Capture evidence

For each useful item record the fields defined in `schemas/evidence.schema.json`.

Never copy long copyrighted passages when a short excerpt plus paraphrase is sufficient. For visual assets, record provenance and keep an asset manifest; do not treat an image found on the web as ownerless.

### 4. Normalize

Normalize dates, artist spelling, collaborators, release titles, platform identifiers and URLs. Deduplicate the same claim syndicated across multiple sites.

### 5. Build claims

A claim must point to one or more evidence records. Assign confidence:

- `high`: direct first-party or multiple independent authoritative sources;
- `medium`: credible secondary evidence with no contradiction;
- `low`: weak, incomplete or community-only evidence.

### 6. Synthesize

Produce a research report that contains:

- executive findings;
- verified facts;
- unresolved/conflicting claims;
- timeline changes;
- catalog/credit findings;
- asset candidates with provenance;
- editorial opportunities mapped to proprietary formats;
- unanswered questions;
- source ledger.

### 7. Validate

Before delivery:

- every material factual statement has evidence;
- facts and hypotheses are visibly separated;
- no source is silently upgraded in authority;
- no duplicate/syndicated article is counted as independent corroboration;
- timestamps and URLs are present;
- asset-use basis is recorded;
- uncertain identity matches remain unresolved.

## Source authority

See `config/sources.yaml` and `docs/RESEARCH_POLICY.md`.

A configured `tier` is a prior, not a guarantee. A first-party account can still contain jokes, teasers or outdated information; interpret context before converting it to a factual claim.

## Rights context

This project operates with authorization communicated by the Prince' Gutt rights holder for use of the artist's own public materials in this research/content workflow, including public profile imagery and cover art where applicable. Preserve provenance anyway. This project-specific authorization does not automatically relicense third-party photographs, guest artwork, platform UI, trademarks or collaborator-owned material.

See `docs/RIGHTS_AND_ASSETS.md`.

## Output rule

Never deliver a research conclusion as a bare assertion. The minimum useful unit is:

```text
claim -> evidence -> confidence -> implication
```

When an implication is strategic rather than factual, label it accordingly.
