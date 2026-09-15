from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from pg_researcher.assets.models import (
    AssetFileRecord,
    AssetFileRole,
    AssetFileVerification,
    AssetIdentityStatus,
    AssetManifest,
    AssetRecord,
    AssetTransformation,
    AssetType,
    ManifestVerification,
    RightsClass,
    UsageBasis,
)


class AssetManifestError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rooted_path(root: Path, path: Path) -> tuple[Path, str]:
    root_resolved = root.resolve()
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise AssetManifestError(f"asset file must stay inside root {root_resolved}: {resolved}") from exc
    return resolved, relative.as_posix()


def resolve_manifest_path(root: Path, stored_path: str) -> Path:
    path = Path(stored_path)
    if path.is_absolute():
        raise AssetManifestError(f"manifest paths must be relative: {stored_path}")
    root_resolved = root.resolve()
    resolved = (root_resolved / path).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise AssetManifestError(f"manifest path escapes root: {stored_path}") from exc
    return resolved


def _file_id(asset_id: str, digest: str) -> str:
    token = hashlib.sha256(f"{asset_id}|{digest}".encode()).hexdigest()[:20]
    return f"pgaf_{token}"


def _transformation_id(parent_file_id: str, digest: str, operation: str) -> str:
    token = hashlib.sha256(
        f"{parent_file_id}|{digest}|{operation.strip().lower()}".encode()
    ).hexdigest()[:20]
    return f"pgt_{token}"


def file_record_from_path(
    asset_id: str,
    path: Path,
    *,
    root: Path,
    role: AssetFileRole,
    media_type: str | None = None,
    parent_file_id: str | None = None,
    transformations: list[AssetTransformation] | None = None,
    acquired_from: str | None = None,
    created_at: datetime | None = None,
) -> AssetFileRecord:
    resolved, relative = _rooted_path(root, path)
    if not resolved.is_file():
        raise AssetManifestError(f"asset file does not exist: {resolved}")
    digest = sha256_file(resolved)
    detected_media_type = media_type or mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
    try:
        return AssetFileRecord(
            file_id=_file_id(asset_id, digest),
            role=role,
            path=relative,
            sha256=digest,
            size_bytes=resolved.stat().st_size,
            media_type=detected_media_type,
            parent_file_id=parent_file_id,
            transformations=transformations or [],
            acquired_from=acquired_from,
            created_at=created_at or datetime.now(UTC),
        )
    except ValidationError as exc:
        raise AssetManifestError(f"invalid asset file record: {exc}") from exc


def create_asset_record(
    *,
    asset_id: str,
    source_url: str,
    asset_type: AssetType,
    rights_class: RightsClass,
    usage_basis: UsageBasis,
    identity_status: AssetIdentityStatus,
    file_path: Path | None = None,
    root: Path = Path("."),
    media_type: str | None = None,
    final_url: str | None = None,
    source_account: str | None = None,
    evidence_id: str | None = None,
    creator: str | None = None,
    work_or_release: str | None = None,
    attribution_required: bool = False,
    attribution_text: str | None = None,
    restrictions: list[str] | None = None,
    notes: str | None = None,
    captured_at: datetime | None = None,
) -> AssetRecord:
    captured = captured_at or datetime.now(UTC)
    files: list[AssetFileRecord] = []
    if file_path is not None:
        files.append(
            file_record_from_path(
                asset_id,
                file_path,
                root=root,
                role=AssetFileRole.ORIGINAL,
                media_type=media_type,
                acquired_from=final_url,
                created_at=captured,
            )
        )
    try:
        record = AssetRecord(
            asset_id=asset_id,
            evidence_id=evidence_id,
            source_url=source_url,
            final_url=final_url,
            source_account=source_account,
            captured_at=captured,
            asset_type=asset_type,
            rights_class=rights_class,
            usage_basis=usage_basis,
            identity_status=identity_status,
            creator=creator,
            work_or_release=work_or_release,
            attribution_required=attribution_required,
            attribution_text=attribution_text,
            restrictions=restrictions or [],
            files=files,
            notes=notes,
        )
    except ValidationError as exc:
        raise AssetManifestError(f"invalid asset record: {exc}") from exc
    validate_asset_structure(record)
    return record


def register_derivative(
    record: AssetRecord,
    derivative_path: Path,
    *,
    root: Path,
    parent_file_id: str,
    operation: str,
    tool: str | None = None,
    parameters: dict[str, Any] | None = None,
    notes: str | None = None,
    media_type: str | None = None,
    created_at: datetime | None = None,
) -> AssetRecord:
    validate_asset_structure(record)
    parent = next((item for item in record.files if item.file_id == parent_file_id), None)
    if parent is None:
        raise AssetManifestError(f"unknown parent_file_id: {parent_file_id}")
    if not operation.strip():
        raise AssetManifestError("derivative operation must not be empty")

    resolved, _ = _rooted_path(root, derivative_path)
    if not resolved.is_file():
        raise AssetManifestError(f"derivative file does not exist: {resolved}")
    digest = sha256_file(resolved)
    created = created_at or datetime.now(UTC)
    transformation = AssetTransformation(
        transformation_id=_transformation_id(parent_file_id, digest, operation),
        operation=operation.strip(),
        tool=tool,
        parameters=parameters or {},
        notes=notes,
        created_at=created,
    )
    derivative = file_record_from_path(
        record.asset_id,
        derivative_path,
        root=root,
        role=AssetFileRole.DERIVATIVE,
        media_type=media_type,
        parent_file_id=parent_file_id,
        transformations=[transformation],
        created_at=created,
    )
    updated = record.model_copy(deep=True)
    updated.files.append(derivative)
    validate_asset_structure(updated)
    return updated


