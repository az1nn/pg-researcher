# Assets

## Purpose

The asset layer turns public visual discovery into a rights-aware, reproducible production inventory. A URL or downloaded image is not considered publishable merely because it is public.

The auditable chain is:

```text
source URL -> asset record -> local file hash -> derivative history -> publication gate
```

## Source of truth

Asset metadata is authoritative in JSON records and the generated `AssetManifest`. Binary files are referenced by relative path, byte size and SHA-256.

A file that no longer matches its recorded hash fails integrity verification and cannot pass the publication gate.

## Rights classes

- **A** — artist-controlled/project-authorized material.
- **B** — collaborator or commissioned third-party work.
- **C** — platform/interface material.
- **D** — press/editorial third-party material.

Artist authorization can clear class A when the project controls the relevant rights. It does not automatically clear classes B, C or D.

## Acquisition

`asset acquire` only accepts public HTTP/HTTPS URLs, an allowlist of visual MIME types and a bounded response size. Redirect targets are revalidated. Tests use mock transports; CI never downloads public assets.

The command requires rights metadata at acquisition time so a downloaded file cannot become an orphan with unknown provenance.

## Local registration

`asset register` hashes an existing authorized/local file and creates the same record contract without downloading anything. This is the preferred path for artist originals supplied directly to the project.

## Derivatives

A derivative points to a parent `file_id` and carries explicit transformation history. The asset layer does not perform creative image editing itself; it records the provenance of crops, cleanup, layout variants, retouching or other authorized transformations produced by the relevant image workflow.

## Manifest

```bash
pg-researcher asset manifest-build \
  --records-dir data/assets/records \
  --output data/assets/manifest.json

pg-researcher asset manifest-validate data/assets/manifest.json
pg-researcher asset inspect data/assets/manifest.json
pg-researcher asset verify data/assets/manifest.json --root .
```

## Publication gate

The gate is fail-closed for unknown usage basis, identity mismatch, missing mandatory creator/attribution data, invalid structure or file-integrity failure.

Assets remain `research_only` when publication needs human clearance, including unresolved/probable identity, research-reference-only usage, platform UI without explicit clearance, third-party material without license/permission, extra restrictions or metadata-only records without a local file.

A result is `approved` only when every blocking and review check passes.

```bash
pg-researcher asset gate data/assets/manifest.json --root . --json
```

## Storage rule

Do not treat the repository as an unbounded media dump. Keep source records and manifests under version control. Store binary originals/derivatives only where the project intentionally wants them, and always preserve the manifest linkage and SHA-256.
