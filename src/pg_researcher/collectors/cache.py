from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from pg_researcher.collectors.types import FetchSnapshot


class FileCache:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _path(self, url: str) -> Path:
        return self.directory / f"{self._key(url)}.json"

    def get(self, url: str, now: datetime, ttl_seconds: int) -> FetchSnapshot | None:
        if ttl_seconds <= 0:
            return None
        path = self._path(url)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            captured_at = datetime.fromisoformat(payload["captured_at"])
            age = (now - captured_at).total_seconds()
            if age < 0 or age > ttl_seconds:
                return None
            return FetchSnapshot(
                requested_url=payload["requested_url"],
                final_url=payload["final_url"],
                status_code=payload["status_code"],
                headers=payload["headers"],
                text=payload["text"],
                captured_at=captured_at,
                from_cache=True,
            )
        except (OSError, KeyError, TypeError, ValueError):
            return None

    def put(self, key_url: str, snapshot: FetchSnapshot) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(key_url)
        tmp = path.with_suffix(".tmp")
        payload = {
            "requested_url": snapshot.requested_url,
            "final_url": snapshot.final_url,
            "status_code": snapshot.status_code,
            "headers": snapshot.headers,
            "text": snapshot.text,
            "captured_at": snapshot.captured_at.isoformat(),
        }
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
