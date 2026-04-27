from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    from catalogue_source import (
        DEFAULT_SOURCE_DIR,
        CatalogueSourceRecords,
        normalize_text,
        records_from_json_source,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import (  # type: ignore
        DEFAULT_SOURCE_DIR,
        CatalogueSourceRecords,
        normalize_text,
        records_from_json_source,
    )


DEFAULT_LOOKUP_DIR = Path("assets/studio/data/catalogue_lookup")

SCHEMAS = {
    "work_search": "studio_catalogue_lookup_work_search_v1",
    "series_search": "studio_catalogue_lookup_series_search_v1",
    "work_detail_search": "studio_catalogue_lookup_work_detail_search_v1",
    "work_record": "studio_catalogue_lookup_work_record_v1",
    "work_detail_record": "studio_catalogue_lookup_work_detail_record_v1",
    "series_record": "studio_catalogue_lookup_series_record_v1",
    "meta": "studio_catalogue_lookup_meta_v1",
}


def record_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_work_lookup_payload(records: CatalogueSourceRecords, work_id: str) -> Dict[str, Any]:
    record = records.works.get(work_id)
    if not isinstance(record, Mapping):
        raise KeyError(f"work_id not found: {work_id}")

    series_title_by_id = {
        series_id: normalize_text(series_record.get("title"))
        for series_id, series_record in records.series.items()
    }

    grouped_details: Dict[str, list[Dict[str, Any]]] = {}
    for detail_uid, detail_record in records.work_details.items():
        if normalize_text(detail_record.get("work_id")) != work_id:
            continue
        section_key = normalize_text(detail_record.get("project_subfolder"))
        grouped_details.setdefault(section_key, []).append(
            {
                "detail_uid": detail_uid,
                "detail_id": normalize_text(detail_record.get("detail_id")),
                "title": normalize_text(detail_record.get("title")),
                "project_subfolder": section_key,
                "status": normalize_text(detail_record.get("status")),
            }
        )

    detail_sections = []
    for section_key in sorted(grouped_details):
        items = sorted(grouped_details[section_key], key=lambda item: item["detail_uid"])
        detail_sections.append(
            {
                "project_subfolder": section_key,
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
        "record_hash": record_hash(record),
        "detail_sections": detail_sections,
        "downloads": list(record.get("downloads", [])) if isinstance(record.get("downloads"), list) else [],
        "links": list(record.get("links", [])) if isinstance(record.get("links"), list) else [],
        "series_summary": series_summary,
    }


def build_work_detail_lookup_payload(records: CatalogueSourceRecords, detail_uid: str) -> Dict[str, Any]:
    record = records.work_details.get(detail_uid)
    if not isinstance(record, Mapping):
        raise KeyError(f"detail_uid not found: {detail_uid}")
    work_id = normalize_text(record.get("work_id"))
    work_record = records.works.get(work_id) or {}
    return {
        "header": {
            "schema": SCHEMAS["work_detail_record"],
        },
        "work_detail": dict(record),
        "record_hash": record_hash(record),
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
        members.append(
            {
                "work_id": work_id,
                "title": normalize_text(work_record.get("title")),
                "year_display": normalize_text(work_record.get("year_display")),
                "status": normalize_text(work_record.get("status")),
                "series_ids": list(series_ids),
                "record_hash": record_hash(work_record),
            }
        )
    members.sort(key=lambda item: item["work_id"])

    return {
        "header": {
            "schema": SCHEMAS["series_record"],
        },
        "series": dict(record),
        "record_hash": record_hash(record),
        "member_works": members,
    }


def build_work_search_payload(records: CatalogueSourceRecords) -> Dict[str, Any]:
    items = []
    for work_id, record in records.works.items():
        items.append(
            {
                "work_id": work_id,
                "title": normalize_text(record.get("title")),
                "year_display": normalize_text(record.get("year_display")),
                "status": normalize_text(record.get("status")),
                "series_ids": list(record.get("series_ids", [])) if isinstance(record.get("series_ids"), list) else [],
                "record_hash": record_hash(record),
            }
        )
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
        items.append(
            {
                "series_id": series_id,
                "title": normalize_text(record.get("title")),
                "status": normalize_text(record.get("status")),
                "primary_work_id": normalize_text(record.get("primary_work_id")),
                "record_hash": record_hash(record),
            }
        )
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
    for detail_uid, record in records.work_details.items():
        items.append(
            {
                "detail_uid": detail_uid,
                "work_id": normalize_text(record.get("work_id")),
                "detail_id": normalize_text(record.get("detail_id")),
                "title": normalize_text(record.get("title")),
                "status": normalize_text(record.get("status")),
            }
        )
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
    detail_search_items = []
    works_by_id: Dict[str, Dict[str, Any]] = {}
    work_details_by_uid: Dict[str, Dict[str, Any]] = {}
    series_by_id: Dict[str, Dict[str, Any]] = {}

    series_title_by_id = {
        series_id: normalize_text(record.get("title"))
        for series_id, record in records.series.items()
    }

    for detail_uid, record in records.work_details.items():
        work_id = normalize_text(record.get("work_id"))
        detail_item = {
            "detail_uid": detail_uid,
            "work_id": work_id,
            "detail_id": normalize_text(record.get("detail_id")),
            "title": normalize_text(record.get("title")),
            "status": normalize_text(record.get("status")),
        }
        detail_search_items.append(detail_item)

        work_record = records.works.get(work_id) or {}
        work_details_by_uid[detail_uid] = {
            "header": {
                "schema": SCHEMAS["work_detail_record"],
            },
            "work_detail": record,
            "record_hash": record_hash(record),
            "work_summary": {
                "work_id": work_id,
                "title": normalize_text(work_record.get("title")),
            },
        }

    for work_id, record in records.works.items():
        work_search_items.append(
            {
                "work_id": work_id,
                "title": normalize_text(record.get("title")),
                "year_display": normalize_text(record.get("year_display")),
                "status": normalize_text(record.get("status")),
                "series_ids": list(record.get("series_ids", [])) if isinstance(record.get("series_ids"), list) else [],
                "record_hash": record_hash(record),
            }
        )
        works_by_id[work_id] = build_work_lookup_payload(records, work_id)

    for series_id, record in records.series.items():
        series_search_items.append(
            {
                "series_id": series_id,
                "title": normalize_text(record.get("title")),
                "status": normalize_text(record.get("status")),
                "primary_work_id": normalize_text(record.get("primary_work_id")),
                "record_hash": record_hash(record),
            }
        )
        members = []
        for work_id, work_record in records.works.items():
            series_ids = work_record.get("series_ids", [])
            if not isinstance(series_ids, list) or series_id not in series_ids:
                continue
            members.append(
                {
                    "work_id": work_id,
                    "title": normalize_text(work_record.get("title")),
                    "year_display": normalize_text(work_record.get("year_display")),
                    "status": normalize_text(work_record.get("status")),
                    "series_ids": list(series_ids),
                    "record_hash": record_hash(work_record),
                }
            )
        members.sort(key=lambda item: item["work_id"])
        series_by_id[series_id] = {
            "header": {
                "schema": SCHEMAS["series_record"],
            },
            "series": record,
            "record_hash": record_hash(record),
            "member_works": members,
        }

    work_search_items.sort(key=lambda item: item["work_id"])
    series_search_items.sort(key=lambda item: item["series_id"])
    detail_search_items.sort(key=lambda item: item["detail_uid"])

    return {
        "root": {
            "meta.json": {
                "header": {
                    "schema": SCHEMAS["meta"],
                },
                "derived_from": str(DEFAULT_SOURCE_DIR),
                "work_count": len(records.works),
                "detail_count": len(records.work_details),
                "series_count": len(records.series),
            },
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
            "work_detail_search.json": {
                "header": {
                    "schema": SCHEMAS["work_detail_search"],
                    "count": len(detail_search_items),
                },
                "items": detail_search_items,
            },
        },
        "works": works_by_id,
        "work_details": work_details_by_uid,
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

    for retired_folder in ["work_files", "work_links"]:
        target_dir = lookup_dir / retired_folder
        if target_dir.exists():
            for stale_path in target_dir.glob("*.json"):
                if stale_path.is_file():
                    try:
                        stale_path.unlink()
                    except OSError:
                        pass
            try:
                target_dir.rmdir()
            except OSError:
                pass

    for folder in ["works", "work_details", "series"]:
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
