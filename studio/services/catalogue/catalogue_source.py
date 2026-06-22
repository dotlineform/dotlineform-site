from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    from catalogue.series_ids import normalize_series_id, parse_series_ids
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.series_ids import normalize_series_id, parse_series_ids


DEFAULT_SOURCE_DIR = Path("studio/data/canonical/catalogue")

ACTIONABLE_STATUSES = {"draft", "published"}

SCHEMAS = {
    "works": "catalogue_source_works_v1",
    "work_details": "catalogue_source_work_detail_record_v1",
    "series": "catalogue_source_series_v1",
}

SOURCE_FILES = {
    "works": "works.json",
    "work_details": "work_details",
    "series": "series.json",
}

DETAIL_COMPAT_SUBFOLDER_FIELD = "project_subfolder"
DETAIL_SECTION_ID_SEPARATOR = "-"

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
    "sort_fields",
]

DETAIL_FIELDS = [
    "detail_uid",
    "work_id",
    "detail_id",
    "section_id",
    "project_filename",
    "title",
    "width_px",
    "height_px",
]

DETAIL_SECTION_FIELDS = [
    "section_id",
    "work_id",
    "details_subfolder",
    "section_title",
    "section_order",
    "detail_sort",
]

DETAIL_SECTION_SORT_MODES = {"detail_id", "title"}

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
OMIT_EMPTY_SOURCE_FIELDS = {"project_subfolder", "details_subfolder", "section_order", "detail_sort"}

SOURCE_FIELDS_BY_RECORD_FAMILY = {
    "work": tuple(WORK_FIELDS),
    "work_detail": tuple(DETAIL_FIELDS),
    "series": tuple(SERIES_FIELDS),
}

SOURCE_IDENTITY_FIELDS_BY_RECORD_FAMILY = {
    "work": ("work_id",),
    "work_detail": ("detail_uid", "work_id", "detail_id"),
    "series": ("series_id",),
}

