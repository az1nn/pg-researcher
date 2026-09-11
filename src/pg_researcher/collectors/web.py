from __future__ import annotations

import hashlib
from typing import Literal

from pg_researcher.collectors.http import FetchError, HttpFetcher
from pg_researcher.collectors.normalize import excerpt, infer_content_type, parse_html
from pg_researcher.models import Evidence, SourceConfig


class CollectorError(RuntimeError):
    pass


def _identity_status(value: str) -> Literal["verified", "probable", "unresolved", "mismatch"]:
    lowered = value.lower()
    if "mismatch" in lowered:
        return "mismatch"
    if "verified" in lowered and "pending" not in lowered:
        return "verified"
    if "confirmed" in lowered or "probable" in lowered or "pending" in lowered:
        return "probable"
    return "unresolved"


def _evidence_id(source_id: str, final_url: str, text: str) -> str:
    material = f"{source_id}\n{final_url}\n{text}".encode()
    digest = hashlib.sha256(material).hexdigest()[:24]
    return f"pge_{digest}"


class WebCollector:
    def __init__(self, fetcher: HttpFetcher, *, subject: str, primary_handle: str) -> None:
        self.fetcher = fetcher
        self.subject = subject
        self.primary_handle = primary_handle

    def collect(
        self,
        source: SourceConfig,
        *,
        url: str | None = None,
        refresh: bool = False,
    ) -> Evidence:
        target = url or (str(source.canonical_url) if source.canonical_url else None)
        if target is None:
            raise CollectorError(
                f"source {source.id} has no canonical URL yet; provide an explicit --url"
            )

        try:
            snapshot = self.fetcher.fetch(target, refresh=refresh)
        except (FetchError, ValueError) as exc:
            raise CollectorError(str(exc)) from exc

        media_type = snapshot.headers.get("content-type", "").split(";", 1)[0].lower()
        title: str | None = None
        description: str | None = None
        page_text = snapshot.text
        if media_type == "text/html" or "<html" in snapshot.text[:500].lower():
            parsed = parse_html(snapshot.text)
            title = parsed.title
            description = parsed.description
            page_text = parsed.text

        body_excerpt = excerpt(page_text)
        summary_parts = [f"Captured public page from {source.platform}."]
        if title:
            summary_parts.append(f"Page title: {title}.")
        if description:
            summary_parts.append(f"Page metadata summary: {description}")

        notes = (
            f"collector=web; from_cache={str(snapshot.from_cache).lower()}; "
            f"requested_url={snapshot.requested_url}"
        )
        account = self.primary_handle if source.source_class.value == "official" else None
        return Evidence(
            evidence_id=_evidence_id(source.id, snapshot.final_url, page_text),
            subject=self.subject,
            source_id=source.id,
            source_class=source.source_class,
            source_url=snapshot.final_url,
            source_title=title,
            source_account=account,
            captured_at=snapshot.captured_at,
            published_at=None,
            content_type=infer_content_type(source),
            observation=" ".join(summary_parts),
            excerpt=body_excerpt,
            identity_status=_identity_status(source.identity_status),
            asset=None,
            notes=notes,
        )
