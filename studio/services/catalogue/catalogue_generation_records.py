"""Pure record projection helpers for generated catalogue artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional

try:
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        is_empty,
        parse_list,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        is_empty,
        parse_list,
    )

try:
    from catalogue.series_ids import normalize_series_id
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.series_ids import normalize_series_id


# Define the Works source-record projection once so adding a new field is a one-line change.
# Each entry is: (record_key, source_column_name, coercer)
WORKS_SCHEMA: List[tuple[str, str, Any]] = [
    ("artist", "artist", coerce_string),
    ("title", "title", coerce_string),
    ("year", "year", coerce_int),
    ("year_display", "year_display", coerce_string),
    ("storage", "storage_location", coerce_string),
    ("medium_type", "medium_type", coerce_string),
    ("medium_caption", "medium_caption", coerce_string),
    ("duration", "duration", coerce_string),
    ("height_cm", "height_cm", coerce_numeric),
    ("width_cm", "width_cm", coerce_numeric),
    ("depth_cm", "depth_cm", coerce_numeric),
    ("width_px", "width_px", coerce_int),
    ("height_px", "height_px", coerce_int),
    # tags handled separately (csv list)
]


WORKS_FIELD_ORDER = [
    "work_id",
    "title",
    "year",
    "year_display",
    "series_id",
    "series_ids",
    "series_title",
    "series_sort",
    "storage",
    "medium_type",
    "medium_caption",
    "duration",
    "links",
    "height_cm",
    "width_cm",
    "depth_cm",
    "width_px",
    "height_px",
    "downloads",
    "artist",
]


def build_work_record_projection(work_record: Mapping[str, Any]) -> Dict[str, Any]:
    """Build the scalar portion of the public work record projection."""
    fm: Dict[str, Any] = {}
    for fm_key, col_name, coercer in WORKS_SCHEMA:
        raw = work_record.get(col_name)
        fm[fm_key] = coercer(raw)
    return fm


def parse_source_list(raw: Any, sep: str = ",") -> List[str]:
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if not is_empty(item)]
    return parse_list(raw, sep=sep)


def parse_work_record_series_ids(work_record: Mapping[str, Any]) -> List[str]:
    series_ids: List[str] = []
    seen_series_ids: set[str] = set()
    for raw_series_id in parse_source_list(work_record.get("series_ids")):
        try:
            sid = normalize_series_id(raw_series_id)
        except ValueError:
            continue
        if sid in seen_series_ids:
            continue
        seen_series_ids.add(sid)
        series_ids.append(sid)
    return series_ids


def compute_work_checksum(record: Mapping[str, Any]) -> str:
    """Compute a deterministic checksum for a generated JSON record."""
    payload = dict(record)
    payload.pop("checksum", None)

    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    h = hashlib.blake2b(canonical, digest_size=16)
    return h.hexdigest()


def build_canonical_work_record(
    wid: str,
    *,
    work_meta_by_id: Mapping[str, Mapping[str, Any]],
    source_work_record: Mapping[str, Any],
    series_title_by_id: Mapping[str, str],
    series_sort_by_series_id: Mapping[str, Mapping[str, str]],
    field_order: List[str] | None = None,
) -> Optional[Dict[str, Any]]:
    base = work_meta_by_id.get(wid)
    if base is None:
        return None
    fm: Dict[str, Any] = {"work_id": wid}
    fm.update(dict(base))
    for key in ["downloads", "links"]:
        items = source_work_record.get(key)
        if isinstance(items, list) and items:
            fm[key] = list(items)
    raw_series_ids = fm.get("series_ids")
    series_ids = [coerce_string(item) for item in raw_series_ids] if isinstance(raw_series_ids, list) else []
    series_ids = [item for item in series_ids if item is not None]
    sid = series_ids[0] if series_ids else coerce_string(fm.get("series_id"))
    fm["series_id"] = sid
    fm["series_ids"] = series_ids
    fm["series_title"] = series_title_by_id.get(sid) if sid is not None else None
    fm["series_sort"] = series_sort_by_series_id.get(sid, {}).get(wid, wid) if sid is not None else wid

    ordered: Dict[str, Any] = {}
    for key in field_order or WORKS_FIELD_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key, value in fm.items():
        if key not in ordered:
            ordered[key] = value
    ordered["checksum"] = compute_work_checksum(ordered)
    return ordered


def build_canonical_detail_record(
    wid: str,
    did: str,
    title: Optional[str],
    width_px: Optional[int],
    height_px: Optional[int],
) -> Dict[str, Any]:
    detail_uid = f"{wid}-{did}"
    dfm: Dict[str, Any] = {
        "work_id": wid,
        "detail_id": did,
        "detail_uid": detail_uid,
        "title": title,
        "width_px": width_px,
        "height_px": height_px,
    }
    return compact_json_object(dfm)


def build_work_json_record(work_record: Mapping[str, Any]) -> Dict[str, Any]:
    public_record = dict(work_record)
    public_record.pop("series_id", None)
    public_record.pop("series_title", None)
    public_record.pop("series_sort", None)
    public_record.pop("storage", None)
    public_record.pop("title_sort", None)
    public_record.pop("checksum", None)
    return compact_json_object(public_record)


def build_series_json_record(series_record: Mapping[str, Any]) -> Dict[str, Any]:
    public_record = dict(series_record)
    public_record.pop("layout", None)
    public_record.pop("checksum", None)
    public_record.pop("works", None)
    public_record.pop("primary_work_id", None)
    public_record.pop("notes", None)
    return compact_json_object(public_record)


def build_sections_from_detail_sections(detail_sections: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    for section in detail_sections:
        detail_records = section.get("details")
        details = [dict(detail) for detail in detail_records] if isinstance(detail_records, list) else []
        sections.append(
            compact_json_object(
                {
                    "section_id": coerce_string(section.get("section_id")),
                    "section_title": coerce_string(section.get("section_title")),
                    "section_order": coerce_int(section.get("section_order")),
                    "detail_sort": coerce_string(section.get("detail_sort")),
                    "details": details,
                }
            )
        )
    return sections
