"""Checksum and content type for a selected media file."""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path


def file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_type_for(path: Path) -> str:
    hls_type = {".m3u8": "application/vnd.apple.mpegurl", ".m4s": "video/iso.segment"}.get(path.suffix.lower())
    if hls_type:
        return hls_type
    content_type, _encoding = mimetypes.guess_type(path.name)
    return content_type or "application/octet-stream"
