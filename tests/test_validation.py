from pathlib import Path

import pytest

from pg_researcher.validation import SchemaValidationError, validate_document, validate_file


def test_valid_evidence_example() -> None:
    validate_file(Path("examples/evidence/minimal.json"), "evidence")


def test_valid_report_example() -> None:
    validate_file(Path("examples/reports/minimal.json"), "report")


def test_evidence_requires_provenance() -> None:
    with pytest.raises(SchemaValidationError, match="source_url"):
        validate_document(
            {
                "evidence_id": "pge_missing_url",
                "subject": "Prince' Gutt",
                "source_class": "official",
                "captured_at": "2026-09-11T18:00:00Z",
                "content_type": "profile",
                "observation": "Official profile observation",
                "identity_status": "verified",
            },
            "evidence",
        )
