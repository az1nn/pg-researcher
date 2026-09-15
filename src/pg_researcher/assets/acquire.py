from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from pg_researcher.assets.policy import AssetFetchPolicy, load_asset_policy
from pg_researcher.collectors.normalize import UnsafeUrlError, validate_public_url


class AssetAcquireError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AcquisitionResult:
    requested_url: str
    final_url: str
    media_type: str
    sha256: str
    size_bytes: int
    path: Path


class AssetAcquirer:
    def __init__(
        self,
        *,
        policy: AssetFetchPolicy | None = None,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.policy = policy or load_asset_policy()
        self.client = client or httpx.Client(follow_redirects=True)
        self.sleeper = sleeper
        self.monotonic = monotonic
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

    def acquire(self, url: str, output: Path) -> AcquisitionResult:
        try:
            target = validate_public_url(url)
        except UnsafeUrlError as exc:
            raise AssetAcquireError(str(exc)) from exc

        last_error: Exception | None = None
        for attempt in range(self.policy.retries + 1):
            self._respect_host_interval(target)
            try:
                response = self.client.get(
                    target,
                    headers={"User-Agent": self.policy.user_agent},
                    timeout=self.policy.timeout_seconds,
                    follow_redirects=True,
                )
                transient = response.status_code == 429 or response.status_code >= 500
                if transient and attempt < self.policy.retries:
                    self.sleeper(self.policy.retry_backoff_seconds * (2**attempt))
                    continue
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > self.policy.max_response_bytes:
                            raise AssetAcquireError(
                                "asset exceeds max_response_bytes "
                                f"({self.policy.max_response_bytes})"
                            )
                    except ValueError:
                        pass

                media_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if media_type not in self.policy.allowed_content_types:
                    rendered_type = media_type or "<missing>"
                    raise AssetAcquireError(
                        f"unsupported asset content type: {rendered_type}"
                    )

                body = response.content
                if len(body) > self.policy.max_response_bytes:
                    raise AssetAcquireError(
                        f"asset exceeds max_response_bytes ({self.policy.max_response_bytes})"
                    )

                try:
                    final_url = validate_public_url(str(response.url))
                except UnsafeUrlError as exc:
                    raise AssetAcquireError(str(exc)) from exc

                output.parent.mkdir(parents=True, exist_ok=True)
                temporary = output.with_name(f"{output.name}.part")
                temporary.write_bytes(body)
                temporary.replace(output)
                digest = hashlib.sha256(body).hexdigest()
                return AcquisitionResult(
                    requested_url=target,
                    final_url=final_url,
                    media_type=media_type,
                    sha256=digest,
                    size_bytes=len(body),
                    path=output,
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < self.policy.retries:
                    self.sleeper(self.policy.retry_backoff_seconds * (2**attempt))
                    continue
                break
            except httpx.HTTPStatusError as exc:
                raise AssetAcquireError(
                    f"HTTP {exc.response.status_code} while acquiring {target}"
                ) from exc

        raise AssetAcquireError(f"asset request failed for {target}: {last_error}") from last_error
