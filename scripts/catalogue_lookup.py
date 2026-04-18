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
    "work_file_record": "studio_catalogue_lookup_work_file_record_v1",
    "work_link_record": "studio_catalogue_lookup_work_link_record_v1",
    "series_record": "studio_catalogue_lookup_series_record_v1",
    "meta": "studio_catalogue_lookup_meta_v1",
}


def record_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_catalogue_lookup_payloads(records: CatalogueSourceRecords) -> Dict[str, Any]:
    work_search_items = []
    series_search_items = []
    detail_search_items = []
    works_by_id: Dict[str, Dict[str, Any]] = {}
    work_details_by_uid: Dict[str, Dict[str, Any]] = {}
    work_files_by_uid: Dict[str, Dict[str, Any]] = {}
    work_links_by_uid: Dict[str, Dict[str, Any]] = {}
    series_by_id: Dict[str, Dict[str, Any]] = {}

    series_title_by_id = {
        series_id: normalize_text(record.get("title"))
        for series_id, record in records.series.items()
    }

    details_by_work_id: Dict[str, list[Dict[str, Any]]] = {}
    files_by_work_id: Dict[str, list[Dict[str, Any]]] = {}
    links_by_work_id: Dict[str, list[Dict[str, Any]]] = {}
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
        details_by_work_id.setdefault(work_id, []).append(detail_item)

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

    for file_uid, record in records.work_files.items():
        work_id = normalize_text(record.get("work_id"))
        file_item = {
            "file_uid": file_uid,
            "work_id": work_id,
            "filename": normalize_text(record.get("filename")),
            "label": normalize_text(record.get("label")),
            "status": normalize_text(record.get("status")),
        }
        files_by_work_id.setdefault(work_id, []).append(file_item)
        work_record = records.works.get(work_id) or {}
        work_files_by_uid[file_uid] = {
            "header": {
                "schema": SCHEMAS["work_file_record"],
            },
            "work_file": record,
            "record_hash": record_hash(record),
            "work_summary": {
                "work_id": work_id,
                "title": normalize_text(work_record.get("title")),
            },
        }

    for link_uid, record in records.work_links.items():
        work_id = normalize_text(record.get("work_id"))
        link_item = {
            "link_uid": link_uid,
            "work_id": work_id,
            "url": normalize_text(record.get("url")),
            "label": normalize_text(record.get("label")),
            "status": normalize_text(record.get("status")),
        }
        links_by_work_id.setdefault(work_id, []).append(link_item)
        work_record = records.works.get(work_id) or {}
        work_links_by_uid[link_uid] = {
            "header": {
                "schema": SCHEMAS["work_link_record"],
            },
            "work_link": record,
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
        detail_sections = []
        grouped: Dict[str, list[Dict[str, Any]]] = {}
        for item in details_by_work_id.get(work_id, []):
            section_key = normalize_text(item.get("project_subfolder"))
            grouped.setdefault(section_key, []).append(item)
        # Re-read from canonical records so project_subfolder is present.
        grouped = {}
        for detail_uid, detail_record in records.work_details.items():
            if normalize_text(detail_record.get("work_id")) != work_id:
                continue
            section_key = normalize_text(detail_record.get("project_subfolder"))
            grouped.setdefault(section_key, []).append(
                {
                    "detail_uid": detail_uid,
                    "detail_id": normalize_text(detail_record.get("detail_id")),
                    "title": normalize_text(detail_record.get("title")),
                    "project_subfolder": section_key,
                    "status": normalize_text(detail_record.get("status")),
                }
            )
        for section_key in sorted(grouped):
            items = sorted(grouped[section_key], key=lambda item: item["detail_uid"])
            detail_sections.append(
                {
                    "project_subfolder": section_key,
                    "count": len(items),
                    "details": items,
                }
            )
        works_by_id[work_id] = {
            "header": {
                "schema": SCHEMAS["work_record"],
            },
            "work": record,
            "record_hash": record_hash(record),
            "detail_sections": detail_sections,
            "work_files": sorted(files_by_work_id.get(work_id, []), key=lambda item: item["file_uid"]),
            "work_links": sorted(links_by_work_id.get(work_id, []), key=lambda item: item["link_uid"]),
            "series_summary": [
                {
                    "series_id": series_id,
                    "title": series_title_by_id.get(series_id, ""),
                }
                for series_id in (record.get("series_ids", []) if isinstance(record.get("series_ids"), list) else [])
            ],
        }

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
        "work_files": work_files_by_uid,
        "work_links": work_links_by_uid,
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

    for folder in ["works", "work_details", "work_files", "work_links", "series"]:
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


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, path)
