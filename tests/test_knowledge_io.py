import json

import pytest

from pg_researcher.knowledge.io import KnowledgeIOError, load_claim_dir


def test_claim_loader_rejects_duplicate_ids(tmp_path) -> None:
    claims = tmp_path / "claims"
    claims.mkdir()
    payload = {
        "claim_id": "pgc_dup",
        "subject": "Prince' Gutt",
        "predicate": "demo",
        "value": "x",
        "epistemic_class": "fact",
        "confidence": "high",
        "evidence_ids": ["pge_demo"],
    }
    (claims / "a.json").write_text(json.dumps(payload), encoding="utf-8")
    (claims / "b.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(KnowledgeIOError, match="duplicate claim_id"):
        load_claim_dir(claims)
