from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from pg_researcher.assets.acquire import AssetAcquireError, AssetAcquirer
from pg_researcher.assets.gate import evaluate_asset
from pg_researcher.assets.manifest import (
    AssetManifestError,
    build_manifest,
    create_asset_record,
    register_derivative,
    verify_manifest,
)
from pg_researcher.assets.models import (
    AssetIdentityStatus,
    AssetType,
    PublicationStatus,
    RightsClass,
    UsageBasis,
)
from pg_researcher.assets.policy import AssetFetchPolicy

NOW = datetime(2026, 9, 15, 11, 30, tzinfo=UTC)


def _record(
    root: Path,
    *,
    rights_class: RightsClass = RightsClass.A,
    usage_basis: UsageBasis = UsageBasis.ARTIST_AUTHORIZATION,
):
    source = root / "assets" / "portrait.jpg"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"artist-owned-image")
    return create_asset_record(
        asset_id="pga_portrait",
        source_url="https://example.com/portrait.jpg",
        asset_type=AssetType.PORTRAIT,
        rights_class=rights_class,
        usage_basis=usage_basis,
        identity_status=AssetIdentityStatus.VERIFIED,
        file_path=source,
        root=root,
        creator="Photographer" if rights_class in {RightsClass.B, RightsClass.D} else None,
        captured_at=NOW,
    )


def test_artist_authorized_verified_intact_asset_is_approved(tmp_path: Path) -> None:
    record = _record(tmp_path)
    decision = evaluate_asset(record, tmp_path)
    assert decision.status is PublicationStatus.APPROVED


def test_tampered_file_blocks_publication(tmp_path: Path) -> None:
    record = _record(tmp_path)
    (tmp_path / record.files[0].path).write_bytes(b"tampered")
    decision = evaluate_asset(record, tmp_path)
    assert decision.status is PublicationStatus.BLOCKED
    assert any(
        check.code.startswith("integrity:") and not check.passed
        for check in decision.checks
    )


def test_unknown_usage_basis_blocks_publication(tmp_path: Path) -> None:
    record = _record(tmp_path, usage_basis=UsageBasis.UNKNOWN)
    assert evaluate_asset(record, tmp_path).status is PublicationStatus.BLOCKED


def test_third_party_artist_authorization_is_research_only(tmp_path: Path) -> None:
    record = _record(tmp_path, rights_class=RightsClass.B)
    assert evaluate_asset(record, tmp_path).status is PublicationStatus.RESEARCH_ONLY


def test_derivative_preserves_parent_and_transformation_history(tmp_path: Path) -> None:
    record = _record(tmp_path)
    derivative = tmp_path / "assets" / "portrait-crop.jpg"
    derivative.write_bytes(b"artist-owned-image-cropped")
    updated = register_derivative(
        record,
        derivative,
        root=tmp_path,
        parent_file_id=record.files[0].file_id,
        operation="crop",
        tool="image-workflow",
        parameters={"aspect_ratio": "4:5"},
        created_at=NOW,
    )
    assert len(updated.files) == 2
    assert updated.files[1].parent_file_id == updated.files[0].file_id
    assert updated.files[1].transformations[0].operation == "crop"


def test_manifest_rejects_duplicate_asset_ids(tmp_path: Path) -> None:
    record = _record(tmp_path)
    with pytest.raises(AssetManifestError, match="duplicate asset_id"):
        build_manifest([record, record], generated_at=NOW)


def test_manifest_verification_detects_integrity(tmp_path: Path) -> None:
    record = _record(tmp_path)
    manifest = build_manifest([record], generated_at=NOW)
    verification = verify_manifest(manifest, tmp_path)
    assert verification.passed is True
    assert verification.files[0].actual_sha256 == record.files[0].sha256


def test_asset_acquisition_accepts_allowed_image(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "image/jpeg"},
            content=b"image-bytes",
            request=request,
        )

    policy = AssetFetchPolicy(
        version=1,
        user_agent="test",
        timeout_seconds=1,
        retries=0,
        retry_backoff_seconds=0,
        min_host_interval_seconds=0,
        max_response_bytes=100,
        allowed_content_types=["image/jpeg"],
    )
    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    output = tmp_path / "image.jpg"
    result = AssetAcquirer(policy=policy, client=client).acquire(
        "https://example.com/image.jpg", output
    )
    assert output.read_bytes() == b"image-bytes"
    assert result.media_type == "image/jpeg"
    assert len(result.sha256) == 64


def test_asset_acquisition_rejects_unsupported_content_type(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"not an image",
            request=request,
        )

    policy = AssetFetchPolicy(
        version=1,
        user_agent="test",
        timeout_seconds=1,
        retries=0,
        retry_backoff_seconds=0,
        min_host_interval_seconds=0,
        max_response_bytes=100,
        allowed_content_types=["image/jpeg"],
    )
    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    with pytest.raises(AssetAcquireError, match="unsupported asset content type"):
        AssetAcquirer(policy=policy, client=client).acquire(
            "https://example.com/page", tmp_path / "bad.jpg"
        )
