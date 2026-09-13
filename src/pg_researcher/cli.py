from __future__ import annotations

import json
from pathlib import Path

import typer

from pg_researcher import __version__
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
collect_app = typer.Typer(help="Capture controlled public-source evidence.")
app.add_typer(sources_app, name="sources")
app.add_typer(evidence_app, name="evidence")
app.add_typer(claim_app, name="claim")
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(report_app, name="report")
app.add_typer(collect_app, name="collect")


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


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
