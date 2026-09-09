"""Read current generated Catalogue data for authoring, runtime and availability audits.

Reads are confined to the configured generated workspace. No document, canonical
Catalogue record, archive lookup or inferred media filename is a dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from studio.services.catalogue.catalogue_output_paths import catalogue_output_workspace, output_path


def _read_generated(repo_root: Path, relative: str) -> dict[str, Any]:
    try:
        workspace = catalogue_output_workspace(repo_root)
        payload = json.loads(output_path(workspace, relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Generated Catalogue data is unavailable") from exc
    if not isinstance(payload, dict):
        raise ValueError("Generated Catalogue data must be an object")
    return payload


def _work_identity(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{5}", value):
        raise ValueError("An exact five-digit Catalogue Work ID is required")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Generated Work {label} is unavailable")
    return value.strip()


def _positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


def _safe_media_url(value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        return ""
    if any(char == "\\" or ord(char) <= 32 or ord(char) == 127 for char in value):
        return ""
    if value.startswith("/") and not value.startswith("//"):
        return value
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname and parsed.username is None and parsed.password is None:
            return value
    except ValueError:
        pass
    return ""


def read_catalogue_media_targets(repo_root: Path) -> dict[str, Any]:
    """Expose identifying Work fields from the generated index, without document filtering."""
    payload = _read_generated(repo_root, "works/works_index.json")
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("Generated Catalogue Work index is unavailable")
    targets = []
    for key, work in works.items():
        work_id = _work_identity(key)
        if not isinstance(work, dict) or work.get("work_id") != work_id:
            raise ValueError("Generated Work index identity is mismatched")
        year = work.get("year_display")
        targets.append({
            "family": "catalogue", "target_type": "work", "target_id": work_id,
            "title": _text(work.get("title"), "title"),
            "meta": [year] if isinstance(year, str) and year else [],
        })
    return {"ok": True, "schema_version": "docs_semantic_token_target_lookup_v2", "targets": targets}


def read_catalogue_work(repo_root: Path, work_id: str) -> dict[str, Any]:
    """Return the generated consumer record; browser presentation belongs to the shared renderer."""
    work_id = _work_identity(work_id)
    payload = _read_generated(repo_root, f"works/index/{work_id}.json")
    work = payload.get("work")
    if not isinstance(work, dict) or work.get("work_id") != work_id:
        raise ValueError(f"Generated data does not match Work {work_id}")
    _text(work.get("title"), "title")
    return payload


def catalogue_media_record(payload: dict[str, Any], work_id: str, detail_id: str = "") -> dict[str, Any]:
    """Validate only the exact requested image; a Detail does not require a Work primary."""
    work_id = _work_identity(work_id)
    record = payload.get("work")
    if not isinstance(record, dict) or record.get("work_id") != work_id:
        raise ValueError(f"Generated data does not match Work {work_id}")
    if detail_id:
        if not re.fullmatch(r"(?:[0-9]{3}|[1-9][0-9]{3,})", detail_id) or not int(detail_id):
            raise ValueError("An exact Catalogue Detail ID is required")
        detail_uid = f"{work_id}-{detail_id}"
        sections = payload.get("sections")
        if not isinstance(sections, list) or any(
            not isinstance(section, dict) or not isinstance(section.get("details"), list) for section in sections
        ):
            raise ValueError("Generated Detail sections are unavailable")
        matches = [
            detail for section in sections
            for detail in section["details"] if isinstance(detail, dict) and detail.get("detail_uid") == detail_uid
        ]
        if len(matches) != 1 or matches[0].get("work_id") != work_id or matches[0].get("detail_id") != detail_id:
            raise ValueError(f"Generated Detail {detail_uid} is unavailable or mismatched")
        record = matches[0]
    _text(record.get("title"), "image title")
    if not all(_positive_integer(record.get(field)) for field in ("width_px", "height_px")):
        raise ValueError("Generated image dimensions are unavailable")
    media = record.get("media")
    primary = media.get("primary") if isinstance(media, dict) else None
    if not isinstance(primary, list) or not primary or any(
        not isinstance(item, dict) or not _positive_integer(item.get("width")) or not _safe_media_url(item.get("url"))
        for item in primary
    ):
        raise ValueError(f"Generated media for Work {work_id} is unavailable or unsafe")
    return record
