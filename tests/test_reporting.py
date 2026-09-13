from datetime import UTC, datetime

import pytest

from pg_researcher.knowledge.index import build_knowledge_index
from pg_researcher.models import (
    ClaimStatus,
    Confidence,
    EditorialFormat,
    EditorialLens,
    EpistemicClass,
    Evidence,
    KnowledgeClaim,
    KnowledgeDomain,
    ReportBridgePlan,
    ReportPlan,
    SourceClass,
)
from pg_researcher.reporting.builder import ReportingError, build_research_report
from pg_researcher.reporting.render import render_markdown

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def _evidence(evidence_id: str = "pge_official") -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        subject="Prince' Gutt",
        source_class=SourceClass.OFFICIAL,
        source_url="https://x.com/princeguttreal",
        source_title="Prince' Gutt official X profile",
        source_account="princeguttreal",
        captured_at=NOW,
        content_type="profile",
        observation="Official Prince' Gutt profile.",
        identity_status="verified",
    )


def _claim(
    claim_id: str = "pgc_identity",
    *,
    value: str = "@princeguttreal",
    status: ClaimStatus = ClaimStatus.OPEN,
) -> KnowledgeClaim:
    return KnowledgeClaim(
        claim_id=claim_id,
        subject="Prince' Gutt",
        predicate="official_x_account",
        value=value,
        epistemic_class=EpistemicClass.FACT,
        confidence=Confidence.HIGH,
        status=status,
        evidence_ids=["pge_official"],
        domain=KnowledgeDomain.IDENTITY,
        entity_id="prince_gutt",
    )


def _plan(claim_id: str = "pgc_identity") -> ReportPlan:
    return ReportPlan(
        report_id="pgr_identity",
        topic="Prince' Gutt identity",
        finding_claim_ids=[claim_id],
        bridges=[
            ReportBridgePlan(
                bridge_id="pgb_identity",
                claim_ids=[claim_id],
                implication="First-party identity can anchor source discovery.",
                editorial_format=EditorialFormat.DIRECTORS_NOTE,
                editorial_lens=EditorialLens.IDENTITY,
                opportunity="Explain authorship from first-party identity signals.",
                objective="Strengthen recognizability.",
            )
        ],
        open_questions=["Which DSP profile URL is canonical?"],
    )


def test_report_builder_preserves_claim_boundary_and_source_ledger() -> None:
    evidence = _evidence()
    index = build_knowledge_index([evidence], [_claim()], generated_at=NOW)

    report = build_research_report(index, [evidence], _plan(), generated_at=NOW)

    assert report.findings[0].claim_id == "pgc_identity"
    assert report.findings[0].status is ClaimStatus.SUPPORTED
    assert report.findings[0].evidence_ids == ["pge_official"]
    assert report.source_ledger[0].supports_claim_ids == ["pgc_identity"]
    assert report.strategic_implications[0].claim_ids == ["pgc_identity"]
    assert report.editorial_opportunities[0].editorial_format is EditorialFormat.DIRECTORS_NOTE


def test_markdown_renderer_labels_strategy_as_separate_sections() -> None:
    evidence = _evidence()
    index = build_knowledge_index([evidence], [_claim()], generated_at=NOW)
    report = build_research_report(index, [evidence], _plan(), generated_at=NOW)

    rendered = render_markdown(report)

    assert "## Executive findings" in rendered
    assert "## Strategic implications" in rendered
    assert "## Editorial opportunities" in rendered
    assert "## Source ledger" in rendered
    assert "not automatically inferred facts" in rendered


def test_unknown_claim_fails_closed() -> None:
    evidence = _evidence()
    index = build_knowledge_index([evidence], [_claim()], generated_at=NOW)

    with pytest.raises(ReportingError, match="unknown claims"):
        build_research_report(index, [evidence], _plan("pgc_missing"), generated_at=NOW)


def test_retracted_claim_cannot_enter_report_plan() -> None:
    evidence = _evidence()
    claim = _claim(status=ClaimStatus.RETRACTED)
    index = build_knowledge_index([evidence], [claim], generated_at=NOW)

    with pytest.raises(ReportingError, match="retracted claims"):
        build_research_report(index, [evidence], _plan(), generated_at=NOW)
