"""Pure record projection helpers for generated catalogue artifacts."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from catalogue.catalogue_generation_common import (
    coerce_int,
    coerce_numeric,
    coerce_string,
    compact_json_object,
    compute_payload_version,
)



WORK_RECORD_SCHEMA_VERSION = "work_record_v11"
GALLERY_RECORD_SCHEMA_VERSION = "gallery_record_v3"


# Define the Works source-record projection once so adding a new field is a one-line change.
# Each entry is: (record_key, source_column_name, coercer)
WORKS_SCHEMA: List[tuple[str, str, Any]] = [
    ("title", "title", coerce_string),
    ("year", "year", coerce_int),
    ("year_display", "year_display", coerce_string),
    ("medium", "medium", coerce_string),
    ("duration", "duration", coerce_string),
    ("height_cm", "height_cm", coerce_numeric),
    ("width_cm", "width_cm", coerce_numeric),
    ("depth_cm", "depth_cm", coerce_numeric),
    ("width_px", "width_px", coerce_int),
    ("height_px", "height_px", coerce_int),
    ("media_version", "media_version", coerce_int),
]


def build_work_record_projection(work_record: Mapping[str, Any]) -> Dict[str, Any]:
    """Build the scalar portion of the public work record projection."""
    fm: Dict[str, Any] = {}
    for fm_key, col_name, coercer in WORKS_SCHEMA:
        raw = work_record.get(col_name)
        fm[fm_key] = coercer(raw)
    return fm


def build_canonical_detail_record(
    wid: str,
    did: str,
    title: Optional[str],
    width_px: Optional[int],
    height_px: Optional[int],
    media_version: Optional[int],
) -> Dict[str, Any]:
    detail_uid = f"{wid}-{did}"
    dfm: Dict[str, Any] = {
        "work_id": wid,
        "detail_id": did,
        "detail_uid": detail_uid,
        "title": title,
        "width_px": width_px,
        "height_px": height_px,
        "media_version": media_version,
    }
    return compact_json_object(dfm)


def build_work_json_payload(
    *,
    work_record: Mapping[str, Any],
    generated_at_utc: str,
) -> Dict[str, Any]:
    """Finalize one complete generated Work by-ID payload."""

    public_record = dict(work_record)
    if not isinstance(public_record.get("galleries"), list):
        raise ValueError("work.galleries must be an array")
    version_input = {"schema": WORK_RECORD_SCHEMA_VERSION, "work": public_record}
    return compact_json_object(
        {
            "header": {
                "schema": WORK_RECORD_SCHEMA_VERSION,
                "version": compute_payload_version(version_input),
                "generated_at_utc": generated_at_utc,
            },
            "work": public_record,
        }
    )


def build_gallery_json_payload(
    *,
    gallery_id: str,
    gallery_record: Mapping[str, Any],
    member_works: Sequence[dict[str, Any]],
    generated_at_utc: str,
) -> Dict[str, Any]:
    """Wrap already projected member rows without reprojecting retained members."""
    public_record = dict(gallery_record)
    if public_record.get("gallery_id") != gallery_id:
        raise ValueError(f"gallery.gallery_id must match exact payload target {gallery_id}")
    return {
        "header": {
            "schema": GALLERY_RECORD_SCHEMA_VERSION,
            "generated_at_utc": generated_at_utc,
            "gallery_id": gallery_id,
        },
        "gallery": public_record,
        "member_works": list(member_works),
    }
