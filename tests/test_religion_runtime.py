from pathlib import Path

import pytest
from pydantic import ValidationError

from pg_researcher.religion.models import Manuscript, RightsRecord
from pg_researcher.validation import SchemaValidationError, validate_document, validate_file


def test_kickoff_video_source_example_is_valid() -> None:
    validate_file(Path("examples/religion/48-laws-video-source.json"), "religion_source")


def test_kickoff_video_rights_example_is_valid() -> None:
    validate_file(Path("examples/religion/48-laws-video-rights.json"), "religion_rights")


def test_unknown_rights_cannot_be_published_by_schema() -> None:
    with pytest.raises(SchemaValidationError, match="publication_allowed"):
        validate_document(
            {
                "rights_id": "pgrr_unknown",
                "source_id": "pgrs_unknown",
                "rights_status": "unknown",
                "basis": "Rights have not been verified.",
                "quote_policy": "blocked",
                "publication_allowed": True,
            },
            "religion_rights",
        )


def test_unknown_rights_must_be_blocked_by_typed_model() -> None:
    with pytest.raises(ValidationError, match="quote_policy=blocked"):
        RightsRecord.model_validate(
            {
                "rights_id": "pgrr_unknown",
                "source_id": "pgrs_unknown",
                "rights_status": "unknown",
                "basis": "Rights have not been verified.",
                "quote_policy": "research_only",
                "publication_allowed": False,
            }
        )


def test_publication_ready_manuscript_requires_both_ledgers() -> None:
    with pytest.raises(ValidationError, match="source_ledger_complete"):
        Manuscript.model_validate(
            {
                "manuscript_id": "pgrm_test",
                "title": "Test manuscript",
                "thesis": "A traceable thesis.",
                "status": "review",
                "source_ids": ["pgrs_source"],
                "sections": [
                    {
                        "section_id": "sec_intro",
                        "title": "Opening",
                        "kind": "context",
                        "purpose": "Establish context.",
                        "claim_ids": [],
                        "parallel_ids": [],
                    }
                ],
                "source_ledger_complete": True,
                "rights_ledger_complete": False,
                "publication_ready": True,
            }
        )


def test_influence_claim_requires_supported_or_unresolved_dependency() -> None:
    with pytest.raises(SchemaValidationError, match="historical_dependency_status"):
        validate_document(
            {
                "parallel_id": "pgrp_bad_influence",
                "concept": "number and cosmic order",
                "left_claim_ids": ["pgc_left"],
                "right_claim_ids": ["pgc_right"],
                "relation_type": "influence_claim",
                "strength": "medium",
                "historical_dependency_status": "not_claimed",
                "statement": "A prohibited unsupported influence claim.",
                "caveats": [],
            },
            "religion_parallel",
        )