def validate_asset_structure(record: AssetRecord) -> None:
    ids = [item.file_id for item in record.files]
    if len(ids) != len(set(ids)):
        raise AssetManifestError(f"asset {record.asset_id} contains duplicate file_id values")
    paths = [item.path for item in record.files]
    if len(paths) != len(set(paths)):
        raise AssetManifestError(f"asset {record.asset_id} contains duplicate file paths")

    originals = [item for item in record.files if item.role is AssetFileRole.ORIGINAL]
    if record.files and len(originals) != 1:
        raise AssetManifestError(f"asset {record.asset_id} must contain exactly one original file")

    by_id = {item.file_id: item for item in record.files}
    for item in record.files:
        if item.role is AssetFileRole.ORIGINAL:
            if item.parent_file_id is not None or item.transformations:
                raise AssetManifestError(
                    f"original file {item.file_id} cannot declare parent/transformation history"
                )
            continue
        if item.parent_file_id is None:
            raise AssetManifestError(f"derivative {item.file_id} requires parent_file_id")
        if item.parent_file_id not in by_id:
            raise AssetManifestError(
                f"derivative {item.file_id} references unknown parent {item.parent_file_id}"
            )
        if item.parent_file_id == item.file_id:
            raise AssetManifestError(f"derivative {item.file_id} cannot parent itself")
        if not item.transformations:
            raise AssetManifestError(f"derivative {item.file_id} requires transformation history")

    for item in record.files:
        visited = {item.file_id}
        current = item
        while current.parent_file_id is not None:
            if current.parent_file_id in visited:
                raise AssetManifestError(f"asset {record.asset_id} contains a derivative cycle")
            visited.add(current.parent_file_id)
            current = by_id[current.parent_file_id]


def load_asset_record(path: Path) -> AssetRecord:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        record = AssetRecord.model_validate(payload)
        validate_asset_structure(record)
        return record
    except (OSError, json.JSONDecodeError, ValidationError, AssetManifestError) as exc:
        raise AssetManifestError(f"invalid asset record {path}: {exc}") from exc


def write_asset_record(record: AssetRecord, path: Path) -> None:
    validate_asset_structure(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False)
    path.write_text(rendered + "\n", encoding="utf-8")


def load_asset_records_dir(directory: Path) -> list[AssetRecord]:
    if not directory.is_dir():
        raise AssetManifestError(f"not a directory: {directory}")
    records = [load_asset_record(path) for path in sorted(directory.rglob("*.json"))]
    ids = [record.asset_id for record in records]
    if len(ids) != len(set(ids)):
        raise AssetManifestError("duplicate asset_id values in records directory")
    return records


def build_manifest(
    records: list[AssetRecord], *, generated_at: datetime | None = None
) -> AssetManifest:
    asset_ids = [record.asset_id for record in records]
    if len(asset_ids) != len(set(asset_ids)):
        raise AssetManifestError("duplicate asset_id values passed to manifest builder")

    file_ids: set[str] = set()
    for record in records:
        validate_asset_structure(record)
        for file_record in record.files:
            if file_record.file_id in file_ids:
                raise AssetManifestError(f"duplicate global file_id: {file_record.file_id}")
            file_ids.add(file_record.file_id)

    return AssetManifest(
        version=1,
        generated_at=generated_at or datetime.now(UTC),
        assets=sorted(records, key=lambda item: item.asset_id),
    )


def write_asset_manifest(manifest: AssetManifest, path: Path) -> None:
    for record in manifest.assets:
        validate_asset_structure(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False)
    path.write_text(rendered + "\n", encoding="utf-8")


def load_asset_manifest(path: Path) -> AssetManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = AssetManifest.model_validate(payload)
        build_manifest(manifest.assets, generated_at=manifest.generated_at)
        return manifest
    except (OSError, json.JSONDecodeError, ValidationError, AssetManifestError) as exc:
        raise AssetManifestError(f"invalid asset manifest {path}: {exc}") from exc


def verify_asset_record(record: AssetRecord, root: Path) -> list[AssetFileVerification]:
    results: list[AssetFileVerification] = []
    for file_record in record.files:
        try:
            path = resolve_manifest_path(root, file_record.path)
        except AssetManifestError as exc:
            results.append(
                AssetFileVerification(
                    asset_id=record.asset_id,
                    file_id=file_record.file_id,
                    path=file_record.path,
                    passed=False,
                    expected_sha256=file_record.sha256,
                    expected_size_bytes=file_record.size_bytes,
                    message=str(exc),
                )
            )
            continue
        if not path.is_file():
            results.append(
                AssetFileVerification(
                    asset_id=record.asset_id,
                    file_id=file_record.file_id,
                    path=file_record.path,
                    passed=False,
                    expected_sha256=file_record.sha256,
                    expected_size_bytes=file_record.size_bytes,
                    message="file is missing",
                )
            )
            continue
        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        passed = actual_size == file_record.size_bytes and actual_sha == file_record.sha256
        results.append(
            AssetFileVerification(
                asset_id=record.asset_id,
                file_id=file_record.file_id,
                path=file_record.path,
                passed=passed,
                expected_sha256=file_record.sha256,
                actual_sha256=actual_sha,
                expected_size_bytes=file_record.size_bytes,
                actual_size_bytes=actual_size,
                message="integrity verified" if passed else "size or sha256 mismatch",
            )
        )
    return results


def verify_manifest(manifest: AssetManifest, root: Path) -> ManifestVerification:
    results = [
        result
        for record in manifest.assets
        for result in verify_asset_record(record, root)
    ]
    return ManifestVerification(passed=all(item.passed for item in results), files=results)