SOURCE_DERIVED_FIELDS_BY_RECORD_FAMILY = {
    "work": ("width_px", "height_px"),
    "work_detail": ("width_px", "height_px"),
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


def build_detail_section_id(work_id: str, section_number: int) -> str:
    if section_number < 1:
        raise ValueError("section_number must be greater than zero")
    return f"{work_id}{DETAIL_SECTION_ID_SEPARATOR}{section_number}"


def detail_section_id_number(work_id: str, section_id: Any) -> int | None:
    text = normalize_text(section_id)
    prefix = f"{work_id}{DETAIL_SECTION_ID_SEPARATOR}"
    if not text.startswith(prefix):
        return None
    suffix = text[len(prefix):]
    if not re.fullmatch(r"[1-9]\d*", suffix):
        return None
    return int(suffix)


def next_detail_section_id(
    work_id: str,
    detail_records: Iterable[Mapping[str, Any]] = (),
    section_records: Iterable[Mapping[str, Any]] = (),
) -> str:
    max_section_number = 0
    for record in [*detail_records, *section_records]:
        if normalize_text(record.get("work_id")) != work_id:
            continue
        section_number = detail_section_id_number(work_id, record.get("section_id"))
        if section_number is not None:
            max_section_number = max(max_section_number, section_number)
    return build_detail_section_id(work_id, max_section_number + 1)


def detail_record_sort_key(item: tuple[str, Mapping[str, Any]]) -> tuple[str, str, str]:
    key, record = item
    work_id = normalize_text(record.get("work_id"))
    detail_id = normalize_text(record.get("detail_id"))
    return (work_id, detail_id, key)


def build_detail_section_resolution_by_uid(
    detail_records: Mapping[str, Mapping[str, Any]],
    section_records: Mapping[str, Mapping[str, Any]] | None = None,
) -> Dict[str, Dict[str, Any]]:
    if section_records is not None:
        resolutions: Dict[str, Dict[str, Any]] = {}
        for detail_uid, record in sorted(detail_records.items(), key=detail_record_sort_key):
            section_id = normalize_text(record.get("section_id"))
            section_record = section_records.get(section_id, {})
            resolutions[detail_uid] = {
                "section_id": section_id,
                "work_id": normalize_text(section_record.get("work_id") or record.get("work_id")),
                "section_title": normalize_text(section_record.get("section_title")),
                "details_subfolder": normalize_text(section_record.get("details_subfolder")),
                "section_order": normalize_optional_int(section_record.get("section_order")),
                "detail_sort": normalize_detail_sort_value(section_record.get("detail_sort")),
            }
        return resolutions

    existing_section_count_by_work: Dict[str, int] = {}
    for _key, record in sorted(detail_records.items(), key=detail_record_sort_key):
        work_id = normalize_text(record.get("work_id"))
        section_number = detail_section_id_number(work_id, record.get("section_id"))
        if section_number is not None:
            existing_section_count_by_work[work_id] = max(
                existing_section_count_by_work.get(work_id, 0),
                section_number,
            )

    assignments_by_work: Dict[str, Dict[str, str]] = {}
    resolutions: Dict[str, Dict[str, Any]] = {}
    for detail_uid, record in sorted(detail_records.items(), key=detail_record_sort_key):
        work_id = normalize_text(record.get("work_id"))
        compat_section = normalize_text(record.get(DETAIL_COMPAT_SUBFOLDER_FIELD))
        section_id = normalize_text(record.get("section_id"))
        if detail_section_id_number(work_id, section_id) is None and compat_section:
            work_assignments = assignments_by_work.setdefault(work_id, {})
            if compat_section not in work_assignments:
                existing_count = existing_section_count_by_work.get(work_id, 0)
                work_assignments[compat_section] = build_detail_section_id(
                    work_id,
                    existing_count + len(work_assignments) + 1,
                )
            section_id = work_assignments[compat_section]
        section_title = normalize_text(record.get("section_title")) or compat_section
        details_subfolder = normalize_text(record.get("details_subfolder")) or compat_section
        resolutions[detail_uid] = {
            "section_id": section_id,
            "section_title": section_title,
            "details_subfolder": details_subfolder,
            "section_order": normalize_optional_int(record.get("sort_order")),
            "detail_sort": None,
        }
    return resolutions


def section_sort_key(section: Mapping[str, Any]) -> tuple[int, int, str]:
    section_order = normalize_optional_int(section.get("section_order"))
    return (
        1 if section_order is None else 0,
        section_order if section_order is not None else 0,
        normalize_text(section.get("section_id")),
    )


def detail_sort_key_for_section(section: Mapping[str, Any], detail: Mapping[str, Any]) -> tuple[str, str, str]:
    sort_mode = normalize_detail_sort_value(section.get("detail_sort")) or "detail_id"
    if sort_mode == "title":
        return (
            normalize_text(detail.get("title")),
            normalize_text(detail.get("detail_id")),
            normalize_text(detail.get("detail_uid")),
        )
    return (
        normalize_text(detail.get("detail_id")),
        normalize_text(detail.get("detail_uid")),
        "",
    )


def ordered_work_detail_sections(
    records: "CatalogueSourceRecords",
    work_id: str,
) -> list[Dict[str, Any]]:
    sections_by_id = {
        section_id: dict(section)
        for section_id, section in records.work_detail_sections.items()
        if normalize_text(section.get("work_id")) == work_id
    }
    details_by_section: Dict[str, list[Dict[str, Any]]] = {
        section_id: []
        for section_id in sections_by_id
    }
    for detail_uid, detail in records.work_details.items():
        if normalize_text(detail.get("work_id")) != work_id:
            continue
        section_id = normalize_text(detail.get("section_id"))
        if section_id not in sections_by_id:
            continue
        detail_payload = dict(detail)
        detail_payload["detail_uid"] = normalize_text(detail_payload.get("detail_uid")) or detail_uid
        details_by_section.setdefault(section_id, []).append(detail_payload)

    ordered_sections: list[Dict[str, Any]] = []
    for section_id, section in sorted(sections_by_id.items(), key=lambda item: section_sort_key(item[1])):
        details = details_by_section.get(section_id, [])
        details.sort(key=lambda detail: detail_sort_key_for_section(section, detail))
        section_payload = dict(section)
        section_payload["details"] = details
        ordered_sections.append(section_payload)
    return ordered_sections


def normalize_detail_sort_value(value: Any) -> str | None:
    text = normalize_text(value)
    return text if text in DETAIL_SECTION_SORT_MODES else None


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
    work_detail_sections: Dict[str, Dict[str, Any]]
    work_details: Dict[str, Dict[str, Any]]
    series: Dict[str, Dict[str, Any]]

    def as_maps(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            "works": self.works,
            "work_detail_sections": self.work_detail_sections,
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


def normalize_detail_uid_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("detail_uid is required")
    if "-" in text:
        raw_work_id, raw_detail_id = text.split("-", 1)
    else:
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) != 8:
            raise ValueError(f"invalid detail_uid: {value!r}")
        raw_work_id, raw_detail_id = digits[:5], digits[5:]
    work_id = slug_id(raw_work_id)
    detail_id = slug_id(raw_detail_id, width=3)
    return f"{work_id}-{detail_id}"


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
        elif field in {"sort_order", "section_order"}:
            normalized_int = normalize_optional_int(value)
            if normalized_int is not None:
                out[field] = normalized_int
            elif not is_empty(value):
                out[field] = normalize_text(value)
            elif field not in OMIT_EMPTY_SOURCE_FIELDS:
                out[field] = None
        elif field == "detail_sort":
            normalized_sort = normalize_detail_sort_value(value)
            if normalized_sort is not None:
                out[field] = normalized_sort
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
    return {
        "header": {
            "schema": SCHEMAS[kind],
            "count": len(records),
        },
        kind: sort_record_map(records),
    }


def work_details_payload_for_maps(
    section_records: Mapping[str, Dict[str, Any]],
    detail_records: Mapping[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "header": {
            "schema": SCHEMAS["work_details"],
            "section_count": len(section_records),
            "count": len(detail_records),
        },
        "work_detail_sections": sort_record_map(section_records),
        "work_details": sort_record_map(detail_records),
    }


def work_detail_source_path(source_dir: Path, work_id: str) -> Path:
    return source_dir / SOURCE_FILES["work_details"] / f"{slug_id(work_id)}.json"


def work_detail_record_payload_for_work(
    work_id: str,
    section_records: Mapping[str, Dict[str, Any]],
    detail_records: Mapping[str, Dict[str, Any]],
) -> Dict[str, Any]:
    normalized_work_id = slug_id(work_id)
    sections: list[Dict[str, Any]] = []
    detail_count = 0
    for section_id, raw_section in sorted(section_records.items(), key=lambda item: section_sort_key(item[1])):
        if normalize_text(raw_section.get("work_id")) != normalized_work_id:
            continue
        section = normalize_source_record(raw_section, DETAIL_SECTION_FIELDS, text_fields=DETAIL_TEXT_FIELDS)
        section_details = [
            normalize_source_record(detail, DETAIL_FIELDS, text_fields=DETAIL_TEXT_FIELDS)
            for _detail_uid, detail in sorted(detail_records.items(), key=detail_record_sort_key)
            if normalize_text(detail.get("work_id")) == normalized_work_id
            and normalize_text(detail.get("section_id")) == normalize_text(section.get("section_id"))
        ]
        if not section_details:
            raise ValueError(f"work_details {normalized_work_id}: section {section_id} has no details")
        details_payload: list[Dict[str, Any]] = []
        for detail in sorted(section_details, key=lambda item: detail_sort_key_for_section(section, item)):
            detail_payload = {
                field: value
                for field, value in detail.items()
                if field not in {"work_id", "section_id"} and value is not None
            }
            details_payload.append(detail_payload)
        section_payload = {
            field: value
            for field, value in section.items()
            if field != "work_id" and value is not None
        }
        section_payload["details"] = details_payload
        sections.append(section_payload)
        detail_count += len(details_payload)
    return {
        "header": {
            "schema": SCHEMAS["work_details"],
            "work_id": normalized_work_id,
            "section_count": len(sections),
            "count": detail_count,
        },
        "work_id": normalized_work_id,
        "detail_sections": sections,
    }


def work_detail_payloads_for_maps(
    source_dir: Path,
    section_records: Mapping[str, Dict[str, Any]],
    detail_records: Mapping[str, Dict[str, Any]],
) -> Dict[Path, Dict[str, Any]]:
    work_ids = sorted({
        normalize_text(record.get("work_id"))
        for record in section_records.values()
        if normalize_text(record.get("work_id"))
    })
    return {
        work_detail_source_path(source_dir, work_id): work_detail_record_payload_for_work(
            work_id,
            section_records,
            detail_records,
        )
        for work_id in work_ids
    }


def flatten_work_detail_record_payload(path: Path, payload: Mapping[str, Any]) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    raw_work_id = payload.get("work_id") or (payload.get("header") or {}).get("work_id") or path.stem
    work_id = slug_id(raw_work_id)
    if path.stem != work_id:
        raise ValueError(f"Invalid source file name {path}: expected {work_id}.json")
    if normalize_text((payload.get("header") or {}).get("work_id")) != work_id:
        raise ValueError(f"Invalid source file {path}: header.work_id must match {work_id}")
    if normalize_text(payload.get("work_id")) != work_id:
        raise ValueError(f"Invalid source file {path}: work_id must match {work_id}")
    raw_sections = payload.get("detail_sections")
    if not isinstance(raw_sections, list):
        raise ValueError(f"Invalid source file {path}: missing detail_sections array")

    section_records: Dict[str, Dict[str, Any]] = {}
    detail_records: Dict[str, Dict[str, Any]] = {}
    for raw_section in raw_sections:
        if not isinstance(raw_section, Mapping):
            raise ValueError(f"Invalid source file {path}: detail section must be an object")
        section = dict(raw_section)
        raw_details = section.pop("details", None)
        if not isinstance(raw_details, list) or not raw_details:
            raise ValueError(f"Invalid source file {path}: section must include one or more details")
        section["work_id"] = work_id
        section_record = {
            field: value
            for field, value in normalize_source_record(section, DETAIL_SECTION_FIELDS, text_fields=DETAIL_TEXT_FIELDS).items()
            if value is not None
        }
        section_id = normalize_text(section_record.get("section_id"))
        if not section_id:
            raise ValueError(f"Invalid source file {path}: section missing section_id")
        if detail_section_id_number(work_id, section_id) is None:
            raise ValueError(f"Invalid source file {path}: section_id {section_id!r} does not belong to {work_id}")
        section_records[section_id] = section_record
        for raw_detail in raw_details:
            if not isinstance(raw_detail, Mapping):
                raise ValueError(f"Invalid source file {path}: detail must be an object")
            if "work_id" in raw_detail or "section_id" in raw_detail:
                raise ValueError(f"Invalid source file {path}: detail records must not repeat work_id or section_id")
            detail = dict(raw_detail)
            detail["work_id"] = work_id
            detail["section_id"] = section_id
            detail_record = {
                field: value
                for field, value in normalize_source_record(detail, DETAIL_FIELDS, text_fields=DETAIL_TEXT_FIELDS).items()
                if value is not None
            }
            detail_uid = normalize_text(detail_record.get("detail_uid"))
            if not detail_uid:
                raise ValueError(f"Invalid source file {path}: detail missing detail_uid")
            if normalize_detail_uid_value(detail_uid).split("-", 1)[0] != work_id:
                raise ValueError(f"Invalid source file {path}: detail_uid {detail_uid!r} does not belong to {work_id}")
            detail_records[detail_uid] = detail_record
    return section_records, detail_records


def load_work_details_flat_payload(path: Path) -> Dict[str, Any]:
    if not path.is_dir():
        raise ValueError(f"Missing source directory: {path}")
    section_records: Dict[str, Dict[str, Any]] = {}
    detail_records: Dict[str, Dict[str, Any]] = {}
    for record_path in sorted(path.glob("*.json")):
        if record_path.name == "index.json":
            continue
        payload = load_json_file(record_path)
        sections, details = flatten_work_detail_record_payload(record_path, payload)
        section_records.update(sections)
        detail_records.update(details)
    return work_details_payload_for_maps(section_records, detail_records)


def payloads_from_records(records: CatalogueSourceRecords) -> Dict[str, Dict[str, Any]]:
    payloads = {
        kind: payload_for_map(kind, record_map)
        for kind, record_map in records.as_maps().items()
        if kind != "work_detail_sections"
    }
    payloads["work_details"] = work_details_payload_for_maps(
        records.work_detail_sections,
        records.work_details,
    )
    return payloads


def write_payloads(source_dir: Path, payloads: Mapping[str, Mapping[str, Any]]) -> list[Path]:
    source_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind in ["works", "series"]:
        path = source_dir / SOURCE_FILES[kind]
        path.write_text(json.dumps(payloads[kind], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    details_payload = payloads.get("work_details")
    if isinstance(details_payload, Mapping):
        written.extend(
            write_work_detail_payloads(
                source_dir,
                details_payload.get("work_detail_sections") if isinstance(details_payload.get("work_detail_sections"), Mapping) else {},
                details_payload.get("work_details") if isinstance(details_payload.get("work_details"), Mapping) else {},
            )
        )
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
        if kind == "work_detail_sections":
            kind = "work_details"
        if kind not in record_maps:
            raise ValueError(f"Unknown source record kind: {kind}")
        if kind == "work_details":
            written.extend(
                write_work_detail_payloads(
                    source_dir,
                    records.work_detail_sections,
                    records.work_details,
                )
            )
            continue
        path = source_dir / SOURCE_FILES[kind]
        payload = payload_for_map(kind, record_maps[kind])
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def write_work_detail_payloads(
    source_dir: Path,
    section_records: Mapping[str, Dict[str, Any]],
    detail_records: Mapping[str, Dict[str, Any]],
) -> list[Path]:
    detail_dir = source_dir / SOURCE_FILES["work_details"]
    detail_dir.mkdir(parents=True, exist_ok=True)
    payloads = work_detail_payloads_for_maps(source_dir, section_records, detail_records)
    expected_paths = set(payloads)
    for stale_path in sorted(detail_dir.glob("*.json")):
        if stale_path.name == "index.json":
            continue
        if stale_path not in expected_paths:
            stale_path.unlink()
    written: list[Path] = []
    for path, payload in payloads.items():
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def load_json_file(path: Path) -> Dict[str, Any]:
    if path.is_dir() and path.name == SOURCE_FILES["work_details"]:
        return load_work_details_flat_payload(path)
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
    old_flat_path = source_dir / "work_details.json"
    if old_flat_path.exists():
        raise ValueError(f"Retired source file must not exist at runtime: {old_flat_path}")
    maps: Dict[str, Dict[str, Dict[str, Any]]] = {}
    section_maps: Dict[str, Dict[str, Any]] = {}
    for kind in ["works", "work_details", "series"]:
        path = source_dir / SOURCE_FILES[kind]
        payload = load_json_file(path)
        record_map = payload.get(kind)
        if not isinstance(record_map, dict):
            raise ValueError(f"Invalid source file shape in {path}: missing object key {kind!r}")
        if kind == "work_details":
            raw_sections = payload.get("work_detail_sections")
            if isinstance(raw_sections, dict):
                section_maps = {
                    str(record_id): dict(record)
                    for record_id, record in raw_sections.items()
                    if isinstance(record, dict)
                }
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
        work_detail_sections=sort_record_map({
            section_id: normalize_source_record(record, DETAIL_SECTION_FIELDS, text_fields=DETAIL_TEXT_FIELDS)
            for section_id, record in section_maps.items()
        }),
        work_details=sort_record_map(maps["work_details"]),
        series=sort_record_map(maps["series"]),
    )


def validate_record_fields(
    errors: list[str],
    *,
    kind: str,
    key: str,
    record: Mapping[str, Any],
    allowed_fields: Iterable[str],
    allowed_compat_fields: Iterable[str] = (),
) -> None:
    allowed = set(allowed_fields)
    allowed.update(allowed_compat_fields)
    unknown = sorted(str(field) for field in record.keys() if str(field) not in allowed)
    if unknown:
        errors.append(f"{kind} {key}: unsupported field(s): {', '.join(unknown)}")


def validate_work_detail_section_record(key: str, record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    raw_work_id = record.get("work_id")
    try:
        work_id = slug_id(raw_work_id)
    except ValueError as exc:
        errors.append(f"work_detail_sections {key}: invalid work_id ({exc})")
        work_id = normalize_text(raw_work_id)
    raw_section_id = record.get("section_id")
    raw_section_title = record.get("section_title")
    if is_empty(raw_section_id):
        errors.append(f"work_detail_sections {key}: missing section_id")
    elif work_id and detail_section_id_number(work_id, raw_section_id) is None:
        errors.append(f"work_detail_sections {key}: section_id must match {work_id}{DETAIL_SECTION_ID_SEPARATOR}<number>")
    elif key != normalize_text(raw_section_id):
        errors.append(f"work_detail_sections {key}: key/section_id does not match")
    if is_empty(raw_section_title):
        errors.append(f"work_detail_sections {key}: missing section_title")
    if "section_order" in record and not is_empty(record.get("section_order")):
        section_order = normalize_optional_int(record.get("section_order"))
        if section_order is None:
            errors.append(f"work_detail_sections {key}: section_order must be a whole number")
        elif section_order < 0:
            errors.append(f"work_detail_sections {key}: section_order must be zero or greater")
    if "detail_sort" in record and not is_empty(record.get("detail_sort")):
        if normalize_detail_sort_value(record.get("detail_sort")) is None:
            errors.append(f"work_detail_sections {key}: detail_sort must be detail_id, title, or empty")
    return errors


def validate_work_detail_media_section_record(key: str, record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("details_subfolder", "section_title", "sort_order"):
        if field in record:
            errors.append(f"work_details {key}: {field} is section metadata; use work_detail_sections")
    if DETAIL_COMPAT_SUBFOLDER_FIELD in record:
        errors.append(f"work_details {key}: project_subfolder is not supported; use work_detail_sections.details_subfolder")
    raw_work_id = record.get("work_id")
    try:
        work_id = slug_id(raw_work_id)
    except ValueError as exc:
        errors.append(f"work_details {key}: invalid work_id ({exc})")
        work_id = normalize_text(raw_work_id)
    raw_section_id = record.get("section_id")
    if is_empty(raw_section_id):
        errors.append(f"work_details {key}: missing section_id")
    elif work_id and detail_section_id_number(work_id, raw_section_id) is None:
        errors.append(f"work_details {key}: section_id must match {work_id}{DETAIL_SECTION_ID_SEPARATOR}<number>")
    return errors


def validate_work_detail_section_metadata_consistency(
    detail_records: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    section_metadata_by_key: Dict[tuple[str, str], tuple[str, int | None]] = {}
    for key, record in sorted(detail_records.items()):
        work_id = normalize_text(record.get("work_id"))
        section_id = normalize_text(record.get("section_id"))
        section_title = normalize_text(record.get("section_title"))
        if not work_id or not section_id or not section_title:
            continue
        section_key = (work_id, section_id)
        section_metadata = (section_title, normalize_optional_int(record.get("sort_order")))
        previous_metadata = section_metadata_by_key.get(section_key)
        if previous_metadata is None:
            section_metadata_by_key[section_key] = section_metadata
        elif previous_metadata != section_metadata:
            errors.append(f"work_details {key}: section metadata conflicts for section_id {section_id}")
    return errors


def validate_source_records(
    records: CatalogueSourceRecords,
    *,
    require_detail_media_sections: bool = False,
    allow_compat_detail_project_subfolder: bool = True,
) -> list[str]:
    errors: list[str] = []
    all_work_ids: set[str] = set()
    all_series_ids: set[str] = set()
    work_series_ids_by_work_id: Dict[str, list[str]] = {}

    for key, record in records.works.items():
        validate_record_fields(errors, kind="works", key=key, record=record, allowed_fields=WORK_FIELDS)
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
        validate_record_fields(errors, kind="series", key=key, record=record, allowed_fields=SERIES_FIELDS)
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

    section_work_by_id: Dict[str, str] = {}
    for key, record in records.work_detail_sections.items():
        validate_record_fields(
            errors,
            kind="work_detail_sections",
            key=key,
            record=record,
            allowed_fields=DETAIL_SECTION_FIELDS,
        )
        errors.extend(validate_work_detail_section_record(key, record))
        work_id = normalize_text(record.get("work_id"))
        if work_id and work_id not in all_work_ids:
            errors.append(f"work_detail_sections {key}: work_id {work_id!r} not found in works")
        if key in section_work_by_id:
            errors.append(f"work_detail_sections {key}: duplicate section_id")
        section_work_by_id[key] = work_id

    for key, record in records.work_details.items():
        allowed_compat_fields = (
            [DETAIL_COMPAT_SUBFOLDER_FIELD]
            if allow_compat_detail_project_subfolder and not require_detail_media_sections
            else []
        )
        validate_record_fields(
            errors,
            kind="work_details",
            key=key,
            record=record,
            allowed_fields=DETAIL_FIELDS,
            allowed_compat_fields=allowed_compat_fields,
        )
        if DETAIL_COMPAT_SUBFOLDER_FIELD in record and not allow_compat_detail_project_subfolder:
            errors.append(f"work_details {key}: project_subfolder is not supported; use details_subfolder")
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
        if work_id not in all_work_ids:
            errors.append(f"work_details {key}: work_id {work_id!r} not found in works")
        errors.extend(validate_work_detail_media_section_record(key, record))
        section_id = normalize_text(record.get("section_id"))
        section_work_id = section_work_by_id.get(section_id)
        if section_id and section_work_id is None:
            errors.append(f"work_details {key}: section_id {section_id!r} not found in work_detail_sections")
        elif section_work_id and section_work_id != work_id:
            errors.append(f"work_details {key}: section_id {section_id!r} belongs to work_id {section_work_id!r}")

    return sorted(dict.fromkeys(errors))


def add_common_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Catalogue source JSON directory")
