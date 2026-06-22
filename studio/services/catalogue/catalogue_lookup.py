from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    from catalogue.catalogue_source import (
        DEFAULT_SOURCE_DIR,
        CatalogueSourceRecords,
        build_detail_section_resolution_by_uid,
        detail_sort_key_for_section,
        normalize_text,
        ordered_work_detail_sections,
        records_from_json_source,
        section_sort_key,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.catalogue_source import (  # type: ignore
        DEFAULT_SOURCE_DIR,
        CatalogueSourceRecords,
        build_detail_section_resolution_by_uid,
        detail_sort_key_for_section,
        normalize_text,
        ordered_work_detail_sections,
        records_from_json_source,
        section_sort_key,
    )


DEFAULT_LOOKUP_DIR = Path("studio/data/generated/catalogue-lookup")

SCHEMAS = {
    "work_search": "studio_catalogue_lookup_work_search_v1",
    "series_search": "studio_catalogue_lookup_series_search_v1",
    "work_detail_search": "studio_catalogue_lookup_work_detail_search_v1",
    "work_record": "studio_catalogue_work_record_v1",
    "work_detail_record": "studio_catalogue_work_detail_record_v1",
    "series_record": "studio_catalogue_lookup_series_record_v1",
}

WORK_SEARCH_FIELDS = frozenset({"work_id", "title", "year_display", "status", "series_ids"})
SERIES_MEMBER_WORK_FIELDS = frozenset({"work_id", "title", "year_display", "status", "series_ids"})
WORK_DETAIL_WORK_SUMMARY_FIELDS = frozenset({"title"})

WORK_DETAIL_SEARCH_FIELDS = frozenset({
    "detail_uid",
    "work_id",
    "detail_id",
    "title",
    "section_id",
    "section_title",
    "section_order",
    "detail_sort",
    "details_subfolder",
    "project_filename",
})
WORK_DETAIL_PARENT_WORK_FIELDS = frozenset({
    "work_id",
    "detail_id",
    "title",
    "section_id",
    "section_title",
    "section_order",
    "detail_sort",
    "details_subfolder",
    "project_filename",
})

SERIES_SEARCH_FIELDS = frozenset({"series_id", "title", "status", "primary_work_id"})
WORK_SERIES_SUMMARY_FIELDS = frozenset({"title"})


def normalize_optional_int(value: Any) -> int | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def build_resolved_work_detail_record(record: Mapping[str, Any], section_resolution: Mapping[str, Any]) -> Dict[str, Any]:
    detail_payload = dict(record)
    detail_payload.pop("project_subfolder", None)
    for field in ("section_id", "section_title", "details_subfolder", "section_order", "detail_sort"):
        value = section_resolution.get(field)
        if value is not None and value != "":
            detail_payload[field] = value
    return detail_payload


def build_work_search_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "work_id": work_id,
        "title": normalize_text(record.get("title")),
        "year_display": normalize_text(record.get("year_display")),
        "status": normalize_text(record.get("status")),
        "series_ids": list(record.get("series_ids", [])) if isinstance(record.get("series_ids"), list) else [],
    }


def build_series_member_work_item(work_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "work_id": work_id,
        "title": normalize_text(record.get("title")),
        "year_display": normalize_text(record.get("year_display")),
        "status": normalize_text(record.get("status")),
        "series_ids": list(record.get("series_ids", [])) if isinstance(record.get("series_ids"), list) else [],
    }


def build_series_search_item(series_id: str, record: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "series_id": series_id,
        "title": normalize_text(record.get("title")),
        "status": normalize_text(record.get("status")),
        "primary_work_id": normalize_text(record.get("primary_work_id")),
    }


def build_work_detail_search_item(
    detail_uid: str,
    record: Mapping[str, Any],
    section_resolution: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "detail_uid": detail_uid,
        "work_id": normalize_text(record.get("work_id")),
        "detail_id": normalize_text(record.get("detail_id")),
        "title": normalize_text(record.get("title")),
        "section_id": normalize_text(section_resolution.get("section_id")),
        "section_title": normalize_text(section_resolution.get("section_title")),
        "section_order": section_resolution.get("section_order"),
        "detail_sort": normalize_text(section_resolution.get("detail_sort")),
        "details_subfolder": normalize_text(section_resolution.get("details_subfolder")),
        "project_filename": normalize_text(record.get("project_filename")),
    }


