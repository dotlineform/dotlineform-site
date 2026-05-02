from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    from series_ids import normalize_series_id, parse_series_ids
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.series_ids import normalize_series_id, parse_series_ids


DEFAULT_SOURCE_DIR = Path("assets/studio/data/catalogue")

ACTIONABLE_STATUSES = {"draft", "published"}

SCHEMAS = {
    "works": "catalogue_source_works_v1",
    "work_details": "catalogue_source_work_details_v1",
    "series": "catalogue_source_series_v1",
    "meta": "catalogue_source_meta_v1",
}

SOURCE_FILES = {
    "works": "works.json",
    "work_details": "work_details.json",
    "series": "series.json",
    "meta": "meta.json",
}

WORK_FIELDS = [
    "work_id",
    "status",
    "published_date",
    "series_ids",
    "project_folder",
    "project_subfolder",
    "project_filename",
    "title",
    "width_cm",
    "height_cm",
    "year",
    "year_display",
    "medium_type",
    "medium_caption",
    "storage_location",
    "notes",
    "duration",
    "depth_cm",
    "width_px",
    "height_px",
    "provenance",
    "artist",
    "downloads",
    "links",
]

SERIES_FIELDS = [
    "series_id",
    "title",
    "series_type",
    "status",
    "published_date",
    "year",
    "year_display",
    "primary_work_id",
    "notes",
    "sort_fields",
]

DETAIL_FIELDS = [
    "detail_uid",
    "work_id",
    "detail_id",
    "details_subfolder",
    "section_id",
    "section_title",
    "sort_order",
    "project_filename",
    "title",
    "status",
    "published_date",
    "width_px",
    "height_px",
]

DOWNLOAD_FIELDS = ["filename", "label"]
WORK_LINK_ENTRY_FIELDS = ["url", "label"]

WORK_TEXT_FIELDS = set(WORK_FIELDS) - {
    "series_ids",
    "downloads",
    "links",
    "width_cm",
    "height_cm",
    "year",
    "depth_cm",
    "width_px",
    "height_px",
}
SERIES_TEXT_FIELDS = set(SERIES_FIELDS) - {"year"}
DETAIL_TEXT_FIELDS = set(DETAIL_FIELDS) - {"width_px", "height_px"}
OMIT_EMPTY_SOURCE_FIELDS = {"project_subfolder", "details_subfolder", "sort_order"}


@dataclass(frozen=True)
class CatalogueSourceRecords:
    works: Dict[str, Dict[str, Any]]
    work_details: Dict[str, Dict[str, Any]]
    series: Dict[str, Dict[str, Any]]

    def as_maps(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            "works": self.works,
            "work_details": self.work_details,
            "series": self.series,
        }


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.startswith("'") and len(text) > 1:
        text = text[1:]
    return text


def normalize_status(value: Any) -> str:
    return normalize_text(value).lower()


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def slug_id(raw: Any, width: int = 5) -> str:
    if raw is None:
        raise ValueError("Missing id")
    text = normalize_text(raw)
    text = re.sub(r"\.0$", "", text)
    text = re.sub(r"\D", "", text)
    if not text:
        raise ValueError(f"Invalid id value: {raw!r}")
    return text.zfill(width)


def normalize_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else value
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = normalize_text(value)
    return text if text else None


def normalize_embedded_entry(value: Any, fields: Iterable[str]) -> Dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    out: Dict[str, Any] = {}
    for field in fields:
        normalized = normalize_scalar_text(value.get(field))
        if normalized is not None:
            out[field] = normalized
    return out if out else None


