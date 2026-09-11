from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from pg_researcher.models import SourceRegistry
from pg_researcher.resources import read_text_resource


class RegistryError(ValueError):
    """Raised when the curated source registry cannot be parsed or validated."""


def load_registry(path: Path | None = None) -> SourceRegistry:
    try:
        raw = yaml.safe_load(read_text_resource("config/sources.yaml", path))
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError(f"Unable to read source registry: {exc}") from exc

    if not isinstance(raw, dict):
        raise RegistryError("Source registry root must be a mapping")

    try:
        registry = SourceRegistry.model_validate(raw)
    except ValidationError as exc:
        raise RegistryError(f"Invalid source registry:\n{exc}") from exc

    source_ids = [source.id for source in registry.sources]
    if len(source_ids) != len(set(source_ids)):
        raise RegistryError("Source registry contains duplicate source ids")

    missing_classes = {source.source_class for source in registry.sources} - set(
        registry.source_classes
    )
    if missing_classes:
        values = ", ".join(sorted(source_class.value for source_class in missing_classes))
        raise RegistryError(f"Source classes missing configuration: {values}")

    return registry
