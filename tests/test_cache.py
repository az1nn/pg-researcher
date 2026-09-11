from datetime import UTC, datetime, timedelta

from pg_researcher.collectors.cache import FileCache
from pg_researcher.collectors.types import FetchSnapshot


def test_file_cache_round_trip_and_expiry(tmp_path) -> None:
    now = datetime(2026, 9, 11, 18, 0, tzinfo=UTC)
    snapshot = FetchSnapshot(
        requested_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        headers={"content-type": "text/html"},
        text="hello",
        captured_at=now,
    )
    cache = FileCache(tmp_path)
    cache.put(snapshot.requested_url, snapshot)

    cached = cache.get(snapshot.requested_url, now + timedelta(seconds=10), 60)
    assert cached is not None
    assert cached.from_cache is True
    assert cached.text == "hello"

    expired = cache.get(snapshot.requested_url, now + timedelta(seconds=61), 60)
    assert expired is None
