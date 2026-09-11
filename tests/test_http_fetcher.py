from datetime import UTC, datetime

import httpx

from pg_researcher.collectors.cache import FileCache
from pg_researcher.collectors.http import HttpFetcher
from pg_researcher.collectors.policy import FetchPolicy


def _policy(**overrides) -> FetchPolicy:
    values = {
        "version": 1,
        "retries": 1,
        "retry_backoff_seconds": 0.0,
        "min_host_interval_seconds": 0.0,
        "cache_ttl_seconds": 60,
        "allowed_content_types": ["text/html"],
    }
    values.update(overrides)
    return FetchPolicy.model_validate(values)


def test_fetcher_retries_429_and_respects_retry_after() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"retry-after": "2"}, request=request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<html>ok</html>",
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(policy=_policy(), client=client, sleeper=sleeps.append)
    result = fetcher.fetch("https://example.com/?utm_source=test")

    assert calls == 2
    assert sleeps == [2.0]
    assert result.requested_url == "https://example.com/"


def test_fetcher_uses_cache_without_second_request(tmp_path) -> None:
    calls = 0
    now = datetime(2026, 9, 11, 18, 0, tzinfo=UTC)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<html>cached</html>",
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(
        policy=_policy(),
        cache=FileCache(tmp_path),
        client=client,
        now=lambda: now,
    )

    first = fetcher.fetch("https://example.com/")
    second = fetcher.fetch("https://example.com/")

    assert first.from_cache is False
    assert second.from_cache is True
    assert calls == 1
