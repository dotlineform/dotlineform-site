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



WORK_RECORD_SCHEMA_VERSION = "work_record_v6"
SERIES_RECORD_SCHEMA_VERSION = "series_record_v5"


# Define the Works source-record projection once so adding a new field is a one-line change.
# Each entry is: (record_key, source_column_name, coercer)
WORKS_SCHEMA: List[tuple[str, str, Any]] = [
    ("artist", "artist", coerce_string),
    ("title", "title", coerce_string),
    ("year", "year", coerce_int),
    ("year_display", "year_display", coerce_string),
    ("medium_type", "medium_type", coerce_string),
    ("medium_caption", "medium_caption", coerce_string),
    ("duration", "duration", coerce_string),
    ("height_cm", "height_cm", coerce_numeric),
    ("width_cm", "width_cm", coerce_numeric),
    ("depth_cm", "depth_cm", coerce_numeric),
    ("width_px", "width_px", coerce_int),
    ("height_px", "height_px", coerce_int),
    ("media_version", "media_version", coerce_int),
    # tags handled separately (csv list)
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


def normalize_catalogue_documents(values: Sequence[Mapping[str, Any]]) -> List[Dict[str, str]]:
    if isinstance(values, (str, bytes)):
        raise ValueError("documents must be an array")
    documents_by_url: Dict[str, str] = {}
    for index, value in enumerate(values):
        if not isinstance(value, Mapping) or set(value) != {"url", "title"}:
            raise ValueError(f"documents[{index}] must contain only url and title")
        url = value.get("url")
        title = value.get("title")
        if not isinstance(url, str) or not url or url != url.strip():
            raise ValueError(f"documents[{index}].url must be a non-empty trimmed string")
        if not isinstance(title, str) or not title or title != title.strip():
            raise ValueError(f"documents[{index}].title must be a non-empty trimmed string")
        existing_title = documents_by_url.get(url)
        if existing_title is not None and existing_title != title:
            raise ValueError(f"documents contains conflicting titles for {url!r}")
        documents_by_url[url] = title
    return [
        {"url": url, "title": title}
        for url, title in sorted(documents_by_url.items())
    ]


def build_work_json_record(
    work_record: Mapping[str, Any],
    *,
    documents: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    public_record = dict(work_record)
    public_record.pop("series_title", None)
    public_record.pop("series_sort", None)
    public_record.pop("title_sort", None)
    public_record.pop("checksum", None)
    public_record["documents"] = normalize_catalogue_documents(documents)
    return compact_json_object(public_record)


def build_series_json_record(
    series_record: Mapping[str, Any],
    *,
    documents: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    public_record = dict(series_record)
    public_record.pop("layout", None)
    public_record.pop("checksum", None)
    public_record.pop("works", None)
    public_record.pop("primary_work_id", None)
    public_record.pop("notes", None)
    public_record["documents"] = normalize_catalogue_documents(documents)
    return compact_json_object(public_record)


def build_work_json_payload(
    *,
    work_id: str,
    work_record: Mapping[str, Any],
    sections: Sequence[Mapping[str, Any]],
    generated_at_utc: str,
    count: int,
) -> Dict[str, Any]:
    """Finalize one complete generated Work by-ID payload."""

    public_record = dict(work_record)
    raw_documents = public_record.get("documents", [])
    if not isinstance(raw_documents, list):
        raise ValueError("work.documents must be an array")
    public_record["documents"] = normalize_catalogue_documents(raw_documents)
    public_sections = [dict(section) for section in sections]
    version_input = {"schema": WORK_RECORD_SCHEMA_VERSION, "work": public_record, "sections": public_sections}
    return compact_json_object(
        {
            "header": {
                "schema": WORK_RECORD_SCHEMA_VERSION,
                "version": compute_payload_version(version_input),
                "generated_at_utc": generated_at_utc,
                "work_id": work_id,
                "count": count,
            },
            "work": public_record,
            "sections": public_sections,
        }
    )


def build_series_json_payload(
    *,
    series_id: str,
    series_record: Mapping[str, Any],
    member_works: Sequence[Mapping[str, Any]],
    generated_at_utc: str,
) -> Dict[str, Any]:
    """Finalize one complete generated Series by-ID payload."""

    public_record = dict(series_record)
    raw_documents = public_record.get("documents", [])
    if not isinstance(raw_documents, list):
        raise ValueError("series.documents must be an array")
    if str(public_record.get("series_id") or "") != series_id:
        raise ValueError(f"series.series_id must match exact payload target {series_id}")
    public_record["documents"] = normalize_catalogue_documents(raw_documents)
    public_member_works = [compact_json_object(dict(work)) for work in member_works]
    version_input = {"schema": SERIES_RECORD_SCHEMA_VERSION, "series": public_record, "member_works": public_member_works}
    return compact_json_object(
        {
            "header": {
                "schema": SERIES_RECORD_SCHEMA_VERSION,
                "version": compute_payload_version(version_input),
                "generated_at_utc": generated_at_utc,
                "series_id": series_id,
                "count": len(public_member_works),
            },
            "series": public_record,
            "member_works": public_member_works,
        }
    )


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
