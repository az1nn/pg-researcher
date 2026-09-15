from __future__ import annotations

import importlib.resources
from pathlib import Path

RESOURCE_MAP = {
    "config/fetch-policy.yaml": "resources/fetch-policy.yaml",
    "config/sources.yaml": "resources/sources.yaml",
    "schemas/claim.schema.json": "resources/claim.schema.json",
    "schemas/evidence.schema.json": "resources/evidence.schema.json",
    "schemas/knowledge-index.schema.json": "resources/knowledge-index.schema.json",
    "schemas/report-plan.schema.json": "resources/report-plan.schema.json",
    "schemas/research-report.schema.json": "resources/research-report.schema.json",
}


def find_repository_file(relative_path: str, start: Path | None = None) -> Path | None:
    start_path = (start or Path.cwd()).resolve()
    candidates = (start_path, *start_path.parents)
    for candidate in candidates:
        path = candidate / relative_path
        if path.is_file():
            return path
    return None


def read_text_resource(relative_path: str, explicit_path: Path | None = None) -> str:
    if explicit_path is not None:
        return explicit_path.read_text(encoding="utf-8")

    repository_path = find_repository_file(relative_path)
    if repository_path is not None:
        return repository_path.read_text(encoding="utf-8")

    packaged_path = RESOURCE_MAP.get(relative_path)
    if packaged_path is None:
        raise FileNotFoundError(f"No packaged resource mapping for {relative_path}")

    resource = importlib.resources.files("pg_researcher").joinpath(*packaged_path.split("/"))
    return resource.read_text(encoding="utf-8")
