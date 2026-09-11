from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FetchSnapshot:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    text: str
    captured_at: datetime
    from_cache: bool = False
