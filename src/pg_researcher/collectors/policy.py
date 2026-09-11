from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field, ValidationError

from pg_researcher.models import StrictModel
from pg_researcher.resources import read_text_resource


class FetchPolicy(StrictModel):
    version: int = Field(default=1, ge=1)
    user_agent: str = "pg-researcher/0.2"
    timeout_seconds: float = Field(default=15.0, gt=0)
    retries: int = Field(default=2, ge=0, le=5)
    retry_backoff_seconds: float = Field(default=0.5, ge=0)
    min_host_interval_seconds: float = Field(default=0.25, ge=0)
    cache_ttl_seconds: int = Field(default=21600, ge=0)
    max_response_bytes: int = Field(default=2_000_000, gt=0)
    allowed_content_types: list[str] = Field(
        default_factory=lambda: ["text/html", "text/plain", "application/json"]
    )


class FetchPolicyError(ValueError):
    pass


def load_fetch_policy(path: Path | None = None) -> FetchPolicy:
    try:
        raw = yaml.safe_load(read_text_resource("config/fetch-policy.yaml", path))
        return FetchPolicy.model_validate(raw)
    except (OSError, ValidationError, yaml.YAMLError) as exc:
        raise FetchPolicyError(f"invalid fetch policy: {exc}") from exc
