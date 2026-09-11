from datetime import UTC, datetime

import httpx

from pg_researcher.collectors.http import HttpFetcher
from pg_researcher.collectors.policy import FetchPolicy
from pg_researcher.collectors.web import WebCollector
from pg_researcher.models import SourceClass, SourceConfig


def test_web_collector_builds_stable_evidence() -> None:
    now = datetime(2026, 9, 11, 18, 0, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><head><title>Prince Gutt</title>"
                '<meta name="description" content="Official page"></head>'
                "<body>Catalog and releases</body></html>"
            ),
            request=request,
        )

    policy = FetchPolicy(
        retries=0,
        min_host_interval_seconds=0,
        allowed_content_types=["text/html"],
    )
    fetcher = HttpFetcher(
        policy=policy,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        now=lambda: now,
    )
    collector = WebCollector(fetcher, subject="Prince' Gutt", primary_handle="princeguttreal")
    source = SourceConfig(
        id="official_example",
        **{
            "class": SourceClass.OFFICIAL,
            "platform": "x",
            "canonical_url": "https://example.com/artist",
            "identity_status": "verified_for_project",
            "capabilities": ["profile_media"],
        },
    )

    first = collector.collect(source)
    second = collector.collect(source)

    assert first.evidence_id == second.evidence_id
    assert first.identity_status == "verified"
    assert first.content_type == "profile"
    assert first.source_account == "princeguttreal"
    assert first.source_title == "Prince Gutt"
    assert "Catalog and releases" in (first.excerpt or "")
