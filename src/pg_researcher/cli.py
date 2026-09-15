from __future__ import annotations

import json
from pathlib import Path

import typer

from pg_researcher import __version__
from pg_researcher.assets.acquire import AssetAcquireError, AssetAcquirer
from pg_researcher.assets.gate import gate_manifest
from pg_researcher.assets.manifest import (
    AssetManifestError,
    build_manifest,
    create_asset_record,
    load_asset_manifest,
    load_asset_record,
    load_asset_records_dir,
    register_derivative,
    sha256_file,
    verify_manifest,
    write_asset_manifest,
    write_asset_record,
)
from pg_researcher.assets.models import (
    AssetIdentityStatus,
    AssetType,
    PublicationStatus,
    RightsClass,
    UsageBasis,
)
from pg_researcher.assets.policy import AssetPolicyError, load_asset_policy
from pg_researcher.collectors.cache import FileCache
from pg_researcher.collectors.http import HttpFetcher
from pg_researcher.collectors.policy import FetchPolicyError, load_fetch_policy
from pg_researcher.collectors.web import CollectorError, WebCollector
from pg_researcher.knowledge.index import KnowledgeIndexError, build_knowledge_index
from pg_researcher.knowledge.io import (
    KnowledgeIOError,
    load_claim_dir,
    load_evidence_dir,
    load_knowledge_index,
    write_knowledge_index,
)
from pg_researcher.registry import RegistryError, load_registry
from pg_researcher.reporting.builder import ReportingError, build_research_report
from pg_researcher.reporting.io import (
    ReportIOError,
    load_report_plan,
    load_research_report,
    write_research_report,
)
from pg_researcher.reporting.render import render_markdown
from pg_researcher.validation import SchemaValidationError, validate_file

app = typer.Typer(
    name="pg-researcher",
    help="Evidence-first research tooling for Prince' Gutt.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Inspect and validate the curated source registry.")
