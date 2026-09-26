"""HTTP cache policies and validators for local Docs Viewer responses.

Validators inspect only the requested file or rendered response. No process cache,
workspace inventory or source/generated lifecycle operation participates in a read.
"""

import hashlib
from pathlib import Path
import re


REVALIDATE = "private, no-cache"
APP_ASSET_CACHE = "private, max-age=86400"
VERSIONED_MEDIA_CACHE = "private, max-age=31536000, immutable"
APP_ASSET_SUFFIXES = {".js", ".css", ".svg", ".ico", ".png", ".webp", ".woff", ".woff2", ".ttf", ".otf"}


def bytes_etag(body: bytes) -> str:
    """Identify the actual serialized representation, including server projections."""
    return '"' + hashlib.sha256(body).hexdigest() + '"'


def read_file_response(path: Path, if_none_match: str | None) -> tuple[str, bytes]:
    """Return a file validator and changed bytes before any response headers are sent.

    An unchanged file needs only metadata and returns an empty body for 304.
    Read errors remain ordinary request failures, without a partially started 200.
    """
    stat = path.stat()
    etag = f'W/"{stat.st_mtime_ns:x}-{stat.st_ctime_ns:x}-{stat.st_size:x}"'
    return etag, b"" if matches_etag(if_none_match, etag) else path.read_bytes()


def matches_etag(value: str | None, etag: str) -> bool:
    """Apply If-None-Match weak comparison to a GET's existing representation."""
    if value is None:
        return False
    if value.strip() == "*":
        return True
    return any(
        candidate.strip().removeprefix("W/") == etag.removeprefix("W/")
        for candidate in value.split(",")
    )


def media_cache_control(path: Path, work_primary: Path, query: dict[str, list[str]]) -> str:
    """Long-cache only Catalogue primary images carrying their positive media version."""
    versions = query.get("v", [])
    if path.is_relative_to(work_primary) and len(versions) == 1 and re.fullmatch(r"[1-9][0-9]*", versions[0]):
        return VERSIONED_MEDIA_CACHE
    return REVALIDATE
