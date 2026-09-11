from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pg_researcher.models import Evidence, KnowledgeClaim

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip().casefold()


def canonical_json(value: Any) -> str:
    if isinstance(value, str):
        return normalize_text(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def stable_digest(*parts: str, prefix: str) -> str:
    material = "\n".join(parts).encode()
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:24]}"


def evidence_fingerprint(evidence: Evidence) -> str:
    return stable_digest(
        normalize_text(evidence.subject),
        normalize_text(evidence.observation),
        normalize_text(evidence.excerpt or ""),
        prefix="efp",
    )


def claim_scope_key(claim: KnowledgeClaim) -> tuple[str, str, str, str]:
    return (
        normalize_text(claim.subject),
        normalize_text(claim.predicate),
        claim.effective_at.isoformat() if claim.effective_at else "",
        claim.effective_until.isoformat() if claim.effective_until else "",
    )


def claim_value_fingerprint(claim: KnowledgeClaim) -> str:
    return stable_digest(canonical_json(claim.value), prefix="cvf")
