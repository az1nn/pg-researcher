import pytest

from pg_researcher.collectors.normalize import (
    UnsafeUrlError,
    canonicalize_url,
    parse_html,
    validate_public_url,
)


def test_canonicalize_url_removes_trackers_and_sorts_query() -> None:
    value = canonicalize_url("HTTPS://Example.COM/path?utm_source=x&b=2&a=1#fragment")
    assert value == "https://example.com/path?a=1&b=2"


def test_validate_public_url_rejects_local_targets() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_public_url("http://127.0.0.1/admin")
    with pytest.raises(UnsafeUrlError):
        validate_public_url("http://localhost:8080")


def test_parse_html_prefers_open_graph_metadata_and_ignores_scripts() -> None:
    parsed = parse_html(
        "<html><head><title>Fallback</title>"
        '<meta property="og:title" content="Prince Gutt">'
        '<meta property="og:description" content="Official artist page">'
        "<script>ignore me</script></head><body>Public catalog page</body></html>"
    )
    assert parsed.title == "Prince Gutt"
    assert parsed.description == "Official artist page"
    assert parsed.text.endswith("Public catalog page")
    assert "ignore me" not in parsed.text
