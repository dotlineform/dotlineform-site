"""Bound native single-file Docs uploads without persistent staging or path claims."""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
import json
from typing import Any

from docs_media_storage import validate_media_filename


MAX_MEDIA_BYTES = 64 * 1024 * 1024
MAX_METADATA_BYTES = 1024 * 1024
MAX_MULTIPART_OVERHEAD_BYTES = 1024 * 1024
MAX_REQUEST_BYTES = MAX_MEDIA_BYTES + MAX_METADATA_BYTES + MAX_MULTIPART_OVERHEAD_BYTES


@dataclass(frozen=True)
class SourceMediaUpload:
    """Browser basename and opaque bytes owned by one awaited media operation."""

    filename: str
    data: bytes


def validate_upload(upload: SourceMediaUpload) -> str:
    """Reject paths and empty/oversized contents before temporary materialisation."""
    filename = validate_media_filename(upload.filename)
    if filename != upload.filename or "\\" in filename or len(filename.encode("utf-8")) > 255:
        raise ValueError("Media filename must be one safe basename of at most 255 UTF-8 bytes")
    if not isinstance(upload.data, bytes) or not upload.data:
        raise ValueError("Selected media file is empty")
    if len(upload.data) > MAX_MEDIA_BYTES:
        raise ValueError("Selected media exceeds the 64 MiB file limit")
    return filename


def parse_media_upload(content_type: str, raw: bytes) -> tuple[dict[str, Any], SourceMediaUpload]:
    """Read exactly metadata JSON and one file from an already bounded HTTP body.

    Filename/MIME declarations do not select a storage owner or accepted format.
    The media service validates those contracts before any permanent write.
    """
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("Media upload request is too large")
    if len(content_type) > 256 or "\r" in content_type or "\n" in content_type:
        raise ValueError("Invalid media upload Content-Type")
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii") + raw,
    )
    if message.get_content_type() != "multipart/form-data" or not message.is_multipart() or message.defects:
        raise ValueError("Media upload requires valid multipart/form-data")
    parts = list(message.iter_parts())
    if len(parts) != 2:
        raise ValueError("Media upload requires metadata and exactly one file")
    fields = {}
    for part in parts:
        name = part.get_param("name", header="content-disposition")
        if (part.get_content_disposition() != "form-data" or part.is_multipart() or part.defects
                or name not in {"metadata", "file"} or name in fields):
            raise ValueError("Invalid or duplicate media upload field")
        fields[name] = part
    metadata_part = fields.get("metadata")
    file_part = fields.get("file")
    if metadata_part is None or file_part is None or metadata_part.get_filename() is not None:
        raise ValueError("Media upload requires metadata and exactly one file")
    metadata_bytes = metadata_part.get_payload(decode=True)
    if not isinstance(metadata_bytes, bytes) or len(metadata_bytes) > MAX_METADATA_BYTES:
        raise ValueError("Media metadata exceeds the 1 MiB limit")
    try:
        body = json.loads(metadata_bytes.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Media metadata must be valid UTF-8 JSON") from error
    if not isinstance(body, dict):
        raise ValueError("Media metadata must be a JSON object")
    filename = file_part.get_filename()
    if not isinstance(filename, str):
        raise ValueError("Media upload requires a file basename")
    upload = SourceMediaUpload(filename, file_part.get_payload(decode=True))
    validate_upload(upload)
    if len(raw) - len(metadata_bytes) - len(upload.data) > MAX_MULTIPART_OVERHEAD_BYTES:
        raise ValueError("Media multipart overhead exceeds the 1 MiB limit")
    return body, upload
