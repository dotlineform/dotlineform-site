from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from catalogue_work_media_sources import (
    resolve_work_media_source_id,
    work_media_source_id_for_storage,
)
from pipeline_config import load_pipeline_config

from catalogue.series_ids import normalize_series_id, parse_series_ids


DEFAULT_SOURCE_DIR = Path("studio/data/canonical/catalogue")

SCHEMAS = {
    "works": "catalogue_source_works_v2",
    "series": "catalogue_source_series_v2",
}

SOURCE_FILES = {
    "works": "works.json",
    "series": "series.json",
}

MEDIA_VERSION_FIELD = "media_version"
MEDIA_SOURCE_FIELD = "media_source_id"
PIPELINE_CONFIG = load_pipeline_config(Path(__file__))

WORK_FIELDS = [
    "work_id",
    "series_id",
    MEDIA_SOURCE_FIELD,
    "project_folder",
    "project_subfolder",
    "project_filename",
    MEDIA_VERSION_FIELD,
    "image_staged",
    "title",
    "width_cm",
    "height_cm",
    "year",
    "year_display",
    "medium",
    "storage_location",
    "duration",
    "depth_cm",
    "width_px",
    "height_px",
    "downloads",
    "links",
]

SERIES_FIELDS = [
    "series_id",
    "title",
]

DOWNLOAD_FIELDS = ["filename", "label", "staged"]
WORK_LINK_ENTRY_FIELDS = ["url", "label"]

WORK_TEXT_FIELDS = set(WORK_FIELDS) - {
    "image_staged",
    "downloads",
    "links",
    "width_cm",
    "height_cm",
    "year",
    "depth_cm",
    "width_px",
    "height_px",
    MEDIA_VERSION_FIELD,
}
SERIES_TEXT_FIELDS = set(SERIES_FIELDS)
OMIT_EMPTY_SOURCE_FIELDS = {
    "series_id",
    MEDIA_SOURCE_FIELD,
    "project_subfolder",
}

SOURCE_FIELDS_BY_RECORD_FAMILY = {
    "work": tuple(WORK_FIELDS),
    "series": tuple(SERIES_FIELDS),
}

SOURCE_IDENTITY_FIELDS_BY_RECORD_FAMILY = {
    "work": ("work_id",),
    "series": ("series_id",),
}

SOURCE_DERIVED_FIELDS_BY_RECORD_FAMILY = {
    "work": ("width_px", "height_px", MEDIA_VERSION_FIELD, "image_staged"),
    "series": (),
}

SOURCE_METADATA_FIELDS_BY_RECORD_FAMILY = {
    family: tuple(
        field
        for field in fields
        if field not in SOURCE_IDENTITY_FIELDS_BY_RECORD_FAMILY[family]
        and field not in SOURCE_DERIVED_FIELDS_BY_RECORD_FAMILY[family]
    )
    for family, fields in SOURCE_FIELDS_BY_RECORD_FAMILY.items()
}


