from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceClass(StrEnum):
    OFFICIAL = "official"
    PLATFORM_PARTNER = "platform_partner"
    REPUTABLE_PRESS = "reputable_press"
    CATALOG_SECONDARY = "catalog_secondary"
    COMMUNITY = "community"


class EpistemicClass(StrEnum):
    FACT = "fact"
    INFERENCE = "inference"
    EDITORIAL_HYPOTHESIS = "editorial_hypothesis"


class ClaimStatus(StrEnum):
    OPEN = "open"
    SUPPORTED = "supported"
    CONFLICTED = "conflicted"
    RETRACTED = "retracted"


class KnowledgeDomain(StrEnum):
    IDENTITY = "identity"
    CATALOG = "catalog"
    RELEASE = "release"
    TRACK = "track"
    COLLABORATION = "collaboration"
    PRODUCTION = "production"
    TERRITORY = "territory"
    BUSINESS = "business"
    COMMUNITY = "community"
    OTHER = "other"


class ArtistConfig(StrictModel):
    canonical_name: str
    primary_handle: str


class SourceClassConfig(StrictModel):
    tier: int = Field(ge=1)
    default_confidence: Confidence


class SourceConfig(StrictModel):
    id: str
    source_class: SourceClass = Field(alias="class")
    platform: str
    canonical_url: AnyUrl | None = None
    discovery_query: str | None = None
    identity_status: str
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)


class RegistryRules(StrictModel):
    require_provenance: bool = True
    preserve_conflicts: bool = True
    syndicated_sources_count_once: bool = True
    community_sources_can_verify_identity: bool = False
    community_sources_can_close_material_claim: bool = False
    canonicalize_tracking_urls: bool = True


class SourceRegistry(StrictModel):
    version: int = Field(ge=1)
    artist: ArtistConfig
    source_classes: dict[SourceClass, SourceClassConfig]
    sources: list[SourceConfig]
    rules: RegistryRules

    def enabled_sources(self) -> list[SourceConfig]:
        return [source for source in self.sources if source.enabled]

    def get(self, source_id: str) -> SourceConfig | None:
        return next((source for source in self.sources if source.id == source_id), None)


class AssetMetadata(StrictModel):
    asset_type: Literal["portrait", "cover", "post", "video_still", "screenshot", "other"]
    rights_class: Literal["A", "B", "C", "D"]
    usage_basis: Literal[
        "artist_authorization", "license", "permission", "research_reference", "unknown"
    ]
    creator: str | None = None
    transformation_notes: str | None = None


class Evidence(StrictModel):
    evidence_id: str
    subject: str
    source_id: str | None = None
    source_class: SourceClass
    source_url: AnyUrl
    source_title: str | None = None
    source_account: str | None = None
    captured_at: datetime
    published_at: datetime | None = None
    content_type: Literal[
        "profile",
        "post",
        "article",
        "release",
        "track",
        "video",
        "image",
        "interview",
        "document",
        "other",
    ]
    observation: str
    excerpt: str | None = None
    identity_status: Literal["verified", "probable", "unresolved", "mismatch"]
    asset: AssetMetadata | None = None
    notes: str | None = None


class KnowledgeClaim(StrictModel):
    claim_id: str = Field(pattern=r"^pgc_[A-Za-z0-9_-]+$")
    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: Any
    epistemic_class: EpistemicClass
    confidence: Confidence
    status: ClaimStatus = ClaimStatus.OPEN
    evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    effective_at: datetime | None = None
    effective_until: datetime | None = None
    domain: KnowledgeDomain = KnowledgeDomain.OTHER
    entity_id: str | None = None
    notes: str | None = None


class DedupGroup(StrictModel):
    fingerprint: str
    canonical_evidence_id: str
    duplicate_evidence_ids: list[str]


class ConflictGroup(StrictModel):
    conflict_id: str
    subject: str
    predicate: str
    temporal_scope: dict[str, str | None]
    claim_ids: list[str]
    values: list[str]


class TimelineEntry(StrictModel):
    claim_id: str
    effective_at: datetime
    effective_until: datetime | None = None
    subject: str
    predicate: str
    value: Any


class CatalogEntry(StrictModel):
    claim_id: str
    domain: KnowledgeDomain
    entity_id: str | None = None
    subject: str
    predicate: str
    value: Any


class KnowledgeIndex(StrictModel):
    version: int = Field(ge=1)
    generated_at: datetime
    evidence_count: int = Field(ge=0)
    canonical_evidence_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    evidence_aliases: dict[str, str]
    dedup_groups: list[DedupGroup]
    conflicts: list[ConflictGroup]
    timeline: list[TimelineEntry]
    catalog: list[CatalogEntry]
    claims: list[KnowledgeClaim]


class Finding(StrictModel):
    finding_id: str
    statement: str
    epistemic_class: EpistemicClass
    confidence: Confidence
    evidence_ids: list[str]
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    editorial_lenses: list[str] = Field(default_factory=list)


class ResearchReport(StrictModel):
    report_id: str
    topic: str
    generated_at: datetime
    scope: str | None = None
    findings: list[Finding]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    asset_candidates: list[dict[str, Any]] = Field(default_factory=list)
    open_questions: list[str]
    evidence_ids: list[str]
