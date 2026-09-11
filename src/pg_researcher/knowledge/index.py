from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from pg_researcher.knowledge.fingerprint import (
    canonical_json,
    claim_scope_key,
    claim_value_fingerprint,
    evidence_fingerprint,
    stable_digest,
)
from pg_researcher.models import (
    CatalogEntry,
    ClaimStatus,
    ConflictGroup,
    DedupGroup,
    Evidence,
    KnowledgeClaim,
    KnowledgeDomain,
    KnowledgeIndex,
    SourceClass,
    TimelineEntry,
)

_SOURCE_RANK = {
    SourceClass.OFFICIAL: 1,
    SourceClass.PLATFORM_PARTNER: 2,
    SourceClass.REPUTABLE_PRESS: 3,
    SourceClass.CATALOG_SECONDARY: 4,
    SourceClass.COMMUNITY: 5,
}

_CATALOG_DOMAINS = {
    KnowledgeDomain.CATALOG,
    KnowledgeDomain.RELEASE,
    KnowledgeDomain.TRACK,
    KnowledgeDomain.COLLABORATION,
    KnowledgeDomain.PRODUCTION,
}


class KnowledgeIndexError(ValueError):
    pass


def _canonical_evidence(
    records: list[Evidence],
) -> tuple[dict[str, str], list[DedupGroup]]:
    grouped: dict[str, list[Evidence]] = defaultdict(list)
    for evidence in records:
        grouped[evidence_fingerprint(evidence)].append(evidence)

    aliases: dict[str, str] = {}
    duplicate_groups: list[DedupGroup] = []
    for fingerprint, items in sorted(grouped.items()):
        ordered = sorted(
            items,
            key=lambda item: (
                _SOURCE_RANK[item.source_class],
                item.captured_at,
                item.evidence_id,
            ),
        )
        canonical = ordered[0]
        for item in ordered:
            aliases[item.evidence_id] = canonical.evidence_id
        if len(ordered) > 1:
            duplicate_groups.append(
                DedupGroup(
                    fingerprint=fingerprint,
                    canonical_evidence_id=canonical.evidence_id,
                    duplicate_evidence_ids=[item.evidence_id for item in ordered[1:]],
                )
            )
    return aliases, duplicate_groups


def _canonicalize_claim(
    claim: KnowledgeClaim,
    aliases: dict[str, str],
    known_evidence: set[str],
) -> KnowledgeClaim:
    referenced = [*claim.evidence_ids, *claim.contradicting_evidence_ids]
    missing = sorted(set(referenced) - known_evidence)
    if missing:
        raise KnowledgeIndexError(
            f"claim {claim.claim_id} references unknown evidence: {', '.join(missing)}"
        )

    support = sorted({aliases[evidence_id] for evidence_id in claim.evidence_ids})
    contradicting = sorted(
        {aliases[evidence_id] for evidence_id in claim.contradicting_evidence_ids}
    )
    return claim.model_copy(
        update={"evidence_ids": support, "contradicting_evidence_ids": contradicting}
    )


def _conflicts(claims: list[KnowledgeClaim]) -> tuple[list[ConflictGroup], set[str]]:
    scoped: dict[tuple[str, str, str, str], list[KnowledgeClaim]] = defaultdict(list)
    for claim in claims:
        if claim.status is ClaimStatus.RETRACTED:
            continue
        scoped[claim_scope_key(claim)].append(claim)

    conflicts: list[ConflictGroup] = []
    conflicted_claim_ids: set[str] = set()
    for scope, items in sorted(scoped.items()):
        values = {claim_value_fingerprint(item) for item in items}
        if len(values) <= 1:
            continue
        ordered = sorted(items, key=lambda item: item.claim_id)
        claim_ids = [item.claim_id for item in ordered]
        conflict_id = stable_digest(*claim_ids, prefix="conf")
        conflicts.append(
            ConflictGroup(
                conflict_id=conflict_id,
                subject=ordered[0].subject,
                predicate=ordered[0].predicate,
                temporal_scope={"effective_at": scope[2] or None, "effective_until": scope[3] or None},
                claim_ids=claim_ids,
                values=[canonical_json(item.value) for item in ordered],
            )
        )
        conflicted_claim_ids.update(claim_ids)
    return conflicts, conflicted_claim_ids


def build_knowledge_index(
    evidence: list[Evidence],
    claims: list[KnowledgeClaim],
    *,
    generated_at: datetime | None = None,
) -> KnowledgeIndex:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    if len(evidence_by_id) != len(evidence):
        raise KnowledgeIndexError("duplicate evidence_id values passed to index builder")
    claim_ids = {item.claim_id for item in claims}
    if len(claim_ids) != len(claims):
        raise KnowledgeIndexError("duplicate claim_id values passed to index builder")

    aliases, dedup_groups = _canonical_evidence(evidence)
    canonical_claims = [
        _canonicalize_claim(claim, aliases, set(evidence_by_id)) for claim in claims
    ]
    conflicts, conflicted_ids = _conflicts(canonical_claims)

    indexed_claims: list[KnowledgeClaim] = []
    for claim in canonical_claims:
        if claim.status is ClaimStatus.RETRACTED:
            status = ClaimStatus.RETRACTED
        elif claim.claim_id in conflicted_ids:
            status = ClaimStatus.CONFLICTED
        elif claim.evidence_ids:
            status = ClaimStatus.SUPPORTED
        else:
            status = ClaimStatus.OPEN
        indexed_claims.append(claim.model_copy(update={"status": status}))

    timeline = [
        TimelineEntry(
            claim_id=claim.claim_id,
            effective_at=claim.effective_at,
            effective_until=claim.effective_until,
            subject=claim.subject,
            predicate=claim.predicate,
            value=claim.value,
        )
        for claim in indexed_claims
        if claim.effective_at is not None and claim.status is not ClaimStatus.RETRACTED
    ]
    timeline.sort(key=lambda item: (item.effective_at, item.claim_id))

    catalog = [
        CatalogEntry(
            claim_id=claim.claim_id,
            domain=claim.domain,
            entity_id=claim.entity_id,
            subject=claim.subject,
            predicate=claim.predicate,
            value=claim.value,
        )
        for claim in indexed_claims
        if claim.domain in _CATALOG_DOMAINS and claim.status is not ClaimStatus.RETRACTED
    ]
    catalog.sort(key=lambda item: (item.domain.value, item.entity_id or "", item.claim_id))

    return KnowledgeIndex(
        version=1,
        generated_at=generated_at or datetime.now(UTC),
        evidence_count=len(evidence),
        canonical_evidence_count=len(set(aliases.values())),
        claim_count=len(indexed_claims),
        evidence_aliases=dict(sorted(aliases.items())),
        dedup_groups=dedup_groups,
        conflicts=conflicts,
        timeline=timeline,
        catalog=catalog,
        claims=sorted(indexed_claims, key=lambda item: item.claim_id),
    )