def normalize_downloads(value: Any) -> list[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[Dict[str, Any]] = []
    for item in value:
        entry = normalize_embedded_entry(item, DOWNLOAD_FIELDS)
        if entry is not None:
            out.append(entry)
    return out


def normalize_links(value: Any) -> list[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[Dict[str, Any]] = []
    for item in value:
        entry = normalize_embedded_entry(item, WORK_LINK_ENTRY_FIELDS)
        if entry is not None:
            out.append(entry)
    return out


def normalize_scalar_text(value: Any) -> str | None:
    text = normalize_text(value)
    return text if text else None


def normalize_source_record(
    record: Mapping[str, Any],
    field_order: Iterable[str],
    *,
    text_fields: set[str] | None = None,
) -> Dict[str, Any]:
    text_fields = text_fields or set()
    out: Dict[str, Any] = {}
    for field in field_order:
        value = record.get(field)
        if field == "downloads":
            entries = normalize_downloads(value)
            if entries:
                out[field] = entries
        elif field == "links":
            entries = normalize_links(value)
            if entries:
                out[field] = entries
        elif isinstance(value, list):
            out[field] = [normalize_json_value(item) for item in value]
        elif field in text_fields:
            normalized_text = normalize_scalar_text(value)
            if normalized_text is not None or field not in OMIT_EMPTY_SOURCE_FIELDS:
                out[field] = normalized_text
        else:
            normalized_value = normalize_json_value(value)
            if normalized_value is not None or field not in OMIT_EMPTY_SOURCE_FIELDS:
                out[field] = normalized_value
    return out


def sort_record_map(records: Mapping[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {key: records[key] for key in sorted(records)}


def payload_for_map(kind: str, records: Mapping[str, Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "header": {
            "schema": SCHEMAS[kind],
            "count": len(records),
        },
        kind: sort_record_map(records),
    }


def payloads_from_records(records: CatalogueSourceRecords) -> Dict[str, Dict[str, Any]]:
    payloads = {
        kind: payload_for_map(kind, record_map)
        for kind, record_map in records.as_maps().items()
    }
    payloads["meta"] = {
        "header": {
            "schema": SCHEMAS["meta"],
        },
        "source": {
            "canonical": "json",
        },
        "id_policy": {
            "work_id_width": 5,
            "detail_id_width": 3,
        },
    }
    return payloads


def write_payloads(source_dir: Path, payloads: Mapping[str, Mapping[str, Any]]) -> list[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind in ["works", "work_details", "series", "meta"]:
        path = source_dir / SOURCE_FILES[kind]
        path.write_text(json.dumps(payloads[kind], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def write_source_record_payloads(
    source_dir: Path,
    records: CatalogueSourceRecords,
    *,
    kinds: Iterable[str] = ("works", "work_details", "series"),
) -> list[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)
    record_maps = records.as_maps()
    written: list[Path] = []
    for kind in kinds:
        if kind not in record_maps:
            raise ValueError(f"Unknown source record kind: {kind}")
        path = source_dir / SOURCE_FILES[kind]
        payload = payload_for_map(kind, record_maps[kind])
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def load_json_file(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing source file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid source file shape in {path}: expected object")
    return payload


def records_from_json_source(source_dir: Path) -> CatalogueSourceRecords:
    maps: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for kind in ["works", "work_details", "series"]:
        path = source_dir / SOURCE_FILES[kind]
        payload = load_json_file(path)
        record_map = payload.get(kind)
        if not isinstance(record_map, dict):
            raise ValueError(f"Invalid source file shape in {path}: missing object key {kind!r}")
        maps[kind] = {
            str(record_id): dict(record)
            for record_id, record in record_map.items()
            if isinstance(record, dict)
        }
    works = sort_record_map({
        work_id: normalize_source_record(record, WORK_FIELDS, text_fields=WORK_TEXT_FIELDS)
        for work_id, record in maps["works"].items()
    })
    return CatalogueSourceRecords(
        works=works,
        work_details=sort_record_map(maps["work_details"]),
        series=sort_record_map(maps["series"]),
    )


def validate_source_records(records: CatalogueSourceRecords) -> list[str]:
    errors: list[str] = []
    all_work_ids: set[str] = set()
    all_series_ids: set[str] = set()
    work_series_ids_by_work_id: Dict[str, list[str]] = {}

    for key, record in records.works.items():
        try:
            work_id = slug_id(record.get("work_id") or key)
        except ValueError as exc:
            errors.append(f"works {key}: invalid work_id ({exc})")
            continue
        if key != work_id:
            errors.append(f"works {key}: key does not match normalized work_id {work_id}")
        all_work_ids.add(work_id)
        series_ids = record.get("series_ids")
        if not isinstance(series_ids, list):
            errors.append(f"works {key}: series_ids must be an array")
            series_ids = []
        parsed_series_ids: list[str] = []
        for raw_series_id in series_ids:
            try:
                parsed_series_ids.append(normalize_series_id(raw_series_id))
            except ValueError as exc:
                errors.append(f"works {key}: {exc}")
        work_series_ids_by_work_id[work_id] = parsed_series_ids
        downloads = record.get("downloads")
        if downloads is not None:
            if not isinstance(downloads, list):
                errors.append(f"works {key}: downloads must be an array")
            else:
                for idx, download in enumerate(downloads, start=1):
                    if not isinstance(download, Mapping):
                        errors.append(f"works {key}: downloads item {idx} must be an object")
                        continue
                    if is_empty(download.get("filename")):
                        errors.append(f"works {key}: downloads item {idx} missing filename")
                    if is_empty(download.get("label")):
                        errors.append(f"works {key}: downloads item {idx} missing label")
        links = record.get("links")
        if links is not None:
            if not isinstance(links, list):
                errors.append(f"works {key}: links must be an array")
            else:
                for idx, link in enumerate(links, start=1):
                    if not isinstance(link, Mapping):
                        errors.append(f"works {key}: links item {idx} must be an object")
                        continue
                    if is_empty(link.get("url")):
                        errors.append(f"works {key}: links item {idx} missing url")
                    if is_empty(link.get("label")):
                        errors.append(f"works {key}: links item {idx} missing label")

    for key, record in records.series.items():
        try:
            series_id = normalize_series_id(record.get("series_id") or key)
        except ValueError as exc:
            errors.append(f"series {key}: {exc}")
            continue
        if key != series_id:
            errors.append(f"series {key}: key does not match normalized series_id {series_id}")
        all_series_ids.add(series_id)

        if normalize_status(record.get("status")) not in ACTIONABLE_STATUSES:
            continue
        status = normalize_status(record.get("status"))
        raw_primary_work_id = record.get("primary_work_id")
        if is_empty(raw_primary_work_id):
            if status == "published":
                errors.append(f"series {series_id}: missing primary_work_id")
            continue
        try:
            primary_work_id = slug_id(raw_primary_work_id)
        except ValueError as exc:
            errors.append(f"series {series_id}: invalid primary_work_id {raw_primary_work_id!r} ({exc})")
            continue
        if primary_work_id not in all_work_ids:
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} not found in works")
            continue
        if series_id not in work_series_ids_by_work_id.get(primary_work_id, []):
            errors.append(
                f"series {series_id}: primary_work_id {primary_work_id!r} is not in that work's series_ids"
            )

    for work_id, series_ids in work_series_ids_by_work_id.items():
        if normalize_status(records.works.get(work_id, {}).get("status")) not in ACTIONABLE_STATUSES:
            continue
        for series_id in series_ids:
            if series_id not in all_series_ids:
                errors.append(f"works {work_id}: references unknown series_id {series_id!r}")

    for key, record in records.work_details.items():
        raw_work_id = record.get("work_id")
        raw_detail_id = record.get("detail_id")
        if is_empty(raw_work_id) or is_empty(raw_detail_id):
            errors.append(f"work_details {key}: missing work_id or detail_id")
            continue
        try:
            work_id = slug_id(raw_work_id)
            detail_id = slug_id(raw_detail_id, width=3)
        except ValueError as exc:
            errors.append(f"work_details {key}: invalid id ({exc})")
            continue
        detail_uid = f"{work_id}-{detail_id}"
        if key != detail_uid or record.get("detail_uid") != detail_uid:
            errors.append(f"work_details {key}: key/detail_uid does not match normalized detail_uid {detail_uid}")
        if normalize_status(record.get("status")) in ACTIONABLE_STATUSES and work_id not in all_work_ids:
            errors.append(f"work_details {key}: work_id {work_id!r} not found in works")

    return sorted(dict.fromkeys(errors))


def add_common_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
