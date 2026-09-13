from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime

from pg_researcher.models import (
    AssetCandidate,
    ClaimStatus,
    EditorialLens,
    EditorialOpportunity,
    Evidence,
    Finding,
    KnowledgeClaim,
    KnowledgeIndex,
    ReportConflict,
    ReportPlan,
    ResearchReport,
    SourceLedgerEntry,
    StrategicImplication,
)


class ReportingError(ValueError):
    pass


def _render_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _finding_statement(claim: KnowledgeClaim) -> str:
    return f"{claim.subject} — {claim.predicate}: {_render_value(claim.value)}"


def _validate_plan(index: KnowledgeIndex, plan: ReportPlan) -> dict[str, KnowledgeClaim]:
    claims = {claim.claim_id: claim for claim in index.claims}
    requested = set(plan.finding_claim_ids)
    for bridge in plan.bridges:
        requested.update(bridge.claim_ids)

    missing = sorted(requested - claims.keys())
    if missing:
        raise ReportingError(f"report plan references unknown claims: {', '.join(missing)}")

    retracted = sorted(
        claim_id for claim_id in requested if claims[claim_id].status is ClaimStatus.RETRACTED
    )
    if retracted:
        raise ReportingError(f"report plan references retracted claims: {', '.join(retracted)}")

    bridge_ids = [bridge.bridge_id for bridge in plan.bridges]
    if len(bridge_ids) != len(set(bridge_ids)):
        raise ReportingError("report plan contains duplicate bridge_id values")

    return claims


def _used_claim_ids(plan: ReportPlan) -> list[str]:
    ids = set(plan.finding_claim_ids)
    for bridge in plan.bridges:
        ids.update(bridge.claim_ids)
    return sorted(ids)


def _conflict_context_claim_ids(index: KnowledgeIndex, selected_ids: set[str]) -> set[str]:
    related = set(selected_ids)
    for conflict in index.conflicts:
        if selected_ids.intersection(conflict.claim_ids):
            related.update(conflict.claim_ids)
    return related


def _claim_evidence(claim: KnowledgeClaim) -> tuple[set[str], set[str]]:
    return set(claim.evidence_ids), set(claim.contradicting_evidence_ids)


def _source_ledger(
    evidence: list[Evidence],
    claims: list[KnowledgeClaim],
) -> tuple[list[SourceLedgerEntry], list[str], list[AssetCandidate]]:
    evidence_by_id = {item.evidence_id: item for item in evidence}
    support: dict[str, set[str]] = defaultdict(set)
    contradict: dict[str, set[str]] = defaultdict(set)

    for claim in claims:
        supporting, contradicting = _claim_evidence(claim)
        for evidence_id in supporting:
            support[evidence_id].add(claim.claim_id)
        for evidence_id in contradicting:
            contradict[evidence_id].add(claim.claim_id)

    used_ids = sorted(set(support) | set(contradict))
    missing = sorted(set(used_ids) - evidence_by_id.keys())
    if missing:
        raise ReportingError(
            "knowledge index references evidence not supplied to reporting: " + ", ".join(missing)
        )

    ledger: list[SourceLedgerEntry] = []
    assets: list[AssetCandidate] = []
    for evidence_id in used_ids:
        item = evidence_by_id[evidence_id]
        ledger.append(
            SourceLedgerEntry(
                evidence_id=item.evidence_id,
                source_class=item.source_class,
                source_url=item.source_url,
                source_title=item.source_title,
                source_account=item.source_account,
                captured_at=item.captured_at,
                published_at=item.published_at,
                supports_claim_ids=sorted(support[evidence_id]),
                contradicts_claim_ids=sorted(contradict[evidence_id]),
            )
        )
        if item.asset is not None:
            assets.append(
                AssetCandidate(
                    evidence_id=item.evidence_id,
                    usage_basis=item.asset.usage_basis,
                    purpose=None,
                )
            )

    return ledger, used_ids, assets


def _report_conflicts(index: KnowledgeIndex, selected_ids: set[str]) -> list[ReportConflict]:
    claims_by_id = {claim.claim_id: claim for claim in index.claims}
    conflicts: list[ReportConflict] = []
    for conflict in index.conflicts:
        if not selected_ids.intersection(conflict.claim_ids):
            continue
        evidence_ids: set[str] = set()
        for claim_id in conflict.claim_ids:
            claim = claims_by_id.get(claim_id)
            if claim is None:
                continue
            evidence_ids.update(claim.evidence_ids)
            evidence_ids.update(claim.contradicting_evidence_ids)
        conflicts.append(
            ReportConflict(
                conflict_id=conflict.conflict_id,
                description=(
                    f"Conflicting values for {conflict.subject} / {conflict.predicate}; "
                    "no winner was selected automatically."
                ),
                claim_ids=sorted(conflict.claim_ids),
                evidence_ids=sorted(evidence_ids),
            )
        )
    return conflicts


def build_research_report(
    index: KnowledgeIndex,
    evidence: list[Evidence],
    plan: ReportPlan,
    *,
    generated_at: datetime | None = None,
) -> ResearchReport:
    claims_by_id = _validate_plan(index, plan)
    selected_ids = set(_used_claim_ids(plan))
    ledger_ids = _conflict_context_claim_ids(index, selected_ids)
    ledger_claims = [claims_by_id[claim_id] for claim_id in sorted(ledger_ids)]

    lenses_by_claim: dict[str, set[EditorialLens]] = defaultdict(set)
    for bridge in plan.bridges:
        for claim_id in bridge.claim_ids:
            lenses_by_claim[claim_id].add(bridge.editorial_lens)

    findings = [
        Finding(
            finding_id=f"pgf_{claim.claim_id.removeprefix('pgc_')}",
            claim_id=claim.claim_id,
            statement=_finding_statement(claim),
            epistemic_class=claim.epistemic_class,
            confidence=claim.confidence,
            status=claim.status,
            evidence_ids=claim.evidence_ids,
            contradicting_evidence_ids=claim.contradicting_evidence_ids,
            editorial_lenses=sorted(
                lenses_by_claim.get(claim.claim_id, set()),
                key=lambda item: item.value,
            ),
        )
        for claim in (claims_by_id[claim_id] for claim_id in plan.finding_claim_ids)
    ]

    ledger, evidence_ids, asset_candidates = _source_ledger(evidence, ledger_claims)

    strategic_implications = [
        StrategicImplication(
            bridge_id=bridge.bridge_id,
            claim_ids=sorted(bridge.claim_ids),
            statement=bridge.implication,
        )
        for bridge in plan.bridges
    ]
    editorial_opportunities = [
        EditorialOpportunity(
            bridge_id=bridge.bridge_id,
            claim_ids=sorted(bridge.claim_ids),
            editorial_format=bridge.editorial_format,
            editorial_lens=bridge.editorial_lens,
            concept=bridge.opportunity,
            objective=bridge.objective,
        )
        for bridge in plan.bridges
    ]

    return ResearchReport(
        report_id=plan.report_id,
        topic=plan.topic,
        generated_at=generated_at or datetime.now(UTC),
        scope=plan.scope,
        findings=findings,
        conflicts=_report_conflicts(index, selected_ids),
        source_ledger=ledger,
        strategic_implications=strategic_implications,
        editorial_opportunities=editorial_opportunities,
        asset_candidates=asset_candidates,
        open_questions=plan.open_questions,
        evidence_ids=evidence_ids,
    )
