from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import httpx

from pg_researcher.collectors.cache import FileCache
from pg_researcher.collectors.normalize import canonicalize_url, validate_public_url
from pg_researcher.collectors.policy import FetchPolicy, load_fetch_policy
from pg_researcher.collectors.types import FetchSnapshot


class FetchError(RuntimeError):
    pass


class HttpFetcher:
    def __init__(
        self,
        *,
        policy: FetchPolicy | None = None,
        cache: FileCache | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.policy = policy or load_fetch_policy()
        self.cache = cache
        self.client = client or httpx.Client(follow_redirects=True)
        self.sleeper = sleeper
        self.monotonic = monotonic
        self.now = now or (lambda: datetime.now(timezone.utc))
        self._last_request_by_host: dict[str, float] = {}

    def _respect_host_interval(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        current = self.monotonic()
        previous = self._last_request_by_host.get(host)
        if previous is not None:
            remaining = self.policy.min_host_interval_seconds - (current - previous)
            if remaining > 0:
                self.sleeper(remaining)
                current = self.monotonic()
        self._last_request_by_host[host] = current

    def _retry_delay(self, response: httpx.Response | None, attempt: int) -> float:
        if response is not None:
            value = response.headers.get("retry-after")
            if value:
                try:
                    return max(0.0, float(value))
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(value)
                        if retry_at.tzinfo is None:
                            retry_at = retry_at.replace(tzinfo=timezone.utc)
                        return max(0.0, (retry_at - self.now()).total_seconds())
                    except (TypeError, ValueError, OverflowError):
                        pass
        return self.policy.retry_backoff_seconds * (2**attempt)

    def fetch(self, url: str, *, refresh: bool = False) -> FetchSnapshot:
        target = validate_public_url(url)
        captured_now = self.now()
        if self.cache is not None and not refresh:
            cached = self.cache.get(target, captured_now, self.policy.cache_ttl_seconds)
            if cached is not None:
                return cached

        last_error: Exception | None = None
        for attempt in range(self.policy.retries + 1):
            self._respect_host_interval(target)
            response: httpx.Response | None = None
            try:
                response = self.client.get(
                    target,
                    headers={"User-Agent": self.policy.user_agent},
                    timeout=self.policy.timeout_seconds,
                    follow_redirects=True,
                )
                transient = response.status_code == 429 or response.status_code >= 500
                if transient and attempt < self.policy.retries:
                    self.sleeper(self._retry_delay(response, attempt))
                    continue
                response.raise_for_status()

                body = response.content
                if len(body) > self.policy.max_response_bytes:
                    raise FetchError(
                        f"response exceeds max_response_bytes ({self.policy.max_response_bytes})"
                    )

                media_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if media_type and media_type not in self.policy.allowed_content_types:
                    raise FetchError(f"unsupported content type: {media_type}")

                final_url = validate_public_url(canonicalize_url(str(response.url)))
                snapshot = FetchSnapshot(
                    requested_url=target,
                    final_url=final_url,
                    status_code=response.status_code,
                    headers={key.lower(): value for key, value in response.headers.items()},
                    text=response.text,
                    captured_at=self.now(),
                )
                if self.cache is not None:
                    self.cache.put(target, snapshot)
                return snapshot
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.policy.retries:
                    self.sleeper(self._retry_delay(response, attempt))
                    continue
                break
            except httpx.HTTPStatusError as exc:
                raise FetchError(f"HTTP {exc.response.status_code} for {target}") from exc

        raise FetchError(f"request failed for {target}: {last_error}") from last_error
