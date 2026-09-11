from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator, FormatChecker

from pg_researcher.resources import read_text_resource

SchemaKind = Literal["evidence", "report"]

_SCHEMA_FILES: dict[SchemaKind, str] = {
    "evidence": "schemas/evidence.schema.json",
    "report": "schemas/research-report.schema.json",
}


class SchemaValidationError(ValueError):
    """Raised when a document violates a pg-researcher JSON Schema contract."""


def load_schema(kind: SchemaKind, path: Path | None = None) -> dict[str, Any]:
    relative_path = _SCHEMA_FILES[kind]
    try:
        raw = json.loads(read_text_resource(relative_path, path))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"Unable to read {kind} schema: {exc}") from exc

    Draft202012Validator.check_schema(raw)
    return raw


def load_json_document(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(f"Unable to read JSON document {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise SchemaValidationError(f"JSON document {path} must contain an object at its root")
    return raw


def validate_document(
    document: dict[str, Any],
    kind: SchemaKind,
    *,
    schema_path: Path | None = None,
) -> None:
    validator = Draft202012Validator(load_schema(kind, schema_path), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if not errors:
        return

    rendered: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{location}: {error.message}")
    raise SchemaValidationError("Schema validation failed:\n- " + "\n- ".join(rendered))


def validate_file(path: Path, kind: SchemaKind, *, schema_path: Path | None = None) -> None:
    validate_document(load_json_document(path), kind, schema_path=schema_path)
