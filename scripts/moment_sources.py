#!/usr/bin/env python3
"""Shared helpers for file-backed moment source metadata."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

MOMENT_METADATA_SCHEMA = "catalogue_source_moments_v1"
MOMENT_METADATA_FILENAME = "moments.json"
CATALOGUE_MOMENT_PROSE_REL_DIR = Path("_docs_src_catalogue/moments")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def normalize_status(value: Any) -> str:
    return normalize_text(value).lower()


def coerce_string(value: Any) -> Optional[str]:
    s = normalize_text(value)
    return s or None


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


def normalize_moment_filename(value: Any) -> str:
    raw = normalize_text(value).lower()
    if not raw:
        raise ValueError("moment_file is required")
    if Path(raw).name != raw:
        raise ValueError("moment_file must be a filename, not a path")
    stem = raw[:-3] if raw.endswith(".md") else raw
    if not stem or not is_slug_safe(stem):
        raise ValueError("moment_file must be a slug-safe markdown filename")
    return f"{stem}.md"


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


def validate_moment_source_entry(entry: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    moment_id = normalize_text(entry.get("moment_id")).lower()
    if not moment_id:
        errors.append("moment_id is required")
    elif not is_slug_safe(moment_id):
        errors.append("moment filename stem must be slug-safe")

    if not coerce_string(entry.get("title")):
        errors.append("title is required")

    status = normalize_status(entry.get("status"))
    if status not in {"draft", "published"}:
        errors.append("status must be draft or published")

    if not parse_date(entry.get("date")):
        errors.append("date is required")

    if status == "published" and not parse_date(entry.get("published_date")):
        errors.append("published moments require published_date")

    return errors


def normalize_moment_metadata_record(moment_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    normalized_id = normalize_text(record.get("moment_id") or moment_id).lower()
    source_image_file = coerce_string(record.get("source_image_file") or record.get("image_file"))
    out: Dict[str, Any] = {
        "moment_id": normalized_id,
        "title": coerce_string(record.get("title")) or "",
        "status": normalize_status(record.get("status")),
        "published_date": parse_date(record.get("published_date")),
        "date": parse_date(record.get("date")),
        "date_display": coerce_string(record.get("date_display")),
        "image_alt": coerce_string(record.get("image_alt")) or coerce_string(record.get("alt")),
    }
    if source_image_file and source_image_file != f"{normalized_id}.jpg":
        out["source_image_file"] = source_image_file
    return out


def validate_moment_metadata_record(record: Mapping[str, Any]) -> list[str]:
    return validate_moment_source_entry(record)


def moments_metadata_path(source_dir: Path) -> Path:
    return source_dir / MOMENT_METADATA_FILENAME


def load_moment_metadata_records(source_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = moments_metadata_path(source_dir)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Invalid moment metadata source: {path}")
    header = payload.get("header")
    if isinstance(header, Mapping) and header.get("schema") not in {MOMENT_METADATA_SCHEMA, None}:
        raise ValueError(f"Unsupported moment metadata source schema: {path}")
    raw_moments = payload.get("moments")
    if not isinstance(raw_moments, Mapping):
        raise ValueError(f"Invalid moment metadata source payload: {path}")
    moments: Dict[str, Dict[str, Any]] = {}
    for raw_moment_id, raw_record in raw_moments.items():
        if not isinstance(raw_record, Mapping):
            continue
        moment_id = normalize_text(raw_record.get("moment_id") or raw_moment_id).lower()
        if not moment_id:
            continue
        moments[moment_id] = normalize_moment_metadata_record(moment_id, raw_record)
    return dict(sorted(moments.items()))


def moment_metadata_payload(records: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    moments = {
        moment_id: normalize_moment_metadata_record(moment_id, record)
        for moment_id, record in sorted(records.items())
    }
    return {
        "header": {
            "schema": MOMENT_METADATA_SCHEMA,
        },
        "moments": moments,
    }


def write_moment_metadata_records(source_dir: Path, records: Mapping[str, Mapping[str, Any]]) -> Path:
    path = moments_metadata_path(source_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(moment_metadata_payload(records), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_moment_metadata_entry(
    moment_id: str,
    record: Mapping[str, Any],
    *,
    prose_root: Path,
    moments_images_root: Optional[Path] = None,
) -> Dict[str, Any]:
    normalized = normalize_moment_metadata_record(moment_id, record)
    normalized_id = normalized["moment_id"]
    source_image_file = coerce_string(normalized.get("source_image_file")) or f"{normalized_id}.jpg"
    source_image_path = (moments_images_root / source_image_file) if moments_images_root is not None else None
    return {
        **normalized,
        "moment_file": f"{normalized_id}.md",
        "image_file": f"{normalized_id}.jpg",
        "source_image_file": source_image_file,
        "source_prose_path": str(prose_root / f"{normalized_id}.md"),
        "source_image_path": str(source_image_path) if source_image_path is not None else "",
    }


def build_moment_metadata_source_index(
    source_dir: Path,
    *,
    repo_root: Path,
    moments_images_root: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    prose_root = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR
    records = load_moment_metadata_records(source_dir)
    return {
        moment_id: build_moment_metadata_entry(moment_id, record, prose_root=prose_root, moments_images_root=moments_images_root)
        for moment_id, record in records.items()
    }
