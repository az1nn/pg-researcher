from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pg_researcher.models import SourceConfig

_TRACKING_KEYS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}
_WHITESPACE = re.compile(r"\s+")


class UnsafeUrlError(ValueError):
    pass


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    is_default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    if port is not None and not is_default_port:
        host = f"{host}:{port}"

    clean_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in _TRACKING_KEYS:
            continue
        clean_query.append((key, value))
    clean_query.sort()

    path = parts.path or "/"
    return urlunsplit((scheme, host, path, urlencode(clean_query, doseq=True), ""))


def validate_public_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"}:
        raise UnsafeUrlError("collector only supports http/https URLs")
    if parts.username or parts.password:
        raise UnsafeUrlError("URLs containing credentials are not allowed")

    hostname = parts.hostname
    if not hostname:
        raise UnsafeUrlError("URL must contain a hostname")
    lowered = hostname.lower().rstrip(".")
    if lowered == "localhost" or lowered.endswith(".localhost") or lowered.endswith(".local"):
        raise UnsafeUrlError("local hostnames are not allowed")

    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise UnsafeUrlError("non-public IP addresses are not allowed")

    return canonicalize_url(url)


def collapse_whitespace(value: str) -> str:
    return _WHITESPACE.sub(" ", unescape(value)).strip()


@dataclass(frozen=True, slots=True)
class ParsedPage:
    title: str | None
    description: str | None
    text: str


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_title = False
        self._ignored_depth = 0
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self.description: str | None = None
        self.og_title: str | None = None
        self.og_description: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        if lowered == "title":
            self._in_title = True
        if lowered != "meta":
            return
        values = {key.lower(): value for key, value in attrs if value is not None}
        name = (values.get("name") or values.get("property") or "").lower()
        content = values.get("content")
        if not content:
            return
        if name == "description":
            self.description = content
        elif name == "og:title":
            self.og_title = content
        elif name == "og:description":
            self.og_description = content

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        if lowered == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._ignored_depth == 0:
            self._text_parts.append(data)

    def parsed(self) -> ParsedPage:
        title = collapse_whitespace(self.og_title or "".join(self._title_parts)) or None
        description = collapse_whitespace(self.og_description or self.description or "") or None
        text = collapse_whitespace(" ".join(self._text_parts))
        return ParsedPage(title=title, description=description, text=text)


def parse_html(value: str) -> ParsedPage:
    parser = _PageParser()
    parser.feed(value)
    parser.close()
    return parser.parsed()


def excerpt(value: str, max_chars: int = 600) -> str | None:
    clean = collapse_whitespace(value)
    if not clean:
        return None
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


def infer_content_type(source: SourceConfig) -> str:
    platform = source.platform.lower()
    if platform in {"x", "instagram", "tiktok", "youtube", "spotify", "deezer"}:
        return "profile"
    if "artist_profile" in source.capabilities:
        return "profile"
    return "document"
