#!/usr/bin/env python3
"""Shared helpers for file-backed moment source metadata."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

MOMENT_SOURCES_MANIFEST_SCHEMA = "moment_sources_manifest_v1"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def normalize_status(value: Any) -> str:
    return normalize_text(value).lower()


def is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def coerce_string(value: Any) -> Optional[str]:
    s = normalize_text(value)
    return s or None


def coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raw = normalize_text(value)
    if raw == "":
        return None
    try:
        return int(raw)
    except Exception:
        return None


def parse_date(value: Any) -> Optional[str]:
    if value is None or normalize_text(value) == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    raw = normalize_text(value)
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw)
    if match:
        y, m, d = map(int, match.groups())
        return dt.date(y, m, d).isoformat()
    return raw


def is_slug_safe(value: str) -> bool:
    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value or "") is not None


def parse_scalar_from_fm_line(raw: str) -> Optional[str]:
    value = raw.strip()
    if value == "" or value == "null":
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_front_matter(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm: Dict[str, Any] = {}
    for line in parts[1].splitlines():
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            continue
        fm[match.group(1)] = parse_scalar_from_fm_line(match.group(2))
    return fm


def yaml_scalar(value: Any) -> str:
    if value is None:
        return ""
    raw = str(value)
    if raw == "":
        return ""
    if re.fullmatch(r"[A-Za-z0-9_.-]+", raw):
        return raw
    escaped = raw.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def update_scalar_front_matter(
    path: Path,
    updates: Mapping[str, Any],
    *,
    key_order: Optional[list[str]] = None,
) -> bool:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_block = parts[1]
            body = parts[2]
        else:
            fm_block = ""
            body = text
    else:
        fm_block = ""
        body = "\n" + text if text and not text.startswith("\n") else text

    lines = fm_block.splitlines()
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    updated_lines: list[str] = []
    seen_keys: set[str] = set()
    key_order = key_order or list(updates.keys())

    for line in lines:
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not match:
            updated_lines.append(line)
            continue
        key = match.group(1)
        if key in updates:
            updated_lines.append(f"{key}: {yaml_scalar(updates[key])}".rstrip())
            seen_keys.add(key)
        else:
            updated_lines.append(line)

    for key in key_order:
        if key in updates and key not in seen_keys:
            updated_lines.append(f"{key}: {yaml_scalar(updates[key])}".rstrip())

    new_text = "---\n" + "\n".join(updated_lines).rstrip() + "\n---" + body
    if not new_text.endswith("\n"):
        new_text += "\n"
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def update_moment_source_front_matter(
    path: Path,
    *,
    title: Optional[str] = None,
    status: Optional[str] = None,
    published_date: Optional[str] = None,
    image_file: Optional[str] = None,
    preserve_existing_published_date: bool = True,
) -> bool:
    existing = parse_front_matter(path)
    existing_published_date = parse_date(existing.get("published_date"))
    next_published_date = existing_published_date if (preserve_existing_published_date and existing_published_date) else parse_date(published_date)
    next_image_file = coerce_string(image_file)
    updates: Dict[str, Any] = {}
    if title is not None:
        updates["title"] = coerce_string(title) or ""
    if status is not None:
        updates["status"] = normalize_status(status)
    updates["published_date"] = next_published_date
    updates["image_file"] = next_image_file
    return update_scalar_front_matter(
        path,
        updates,
        key_order=["title", "status", "published_date", "image_file"],
    )


def workbook_headers(ws) -> list[str]:
    return [normalize_text(cell.value) for cell in next(ws.iter_rows(min_row=1, max_row=1))]


def normalize_row_payload(headers: list[str], row: tuple[Any, ...]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for idx, header in enumerate(headers):
        if not header:
            continue
        payload[header] = row[idx] if idx < len(row) else None
    return payload


def scan_moment_source_files(moments_root: Path) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not moments_root.exists():
        return out
    for path in sorted(moments_root.glob("*.md")):
        moment_id = path.stem.strip().lower()
        if not moment_id or not is_slug_safe(moment_id):
            continue
        front_matter = parse_front_matter(path)
        out[moment_id] = {
            "moment_id": moment_id,
            "title": coerce_string(front_matter.get("title")),
            "status": normalize_status(front_matter.get("status")),
            "published_date": parse_date(front_matter.get("published_date")),
            "date": parse_date(front_matter.get("date")),
            "date_display": coerce_string(front_matter.get("date_display")),
            "image_alt": coerce_string(front_matter.get("image_alt")) or coerce_string(front_matter.get("alt")),
            "source_image_file": coerce_string(front_matter.get("image_file")),
            "source_prose_path": str(path),
        }
    return out


def build_moment_sources_manifest_payload(
    *,
    moments_root: Path,
    moments_images_root: Path,
    source_index: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    source_index = source_index if source_index is not None else scan_moment_source_files(moments_root)
    moments: Dict[str, Dict[str, Any]] = {}

    for moment_id, source_entry in source_index.items():
        source_image_file = coerce_string(source_entry.get("source_image_file")) or f"{moment_id}.jpg"
        prose_path = Path(str(source_entry.get("source_prose_path") or (moments_root / f"{moment_id}.md")))
        image_path = moments_images_root / source_image_file
        moments[moment_id] = {
            "moment_id": moment_id,
            "title": coerce_string(source_entry.get("title")) or moment_id,
            "status": normalize_status(source_entry.get("status")),
            "published_date": parse_date(source_entry.get("published_date")),
            "date": parse_date(source_entry.get("date")),
            "date_display": coerce_string(source_entry.get("date_display")),
            "width_px": None,
            "height_px": None,
            "image_alt": coerce_string(source_entry.get("image_alt")),
            "image_file": f"{moment_id}.jpg",
            "source_image_file": source_image_file,
            "source_prose_path": str(prose_path),
            "source_image_path": str(image_path),
        }

    return {
        "header": {
            "schema": MOMENT_SOURCES_MANIFEST_SCHEMA,
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "count": len(moments),
        },
        "moments": moments,
    }


def build_compat_moment_sources_manifest_payload(
    *,
    xlsx_path: Path,
    moments_sheet: str,
    moments_root: Path,
    moments_images_root: Path,
    source_index: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compatibility wrapper for older callers; workbook arguments are ignored."""
    del xlsx_path, moments_sheet
    return build_moment_sources_manifest_payload(
        moments_root=moments_root,
        moments_images_root=moments_images_root,
        source_index=source_index,
    )