def normalize_optional_int(value: Any) -> int | None:
    if is_empty(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = normalize_text(value)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return None


@dataclass(frozen=True)
class CatalogueSourceRecords:
    works: Dict[str, Dict[str, Any]]
    series: Dict[str, Dict[str, Any]]

    def as_maps(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            "works": self.works,
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


def normalize_series_ids_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        seen: set[str] = set()
        for raw in value:
            series_id = normalize_series_id(raw)
            if series_id in seen:
                continue
            seen.add(series_id)
            out.append(series_id)
        return out
    return parse_series_ids(value)


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
        entry = normalize_embedded_entry(item, ("filename", "label"))
        if entry is not None:
            entry["staged"] = item.get("staged")
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
        if field == MEDIA_SOURCE_FIELD:
            source_id = work_media_source_id_for_storage(PIPELINE_CONFIG, value)
            if source_id is not None:
                out[field] = source_id
        elif field == "downloads":
            entries = normalize_downloads(value)
            if entries:
                out[field] = entries
        elif field == "links":
            entries = normalize_links(value)
            if entries:
                out[field] = entries
        elif field in {"project_folder", "project_subfolder", "project_filename"}:
            # Source path components are identities, not prose to trim or unquote.
            if value is not None and value != "":
                out[field] = value
            elif field not in OMIT_EMPTY_SOURCE_FIELDS:
                out[field] = None
        elif field == MEDIA_VERSION_FIELD:
            normalized_int = normalize_optional_int(value)
            if normalized_int is not None:
                out[field] = normalized_int
            elif not is_empty(value):
                out[field] = normalize_text(value)
            elif field not in OMIT_EMPTY_SOURCE_FIELDS:
                out[field] = None
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
    """Serialize an ordered source map with a schema-only header."""
    return {
        "header": {"schema": SCHEMAS[kind]},
        kind: sort_record_map(records),
    }


def payloads_from_records(records: CatalogueSourceRecords) -> Dict[str, Dict[str, Any]]:
    return {
        kind: payload_for_map(kind, record_map)
        for kind, record_map in records.as_maps().items()
    }


def write_payloads(source_dir: Path, payloads: Mapping[str, Mapping[str, Any]]) -> list[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind in ["works", "series"]:
        path = source_dir / SOURCE_FILES[kind]
        path.write_text(json.dumps(payloads[kind], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def write_source_record_payloads(
    source_dir: Path,
    records: CatalogueSourceRecords,
    *,
    kinds: Iterable[str] = ("works", "series"),
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


def read_source_map(source_dir: Path, kind: str) -> Dict[str, Dict[str, Any]]:
    """Load one Work/Series map without count validation; mutations and maintenance own audits."""
    if kind not in {"works", "series"}:
        raise ValueError(f"Unsupported Catalogue source family: {kind!r}")
    path = source_dir / SOURCE_FILES[kind]
    record_map = load_json_file(path).get(kind)
    if not isinstance(record_map, dict):
        raise ValueError(f"Invalid source file shape in {path}: missing object key {kind!r}")
    return record_map


def records_from_json_source(source_dir: Path) -> CatalogueSourceRecords:
    """Read Work/Series authorities without loading unrelated Gallery data."""
    return CatalogueSourceRecords(
        works=read_source_map(source_dir, "works"),
        series=read_source_map(source_dir, "series"),
    )


def validate_record_fields(
    errors: list[str],
    *,
    kind: str,
    key: str,
    record: Mapping[str, Any],
    allowed_fields: Iterable[str],
) -> None:
    allowed = set(allowed_fields)
    unknown = sorted(str(field) for field in record.keys() if str(field) not in allowed)
    if unknown:
        errors.append(f"{kind} {key}: unsupported field(s): {', '.join(unknown)}")


def validate_media_version(errors: list[str], *, kind: str, key: str, record: Mapping[str, Any]) -> None:
    value = record.get(MEDIA_VERSION_FIELD)
    has_media = not is_empty(record.get("project_filename"))
    if is_empty(value):
        if has_media:
            errors.append(f"{kind} {key}: media_version is required when project_filename is set")
        return
    normalized = normalize_optional_int(value)
    if normalized is None or normalized < 1:
        errors.append(f"{kind} {key}: media_version must be a positive whole number")


def validate_work_media_source(errors: list[str], *, key: str, record: Mapping[str, Any]) -> None:
    try:
        resolve_work_media_source_id(PIPELINE_CONFIG, record.get(MEDIA_SOURCE_FIELD))
    except ValueError as exc:
        errors.append(f"works {key}: {exc}")


def validate_source_records(
    records: CatalogueSourceRecords,
) -> list[str]:
    errors: list[str] = []
    all_series_ids: set[str] = set()
    series_title_ids: Dict[str, str] = {}
    work_series_by_work_id: Dict[str, str] = {}

    for key, record in records.works.items():
        validate_record_fields(errors, kind="works", key=key, record=record, allowed_fields=WORK_FIELDS)
        validate_work_media_source(errors, key=key, record=record)
        validate_media_version(errors, kind="works", key=key, record=record)
        if type(record.get("image_staged")) is not bool:
            errors.append(f"works {key}: image_staged must be an explicit boolean")
        try:
            work_id = slug_id(record.get("work_id") or key)
        except ValueError as exc:
            errors.append(f"works {key}: invalid work_id ({exc})")
            continue
        if key != work_id:
            errors.append(f"works {key}: key does not match normalized work_id {work_id}")
        if "series_id" not in record:
            errors.append(f"works {key}: exactly one series_id is required")
        if "series_id" in record:
            raw_series_id = record["series_id"]
            try:
                if not isinstance(raw_series_id, str):
                    raise ValueError("series_id must be a string")
                series_id = normalize_series_id(raw_series_id)
                if series_id != raw_series_id:
                    raise ValueError("series_id must be normalized")
                work_series_by_work_id[work_id] = series_id
            except ValueError as exc:
                errors.append(f"works {key}: {exc}")
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
                    if type(download.get("staged")) is not bool:
                        errors.append(f"works {key}: downloads item {idx} staged must be an explicit boolean")
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
        validate_record_fields(errors, kind="series", key=key, record=record, allowed_fields=SERIES_FIELDS)
        try:
            series_id = normalize_series_id(record.get("series_id") or key)
        except ValueError as exc:
            errors.append(f"series {key}: {exc}")
            continue
        if key != series_id:
            errors.append(f"series {key}: key does not match normalized series_id {series_id}")
        all_series_ids.add(series_id)
        title = record.get("title")
        if isinstance(title, str) and title.strip():
            title_key = " ".join(title.split()).casefold()
            other_id = series_title_ids.get(title_key)
            if other_id is not None:
                errors.append(
                    f'Series titles must be unique: “{records.series[other_id]["title"]}” ({other_id}) '
                    f'matches “{title}” ({key}).'
                )
            else:
                series_title_ids[title_key] = key

    for work_id, series_id in work_series_by_work_id.items():
        if series_id not in all_series_ids:
            errors.append(f"works {work_id}: references unknown series_id {series_id!r}")

    return sorted(dict.fromkeys(errors))


def add_common_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
