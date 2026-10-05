"""Bound native Work attachments and derive their managed identities at Save."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence


MAX_WORK_ATTACHMENT_BYTES = 64 * 1024 * 1024
MAX_WORK_METADATA_BYTES = 1024 * 1024
MAX_WORK_MULTIPART_OVERHEAD_BYTES = 1024 * 1024
MAX_WORK_SAVE_BODY_BYTES = MAX_WORK_ATTACHMENT_BYTES + MAX_WORK_METADATA_BYTES + MAX_WORK_MULTIPART_OVERHEAD_BYTES


@dataclass(frozen=True)
class WorkAttachment:
    """Original browser basename and opaque bytes held only for the awaited Save."""

    original_filename: str
    data: bytes


def safe_download_filename(value: Any) -> str:
    """Preserve a basename exactly; reject paths, controls and unrepresentable names."""
    if (
        not isinstance(value, str) or not value or value != value.strip()
        or value in {".", ".."} or "/" in value or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Work attachment filename must be one safe basename")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("Work attachment filename must be valid Unicode") from error
    if size > 255:
        raise ValueError("Work attachment filename is too long")
    return value


def _attachment_filename(work_id: str, original: str) -> str:
    """Normalize a validated basename and validate its prefixed destination."""
    match = re.fullmatch(r"(.+)\.([A-Za-z0-9]+)", original)
    stem = match[1] if match else original
    stem = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "attachment"
    extension = f".{match[2].lower()}" if match else ""
    return safe_download_filename(f"{work_id}-{stem}{extension}")


def bind_work_attachments(
    body: Mapping[str, Any], attachments: Sequence[WorkAttachment],
) -> dict[str, bytes]:
    """Validate upload/reference agreement before mutation; only the server names writes.

    Existing references keep their identity. Native replacements target the exact
    normalized prefixed identity, with labels supplied by the ordinary Work draft.
    """
    work_id = body.get("work_id")
    if not isinstance(work_id, str) or re.fullmatch(r"[0-9]{5}", work_id) is None:
        raise ValueError("work_id must be exactly five digits")
    record = body.get("record")
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    if "work_id" in record and record["work_id"] != work_id:
        raise ValueError("record work_id must match the requested Work")
    regenerate = body.get("regenerate_image", False)
    if type(regenerate) is not bool:
        raise ValueError("regenerate_image must be a boolean")
    if "attachment_names" in body:
        raise ValueError("attachment_names belongs to the multipart Work upload")
    if regenerate and (not record.get("project_folder") or not record.get("project_filename")):
        raise ValueError("Image regeneration requires a project folder and filename")
    downloads = record.get("downloads", [])
    if not isinstance(downloads, list):
        raise ValueError("downloads must be an array")
    references = []
    for entry in downloads:
        if not isinstance(entry, dict):
            raise ValueError("Each download must be an object")
        references.append(safe_download_filename(entry.get("filename")))
    if len(set(references)) != len(references):
        raise ValueError("Download filenames must be unique within a Work")
    files = {}
    total = 0
    for attachment in attachments:
        original = safe_download_filename(attachment.original_filename)
        filename = _attachment_filename(work_id, original)
        if filename in files:
            raise ValueError("Duplicate Work attachment upload")
        if filename not in references:
            raise ValueError("Work attachment upload must have its canonical download reference")
        if not isinstance(attachment.data, bytes) or not attachment.data:
            raise ValueError(f"Work attachment is empty: {original}")
        total += len(attachment.data)
        if total > MAX_WORK_ATTACHMENT_BYTES:
            raise ValueError("Combined Work attachments exceed the 64 MiB Save limit")
        files[filename] = attachment.data
    return files
