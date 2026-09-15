from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from pg_researcher.resources import read_text_resource


class AssetPolicyError(ValueError):
    pass


class AssetFetchPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    user_agent: str = Field(min_length=1)
    timeout_seconds: float = Field(gt=0)
    retries: int = Field(ge=0, le=5)
    retry_backoff_seconds: float = Field(ge=0)
    min_host_interval_seconds: float = Field(ge=0)
    max_response_bytes: int = Field(gt=0)
    allowed_content_types: list[str] = Field(min_length=1)


def load_asset_policy(path: Path | None = None) -> AssetFetchPolicy:
    try:
        raw = yaml.safe_load(read_text_resource("config/asset-policy.yaml", path))
        if not isinstance(raw, dict):
            raise AssetPolicyError("asset policy root must be a mapping")
        return AssetFetchPolicy.model_validate(raw)
    except (OSError, ValidationError, yaml.YAMLError) as exc:
        raise AssetPolicyError(f"unable to load asset policy: {exc}") from exc