def build_work_lookup_payload(records: CatalogueSourceRecords, work_id: str) -> Dict[str, Any]:
    record = records.works.get(work_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"work_id not found: {work_id}")

    series_title_by_id = {
        series_id: normalize_text(series_record.get("title"))
        for series_id, series_record in records.series.items()
    }

    detail_sections = []
    for section in ordered_work_detail_sections(records, work_id):
        items = [
            {
                "detail_uid": normalize_text(item.get("detail_uid")),
                "detail_id": normalize_text(item.get("detail_id")),
                "title": normalize_text(item.get("title")),
                "project_filename": normalize_text(item.get("project_filename")),
            }
            for item in section.get("details", [])
            if isinstance(item, Mapping)
        ]
        detail_sections.append(
            {
                "section_id": normalize_text(section.get("section_id")),
                "details_subfolder": normalize_text(section.get("details_subfolder")),
                "section_title": normalize_text(section.get("section_title")),
                "section_order": section.get("section_order"),
                "detail_sort": section.get("detail_sort"),
                "count": len(items),
                "details": items,
            }
        )

    series_summary = [
        {
            "series_id": series_id,
            "title": series_title_by_id.get(series_id, ""),
        }
        for series_id in (record.get("series_ids", []) if isinstance(record.get("series_ids"), list) else [])
    ]

    return {
        "header": {
            "schema": SCHEMAS["work_record"],
        },
        "work": dict(record),
        "detail_sections": detail_sections,
        "downloads": list(record.get("downloads", [])) if isinstance(record.get("downloads"), list) else [],
        "links": list(record.get("links", [])) if isinstance(record.get("links"), list) else [],
        "series_summary": series_summary,
    }


def build_work_detail_lookup_payload(records: CatalogueSourceRecords, detail_uid: str) -> Dict[str, Any]:
    record = records.work_details.get(detail_uid)
    if not isinstance(record, Mapping):
        raise KeyError(f"detail_uid not found: {detail_uid}")
    section_resolution = build_detail_section_resolution_by_uid(
        records.work_details,
        records.work_detail_sections,
    ).get(detail_uid, {})
    detail_payload = build_resolved_work_detail_record(record, section_resolution)
    work_id = normalize_text(record.get("work_id"))
    work_record = records.works.get(work_id) or {}
    return {
        "header": {
            "schema": SCHEMAS["work_detail_record"],
        },
        "work_detail": detail_payload,
        "work_summary": {
            "work_id": work_id,
            "title": normalize_text(work_record.get("title")),
        },
    }


def build_series_lookup_payload(records: CatalogueSourceRecords, series_id: str) -> Dict[str, Any]:
    record = records.series.get(series_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"series_id not found: {series_id}")

    members = []
    for work_id, work_record in records.works.items():
        series_ids = work_record.get("series_ids", [])
        if not isinstance(series_ids, list) or series_id not in series_ids:
            continue
        members.append(build_series_member_work_item(work_id, work_record))
    members.sort(key=lambda item: item["work_id"])

    return {
        "header": {
            "schema": SCHEMAS["series_record"],
        },
        "series": dict(record),
        "member_works": members,
    }


def build_work_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    for work_id, record in records.works.items():
        items.append(build_work_search_item(work_id, record))
    items.sort(key=lambda item: item["work_id"])
    return {
        "header": {
            "schema": SCHEMAS["work_search"],
            "count": len(items),
        },
        "items": items,
    }


def build_series_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    for series_id, record in records.series.items():
        items.append(build_series_search_item(series_id, record))
    items.sort(key=lambda item: item["series_id"])
    return {
        "header": {
            "schema": SCHEMAS["series_search"],
            "count": len(items),
        },
        "items": items,
    }


