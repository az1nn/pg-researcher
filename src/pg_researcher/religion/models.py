from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import AnyUrl, Field, model_validator

from pg_researcher.models import StrictModel


class ReligionSourceClass(StrEnum):
    PRIMARY_CANONICAL = "primary_canonical"
    ACADEMIC_CRITICAL = "academic_critical"
    TRADITION_COMMENTARY = "tradition_commentary"
    MODERN_ESOTERIC = "modern_esoteric"
    POPULAR_ORAL = "popular_oral"


class RightsStatus(StrEnum):
    PUBLIC_DOMAIN_TEXT = "public_domain_text"
    LICENSED_OR_AUTHORIZED = "licensed_or_authorized"
    QUOTATION_ONLY = "quotation_only"
    RESEARCH_ONLY = "research_only"
    UNKNOWN = "unknown"


class QuotePolicy(StrEnum):
    PUBLIC_DOMAIN_FULL_TEXT = "public_domain_full_text"
    AUTHORIZED_FULL_TEXT = "authorized_full_text"
    BRIEF_QUOTATION = "brief_quotation"
    RESEARCH_ONLY = "research_only"
    BLOCKED = "blocked"


class ParallelRelation(StrEnum):
    LEXICAL = "lexical"
    STRUCTURAL = "structural"
    HISTORICAL = "historical"
    INFLUENCE_CLAIM = "influence_claim"
    EDITORIAL = "editorial"


class DependencyStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNRESOLVED = "unresolved"
    NOT_CLAIMED = "not_claimed"


class ParallelStrength(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ManuscriptStatus(StrEnum):
    OUTLINE = "outline"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"


class SectionKind(StrEnum):
    SOURCE = "source"
    CONTEXT = "context"
    INTERPRETATION = "interpretation"
    CORRESPONDENCE = "correspondence"
    PG_EDITORIAL_SYNTHESIS = "pg_editorial_synthesis"
    PRACTICE = "practice"
    NOTES = "notes"


class ReligionSource(StrictModel):
    source_id: str = Field(pattern=r"^pgrs_[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1)
    creator: str | None = None
    source_class: ReligionSourceClass
    work_type: str = Field(min_length=1)
    language: str | None = None
    edition: str | None = None
    translator: str | None = None
    publisher: str | None = None
    published_at: datetime | None = None
    canonical_url: AnyUrl | None = None
    discovery_url: AnyUrl | None = None
    rights_status: RightsStatus
    zotero_item_key: str | None = None
    bibtex_key: str | None = None
    notes: str | None = None


class RightsRecord(StrictModel):
    rights_id: str = Field(pattern=r"^pgrr_[A-Za-z0-9_-]+$")
    source_id: str = Field(pattern=r"^pgrs_[A-Za-z0-9_-]+$")
    rights_status: RightsStatus
    basis: str = Field(min_length=1)
    quote_policy: QuotePolicy
    publication_allowed: bool
    jurisdiction: str | None = None
    verified_at: datetime | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def publication_gate(self) -> RightsRecord:
        blocked_statuses = {RightsStatus.RESEARCH_ONLY, RightsStatus.UNKNOWN}
        if self.rights_status in blocked_statuses and self.publication_allowed:
            raise ValueError("research_only/unknown rights cannot be publication_allowed")
        if self.rights_status is RightsStatus.UNKNOWN and self.quote_policy is not QuotePolicy.BLOCKED:
            raise ValueError("unknown rights must use quote_policy=blocked")
        return self


class ComparativeParallel(StrictModel):
    parallel_id: str = Field(pattern=r"^pgrp_[A-Za-z0-9_-]+$")
    concept: str = Field(min_length=1)
    left_claim_ids: list[str] = Field(min_length=1)
    right_claim_ids: list[str] = Field(min_length=1)
    relation_type: ParallelRelation
    strength: ParallelStrength
    historical_dependency_status: DependencyStatus = DependencyStatus.NOT_CLAIMED
    statement: str = Field(min_length=1)
    caveats: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def influence_gate(self) -> ComparativeParallel:
        if self.relation_type is ParallelRelation.INFLUENCE_CLAIM and self.historical_dependency_status in {
            DependencyStatus.NOT_CLAIMED,
            DependencyStatus.UNSUPPORTED,
        }:
            raise ValueError(
                "influence_claim requires historical dependency to be supported or unresolved"
            )
        return self


class ManuscriptSection(StrictModel):
    section_id: str = Field(pattern=r"^sec_[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1)
    kind: SectionKind
    purpose: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    parallel_ids: list[str] = Field(default_factory=list)


class Manuscript(StrictModel):
    manuscript_id: str = Field(pattern=r"^pgrm_[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    status: ManuscriptStatus = ManuscriptStatus.OUTLINE
    source_ids: list[str] = Field(min_length=1)
    sections: list[ManuscriptSection] = Field(min_length=1)
    source_ledger_complete: bool = False
    rights_ledger_complete: bool = False
    publication_ready: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def publication_gate(self) -> Manuscript:
        if self.publication_ready and not (
            self.source_ledger_complete and self.rights_ledger_complete
        ):
            raise ValueError(
                "publication_ready requires source_ledger_complete and rights_ledger_complete"
            )
        return self
