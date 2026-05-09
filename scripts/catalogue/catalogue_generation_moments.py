#!/usr/bin/env python3
"""Pure moment artifact builders for generated catalogue payloads."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

try:
    from catalogue import catalogue_generation_records as records
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        normalize_status,
        parse_date,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue import catalogue_generation_records as records
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        normalize_status,
        parse_date,
    )


MISSING_ID = "missing_id"
NOT_SELECTED = "not_selected"
NOT_ACTIONABLE_STATUS = "not_actionable_status"
INVALID_SLUG = "invalid_slug"
MISSING_PROSE = "missing_prose"


@dataclass(frozen=True)
class MomentArtifactDecision:
    moment_id: str
    selected: bool
    actionable: bool
    slug_safe: bool
    prose_exists: bool
    skip_reason: Optional[str] = None

    @property
    def should_generate(self) -> bool:
        return self.skip_reason is None


def is_slug_safe(value: str) -> bool:
    return bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", str(value or "")))


def moment_entry_id(moment_entry: Mapping[str, Any]) -> str:
    return str(moment_entry.get("moment_id") or "").strip().lower()


def is_actionable_moment_status(status_value: Any, *, refresh_published: bool) -> bool:
    status = normalize_status(status_value)
    if status == "draft":
        return True
    if status == "published" and refresh_published:
        return True
    return False


def is_selected_moment(moment_id: str, selected_moment_ids: Optional[set[str]]) -> bool:
    return selected_moment_ids is None or moment_id in selected_moment_ids


def decide_moment_artifact(
    moment_entry: Mapping[str, Any],
    *,
    selected_moment_ids: Optional[set[str]],
    refresh_published: bool,
    prose_exists: bool,
) -> MomentArtifactDecision:
    moment_id = moment_entry_id(moment_entry)
    selected = bool(moment_id and is_selected_moment(moment_id, selected_moment_ids))
    actionable = is_actionable_moment_status(moment_entry.get("status"), refresh_published=refresh_published)
    slug_safe = bool(moment_id and is_slug_safe(moment_id))

    if not moment_id:
        skip_reason = MISSING_ID
    elif not selected:
        skip_reason = NOT_SELECTED
    elif not actionable:
        skip_reason = NOT_ACTIONABLE_STATUS
    elif not slug_safe:
        skip_reason = INVALID_SLUG
    elif not prose_exists:
        skip_reason = MISSING_PROSE
    else:
        skip_reason = None

    return MomentArtifactDecision(
        moment_id=moment_id,
        selected=selected,
        actionable=actionable,
        slug_safe=slug_safe,
        prose_exists=prose_exists,
        skip_reason=skip_reason,
    )


def build_moment_source_records(
    source_moment_index: Mapping[str, Mapping[str, Any]],
    *,
    moments_prose_root: Path,
    moments_images_root: Path,
) -> list[Dict[str, Any]]:
    source_records: list[Dict[str, Any]] = []
    for moment_id in sorted(source_moment_index.keys()):
        source_record = source_moment_index[moment_id]
        source_image_file = coerce_string(source_record.get("source_image_file")) or f"{moment_id}.jpg"
        source_records.append(
            {
                "moment_id": moment_id,
                "title": coerce_string(source_record.get("title")) or moment_id,
                "status": normalize_status(source_record.get("status")),
                "published_date": parse_date(source_record.get("published_date")),
                "date": parse_date(source_record.get("date")),
                "date_display": coerce_string(source_record.get("date_display")),
                "width_px": None,
                "height_px": None,
                "image_file": f"{moment_id}.jpg",
                "source_image_file": source_image_file,
                "image_alt": coerce_string(source_record.get("image_alt")),
                "source_prose_path": Path(
                    coerce_string(source_record.get("source_prose_path")) or (moments_prose_root / f"{moment_id}.md")
                ),
                "source_image_path": Path(
                    coerce_string(source_record.get("source_image_path")) or (moments_images_root / source_image_file)
                ),
            }
        )
    return source_records


def build_moment_runtime_record(
    moment_entry: Mapping[str, Any],
    *,
    source_image_exists: bool,
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
    include_layout: bool = False,
) -> Dict[str, Any]:
    moment_id = moment_entry_id(moment_entry)
    title = coerce_string(moment_entry.get("title")) or moment_id
    image_file = coerce_string(moment_entry.get("image_file")) or f"{moment_id}.jpg"
    image_alt = coerce_string(moment_entry.get("image_alt")) or title or moment_id

    images_list: list[Dict[str, Any]] = []
    if image_file is not None and source_image_exists:
        images_list.append(
            {
                "file": image_file,
                "alt": image_alt,
            }
        )

    moment_record: Dict[str, Any] = {
        "moment_id": moment_id,
        "title": title,
        "date": parse_date(moment_entry.get("date")),
        "date_display": coerce_string(moment_entry.get("date_display")),
        "images": images_list,
        "width_px": coerce_int(width_px if width_px is not None else moment_entry.get("width_px")),
        "height_px": coerce_int(height_px if height_px is not None else moment_entry.get("height_px")),
    }
    if include_layout:
        moment_record["layout"] = "moment"
    return moment_record


def build_moment_record_payload(
    moment_record: Mapping[str, Any],
    *,
    content_html: str,
    generated_at_utc: str,
) -> Dict[str, Any]:
    moment_id = coerce_string(moment_record.get("moment_id")) or ""
    moment_json_record = records.build_moment_json_record(moment_record)
    payload_version = compute_payload_version(
        compact_json_object({"moment": moment_json_record, "content_html": content_html})
    )
    return compact_json_object(
        {
            "header": {
                "schema": "moment_record_v1",
                "version": payload_version,
                "generated_at_utc": generated_at_utc,
                "moment_id": moment_id,
            },
            "moment": moment_json_record,
            "content_html": content_html,
        }
    )


def build_moments_index_payload(
    moment_records: Iterable[Mapping[str, Any]],
    *,
    generated_at_utc: str,
) -> Dict[str, Any]:
    moments_payload: Dict[str, Dict[str, Any]] = {}
    for moment_record in sorted(moment_records, key=lambda item: coerce_string(item.get("moment_id")) or ""):
        moment_id = coerce_string(moment_record.get("moment_id"))
        if not moment_id:
            continue
        moments_payload[moment_id] = records.build_moment_index_record(moment_record)

    version_payload = compact_json_object(
        {
            "schema": "moments_index_v1",
            "moments": moments_payload,
        }
    )
    version = compute_payload_version(version_payload)
    return compact_json_object(
        {
            "header": {
                "schema": "moments_index_v1",
                "version": version,
                "generated_at_utc": generated_at_utc,
                "count": len(moments_payload),
            },
            "moments": moments_payload,
        }
    )
