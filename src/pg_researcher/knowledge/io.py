from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from pg_researcher.models import Evidence, KnowledgeClaim, KnowledgeIndex

T = TypeVar("T", bound=BaseModel)


class KnowledgeIOError(ValueError):
    pass


def _load_directory(directory: Path, model: type[T], id_field: str) -> list[T]:
    if not directory.is_dir():
        raise KnowledgeIOError(f"not a directory: {directory}")

    records: list[T] = []
    seen: dict[str, Path] = {}
    for path in sorted(directory.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = model.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise KnowledgeIOError(f"invalid {model.__name__} file {path}: {exc}") from exc

        record_id = str(getattr(record, id_field))
        previous = seen.get(record_id)
        if previous is not None:
            raise KnowledgeIOError(
                f"duplicate {id_field} {record_id!r}: {previous} and {path}"
            )
        seen[record_id] = path
        records.append(record)
    return records


def load_evidence_dir(directory: Path) -> list[Evidence]:
    return _load_directory(directory, Evidence, "evidence_id")


def load_claim_dir(directory: Path) -> list[KnowledgeClaim]:
    return _load_directory(directory, KnowledgeClaim, "claim_id")


def write_knowledge_index(index: KnowledgeIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(index.model_dump(mode="json"), indent=2, ensure_ascii=False)
    path.write_text(rendered + "\n", encoding="utf-8")


def load_knowledge_index(path: Path) -> KnowledgeIndex:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return KnowledgeIndex.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise KnowledgeIOError(f"invalid knowledge index {path}: {exc}") from exc
