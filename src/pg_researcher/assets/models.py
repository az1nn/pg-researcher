from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class StrictAssetModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AssetType(StrEnum):
    PORTRAIT = "portrait"
    COVER = "cover"
    POST = "post"
    VIDEO_STILL = "video_still"
    SCREENSHOT = "screenshot"
    OTHER = "other"


class RightsClass(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class UsageBasis(StrEnum):
    ARTIST_AUTHORIZATION = "artist_authorization"
    LICENSE = "license"
    PERMISSION = "permission"
    RESEARCH_REFERENCE = "research_reference"
    UNKNOWN = "unknown"


class AssetIdentityStatus(StrEnum):
    VERIFIED = "verified"
    PROBABLE = "probable"
    UNRESOLVED = "unresolved"
    MISMATCH = "mismatch"


class AssetFileRole(StrEnum):
    ORIGINAL = "original"
    DERIVATIVE = "derivative"


class PublicationStatus(StrEnum):
    APPROVED = "approved"
    RESEARCH_ONLY = "research_only"
    BLOCKED = "blocked"


class CheckSeverity(StrEnum):
    BLOCK = "block"
    REVIEW = "review"


class AssetTransformation(StrictAssetModel):
    transformation_id: str = Field(pattern=r"^pgt_[A-Za-z0-9_-]+$")
    operation: str = Field(min_length=1)
    tool: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    created_at: datetime


class AssetFileRecord(StrictAssetModel):
    file_id: str = Field(pattern=r"^pgaf_[A-Za-z0-9_-]+$")
    role: AssetFileRole
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(ge=0)
    media_type: str = Field(min_length=1)
    parent_file_id: str | None = None
    transformations: list[AssetTransformation] = Field(default_factory=list)
    acquired_from: AnyUrl | None = None
    created_at: datetime


class AssetRecord(StrictAssetModel):
    asset_id: str = Field(pattern=r"^pga_[A-Za-z0-9_-]+$")
    evidence_id: str | None = None
    source_url: AnyUrl
    final_url: AnyUrl | None = None
    source_account: str | None = None
    captured_at: datetime
    asset_type: AssetType
    rights_class: RightsClass
    usage_basis: UsageBasis
    identity_status: AssetIdentityStatus = AssetIdentityStatus.UNRESOLVED
    creator: str | None = None
    work_or_release: str | None = None
    attribution_required: bool = False
    attribution_text: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    files: list[AssetFileRecord] = Field(default_factory=list)
    notes: str | None = None


class AssetManifest(StrictAssetModel):
    version: int = Field(ge=1)
    generated_at: datetime
    assets: list[AssetRecord]


class AssetFileVerification(StrictAssetModel):
    asset_id: str
    file_id: str
    path: str
    passed: bool
    expected_sha256: str
    actual_sha256: str | None = None
    expected_size_bytes: int
    actual_size_bytes: int | None = None
    message: str


class ManifestVerification(StrictAssetModel):
    passed: bool
    files: list[AssetFileVerification]


class PublicationCheck(StrictAssetModel):
    code: str
    passed: bool
    severity: CheckSeverity
    message: str


class PublicationDecision(StrictAssetModel):
    asset_id: str
    status: PublicationStatus
    checks: list[PublicationCheck]