def build_work_detail_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    section_resolution_by_uid = build_detail_section_resolution_by_uid(
        records.work_details,
        records.work_detail_sections,
    )
    for detail_uid, record in records.work_details.items():
        items.append(build_work_detail_search_item(detail_uid, record, section_resolution_by_uid.get(detail_uid, {})))
    items.sort(key=lambda item: item["detail_uid"])
    return {
        "header": {
            "schema": SCHEMAS["work_detail_search"],
            "count": len(items),
        },
        "items": items,
    }


def build_catalogue_lookup_payloads(records: CatalogueSourceRecords) -> Dict[str, Any]:
    work_search_items = []
    series_search_items = []
    series_by_id: Dict[str, Dict[str, Any]] = {}

    for work_id, record in records.works.items():
        work_search_items.append(build_work_search_item(work_id, record))

    for series_id, record in records.series.items():
        series_search_items.append(build_series_search_item(series_id, record))
        members = []
        for work_id, work_record in records.works.items():
            series_ids = work_record.get("series_ids", [])
            if not isinstance(series_ids, list) or series_id not in series_ids:
                continue
            members.append(build_series_member_work_item(work_id, work_record))
        members.sort(key=lambda item: item["work_id"])
        series_by_id[series_id] = {
            "header": {
                "schema": SCHEMAS["series_record"],
            },
            "series": record,
            "member_works": members,
        }

    work_search_items.sort(key=lambda item: item["work_id"])
    series_search_items.sort(key=lambda item: item["series_id"])

    return {
        "root": {
            "work_search.json": {
                "header": {
                    "schema": SCHEMAS["work_search"],
                    "count": len(work_search_items),
                },
                "items": work_search_items,
            },
            "series_search.json": {
                "header": {
                    "schema": SCHEMAS["series_search"],
                    "count": len(series_search_items),
                },
                "items": series_search_items,
            },
        },
        "series": series_by_id,
    }


def write_catalogue_lookup_payloads(lookup_dir: Path, payloads: Mapping[str, Any]) -> list[Path]:
    lookup_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    root_payloads = payloads.get("root", {})
    for name, payload in root_payloads.items():
        path = lookup_dir / name
        _atomic_write_json(path, payload)
        written.append(path)

    for folder in ["series"]:
        target_dir = lookup_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        current_files = {
            path.name
            for path in target_dir.glob("*.json")
            if path.is_file()
        }
        next_payloads = payloads.get(folder, {})
        expected_files = {f"{key}.json" for key in next_payloads.keys()}
        for stale_name in sorted(current_files - expected_files):
            try:
                (target_dir / stale_name).unlink()
            except OSError:
                pass
        for key, payload in next_payloads.items():
            path = target_dir / f"{key}.json"
            _atomic_write_json(path, payload)
            written.append(path)

    return written


def build_and_write_catalogue_lookup(source_dir: Path, lookup_dir: Path) -> list[Path]:
    records = records_from_json_source(source_dir)
    payloads = build_catalogue_lookup_payloads(records)
    return write_catalogue_lookup_payloads(lookup_dir, payloads)


def write_lookup_root_payload(lookup_dir: Path, name: str, payload: Mapping[str, Any]) -> Path:
    lookup_dir.mkdir(parents=True, exist_ok=True)
    path = lookup_dir / name
    _atomic_write_json(path, payload)
    return path


def write_work_lookup_payload(lookup_dir: Path, work_id: str, payload: Mapping[str, Any]) -> Path:
    works_dir = lookup_dir / "works"
    works_dir.mkdir(parents=True, exist_ok=True)
    path = works_dir / f"{work_id}.json"
    _atomic_write_json(path, payload)
    return path


def write_detail_lookup_payload(lookup_dir: Path, detail_uid: str, payload: Mapping[str, Any]) -> Path:
    target_dir = lookup_dir / "work_details"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{detail_uid}.json"
    _atomic_write_json(path, payload)
    return path


def write_series_lookup_payload(lookup_dir: Path, series_id: str, payload: Mapping[str, Any]) -> Path:
    target_dir = lookup_dir / "series"
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{series_id}.json"
    _atomic_write_json(path, payload)
    return path


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, path)
