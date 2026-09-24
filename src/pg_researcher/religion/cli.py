from __future__ import annotations

from pathlib import Path

import typer

from pg_researcher.validation import SchemaValidationError, validate_file

app = typer.Typer(
    name="pg-religion",
    help="Validation tooling for PG RELIGION RESEARCH corpus artifacts.",
    no_args_is_help=True,
)


def _validate(path: Path, kind: str, label: str) -> None:
    try:
        validate_file(path, kind)  # type: ignore[arg-type]
    except SchemaValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"valid {label}: {path}")


@app.command("source-validate")
def source_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one religion-source record."""
    _validate(path, "religion_source", "religion source")


@app.command("rights-validate")
def rights_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one rights/publication record."""
    _validate(path, "religion_rights", "rights record")


@app.command("parallel-validate")
def parallel_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one comparative-parallel record."""
    _validate(path, "religion_parallel", "comparative parallel")


@app.command("manuscript-validate")
def manuscript_validate(path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Validate one e-book manuscript contract."""
    _validate(path, "religion_manuscript", "manuscript")


def main() -> None:
    app()
