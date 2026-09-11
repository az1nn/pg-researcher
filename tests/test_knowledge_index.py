from datetime import UTC, datetime

from pg_researcher.knowledge.index import build_knowledge_index
from pg_researcher.models import (
    ClaimStatus,
    Confidence,
    EpistemicClass,
    Evidence,
    KnowledgeClaim,
    KnowledgeDomain,
    SourceClass,
)

NOW = datetime(2026, 9, 11, 18, 0, tzinfo=UTC)


def _evidence(evidence_id: str, source_class: SourceClass) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        subject="Prince' Gutt",
        source_class=source_class,
        source_url=f"https://example.com/{evidence_id}",
        captured_at=NOW,
        content_type="profile",
        observation="Prince' Gutt official profile",
        excerpt="Prince Gutt",
        identity_status="verified",
    )


def _claim(claim_id: str, value: str, evidence_ids: list[str]) -> KnowledgeClaim:
    return KnowledgeClaim(
        claim_id=claim_id,
        subject="Prince' Gutt",
        predicate="release_date",
        value=value,
        epistemic_class=EpistemicClass.FACT,
        confidence=Confidence.HIGH,
        evidence_ids=evidence_ids,
        effective_at=NOW,
        domain=KnowledgeDomain.RELEASE,
        entity_id="release_demo",
    )


def test_dedup_prefers_higher_authority_and_collapses_claim_refs() -> None:
    official = _evidence("pge_official", SourceClass.OFFICIAL)
    press = _evidence("pge_press", SourceClass.REPUTABLE_PRESS)
    claim = _claim("pgc_release", "2026-09-11", [press.evidence_id, official.evidence_id])

    index = build_knowledge_index([press, official], [claim], generated_at=NOW)

    assert index.canonical_evidence_count == 1
    assert index.evidence_aliases[press.evidence_id] == official.evidence_id
    assert index.claims[0].evidence_ids == [official.evidence_id]
    assert index.claims[0].status is ClaimStatus.SUPPORTED


def test_conflicts_timeline_and_catalog_are_explicit() -> None:
    evidence = _evidence("pge_one", SourceClass.OFFICIAL)
    first = _claim("pgc_a", "2026-09-11", [evidence.evidence_id])
    second = _claim("pgc_b", "2026-09-12", [evidence.evidence_id])

    index = build_knowledge_index([evidence], [second, first], generated_at=NOW)

    assert len(index.conflicts) == 1
    assert index.conflicts[0].claim_ids == ["pgc_a", "pgc_b"]
    assert {claim.status for claim in index.claims} == {ClaimStatus.CONFLICTED}
    assert [item.claim_id for item in index.timeline] == ["pgc_a", "pgc_b"]
    assert [item.claim_id for item in index.catalog] == ["pgc_a", "pgc_b"]
