from __future__ import annotations

import json
from pathlib import Path

import typer

from pg_researcher import __version__
from pg_researcher.collectors.cache import FileCache
from pg_researcher.collectors.http import HttpFetcher
from pg_researcher.collectors.policy import FetchPolicyError, load_fetch_policy
from pg_researcher.collectors.web import CollectorError, WebCollector
from pg_researcher.registry import RegistryError, load_registry
from pg_researcher.validation import SchemaValidationError, validate_file

app = typer.Typer(
    name="pg-researcher",
    help="Evidence-first research tooling for Prince' Gutt.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="Inspect and validate the curated source registry.")
evidence_app = typer.Typer(help="Validate evidence artifacts.")
report_app = typer.Typer(help="Validate research-report artifacts.")
collect_app = typer.Typer(help="Capture controlled public-source evidence.")
app.add_typer(sources_app, name="sources")
app.add_typer(evidence_app, name="evidence")
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


@report_app.command("validate")
def report_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one research report JSON document against the canonical schema."""
    try:
        validate_file(path, "report")
    except SchemaValidationError as exc:
        _fail(str(exc))
    typer.echo(f"valid report: {path}")


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