def load_moment_sources_manifest(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Invalid moment sources manifest: {path}")
    header = payload.get("header")
    if not isinstance(header, Mapping) or header.get("schema") != MOMENT_SOURCES_MANIFEST_SCHEMA:
        raise ValueError(f"Unsupported moment sources manifest schema: {path}")
    raw_moments = payload.get("moments")
    if not isinstance(raw_moments, Mapping):
        raise ValueError(f"Invalid moment sources manifest payload: {path}")

    moments: Dict[str, Dict[str, Any]] = {}
    for raw_moment_id, raw_record in raw_moments.items():
        if not isinstance(raw_record, Mapping):
            continue
        moment_id = normalize_text(raw_record.get("moment_id") or raw_moment_id).lower()
        if not moment_id:
            continue
        moments[moment_id] = {
            "moment_id": moment_id,
            "title": coerce_string(raw_record.get("title")) or moment_id,
            "status": normalize_status(raw_record.get("status")),
            "published_date": parse_date(raw_record.get("published_date")),
            "date": parse_date(raw_record.get("date")),
            "date_display": coerce_string(raw_record.get("date_display")),
            "width_px": coerce_int(raw_record.get("width_px")),
            "height_px": coerce_int(raw_record.get("height_px")),
            "image_alt": coerce_string(raw_record.get("image_alt")),
            "image_file": coerce_string(raw_record.get("image_file")) or f"{moment_id}.jpg",
            "source_image_file": coerce_string(raw_record.get("source_image_file")) or f"{moment_id}.jpg",
            "source_prose_path": coerce_string(raw_record.get("source_prose_path")),
            "source_image_path": coerce_string(raw_record.get("source_image_path")),
        }
    return moments


def write_moment_sources_manifest(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
