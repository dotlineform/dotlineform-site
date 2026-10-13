"""Pure record projection helpers for generated catalogue artifacts."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from catalogue.catalogue_generation_common import (
    coerce_int,
    compact_json_object,
    compute_payload_version,
)


WORK_RECORD_SCHEMA_VERSION = "work_record_v11"
GALLERY_RECORD_SCHEMA_VERSION = "gallery_record_v3"


def build_work_record_projection(work_record: Mapping[str, Any]) -> Dict[str, Any]:
    """Copy UI-authored values and Save-measured pixels without repair or validation."""
    fm: Dict[str, Any] = {field: work_record[field] for field in ("title", "year", "year_display")}
    for field in ("width_px", "height_px", "height_cm", "width_cm", "depth_cm"):
        if field in work_record:
            fm[field] = work_record[field]
    for field in ("medium", "duration"):
        if field in work_record:
            value = work_record[field]
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Work {field} must be a string or null")
            fm[field] = value
    fm["media_version"] = coerce_int(work_record.get("media_version"))
    return fm


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