evidence_app = typer.Typer(help="Validate evidence artifacts.")
claim_app = typer.Typer(help="Validate explicit knowledge claims.")
knowledge_app = typer.Typer(help="Build and inspect the deterministic knowledge index.")
report_app = typer.Typer(help="Build, render and validate research reports.")
asset_app = typer.Typer(help="Acquire, register, verify and gate visual assets.")
collect_app = typer.Typer(help="Capture controlled public-source evidence.")
app.add_typer(sources_app, name="sources")
app.add_typer(evidence_app, name="evidence")
app.add_typer(claim_app, name="claim")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(report_app, name="report")
app.add_typer(asset_app, name="asset")
app.add_typer(collect_app, name="collect")


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _restrictions(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def _parameters(value: str | None) -> dict:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        _fail(f"invalid --parameters JSON: {exc}")
    if not isinstance(parsed, dict):
        _fail("--parameters must contain a JSON object")
    return parsed


def _ensure_inside_root(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        _fail(f"path must stay inside --root {root.resolve()}: {path.resolve()}")


@app.command("version")
def version() -> None:
    """Print the executable-core version."""
    typer.echo(__version__)


@sources_app.command("list")
def sources_list(
    registry: Path | None = typer.Option(None, "--registry", exists=True, dir_okay=False),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
    include_disabled: bool = typer.Option(False, "--all", help="Include disabled sources."),
) -> None:
    """List configured research sources."""
    try:
        loaded = load_registry(registry)
    except RegistryError as exc:
        _fail(str(exc))

    items = loaded.sources if include_disabled else loaded.enabled_sources()
    if json_output:
        payload = [
            {
                "id": source.id,
                "class": source.source_class.value,
                "platform": source.platform,
                "canonical_url": str(source.canonical_url) if source.canonical_url else None,
                "identity_status": source.identity_status,
                "enabled": source.enabled,
            }
            for source in items
        ]
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for source in items:
        url = str(source.canonical_url) if source.canonical_url else "<discovery pending>"
        typer.echo(f"{source.id}\t{source.source_class.value}\t{source.platform}\t{url}")


@sources_app.command("validate")
def sources_validate(
    registry: Path | None = typer.Option(None, "--registry", exists=True, dir_okay=False),
) -> None:
    """Validate registry structure and cross-record invariants."""
    try:
        loaded = load_registry(registry)
    except RegistryError as exc:
        _fail(str(exc))
    typer.echo(f"valid: {len(loaded.sources)} sources / registry v{loaded.version}")


@evidence_app.command("validate")
def evidence_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one evidence JSON document against the canonical schema."""
    try:
        validate_file(path, "evidence")
    except SchemaValidationError as exc:
        _fail(str(exc))
    typer.echo(f"valid evidence: {path}")


@claim_app.command("validate")
def claim_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one explicit knowledge claim."""
    try:
        validate_file(path, "claim")
    except SchemaValidationError as exc:
        _fail(str(exc))
    typer.echo(f"valid claim: {path}")


@knowledge_app.command("build")
def knowledge_build(
    evidence_dir: Path = typer.Option(..., "--evidence-dir", exists=True, file_okay=False),
    claims_dir: Path = typer.Option(..., "--claims-dir", exists=True, file_okay=False),
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Build a deterministic knowledge index from evidence and explicit claims."""
    try:
        evidence = load_evidence_dir(evidence_dir)
        claims = load_claim_dir(claims_dir)
        index = build_knowledge_index(evidence, claims)
        write_knowledge_index(index, output)
    except (KnowledgeIOError, KnowledgeIndexError) as exc:
        _fail(str(exc))
    typer.echo(
        f"wrote knowledge index: {output} "
        f"({index.claim_count} claims / {len(index.conflicts)} conflicts)"
    )


@knowledge_app.command("inspect")
def knowledge_inspect(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Show high-level counts for one generated knowledge index."""
    try:
        index = load_knowledge_index(path)
    except KnowledgeIOError as exc:
        _fail(str(exc))
    typer.echo(f"evidence: {index.evidence_count}")
    typer.echo(f"canonical evidence: {index.canonical_evidence_count}")
    typer.echo(f"claims: {index.claim_count}")
    typer.echo(f"conflicts: {len(index.conflicts)}")
    typer.echo(f"timeline entries: {len(index.timeline)}")
    typer.echo(f"catalog entries: {len(index.catalog)}")


@report_app.command("plan-validate")
def report_plan_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate a report plan before synthesis."""
    try:
        validate_file(path, "report_plan")
    except SchemaValidationError as exc:
        _fail(str(exc))
    typer.echo(f"valid report plan: {path}")


@report_app.command("validate")
def report_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one generated research report."""
    try:
        validate_file(path, "report")
    except SchemaValidationError as exc:
        _fail(str(exc))
    typer.echo(f"valid report: {path}")


@report_app.command("build")
def report_build(
    knowledge: Path = typer.Option(..., "--knowledge", exists=True, dir_okay=False),
    evidence_dir: Path = typer.Option(..., "--evidence-dir", exists=True, file_okay=False),
    plan: Path = typer.Option(..., "--plan", exists=True, dir_okay=False),
    output_json: Path = typer.Option(..., "--output-json", dir_okay=False),
    output_markdown: Path | None = typer.Option(None, "--output-markdown", dir_okay=False),
) -> None:
    """Build an evidence-backed report from a knowledge index and explicit report plan."""
    try:
        index = load_knowledge_index(knowledge)
        evidence = load_evidence_dir(evidence_dir)
        loaded_plan = load_report_plan(plan)
        report = build_research_report(index, evidence, loaded_plan)
        write_research_report(report, output_json)
    except (KnowledgeIOError, ReportIOError, ReportingError) as exc:
        _fail(str(exc))

    if output_markdown is not None:
        output_markdown.parent.mkdir(parents=True, exist_ok=True)
        output_markdown.write_text(render_markdown(report), encoding="utf-8")
        typer.echo(f"wrote report Markdown: {output_markdown}")
    typer.echo(f"wrote report JSON: {output_json}")


@report_app.command("render")
def report_render(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
    output: Path | None = typer.Option(None, "--output", dir_okay=False),
) -> None:
    """Render a generated research report as Markdown."""
    try:
        report = load_research_report(path)
    except ReportIOError as exc:
        _fail(str(exc))
    rendered = render_markdown(report)
    if output is None:
        typer.echo(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    typer.echo(f"wrote report Markdown: {output}")


@asset_app.command("record-validate")
def asset_record_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one asset record against schema and structural invariants."""
    try:
        validate_file(path, "asset_record")
        load_asset_record(path)
    except (SchemaValidationError, AssetManifestError) as exc:
        _fail(str(exc))
    typer.echo(f"valid asset record: {path}")


@asset_app.command("manifest-validate")
def asset_manifest_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one generated asset manifest."""
    try:
        validate_file(path, "asset_manifest")
        load_asset_manifest(path)
    except (SchemaValidationError, AssetManifestError) as exc:
        _fail(str(exc))
    typer.echo(f"valid asset manifest: {path}")


@asset_app.command("hash")
def asset_hash(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Print the SHA-256 of one local asset file."""
    typer.echo(sha256_file(path))


@asset_app.command("register")
def asset_register(
    file: Path = typer.Argument(..., exists=True, dir_okay=False),
    asset_id: str = typer.Option(..., "--asset-id"),
    source_url: str = typer.Option(..., "--source-url"),
    asset_type: AssetType = typer.Option(..., "--asset-type"),
    rights_class: RightsClass = typer.Option(..., "--rights-class"),
    usage_basis: UsageBasis = typer.Option(..., "--usage-basis"),
    output_record: Path = typer.Option(..., "--output-record", dir_okay=False),
    root: Path = typer.Option(Path("."), "--root", exists=True, file_okay=False),
    identity_status: AssetIdentityStatus = typer.Option(
        AssetIdentityStatus.UNRESOLVED, "--identity-status"
    ),
    source_account: str | None = typer.Option(None, "--source-account"),
    evidence_id: str | None = typer.Option(None, "--evidence-id"),
    creator: str | None = typer.Option(None, "--creator"),
    work_or_release: str | None = typer.Option(None, "--work-or-release"),
    attribution_required: bool = typer.Option(False, "--attribution-required"),
    attribution_text: str | None = typer.Option(None, "--attribution-text"),
    restrictions: str | None = typer.Option(None, "--restrictions"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Register an existing local file as a provenance-tracked asset."""
    try:
        record = create_asset_record(
            asset_id=asset_id,
            source_url=source_url,
            asset_type=asset_type,
            rights_class=rights_class,
            usage_basis=usage_basis,
            identity_status=identity_status,
            file_path=file,
            root=root,
            source_account=source_account,
            evidence_id=evidence_id,
            creator=creator,
            work_or_release=work_or_release,
            attribution_required=attribution_required,
            attribution_text=attribution_text,
            restrictions=_restrictions(restrictions),
            notes=notes,
        )
        write_asset_record(record, output_record)
    except AssetManifestError as exc:
        _fail(str(exc))
    typer.echo(f"wrote asset record: {output_record}")


@asset_app.command("acquire")
def asset_acquire(
    url: str = typer.Argument(...),
    output_file: Path = typer.Option(..., "--output-file", dir_okay=False),
    output_record: Path = typer.Option(..., "--output-record", dir_okay=False),
    asset_id: str = typer.Option(..., "--asset-id"),
    asset_type: AssetType = typer.Option(..., "--asset-type"),
    rights_class: RightsClass = typer.Option(..., "--rights-class"),
    usage_basis: UsageBasis = typer.Option(..., "--usage-basis"),
    root: Path = typer.Option(Path("."), "--root", exists=True, file_okay=False),
    policy: Path | None = typer.Option(None, "--policy", exists=True, dir_okay=False),
    identity_status: AssetIdentityStatus = typer.Option(
        AssetIdentityStatus.UNRESOLVED, "--identity-status"
    ),
    source_account: str | None = typer.Option(None, "--source-account"),
    evidence_id: str | None = typer.Option(None, "--evidence-id"),
    creator: str | None = typer.Option(None, "--creator"),
    work_or_release: str | None = typer.Option(None, "--work-or-release"),
    attribution_required: bool = typer.Option(False, "--attribution-required"),
    attribution_text: str | None = typer.Option(None, "--attribution-text"),
    restrictions: str | None = typer.Option(None, "--restrictions"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Acquire one public visual asset and immediately write its rights-aware record."""
    _ensure_inside_root(output_file, root)
    try:
        loaded_policy = load_asset_policy(policy)
        result = AssetAcquirer(policy=loaded_policy).acquire(url, output_file)
        record = create_asset_record(
            asset_id=asset_id,
            source_url=result.requested_url,
            final_url=result.final_url,
            asset_type=asset_type,
            rights_class=rights_class,
            usage_basis=usage_basis,
            identity_status=identity_status,
            file_path=result.path,
            root=root,
            media_type=result.media_type,
            source_account=source_account,
            evidence_id=evidence_id,
            creator=creator,
            work_or_release=work_or_release,
            attribution_required=attribution_required,
            attribution_text=attribution_text,
            restrictions=_restrictions(restrictions),
            notes=notes,
        )
        write_asset_record(record, output_record)
    except (AssetPolicyError, AssetAcquireError, AssetManifestError) as exc:
        _fail(str(exc))
    typer.echo(f"wrote asset file: {output_file}")
    typer.echo(f"wrote asset record: {output_record}")


@asset_app.command("derivative")
def asset_derivative(
    record_path: Path = typer.Argument(..., exists=True, dir_okay=False),
    file: Path = typer.Argument(..., exists=True, dir_okay=False),
    parent_file_id: str = typer.Option(..., "--parent-file-id"),
    operation: str = typer.Option(..., "--operation"),
    output_record: Path = typer.Option(..., "--output-record", dir_okay=False),
    root: Path = typer.Option(Path("."), "--root", exists=True, file_okay=False),
    tool: str | None = typer.Option(None, "--tool"),
    parameters: str | None = typer.Option(None, "--parameters"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Register one externally produced derivative with parent/transformation provenance."""
    try:
        record = load_asset_record(record_path)
        updated = register_derivative(
            record,
            file,
            root=root,
            parent_file_id=parent_file_id,
            operation=operation,
            tool=tool,
            parameters=_parameters(parameters),
            notes=notes,
        )
        write_asset_record(updated, output_record)
    except AssetManifestError as exc:
        _fail(str(exc))
    typer.echo(f"wrote asset record with derivative: {output_record}")


@asset_app.command("manifest-build")
def asset_manifest_build(
    records_dir: Path = typer.Option(..., "--records-dir", exists=True, file_okay=False),
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Build a deterministic asset manifest from individual records."""
    try:
        records = load_asset_records_dir(records_dir)
        manifest = build_manifest(records)
        write_asset_manifest(manifest, output)
    except AssetManifestError as exc:
        _fail(str(exc))
    typer.echo(f"wrote asset manifest: {output} ({len(manifest.assets)} assets)")


@asset_app.command("inspect")
def asset_inspect(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Show high-level counts for an asset manifest."""
    try:
        manifest = load_asset_manifest(path)
    except AssetManifestError as exc:
        _fail(str(exc))
    file_count = sum(len(record.files) for record in manifest.assets)
    derivative_count = sum(
        1 for record in manifest.assets for item in record.files if item.role.value == "derivative"
    )
    typer.echo(f"assets: {len(manifest.assets)}")
    typer.echo(f"files: {file_count}")
    typer.echo(f"derivatives: {derivative_count}")


@asset_app.command("verify")
def asset_verify(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
    root: Path = typer.Option(Path("."), "--root", exists=True, file_okay=False),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Verify every registered local file against size and SHA-256."""
    try:
        manifest = load_asset_manifest(path)
        verification = verify_manifest(manifest, root)
    except AssetManifestError as exc:
        _fail(str(exc))
    if json_output:
        typer.echo(json.dumps(verification.model_dump(mode="json"), indent=2))
    else:
        for item in verification.files:
            state = "ok" if item.passed else "FAIL"
            typer.echo(f"{state}\t{item.asset_id}\t{item.file_id}\t{item.path}\t{item.message}")
    if not verification.passed:
        raise typer.Exit(code=1)


@asset_app.command("gate")
def asset_gate(
    path: Path = typer.Argument(..., exists=True, dir_okay=False),
    root: Path = typer.Option(Path("."), "--root", exists=True, file_okay=False),
    asset_id: str | None = typer.Option(None, "--asset-id"),
    json_output: bool = typer.Option(False, "--json"),
    require_approved: bool = typer.Option(False, "--require-approved"),
) -> None:
    """Evaluate rights, provenance and file integrity before public use."""
    try:
        manifest = load_asset_manifest(path)
        decisions = gate_manifest(manifest, root, asset_id=asset_id)
    except AssetManifestError as exc:
        _fail(str(exc))
    if json_output:
        payload = [decision.model_dump(mode="json") for decision in decisions]
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for decision in decisions:
            typer.echo(f"{decision.asset_id}\t{decision.status.value}")
            for check in decision.checks:
                if not check.passed:
                    typer.echo(f"  {check.severity.value}: {check.code}: {check.message}")
    if require_approved and any(
        decision.status is not PublicationStatus.APPROVED for decision in decisions
    ):
        raise typer.Exit(code=1)


@collect_app.command("source")
def collect_source(
    source_id: str = typer.Argument(..., help="Source id from config/sources.yaml."),
    url: str | None = typer.Option(None, "--url", help="Explicit public URL override."),
    output: Path | None = typer.Option(None, "--output", dir_okay=False),
    registry: Path | None = typer.Option(None, "--registry", exists=True, dir_okay=False),
    policy: Path | None = typer.Option(None, "--policy", exists=True, dir_okay=False),
    cache_dir: Path = typer.Option(Path(".pg-researcher/cache"), "--cache-dir"),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the local cache."),
) -> None:
    """Capture one registered public source as a validated Evidence object."""
    try:
        loaded = load_registry(registry)
        source = loaded.get(source_id)
        if source is None:
            _fail(f"unknown source id: {source_id}")
        if not source.enabled:
            _fail(f"source is disabled: {source_id}")
        fetch_policy = load_fetch_policy(policy)
        fetcher = HttpFetcher(policy=fetch_policy, cache=FileCache(cache_dir))
        collector = WebCollector(
            fetcher,
            subject=loaded.artist.canonical_name,
            primary_handle=loaded.artist.primary_handle,
        )
        evidence = collector.collect(source, url=url, refresh=refresh)
    except (RegistryError, FetchPolicyError, CollectorError) as exc:
        _fail(str(exc))

    rendered = json.dumps(evidence.model_dump(mode="json"), indent=2, ensure_ascii=False)
    if output is None:
        typer.echo(rendered)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    typer.echo(f"wrote evidence: {output}")


def main() -> None:
    app()
