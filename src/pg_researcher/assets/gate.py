from __future__ import annotations

from pathlib import Path

from pg_researcher.assets.manifest import AssetManifestError, validate_asset_structure, verify_asset_record
from pg_researcher.assets.models import (
    AssetIdentityStatus,
    AssetManifest,
    AssetRecord,
    CheckSeverity,
    PublicationCheck,
    PublicationDecision,
    PublicationStatus,
    RightsClass,
    UsageBasis,
)


def _check(code: str, passed: bool, severity: CheckSeverity, message: str) -> PublicationCheck:
    return PublicationCheck(code=code, passed=passed, severity=severity, message=message)


def evaluate_asset(record: AssetRecord, root: Path) -> PublicationDecision:
    checks: list[PublicationCheck] = []

    try:
        validate_asset_structure(record)
        checks.append(_check("structure", True, CheckSeverity.BLOCK, "asset structure is valid"))
    except AssetManifestError as exc:
        checks.append(_check("structure", False, CheckSeverity.BLOCK, str(exc)))

    if record.files:
        integrity = verify_asset_record(record, root)
        for result in integrity:
            checks.append(
                _check(
                    f"integrity:{result.file_id}",
                    result.passed,
                    CheckSeverity.BLOCK,
                    result.message,
                )
            )
    else:
        checks.append(
            _check(
                "files",
                False,
                CheckSeverity.REVIEW,
                "no local file is registered; record remains research-only",
            )
        )

    if record.identity_status is AssetIdentityStatus.VERIFIED:
        checks.append(_check("identity", True, CheckSeverity.BLOCK, "asset identity is verified"))
    elif record.identity_status is AssetIdentityStatus.MISMATCH:
        checks.append(_check("identity", False, CheckSeverity.BLOCK, "asset identity is a mismatch"))
    else:
        checks.append(
            _check(
                "identity",
                False,
                CheckSeverity.REVIEW,
                f"asset identity is {record.identity_status.value}",
            )
        )

    if record.usage_basis is UsageBasis.UNKNOWN:
        checks.append(_check("usage_basis", False, CheckSeverity.BLOCK, "usage basis is unknown"))
    elif record.usage_basis is UsageBasis.RESEARCH_REFERENCE:
        checks.append(
            _check(
                "usage_basis",
                False,
                CheckSeverity.REVIEW,
                "research-reference basis does not clear public reuse",
            )
        )
    else:
        checks.append(_check("usage_basis", True, CheckSeverity.BLOCK, "usage basis is explicit"))

    if record.rights_class is RightsClass.A:
        clear = record.usage_basis in {
            UsageBasis.ARTIST_AUTHORIZATION,
            UsageBasis.LICENSE,
            UsageBasis.PERMISSION,
        }
        checks.append(
            _check(
                "rights_clearance",
                clear,
                CheckSeverity.REVIEW,
                "artist-controlled asset has publication-capable basis"
                if clear
                else "class A asset lacks publication-capable basis",
            )
        )
    elif record.rights_class is RightsClass.B:
        checks.append(
            _check(
                "creator",
                bool(record.creator),
                CheckSeverity.BLOCK,
                "third-party creator is recorded"
                if record.creator
                else "class B asset requires creator attribution/provenance",
            )
        )
        clear = record.usage_basis in {UsageBasis.LICENSE, UsageBasis.PERMISSION}
        checks.append(
            _check(
                "rights_clearance",
                clear,
                CheckSeverity.REVIEW,
                "collaborator/commissioned work has explicit license or permission"
                if clear
                else "artist authorization alone does not clear collaborator rights",
            )
        )
    elif record.rights_class is RightsClass.C:
        clear = record.usage_basis in {UsageBasis.LICENSE, UsageBasis.PERMISSION}
        checks.append(
            _check(
                "rights_clearance",
                clear,
                CheckSeverity.REVIEW,
                "platform/interface material has explicit reuse clearance"
                if clear
                else "platform/interface material remains contextual research material",
            )
        )
    else:
        checks.append(
            _check(
                "creator",
                bool(record.creator),
                CheckSeverity.BLOCK,
                "press/editorial creator is recorded"
                if record.creator
                else "class D asset requires creator/source authorship",
            )
        )
        clear = record.usage_basis in {UsageBasis.LICENSE, UsageBasis.PERMISSION}
        checks.append(
            _check(
                "rights_clearance",
                clear,
                CheckSeverity.REVIEW,
                "press/editorial asset has explicit license or permission"
                if clear
                else "public availability does not clear press/editorial image reuse",
            )
        )

    if record.attribution_required:
        checks.append(
            _check(
                "attribution",
                bool(record.attribution_text),
                CheckSeverity.BLOCK,
                "required attribution is recorded"
                if record.attribution_text
                else "required attribution text is missing",
            )
        )
    else:
        checks.append(_check("attribution", True, CheckSeverity.BLOCK, "no attribution is required"))

    checks.append(
        _check(
            "restrictions",
            not record.restrictions,
            CheckSeverity.REVIEW,
            "no additional restrictions are recorded"
            if not record.restrictions
            else "additional restrictions require manual publication review",
        )
    )

    blocking_failure = any(
        not item.passed and item.severity is CheckSeverity.BLOCK for item in checks
    )
    review_failure = any(
        not item.passed and item.severity is CheckSeverity.REVIEW for item in checks
    )
    if blocking_failure:
        status = PublicationStatus.BLOCKED
    elif review_failure:
        status = PublicationStatus.RESEARCH_ONLY
    else:
        status = PublicationStatus.APPROVED
    return PublicationDecision(asset_id=record.asset_id, status=status, checks=checks)


def gate_manifest(
    manifest: AssetManifest, root: Path, *, asset_id: str | None = None
) -> list[PublicationDecision]:
    records = manifest.assets
    if asset_id is not None:
        records = [record for record in records if record.asset_id == asset_id]
        if not records:
            raise AssetManifestError(f"unknown asset_id: {asset_id}")
    return [evaluate_asset(record, root) for record in records]
