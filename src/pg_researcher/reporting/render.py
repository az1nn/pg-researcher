from __future__ import annotations

from pg_researcher.models import ResearchReport


def _bullet(lines: list[str], text: str) -> None:
    lines.append(f"- {text}")


def render_markdown(report: ResearchReport) -> str:
    lines = [f"# {report.topic}", ""]
    if report.scope:
        lines.extend([f"**Scope:** {report.scope}", ""])

    lines.extend(["## Executive findings", ""])
    if report.findings:
        for finding in report.findings:
            labels = (
                f"{finding.epistemic_class.value} / {finding.confidence.value} / "
                f"{finding.status.value}"
            )
            _bullet(lines, f"**{finding.claim_id}** — {finding.statement} _({labels})_")
    else:
        _bullet(lines, "No findings selected in the report plan.")
    lines.append("")

    if report.conflicts:
        lines.extend(["## Conflicts", ""])
        for conflict in report.conflicts:
            _bullet(lines, f"**{conflict.conflict_id}** — {conflict.description}")
            lines.append(f"  Claims: {', '.join(conflict.claim_ids)}")
        lines.append("")

    lines.extend(["## Strategic implications", ""])
    if report.strategic_implications:
        for implication in report.strategic_implications:
            _bullet(lines, f"**{implication.bridge_id}** — {implication.statement}")
            lines.append(f"  Claims: {', '.join(implication.claim_ids)}")
    else:
        _bullet(lines, "No strategic implications declared in the report plan.")
    lines.append("")

    lines.extend(["## Editorial opportunities", ""])
    if report.editorial_opportunities:
        for opportunity in report.editorial_opportunities:
            _bullet(
                lines,
                (
                    f"**{opportunity.editorial_format.value}** / "
                    f"{opportunity.editorial_lens.value} — {opportunity.concept}"
                ),
            )
            if opportunity.objective:
                lines.append(f"  Objective: {opportunity.objective}")
            lines.append(f"  Claims: {', '.join(opportunity.claim_ids)}")
    else:
        _bullet(lines, "No editorial opportunities declared in the report plan.")
    lines.append("")

    if report.asset_candidates:
        lines.extend(["## Asset candidates", ""])
        for asset in report.asset_candidates:
            purpose = f" — {asset.purpose}" if asset.purpose else ""
            _bullet(lines, f"{asset.evidence_id}: {asset.usage_basis}{purpose}")
        lines.append("")

    lines.extend(["## Source ledger", ""])
    if report.source_ledger:
        for source in report.source_ledger:
            title = source.source_title or source.source_account or source.evidence_id
            _bullet(
                lines,
                f"**{source.evidence_id}** — {title} ({source.source_class.value})",
            )
            lines.append(f"  URL: {source.source_url}")
            if source.supports_claim_ids:
                lines.append(f"  Supports: {', '.join(source.supports_claim_ids)}")
            if source.contradicts_claim_ids:
                lines.append(f"  Contradicts: {', '.join(source.contradicts_claim_ids)}")
    else:
        _bullet(lines, "No evidence referenced by this report.")
    lines.append("")

    lines.extend(["## Open questions", ""])
    if report.open_questions:
        for question in report.open_questions:
            _bullet(lines, question)
    else:
        _bullet(lines, "None declared.")
    lines.append("")

    lines.extend(
        [
            "---",
            "",
            (
                "Generated from explicit claims and evidence. Strategic implications and editorial "
                "opportunities are plan-authored decisions, not automatically inferred facts."
            ),
            "",
        ]
    )
    return "\n".join(lines)
