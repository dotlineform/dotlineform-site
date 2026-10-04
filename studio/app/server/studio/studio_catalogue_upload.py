"""Decode a bounded multipart Work Save without staging files or writing assets."""

from __future__ import annotations

from email import policy
from email.parser import BytesParser
import json
from typing import Any

from catalogue.catalogue_work_attachments import (
    MAX_WORK_ATTACHMENT_BYTES, MAX_WORK_METADATA_BYTES, MAX_WORK_MULTIPART_OVERHEAD_BYTES,
    MAX_WORK_SAVE_BODY_BYTES, WorkAttachment,
)


def parse_work_save_upload(content_type: str, raw: bytes) -> tuple[dict[str, Any], list[WorkAttachment]]:
    """Accept one metadata part and exactly its numbered opaque attachment parts.

    Filenames come from UTF-8 JSON so MIME header/browser filename transformations
    cannot rename an attachment. The service validates and prefixes those names.
    The entire request and each owned family are bounded independently.
    """
    if len(raw) > MAX_WORK_SAVE_BODY_BYTES or "\r" in content_type or "\n" in content_type:
        raise ValueError("Invalid Work upload request")
    envelope = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii") + raw,
    )
    if envelope.get_content_type() != "multipart/form-data" or not envelope.is_multipart() or envelope.defects:
        raise ValueError("Work upload must be valid multipart/form-data")
    parts: dict[str, bytes] = {}
    for part in envelope.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if (
            part.get_content_disposition() != "form-data" or not isinstance(name, str)
            or name in parts or part.is_multipart() or part.defects
            or part.get("Content-Transfer-Encoding") is not None
        ):
            raise ValueError("Invalid or duplicate Work upload part")
        if name != "payload" and part.get_content_type() != "application/octet-stream":
            raise ValueError("Work attachment parts must contain opaque bytes")
        data = part.get_payload(decode=True)
        if not isinstance(data, bytes):
            raise ValueError("Work upload part has no bytes")
        parts[name] = data
    metadata = parts.pop("payload", None)
    if metadata is None or len(metadata) > MAX_WORK_METADATA_BYTES:
        raise ValueError("Work upload requires metadata within the 1 MiB limit")
    try:
        body = json.loads(metadata.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("Work upload metadata must be valid UTF-8 JSON") from error
    if not isinstance(body, dict):
        raise ValueError("Work upload metadata must be an object")
    names = body.pop("attachment_names", None)
    if not isinstance(names, list) or not names or any(not isinstance(name, str) for name in names):
        raise ValueError("Work upload requires attachment_names")
    if set(parts) != {f"attachment_{index}" for index in range(len(names))}:
        raise ValueError("Work upload parts must match attachment_names exactly")
    attachment_size = sum(len(data) for data in parts.values())
    if attachment_size > MAX_WORK_ATTACHMENT_BYTES:
        raise ValueError("Combined Work attachments exceed the 64 MiB Save limit")
    if len(raw) - attachment_size - len(metadata) > MAX_WORK_MULTIPART_OVERHEAD_BYTES:
        raise ValueError("Work upload multipart overhead exceeds the 1 MiB limit")
    return body, [WorkAttachment(name, parts[f"attachment_{index}"]) for index, name in enumerate(names)]
