"""Bound one Source Save's metadata and selected native files without staging."""

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
    """Validated browser basename and bytes carried into the owning Save."""

    filename: str
    data: bytes


def validate_upload_filename(value: str) -> str:
    filename = validate_media_filename(value)
    if filename != value or "\\" in filename or len(filename.encode("utf-8")) > 255:
        raise ValueError("Media filename must be one safe basename of at most 255 UTF-8 bytes")
    return filename


def parse_source_save(content_type: str, raw: bytes) -> tuple[dict[str, Any], list[SourceMediaUpload]]:
    """Parse metadata plus file_0…file_N and enforce all limits before processing."""
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("Source Save exceeds the 66 MiB request limit")
    if len(content_type) > 256 or "\r" in content_type or "\n" in content_type:
        raise ValueError("Invalid Source Save Content-Type")
    try:
        header = ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii")
    except UnicodeError as error:
        raise ValueError("Invalid Source Save Content-Type") from error
    message = BytesParser(policy=policy.default).parsebytes(header + raw)
    if message.get_content_type() != "multipart/form-data" or not message.is_multipart() or message.defects:
        raise ValueError("Source Save requires valid multipart/form-data")
    fields = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if (part.get_content_disposition() != "form-data" or part.is_multipart() or part.defects
                or not isinstance(name, str) or name in fields):
            raise ValueError("Invalid or duplicate Source Save field")
        fields[name] = part
    metadata = fields.pop("metadata", None)
    if metadata is None or metadata.get_filename() is not None:
        raise ValueError("Source Save requires metadata JSON")
    metadata_bytes = metadata.get_payload(decode=True)
    if not isinstance(metadata_bytes, bytes) or len(metadata_bytes) > MAX_METADATA_BYTES:
        raise ValueError("Source Save metadata exceeds the 1 MiB limit")
    try:
        body = json.loads(metadata_bytes.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Source Save metadata must be valid UTF-8 JSON") from error
    if not isinstance(body, dict) or not isinstance(body.get("media"), list):
        raise ValueError("Source Save requires metadata with a media list")
    if set(fields) != {f"file_{index}" for index in range(len(body["media"]))}:
        raise ValueError("Source Save file fields must match its selected media")
    uploads = []
    total = 0
    for index in range(len(body["media"])):
        part = fields[f"file_{index}"]
        filename = part.get_filename()
        if not isinstance(filename, str):
            raise ValueError("Source Save requires native file basenames")
        validate_upload_filename(filename)
        data = part.get_payload(decode=True)
        if not isinstance(data, bytes) or not data:
            raise ValueError(f"Selected media file is empty: {filename}")
        if len(data) > MAX_MEDIA_BYTES:
            raise ValueError(f"Selected media exceeds the 64 MiB file limit: {filename}")
        total += len(data)
        if total > MAX_MEDIA_BYTES:
            raise ValueError("Selected pending media exceeds the combined 64 MiB limit")
        uploads.append(SourceMediaUpload(filename, data))
    if len(raw) - len(metadata_bytes) - total > MAX_MULTIPART_OVERHEAD_BYTES:
        raise ValueError("Source Save multipart overhead exceeds the 1 MiB limit")
    return body, uploads
