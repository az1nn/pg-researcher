from pathlib import Path

import pytest

from pg_researcher.models import SourceClass
from pg_researcher.registry import RegistryError, load_registry


def test_loads_seed_registry() -> None:
    registry = load_registry()

    assert registry.artist.canonical_name == "Prince' Gutt"
    assert registry.get("x_princeguttreal") is not None
    assert registry.source_classes[SourceClass.OFFICIAL].tier == 1
    assert all(source.enabled for source in registry.enabled_sources())


def test_rejects_duplicate_source_ids(tmp_path: Path) -> None:
    registry = tmp_path / "sources.yaml"
    registry.write_text(
        """
version: 1
artist:
  canonical_name: "Prince' Gutt"
  primary_handle: princeguttreal
source_classes:
  official:
    tier: 1
    default_confidence: high
sources:
  - id: duplicate
    class: official
    platform: x
    canonical_url: https://x.com/princeguttreal
    identity_status: verified
  - id: duplicate
    class: official
    platform: instagram
    canonical_url: https://instagram.com/princeguttreal
    identity_status: verified
rules: {}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(RegistryError, match="duplicate source ids"):
        load_registry(registry)
