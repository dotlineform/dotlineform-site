#!/usr/bin/env python3
"""
Localhost-only write service for canonical catalogue source JSON.

Run:
  ./scripts/studio/catalogue_write_server.py
  ./scripts/studio/catalogue_write_server.py --port 8788
  ./scripts/studio/catalogue_write_server.py --repo-root /path/to/dotlineform-site
  ./scripts/studio/catalogue_write_server.py --dry-run

Endpoints:
  GET /health
  POST /catalogue/bulk-save
  POST /catalogue/delete-preview
  POST /catalogue/delete-apply
  POST /catalogue/work/create
  POST /catalogue/work/save
  POST /catalogue/work-detail/create
  POST /catalogue/work-detail/save
  POST /catalogue/import-preview
  POST /catalogue/import-apply
  POST /catalogue/series/create
  POST /catalogue/series/save
  POST /catalogue/build-preview
  POST /catalogue/build-apply

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only http://localhost:* and http://127.0.0.1:*.
  - Writes only allowlisted canonical catalogue source files.
  - Creates backups under var/studio/catalogue/backups/.
  - Writes minimal local logs under var/studio/catalogue/logs/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue_source import (  # noqa: E402
    DEFAULT_SOURCE_DIR,
    DETAIL_FIELDS,
    DETAIL_TEXT_FIELDS,
    FILE_FIELDS,
    FILE_TEXT_FIELDS,
    LINK_FIELDS,
    LINK_TEXT_FIELDS,
    SERIES_FIELDS,
    SERIES_TEXT_FIELDS,
    SOURCE_FILES,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    CatalogueSourceRecords,
    load_json_file,
    normalize_source_record,
    normalize_status,
    payload_for_map,
    records_from_json_source,
    safe_uid_fragment,
    slug_id,
    sort_record_map,
    unique_uid,
    validate_source_records,
)
from catalogue_activity import append_catalogue_activity  # noqa: E402
from catalogue_lookup import DEFAULT_LOOKUP_DIR, build_and_write_catalogue_lookup  # noqa: E402
from catalogue_json_build import (  # noqa: E402
    build_scope_for_moment,
    build_scope_for_series,
    build_scope_for_work,
    preview_moment_source,
    run_moment_scoped_build,
    run_scoped_build,
    run_series_scoped_build,
)
from catalogue_workbook_import import (  # noqa: E402
    DEFAULT_IMPORT_WORKBOOK_PATH,
    IMPORT_MODE_WORKS,
    IMPORT_MODE_WORK_DETAILS,
    apply_workbook_import_plan,
    build_workbook_import_plan,
    normalize_import_mode,
    plan_to_response,
)
from script_logging import append_script_log  # noqa: E402
from series_ids import normalize_series_id, parse_series_ids  # noqa: E402


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")
MAX_BODY_BYTES = 1024 * 1024
WORK_SAVE_PATH = "/catalogue/work/save"
WORK_CREATE_PATH = "/catalogue/work/create"
DETAIL_SAVE_PATH = "/catalogue/work-detail/save"
DETAIL_CREATE_PATH = "/catalogue/work-detail/create"
WORK_FILE_SAVE_PATH = "/catalogue/work-file/save"
WORK_FILE_CREATE_PATH = "/catalogue/work-file/create"
WORK_FILE_DELETE_PATH = "/catalogue/work-file/delete"
WORK_LINK_SAVE_PATH = "/catalogue/work-link/save"
WORK_LINK_CREATE_PATH = "/catalogue/work-link/create"
WORK_LINK_DELETE_PATH = "/catalogue/work-link/delete"
IMPORT_PREVIEW_PATH = "/catalogue/import-preview"
IMPORT_APPLY_PATH = "/catalogue/import-apply"
SERIES_SAVE_PATH = "/catalogue/series/save"
SERIES_CREATE_PATH = "/catalogue/series/create"
BUILD_PREVIEW_PATH = "/catalogue/build-preview"
BUILD_APPLY_PATH = "/catalogue/build-apply"
MOMENT_IMPORT_PREVIEW_PATH = "/catalogue/moment/import-preview"
MOMENT_IMPORT_APPLY_PATH = "/catalogue/moment/import-apply"
BULK_SAVE_PATH = "/catalogue/bulk-save"
DELETE_PREVIEW_PATH = "/catalogue/delete-preview"
DELETE_APPLY_PATH = "/catalogue/delete-apply"

BULK_WORK_EDITABLE_FIELDS = {
    "status",
    "published_date",
    "project_folder",
    "project_filename",
    "title",
    "year",
    "year_display",
    "medium_type",
    "medium_caption",
    "duration",
    "height_cm",
    "width_cm",
    "depth_cm",
    "storage_location",
    "work_prose_file",
    "notes",
    "provenance",
    "artist",
}

BULK_DETAIL_EDITABLE_FIELDS = {
    "project_subfolder",
    "project_filename",
    "title",
    "status",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def activity_id(now_utc: str, operation: str) -> str:
    safe_operation = "".join(ch if ch.isalnum() else "-" for ch in operation.lower()).strip("-")
    return f"{now_utc}-{safe_operation or 'catalogue-event'}"


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def allowed_origin(origin: str) -> Optional[str]:
    if not origin:
        return None

    try:
        parsed = urlparse(origin)
    except Exception:
        return None

    if parsed.scheme != "http":
        return None
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return None
    if parsed.path not in {"", "/"}:
        return None
    if parsed.params or parsed.query or parsed.fragment:
        return None
    if parsed.port is None:
        return f"{parsed.scheme}://{parsed.hostname}"
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"


def record_hash(record: Mapping[str, Any]) -> str:
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def extract_build_request(body: Mapping[str, Any]) -> tuple[str, list[str], bool]:
    work_id = slug_id(body.get("work_id"))
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    force = bool(body.get("force"))
    return work_id, extra_series_ids, force


def extract_generic_build_request(body: Mapping[str, Any]) -> tuple[str, str, list[str], list[str], bool]:
    work_id = str(body.get("work_id") or "").strip()
    series_id = str(body.get("series_id") or "").strip()
    if bool(work_id) == bool(series_id):
        raise ValueError("build request must include exactly one of work_id or series_id")
    normalized_work_id = slug_id(work_id) if work_id else ""
    normalized_series_id = normalize_series_id(series_id) if series_id else ""
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    extra_work_ids: list[str] = []
    for raw in body.get("extra_work_ids") or []:
        extra_work_ids.append(slug_id(raw))
    force = bool(body.get("force"))
    return normalized_work_id, normalized_series_id, extra_series_ids, extra_work_ids, force


def extract_moment_import_request(body: Mapping[str, Any]) -> tuple[str, bool]:
    moment_file = str(body.get("moment_file") or body.get("file") or "").strip()
    if not moment_file:
        raise ValueError("moment_file is required")
    force = bool(body.get("force"))
    return moment_file, force


def extract_import_mode(body: Mapping[str, Any]) -> str:
    return normalize_import_mode(body.get("mode"))


def extract_bulk_save_request(body: Mapping[str, Any]) -> Dict[str, Any]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"works", "work_details"}:
        raise ValueError("bulk save kind must be works or work_details")

    raw_ids = body.get("ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("bulk save ids must be a non-empty array")

    ids: list[str] = []
    seen_ids: set[str] = set()
    for raw in raw_ids:
        if kind == "works":
            record_id = slug_id(raw)
        else:
            record_id = normalize_detail_uid_value(raw)
        if record_id in seen_ids:
            continue
        seen_ids.add(record_id)
        ids.append(record_id)
    if not ids:
        raise ValueError("bulk save ids must include at least one valid id")

    raw_expected_hashes = body.get("expected_record_hashes") or {}
    if not isinstance(raw_expected_hashes, dict):
        raise ValueError("expected_record_hashes must be an object")
    expected_hashes: Dict[str, str] = {}
    for record_id in ids:
        expected_hashes[record_id] = str(raw_expected_hashes.get(record_id) or "").strip()

    raw_set_fields = body.get("set_fields") or {}
    if not isinstance(raw_set_fields, dict):
        raise ValueError("set_fields must be an object")
    allowed_fields = BULK_WORK_EDITABLE_FIELDS if kind == "works" else BULK_DETAIL_EDITABLE_FIELDS
    unknown_fields = sorted(str(key) for key in raw_set_fields.keys() if str(key) not in allowed_fields)
    if unknown_fields:
        raise ValueError(f"bulk save contains unsupported fields: {', '.join(unknown_fields)}")
    set_fields = {str(key): raw_set_fields[key] for key in raw_set_fields.keys()}

    raw_series_operation = body.get("series_operation")
    if kind != "works" and raw_series_operation not in (None, "", {}):
        raise ValueError("series_operation is only supported for works bulk save")

    series_operation = None
    if kind == "works" and raw_series_operation is not None:
        if not isinstance(raw_series_operation, dict):
            raise ValueError("series_operation must be an object")
        mode = str(raw_series_operation.get("mode") or "").strip().lower()
        if mode not in {"replace", "add_remove"}:
            raise ValueError("series_operation.mode must be replace or add_remove")
        operation: Dict[str, Any] = {"mode": mode}
        if mode == "replace":
            operation["series_ids"] = normalize_series_ids_value(raw_series_operation.get("series_ids"))
        else:
            operation["add_series_ids"] = normalize_series_ids_value(raw_series_operation.get("add_series_ids"))
            operation["remove_series_ids"] = normalize_series_ids_value(raw_series_operation.get("remove_series_ids"))
        series_operation = operation

    return {
        "kind": kind,
        "ids": ids,
        "expected_record_hashes": expected_hashes,
        "set_fields": set_fields,
        "series_operation": series_operation,
    }


def extract_delete_request(body: Mapping[str, Any]) -> Dict[str, str]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "work_detail", "series"}:
        raise ValueError("delete kind must be work, work_detail, or series")

    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "work_detail":
        record_id = normalize_detail_uid_value(body.get("detail_uid") or body.get("id"))
    else:
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    expected_record_hash = str(body.get("expected_record_hash") or "").strip()
    return {
        "kind": kind,
        "id": record_id,
        "expected_record_hash": expected_record_hash,
    }


def extract_work_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("work"))
    if raw_record is None:
        raw_record = {field: body[field] for field in WORK_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")

    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in WORK_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work field")
    return dict(raw_record)


def extract_work_detail_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("work_detail"))
    if raw_record is None:
        raw_record = {field: body[field] for field in DETAIL_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")

    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in DETAIL_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work detail field")
    return dict(raw_record)


def extract_series_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("series"))
    if raw_record is None:
        raw_record = {field: body[field] for field in SERIES_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")

    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in SERIES_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one series field")
    return dict(raw_record)


def extract_series_work_updates(body: Mapping[str, Any]) -> list[Dict[str, Any]]:
    raw_updates = body.get("work_updates") or []
    if raw_updates == []:
        return []
    if not isinstance(raw_updates, list):
        raise ValueError("work_updates must be an array")
    updates: list[Dict[str, Any]] = []
    for raw in raw_updates:
        if not isinstance(raw, dict):
            raise ValueError("work_updates entries must be objects")
        unknown = sorted(str(key) for key in raw.keys() if str(key) not in {"work_id", "series_ids", "expected_record_hash"})
        if unknown:
            raise ValueError(f"work_updates entry contains unsupported fields: {', '.join(unknown)}")
        work_id = slug_id(raw.get("work_id"))
        series_ids = normalize_series_ids_value(raw.get("series_ids"))
        updates.append(
            {
                "work_id": work_id,
                "series_ids": series_ids,
                "expected_record_hash": str(raw.get("expected_record_hash") or "").strip(),
            }
        )
    return updates


def extract_work_file_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("work_file"))
    if raw_record is None:
        raw_record = {field: body[field] for field in FILE_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in FILE_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work file field")
    return dict(raw_record)


def extract_work_link_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("work_link"))
    if raw_record is None:
        raw_record = {field: body[field] for field in LINK_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in LINK_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work link field")
    return dict(raw_record)


def normalize_work_update(work_id: str, current_record: Mapping[str, Any], update: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["work_id"] = slug_id(merged.get("work_id") or work_id)
    if merged["work_id"] != work_id:
        raise ValueError("record.work_id must match work_id")

    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    if "series_ids" in update:
        merged["series_ids"] = normalize_series_ids_value(update.get("series_ids"))

    return normalize_source_record(merged, WORK_FIELDS, text_fields=WORK_TEXT_FIELDS)


def normalize_work_detail_update(
    detail_uid: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["detail_uid"] = str(merged.get("detail_uid") or detail_uid).strip()
    if merged["detail_uid"] != detail_uid:
        raise ValueError("record.detail_uid must match detail_uid")

    work_id = slug_id(merged.get("work_id"))
    detail_id = slug_id(merged.get("detail_id"), width=3)
    normalized_uid = f"{work_id}-{detail_id}"
    if normalized_uid != detail_uid:
        raise ValueError("record.work_id/detail_id do not match detail_uid")

    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    merged["work_id"] = work_id
    merged["detail_id"] = detail_id
    merged["detail_uid"] = normalized_uid
    return normalize_source_record(merged, DETAIL_FIELDS, text_fields=DETAIL_TEXT_FIELDS)


def normalize_series_update(
    series_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["series_id"] = normalize_series_id(merged.get("series_id") or series_id)
    if merged["series_id"] != series_id:
        raise ValueError("record.series_id must match series_id")
    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    if "primary_work_id" in update:
        primary_work_id = update.get("primary_work_id")
        merged["primary_work_id"] = slug_id(primary_work_id) if primary_work_id not in {None, ""} else None
    return normalize_source_record(merged, SERIES_FIELDS, text_fields=SERIES_TEXT_FIELDS)


def normalize_work_file_update(
    file_uid: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["file_uid"] = str(merged.get("file_uid") or file_uid).strip()
    if merged["file_uid"] != file_uid:
        raise ValueError("record.file_uid must match file_uid")
    merged["work_id"] = slug_id(merged.get("work_id"))
    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    return normalize_source_record(merged, FILE_FIELDS, text_fields=FILE_TEXT_FIELDS)


def normalize_work_link_update(
    link_uid: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["link_uid"] = str(merged.get("link_uid") or link_uid).strip()
    if merged["link_uid"] != link_uid:
        raise ValueError("record.link_uid must match link_uid")
    merged["work_id"] = slug_id(merged.get("work_id"))
    if "status" in update:
        merged["status"] = normalize_status(update.get("status")) or None
    return normalize_source_record(merged, LINK_FIELDS, text_fields=LINK_TEXT_FIELDS)


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in after.keys() if before.get(field) != after.get(field)]


def validate_bulk_records(
    source_dir: Path,
    *,
    work_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
    detail_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> list[str]:
    source_records = records_from_json_source(source_dir)
    if work_updates:
        for work_id, work_record in work_updates.items():
            source_records.works[work_id] = work_record
    if detail_updates:
        for detail_uid, detail_record in detail_updates.items():
            source_records.work_details[detail_uid] = detail_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def apply_work_bulk_series_operation(
    current_series_ids: list[str],
    operation: Optional[Mapping[str, Any]],
) -> list[str]:
    if not operation:
        return current_series_ids
    mode = str(operation.get("mode") or "").strip().lower()
    if mode == "replace":
        return normalize_series_ids_value(operation.get("series_ids"))
    if mode != "add_remove":
        raise ValueError("unsupported series bulk operation")

    add_series_ids = normalize_series_ids_value(operation.get("add_series_ids"))
    remove_series_ids = set(normalize_series_ids_value(operation.get("remove_series_ids")))
    next_series_ids = [series_id for series_id in current_series_ids if series_id not in remove_series_ids]
    seen = set(next_series_ids)
    for series_id in add_series_ids:
        if series_id in seen:
            continue
        seen.add(series_id)
        next_series_ids.append(series_id)
    return next_series_ids


def preview_work_delete(source_dir: Path, work_id: str) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    work_record = source_records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    dependent_detail_ids = sorted(
        detail_uid
        for detail_uid, detail_record in source_records.work_details.items()
        if str(detail_record.get("work_id") or "") == work_id
    )
    dependent_file_ids = sorted(
        file_uid
        for file_uid, file_record in source_records.work_files.items()
        if str(file_record.get("work_id") or "") == work_id
    )
    dependent_link_ids = sorted(
        link_uid
        for link_uid, link_record in source_records.work_links.items()
        if str(link_record.get("work_id") or "") == work_id
    )
    primary_series_ids = sorted(
        series_id
        for series_id, series_record in source_records.series.items()
        if str(series_record.get("primary_work_id") or "") == work_id
    )
    blockers: list[str] = []
    if primary_series_ids:
        blockers.append(
            "Work is primary_work_id for series: " + ", ".join(primary_series_ids) + ". Reassign those series before deleting the work."
        )
    return {
        "kind": "work",
        "id": work_id,
        "record": work_record,
        "blockers": blockers,
        "affected": {
            "works": [work_id],
            "series": normalize_series_ids_value(work_record.get("series_ids")),
            "work_details": dependent_detail_ids,
            "work_files": dependent_file_ids,
            "work_links": dependent_link_ids,
        },
        "summary": f"Delete work {work_id}, {len(dependent_detail_ids)} detail record(s), {len(dependent_file_ids)} file record(s), and {len(dependent_link_ids)} link record(s).",
    }


def preview_work_detail_delete(source_dir: Path, detail_uid: str) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    detail_record = source_records.work_details.get(detail_uid)
    if not isinstance(detail_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")
    work_id = str(detail_record.get("work_id") or "")
    return {
        "kind": "work_detail",
        "id": detail_uid,
        "record": detail_record,
        "blockers": [],
        "affected": {
            "works": [work_id] if work_id else [],
            "series": [],
            "work_details": [detail_uid],
            "work_files": [],
            "work_links": [],
        },
        "summary": f"Delete work detail {detail_uid}.",
    }


def preview_series_delete(source_dir: Path, series_id: str) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    series_record = source_records.series.get(series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")
    member_work_ids = sorted(
        work_id
        for work_id, work_record in source_records.works.items()
        if series_id in normalize_series_ids_value(work_record.get("series_ids"))
    )
    return {
        "kind": "series",
        "id": series_id,
        "record": series_record,
        "blockers": [],
        "affected": {
            "works": member_work_ids,
            "series": [series_id],
            "work_details": [],
            "work_files": [],
            "work_links": [],
        },
        "summary": f"Delete series {series_id} and remove it from {len(member_work_ids)} member work record(s).",
    }


def validate_work_delete_records(source_dir: Path, work_id: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    updated_works = dict(source_records.works)
    updated_works.pop(work_id, None)
    updated_work_details = {
        detail_uid: detail_record
        for detail_uid, detail_record in source_records.work_details.items()
        if str(detail_record.get("work_id") or "") != work_id
    }
    updated_work_files = {
        file_uid: file_record
        for file_uid, file_record in source_records.work_files.items()
        if str(file_record.get("work_id") or "") != work_id
    }
    updated_work_links = {
        link_uid: link_record
        for link_uid, link_record in source_records.work_links.items()
        if str(link_record.get("work_id") or "") != work_id
    }
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(updated_works),
        work_details=sort_record_map(updated_work_details),
        series=sort_record_map(source_records.series),
        work_files=sort_record_map(updated_work_files),
        work_links=sort_record_map(updated_work_links),
    )
    return validate_source_records(normalized_records)


def validate_work_detail_delete_records(source_dir: Path, detail_uid: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_details.pop(detail_uid, None)
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_series_delete_records(source_dir: Path, series_id: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.series.pop(series_id, None)
    updated_works: Dict[str, Dict[str, Any]] = {}
    for work_id, work_record in source_records.works.items():
        current_series_ids = normalize_series_ids_value(work_record.get("series_ids"))
        if series_id not in current_series_ids:
            continue
        updated_works[work_id] = normalize_work_update(
            work_id,
            work_record,
            {"series_ids": [value for value in current_series_ids if value != series_id]},
        )
    source_records.works.update(updated_works)
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=sort_record_map(source_records.series),
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def build_delete_preview(source_dir: Path, kind: str, record_id: str) -> Dict[str, Any]:
    if kind == "work":
        preview = preview_work_delete(source_dir, record_id)
        preview["validation_errors"] = validate_work_delete_records(source_dir, record_id)
    elif kind == "work_detail":
        preview = preview_work_detail_delete(source_dir, record_id)
        preview["validation_errors"] = validate_work_detail_delete_records(source_dir, record_id)
    else:
        preview = preview_series_delete(source_dir, record_id)
        preview["validation_errors"] = validate_series_delete_records(source_dir, record_id)
    blockers = list(preview.get("blockers") or [])
    validation_errors = list(preview.get("validation_errors") or [])
    preview["blockers"] = blockers
    preview["blocked"] = bool(blockers or validation_errors)
    return preview


def validate_updated_records(source_dir: Path, work_id: str, work_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_created_work_records(source_dir: Path, work_id: str, work_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_updated_detail_records(source_dir: Path, detail_uid: str, detail_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_details[detail_uid] = detail_record
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_created_detail_records(source_dir: Path, detail_uid: str, detail_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_details[detail_uid] = detail_record
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_updated_file_records(source_dir: Path, file_uid: str, file_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_files[file_uid] = file_record
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=sort_record_map(source_records.work_files),
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_created_file_records(source_dir: Path, file_uid: str, file_record: Dict[str, Any]) -> list[str]:
    return validate_updated_file_records(source_dir, file_uid, file_record)


def validate_deleted_file_records(source_dir: Path, file_uid: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_files.pop(file_uid, None)
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=sort_record_map(source_records.work_files),
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_updated_link_records(source_dir: Path, link_uid: str, link_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_links[link_uid] = link_record
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=sort_record_map(source_records.work_links),
    )
    return validate_source_records(normalized_records)


def validate_created_link_records(source_dir: Path, link_uid: str, link_record: Dict[str, Any]) -> list[str]:
    return validate_updated_link_records(source_dir, link_uid, link_record)


def validate_deleted_link_records(source_dir: Path, link_uid: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_links.pop(link_uid, None)
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=source_records.work_details,
        series=source_records.series,
        work_files=source_records.work_files,
        work_links=sort_record_map(source_records.work_links),
    )
    return validate_source_records(normalized_records)


def validate_updated_series_records(
    source_dir: Path,
    series_id: str,
    series_record: Dict[str, Any],
    work_updates: Mapping[str, Dict[str, Any]],
) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.series[series_id] = series_record
    for work_id, work_record in work_updates.items():
        source_records.works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=sort_record_map(source_records.series),
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def validate_created_series_records(
    source_dir: Path,
    series_id: str,
    series_record: Dict[str, Any],
    work_updates: Mapping[str, Dict[str, Any]],
) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.series[series_id] = series_record
    for work_id, work_record in work_updates.items():
        source_records.works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=sort_record_map(source_records.series),
        work_files=source_records.work_files,
        work_links=source_records.work_links,
    )
    return validate_source_records(normalized_records)


def load_works_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("works source file must include a works object")
    return payload


def load_work_details_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    work_details = payload.get("work_details")
    if not isinstance(work_details, dict):
        raise ValueError("work details source file must include a work_details object")
    return payload


def load_series_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    series = payload.get("series")
    if not isinstance(series, dict):
        raise ValueError("series source file must include a series object")
    return payload


def load_work_files_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    work_files = payload.get("work_files")
    if not isinstance(work_files, dict):
        raise ValueError("work files source file must include a work_files object")
    return payload


def load_work_links_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    work_links = payload.get("work_links")
    if not isinstance(work_links, dict):
        raise ValueError("work links source file must include a work_links object")
    return payload


def atomic_write_many(payloads_by_path: Dict[Path, Dict[str, Any]], backups_dir: Path) -> list[Path]:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = backup_stamp_now()
    bundle_dir = backups_dir / f"catalogue-save-{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=False)
    backups: Dict[Path, Path] = {}
    temp_paths: Dict[Path, Path] = {}
    replaced_paths: list[Path] = []

    try:
        for path, payload in payloads_by_path.items():
            if path.exists():
                backup_path = bundle_dir / path.name
                shutil.copy2(path, backup_path)
                backups[path] = backup_path

            fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
            temp_paths[path] = temp_path

        for path, temp_path in temp_paths.items():
            os.replace(temp_path, path)
            replaced_paths.append(path)
    except Exception:
        for path in reversed(replaced_paths):
            backup_path = backups.get(path)
            try:
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, path)
                elif path.exists():
                    path.unlink()
            except Exception:
                pass
        raise
    finally:
        for temp_path in temp_paths.values():
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    return list(backups.values())


class CatalogueWriteServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_cls,
        repo_root: Path,
        source_dir: Path,
        lookup_dir: Path,
        works_path: Path,
        work_details_path: Path,
        work_files_path: Path,
        work_links_path: Path,
        series_path: Path,
        allowed_write_paths: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.source_dir = source_dir.resolve()
        self.lookup_dir = lookup_dir.resolve()
        self.works_path = works_path.resolve()
        self.work_details_path = work_details_path.resolve()
        self.work_files_path = work_files_path.resolve()
        self.work_links_path = work_links_path.resolve()
        self.series_path = series_path.resolve()
        self.allowed_write_paths = {path.resolve() for path in allowed_write_paths}
        self.backups_dir = backups_dir.resolve()
        self.dry_run = dry_run

    def rel_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.repo_root))
        except ValueError:
            return path.name

    def log_event(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        try:
            append_script_log(
                Path(__file__),
                event=event,
                details=details,
                repo_root=self.repo_root,
                log_dir_rel=LOGS_REL_DIR,
            )
        except Exception:
            pass

    def append_activity(self, entry: Dict[str, Any]) -> None:
        try:
            append_catalogue_activity(self.repo_root, entry)
        except Exception:
            pass


class Handler(BaseHTTPRequestHandler):
    server: CatalogueWriteServer  # type: ignore[assignment]

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path not in {
            BULK_SAVE_PATH,
            DELETE_PREVIEW_PATH,
            DELETE_APPLY_PATH,
            WORK_CREATE_PATH,
            WORK_SAVE_PATH,
            DETAIL_CREATE_PATH,
            DETAIL_SAVE_PATH,
            WORK_FILE_CREATE_PATH,
            WORK_FILE_SAVE_PATH,
            WORK_FILE_DELETE_PATH,
            WORK_LINK_CREATE_PATH,
            WORK_LINK_SAVE_PATH,
            WORK_LINK_DELETE_PATH,
            IMPORT_PREVIEW_PATH,
            IMPORT_APPLY_PATH,
            SERIES_SAVE_PATH,
            SERIES_CREATE_PATH,
            BUILD_PREVIEW_PATH,
            BUILD_APPLY_PATH,
            MOMENT_IMPORT_PREVIEW_PATH,
            MOMENT_IMPORT_APPLY_PATH,
        }:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_cors_headers(allowed)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        if self.path != "/health":
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "catalogue_write_server",
                "source_dir": self.server.rel_path(self.server.source_dir),
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "works_path": self.server.rel_path(self.server.works_path),
                "backups_dir": self.server.rel_path(self.server.backups_dir),
                "dry_run": self.server.dry_run,
                "time_utc": utc_now(),
            },
            allowed,
        )

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        try:
            if self.path == WORK_CREATE_PATH:
                self._handle_work_create(allowed)
                return
            if self.path == BULK_SAVE_PATH:
                self._handle_bulk_save(allowed)
                return
            if self.path == DELETE_PREVIEW_PATH:
                self._handle_delete_preview(allowed)
                return
            if self.path == DELETE_APPLY_PATH:
                self._handle_delete_apply(allowed)
                return
            if self.path == WORK_SAVE_PATH:
                self._handle_work_save(allowed)
                return
            if self.path == DETAIL_CREATE_PATH:
                self._handle_work_detail_create(allowed)
                return
            if self.path == DETAIL_SAVE_PATH:
                self._handle_work_detail_save(allowed)
                return
            if self.path == WORK_FILE_CREATE_PATH:
                self._handle_work_file_create(allowed)
                return
            if self.path == WORK_FILE_SAVE_PATH:
                self._handle_work_file_save(allowed)
                return
            if self.path == WORK_FILE_DELETE_PATH:
                self._handle_work_file_delete(allowed)
                return
            if self.path == WORK_LINK_CREATE_PATH:
                self._handle_work_link_create(allowed)
                return
            if self.path == WORK_LINK_SAVE_PATH:
                self._handle_work_link_save(allowed)
                return
            if self.path == WORK_LINK_DELETE_PATH:
                self._handle_work_link_delete(allowed)
                return
            if self.path == IMPORT_PREVIEW_PATH:
                self._handle_import_preview(allowed)
                return
            if self.path == IMPORT_APPLY_PATH:
                self._handle_import_apply(allowed)
                return
            if self.path == SERIES_SAVE_PATH:
                self._handle_series_save(allowed)
                return
            if self.path == SERIES_CREATE_PATH:
                self._handle_series_create(allowed)
                return
            if self.path == BUILD_PREVIEW_PATH:
                self._handle_build_preview(allowed)
                return
            if self.path == BUILD_APPLY_PATH:
                self._handle_build_apply(allowed)
                return
            if self.path == MOMENT_IMPORT_PREVIEW_PATH:
                self._handle_moment_import_preview(allowed)
                return
            if self.path == MOMENT_IMPORT_APPLY_PATH:
                self._handle_moment_import_apply(allowed)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
        except ValueError as exc:
            self.server.log_event("request_error", {"path": self.path, "error": str(exc), "kind": "validation"})
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "request.validation_failed"),
                        "time_utc": now_utc,
                        "kind": "validation",
                        "operation": self.path.strip("/") or "request",
                        "status": "failed",
                        "summary": "Catalogue request failed validation.",
                        "affected": {"works": [], "series": [], "work_details": [], "work_files": [], "work_links": [], "moments": []},
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self.server.log_event("request_error", {"path": self.path, "error": str(exc), "kind": "internal"})
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_work_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_work_id = body.get("work_id")
        work_update = extract_work_update(body)
        if requested_work_id is None:
            requested_work_id = work_update.get("work_id")
        work_id = slug_id(requested_work_id)

        works_payload = load_works_payload(self.server.works_path)
        works = works_payload["works"]
        current_record = works.get(work_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"work_id not found: {work_id}")

        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "error": "record changed since loaded",
                    "work_id": work_id,
                    "current_record_hash": current_hash,
                },
                allowed,
            )
            return

        updated_record = normalize_work_update(work_id, current_record, work_update)
        fields_changed = changed_fields(current_record, updated_record)
        validation_errors = validate_updated_records(self.server.source_dir, work_id, updated_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        changed = bool(fields_changed)
        backup_paths: list[Path] = []
        if changed:
            updated_works = dict(works)
            updated_works[work_id] = updated_record
            updated_payload = payload_for_map("works", updated_works)
            target_path = self.server.works_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: updated_payload}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "work_id": work_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record_hash": record_hash(updated_record),
            "record": updated_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_save",
            {
                "work_id": work_id,
                "changed": changed,
                "changed_fields": fields_changed,
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work.save",
                    "status": "completed",
                    "summary": "Saved 1 work source record.",
                    "affected": {"works": [work_id], "series": [], "work_details": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_bulk_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_bulk_save_request(body)
        kind = request["kind"]
        selected_ids: list[str] = request["ids"]
        expected_hashes: Dict[str, str] = request["expected_record_hashes"]
        set_fields: Dict[str, Any] = request["set_fields"]
        series_operation = request["series_operation"]

        source_records = records_from_json_source(self.server.source_dir)
        changed_record_payloads: list[Dict[str, Any]] = []
        changed_ids: list[str] = []
        changed_field_names: set[str] = set()
        build_targets: list[Dict[str, Any]] = []
        affected_work_ids: list[str] = []
        affected_series_ids: set[str] = set()

        if kind == "works":
            works_payload = load_works_payload(self.server.works_path)
            works_map = works_payload["works"]
            pending_updates: Dict[str, Dict[str, Any]] = {}
            for work_id in selected_ids:
                current_record = works_map.get(work_id)
                if not isinstance(current_record, dict):
                    raise ValueError(f"work_id not found: {work_id}")
                expected_hash = expected_hashes.get(work_id) or ""
                current_hash = record_hash(current_record)
                if expected_hash and expected_hash != current_hash:
                    self._send_json(
                        HTTPStatus.CONFLICT,
                        {
                            "ok": False,
                            "error": "record changed since loaded",
                            "kind": kind,
                            "work_id": work_id,
                            "current_record_hash": current_hash,
                        },
                        allowed,
                    )
                    return

                update = dict(set_fields)
                if series_operation is not None:
                    update["series_ids"] = apply_work_bulk_series_operation(
                        normalize_series_ids_value(current_record.get("series_ids")),
                        series_operation,
                    )
                updated_record = normalize_work_update(work_id, current_record, update)
                pending_updates[work_id] = updated_record

            validation_errors = validate_bulk_records(self.server.source_dir, work_updates=pending_updates)
            if validation_errors:
                raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

            updated_works = dict(works_map)
            for work_id in selected_ids:
                current_record = works_map[work_id]
                updated_record = pending_updates[work_id]
                fields_changed = changed_fields(current_record, updated_record)
                if not fields_changed:
                    continue
                changed_ids.append(work_id)
                changed_field_names.update(fields_changed)
                changed_record_payloads.append(
                    {
                        "work_id": work_id,
                        "record_hash": record_hash(updated_record),
                        "record": updated_record,
                    }
                )
                previous_series_ids = normalize_series_ids_value(current_record.get("series_ids"))
                next_series_ids = normalize_series_ids_value(updated_record.get("series_ids"))
                extra_series_ids = [series_id for series_id in previous_series_ids if series_id not in next_series_ids]
                build_targets.append({"work_id": work_id, "extra_series_ids": extra_series_ids})
                affected_work_ids.append(work_id)
                affected_series_ids.update(previous_series_ids)
                affected_series_ids.update(next_series_ids)
                updated_works[work_id] = updated_record

            changed = bool(changed_ids)
            backup_paths: list[Path] = []
            if changed:
                target_path = self.server.works_path.resolve()
                if target_path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
                if not self.server.dry_run:
                    backup_paths = atomic_write_many({target_path: payload_for_map("works", updated_works)}, self.server.backups_dir)

            response_payload: Dict[str, Any] = {
                "ok": True,
                "kind": kind,
                "selected_ids": selected_ids,
                "selected_count": len(selected_ids),
                "changed": changed,
                "changed_ids": changed_ids,
                "changed_count": len(changed_ids),
                "changed_fields": sorted(changed_field_names),
                "records": changed_record_payloads,
                "build_targets": build_targets,
                "affected_work_ids": affected_work_ids,
                "affected_series_ids": sorted(affected_series_ids),
            }
            if self.server.dry_run:
                response_payload["dry_run"] = True
                response_payload["would_write"] = changed
            elif changed:
                response_payload["saved_at_utc"] = utc_now()
                if backup_paths:
                    response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

            self.server.log_event(
                "catalogue_bulk_save",
                {
                    "kind": kind,
                    "selected_count": len(selected_ids),
                    "changed_count": len(changed_ids),
                    "changed_fields": sorted(changed_field_names),
                    "dry_run": self.server.dry_run,
                },
            )
            if changed and not self.server.dry_run:
                self._refresh_lookup_payloads()
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "bulk-save.works"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "bulk-save.works",
                        "status": "completed",
                        "summary": f"Bulk-saved {len(changed_ids)} work source record(s).",
                        "affected": {"works": changed_ids, "series": sorted(affected_series_ids), "work_details": []},
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
            self._send_json(HTTPStatus.OK, response_payload, allowed)
            return

        details_payload = load_work_details_payload(self.server.work_details_path)
        detail_map = details_payload["work_details"]
        pending_updates = {}
        for detail_uid in selected_ids:
            current_record = detail_map.get(detail_uid)
            if not isinstance(current_record, dict):
                raise ValueError(f"detail_uid not found: {detail_uid}")
            expected_hash = expected_hashes.get(detail_uid) or ""
            current_hash = record_hash(current_record)
            if expected_hash and expected_hash != current_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {
                        "ok": False,
                        "error": "record changed since loaded",
                        "kind": kind,
                        "detail_uid": detail_uid,
                        "current_record_hash": current_hash,
                    },
                    allowed,
                )
                return
            updated_record = normalize_work_detail_update(detail_uid, current_record, set_fields)
            work_id = str(updated_record.get("work_id") or "")
            if work_id not in source_records.works:
                raise ValueError(f"parent work_id not found: {work_id}")
            pending_updates[detail_uid] = updated_record

        validation_errors = validate_bulk_records(self.server.source_dir, detail_updates=pending_updates)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        updated_details = dict(detail_map)
        for detail_uid in selected_ids:
            current_record = detail_map[detail_uid]
            updated_record = pending_updates[detail_uid]
            fields_changed = changed_fields(current_record, updated_record)
            if not fields_changed:
                continue
            changed_ids.append(detail_uid)
            changed_field_names.update(fields_changed)
            changed_record_payloads.append(
                {
                    "detail_uid": detail_uid,
                    "record_hash": record_hash(updated_record),
                    "record": updated_record,
                }
            )
            work_id = str(updated_record.get("work_id") or "")
            affected_work_ids.append(work_id)
            build_targets.append({"work_id": work_id, "extra_series_ids": []})
            updated_details[detail_uid] = updated_record

        changed = bool(changed_ids)
        backup_paths = []
        if changed:
            target_path = self.server.work_details_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: payload_for_map("work_details", updated_details)}, self.server.backups_dir)

        response_payload = {
            "ok": True,
            "kind": kind,
            "selected_ids": selected_ids,
            "selected_count": len(selected_ids),
            "changed": changed,
            "changed_ids": changed_ids,
            "changed_count": len(changed_ids),
            "changed_fields": sorted(changed_field_names),
            "records": changed_record_payloads,
            "build_targets": [
                {"work_id": work_id, "extra_series_ids": []}
                for work_id in sorted(set(affected_work_ids))
            ],
            "affected_work_ids": sorted(set(affected_work_ids)),
            "affected_series_ids": [],
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_bulk_save",
            {
                "kind": kind,
                "selected_count": len(selected_ids),
                "changed_count": len(changed_ids),
                "changed_fields": sorted(changed_field_names),
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "bulk-save.work-details"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "bulk-save.work-details",
                    "status": "completed",
                    "summary": f"Bulk-saved {len(changed_ids)} work detail source record(s).",
                    "affected": {"works": sorted(set(affected_work_ids)), "series": [], "work_details": changed_ids},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_delete_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_delete_request(body)
        preview = build_delete_preview(self.server.source_dir, request["kind"], request["id"])
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "kind": request["kind"],
                "id": request["id"],
                "preview": preview,
            },
            allowed,
        )

    def _handle_delete_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_delete_request(body)
        kind = request["kind"]
        record_id = request["id"]
        expected_hash = request["expected_record_hash"]
        preview = build_delete_preview(self.server.source_dir, kind, record_id)
        if preview.get("blocked"):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "delete preview contains blockers",
                    "kind": kind,
                    "id": record_id,
                    "preview": preview,
                },
                allowed,
            )
            return

        backup_paths: list[Path] = []
        response_payload: Dict[str, Any]

        if kind == "work":
            works_payload = load_works_payload(self.server.works_path)
            details_payload = load_work_details_payload(self.server.work_details_path)
            files_payload = load_work_files_payload(self.server.work_files_path)
            links_payload = load_work_links_payload(self.server.work_links_path)
            current_record = works_payload["works"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"work_id not found: {record_id}")
            current_hash = record_hash(current_record)
            if expected_hash and expected_hash != current_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"ok": False, "error": "record changed since loaded", "work_id": record_id, "current_record_hash": current_hash},
                    allowed,
                )
                return
            updated_works = dict(works_payload["works"])
            del updated_works[record_id]
            updated_details = {
                detail_uid: detail_record
                for detail_uid, detail_record in details_payload["work_details"].items()
                if str(detail_record.get("work_id") or "") != record_id
            }
            updated_files = {
                file_uid: file_record
                for file_uid, file_record in files_payload["work_files"].items()
                if str(file_record.get("work_id") or "") != record_id
            }
            updated_links = {
                link_uid: link_record
                for link_uid, link_record in links_payload["work_links"].items()
                if str(link_record.get("work_id") or "") != record_id
            }
            if not self.server.dry_run:
                payloads = {
                    self.server.works_path.resolve(): payload_for_map("works", updated_works),
                    self.server.work_details_path.resolve(): payload_for_map("work_details", updated_details),
                    self.server.work_files_path.resolve(): payload_for_map("work_files", updated_files),
                    self.server.work_links_path.resolve(): payload_for_map("work_links", updated_links),
                }
                for target_path in payloads:
                    if target_path not in self.server.allowed_write_paths:
                        raise ValueError("write target not allowlisted")
                backup_paths = atomic_write_many(payloads, self.server.backups_dir)
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
            }
            if not self.server.dry_run:
                self._refresh_lookup_payloads()
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "work.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "work.delete",
                        "status": "completed",
                        "summary": f"Deleted work {record_id} and dependent source records.",
                        "affected": preview["affected"],
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
        elif kind == "work_detail":
            details_payload = load_work_details_payload(self.server.work_details_path)
            current_record = details_payload["work_details"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"detail_uid not found: {record_id}")
            current_hash = record_hash(current_record)
            if expected_hash and expected_hash != current_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"ok": False, "error": "record changed since loaded", "detail_uid": record_id, "current_record_hash": current_hash},
                    allowed,
                )
                return
            updated_details = dict(details_payload["work_details"])
            del updated_details[record_id]
            if not self.server.dry_run:
                target_path = self.server.work_details_path.resolve()
                if target_path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
                backup_paths = atomic_write_many({target_path: payload_for_map("work_details", updated_details)}, self.server.backups_dir)
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
            }
            if not self.server.dry_run:
                self._refresh_lookup_payloads()
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "work-detail.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "work-detail.delete",
                        "status": "completed",
                        "summary": f"Deleted work detail {record_id}.",
                        "affected": preview["affected"],
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
        else:
            series_payload = load_series_payload(self.server.series_path)
            works_payload = load_works_payload(self.server.works_path)
            current_record = series_payload["series"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"series_id not found: {record_id}")
            current_hash = record_hash(current_record)
            if expected_hash and expected_hash != current_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"ok": False, "error": "record changed since loaded", "series_id": record_id, "current_record_hash": current_hash},
                    allowed,
                )
                return
            updated_series = dict(series_payload["series"])
            del updated_series[record_id]
            updated_works = dict(works_payload["works"])
            for work_id in preview["affected"]["works"]:
                work_record = updated_works.get(work_id)
                if not isinstance(work_record, dict):
                    continue
                next_series_ids = [value for value in normalize_series_ids_value(work_record.get("series_ids")) if value != record_id]
                updated_works[work_id] = normalize_work_update(work_id, work_record, {"series_ids": next_series_ids})
            if not self.server.dry_run:
                payloads = {
                    self.server.series_path.resolve(): payload_for_map("series", updated_series),
                    self.server.works_path.resolve(): payload_for_map("works", updated_works),
                }
                for target_path in payloads:
                    if target_path not in self.server.allowed_write_paths:
                        raise ValueError("write target not allowlisted")
                backup_paths = atomic_write_many(payloads, self.server.backups_dir)
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
            }
            if not self.server.dry_run:
                self._refresh_lookup_payloads()
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "series.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "series.delete",
                        "status": "completed",
                        "summary": f"Deleted series {record_id} and updated member work records.",
                        "affected": preview["affected"],
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )

        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_work_id = body.get("work_id")
        work_update = extract_work_update(body)
        if requested_work_id is None:
            requested_work_id = work_update.get("work_id")
        work_id = slug_id(requested_work_id)

        works_payload = load_works_payload(self.server.works_path)
        works = works_payload["works"]
        if isinstance(works.get(work_id), dict):
            raise ValueError(f"work_id already exists: {work_id}")

        blank_work_record = {field: None for field in WORK_FIELDS}
        blank_work_record["work_id"] = work_id
        work_update = dict(work_update)
        if not normalize_status(work_update.get("status")):
            work_update["status"] = "draft"
        if "series_ids" not in work_update:
            work_update["series_ids"] = []
        created_record = normalize_work_update(work_id, blank_work_record, work_update)
        if not str(created_record.get("title") or "").strip():
            raise ValueError("work title is required")

        validation_errors = validate_created_work_records(self.server.source_dir, work_id, created_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        target_path = self.server.works_path.resolve()
        if target_path not in self.server.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_works = dict(works)
            updated_works[work_id] = created_record
            backup_paths = atomic_write_many({target_path: payload_for_map("works", updated_works)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_work_record, created_record),
            "record_hash": record_hash(created_record),
            "record": created_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_create",
            {
                "work_id": work_id,
                "changed_fields": response_payload["changed_fields"],
                "dry_run": self.server.dry_run,
            },
        )
        if not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work.create"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work.create",
                    "status": "completed",
                    "summary": f"Created draft work {work_id}.",
                    "affected": {"works": [work_id], "series": [], "work_details": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_detail_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_detail_uid = body.get("detail_uid")
        detail_update = extract_work_detail_update(body)
        requested_work_id = body.get("work_id", detail_update.get("work_id"))
        requested_detail_id = body.get("detail_id", detail_update.get("detail_id"))
        work_id = slug_id(requested_work_id)
        detail_id = slug_id(requested_detail_id, width=3)
        detail_uid = normalize_detail_uid_value(requested_detail_uid or f"{work_id}-{detail_id}")

        details_payload = load_work_details_payload(self.server.work_details_path)
        work_details = details_payload["work_details"]
        if isinstance(work_details.get(detail_uid), dict):
            raise ValueError(f"detail_uid already exists: {detail_uid}")

        source_records = records_from_json_source(self.server.source_dir)
        if work_id not in source_records.works:
            raise ValueError(f"parent work_id not found: {work_id}")

        blank_detail_record = {field: None for field in DETAIL_FIELDS}
        blank_detail_record["detail_uid"] = detail_uid
        blank_detail_record["work_id"] = work_id
        blank_detail_record["detail_id"] = detail_id
        detail_update = dict(detail_update)
        detail_update["detail_uid"] = detail_uid
        detail_update["work_id"] = work_id
        detail_update["detail_id"] = detail_id
        if not normalize_status(detail_update.get("status")):
            detail_update["status"] = "draft"
        created_record = normalize_work_detail_update(detail_uid, blank_detail_record, detail_update)
        if not str(created_record.get("title") or "").strip():
            raise ValueError("work detail title is required")

        validation_errors = validate_created_detail_records(self.server.source_dir, detail_uid, created_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        target_path = self.server.work_details_path.resolve()
        if target_path not in self.server.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_details = dict(work_details)
            updated_details[detail_uid] = created_record
            backup_paths = atomic_write_many({target_path: payload_for_map("work_details", updated_details)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "detail_uid": detail_uid,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_detail_record, created_record),
            "record_hash": record_hash(created_record),
            "record": created_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_detail_create",
            {
                "detail_uid": detail_uid,
                "work_id": work_id,
                "changed_fields": response_payload["changed_fields"],
                "dry_run": self.server.dry_run,
            },
        )
        if not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-detail.create"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-detail.create",
                    "status": "completed",
                    "summary": f"Created draft work detail {detail_uid}.",
                    "affected": {"works": [work_id], "series": [], "work_details": [detail_uid]},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_detail_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_detail_uid = body.get("detail_uid")
        detail_update = extract_work_detail_update(body)
        if not requested_detail_uid:
            requested_detail_uid = detail_update.get("detail_uid")
        detail_uid = normalize_detail_uid_value(requested_detail_uid)

        details_payload = load_work_details_payload(self.server.work_details_path)
        work_details = details_payload["work_details"]
        current_record = work_details.get(detail_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"detail_uid not found: {detail_uid}")

        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "error": "record changed since loaded",
                    "detail_uid": detail_uid,
                    "current_record_hash": current_hash,
                },
                allowed,
            )
            return

        updated_record = normalize_work_detail_update(detail_uid, current_record, detail_update)
        work_id = str(updated_record.get("work_id") or "")
        if not work_id:
            raise ValueError("work detail missing work_id")

        source_records = records_from_json_source(self.server.source_dir)
        if work_id not in source_records.works:
            raise ValueError(f"parent work_id not found: {work_id}")

        fields_changed = changed_fields(current_record, updated_record)
        validation_errors = validate_updated_detail_records(self.server.source_dir, detail_uid, updated_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        changed = bool(fields_changed)
        backup_paths: list[Path] = []
        if changed:
            updated_details = dict(work_details)
            updated_details[detail_uid] = updated_record
            updated_payload = payload_for_map("work_details", updated_details)
            target_path = self.server.work_details_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: updated_payload}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "detail_uid": detail_uid,
            "work_id": work_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record_hash": record_hash(updated_record),
            "record": updated_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_detail_save",
            {
                "detail_uid": detail_uid,
                "work_id": work_id,
                "changed": changed,
                "changed_fields": fields_changed,
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-detail.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-detail.save",
                    "status": "completed",
                    "summary": "Saved 1 work detail source record.",
                    "affected": {"works": [work_id], "series": [], "work_details": [detail_uid]},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_file_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        file_update = extract_work_file_update(body)
        work_id = slug_id(body.get("work_id", file_update.get("work_id")))
        source_records = records_from_json_source(self.server.source_dir)
        if work_id not in source_records.works:
            raise ValueError(f"parent work_id not found: {work_id}")
        filename = str(file_update.get("filename") or "").strip()
        label = str(file_update.get("label") or "").strip()
        if not filename:
            raise ValueError("work file filename is required")
        if not label:
            raise ValueError("work file label is required")
        work_files_payload = load_work_files_payload(self.server.work_files_path)
        work_files = work_files_payload["work_files"]
        used_uids = set(work_files.keys())
        fragment = safe_uid_fragment(Path(filename).stem or label, "file")
        file_uid = unique_uid(f"{work_id}:{fragment}", used_uids)
        blank_record = {field: None for field in FILE_FIELDS}
        blank_record["file_uid"] = file_uid
        blank_record["work_id"] = work_id
        file_update = dict(file_update)
        file_update["file_uid"] = file_uid
        file_update["work_id"] = work_id
        if not normalize_status(file_update.get("status")):
            file_update["status"] = "draft"
        created_record = normalize_work_file_update(file_uid, blank_record, file_update)
        validation_errors = validate_created_file_records(self.server.source_dir, file_uid, created_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        target_path = self.server.work_files_path.resolve()
        if target_path not in self.server.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_records = dict(work_files)
            updated_records[file_uid] = created_record
            backup_paths = atomic_write_many({target_path: payload_for_map("work_files", updated_records)}, self.server.backups_dir)
        response_payload: Dict[str, Any] = {
            "ok": True,
            "file_uid": file_uid,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_record, created_record),
            "record_hash": record_hash(created_record),
            "record": created_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-file.create"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-file.create",
                    "status": "completed",
                    "summary": f"Created draft work file {file_uid}.",
                    "affected": {"works": [work_id], "series": [], "work_details": [], "work_files": [file_uid], "work_links": [], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_file_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_uid = str(body.get("file_uid") or "").strip()
        file_update = extract_work_file_update(body)
        if not requested_uid:
            requested_uid = str(file_update.get("file_uid") or "").strip()
        file_uid = requested_uid
        payload = load_work_files_payload(self.server.work_files_path)
        record_map = payload["work_files"]
        current_record = record_map.get(file_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"file_uid not found: {file_uid}")
        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "record changed since loaded", "file_uid": file_uid, "current_record_hash": current_hash}, allowed)
            return
        updated_record = normalize_work_file_update(file_uid, current_record, file_update)
        if not str(updated_record.get("filename") or "").strip():
            raise ValueError("work file filename is required")
        if not str(updated_record.get("label") or "").strip():
            raise ValueError("work file label is required")
        validation_errors = validate_updated_file_records(self.server.source_dir, file_uid, updated_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        fields_changed = changed_fields(current_record, updated_record)
        changed = bool(fields_changed)
        backup_paths: list[Path] = []
        if changed:
            updated_map = dict(record_map)
            updated_map[file_uid] = updated_record
            target_path = self.server.work_files_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: payload_for_map("work_files", updated_map)}, self.server.backups_dir)
        response_payload: Dict[str, Any] = {
            "ok": True,
            "file_uid": file_uid,
            "work_id": updated_record.get("work_id"),
            "changed": changed,
            "changed_fields": fields_changed,
            "record_hash": record_hash(updated_record),
            "record": updated_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-file.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-file.save",
                    "status": "completed",
                    "summary": "Saved 1 work file source record.",
                    "affected": {"works": [updated_record.get("work_id")], "series": [], "work_details": [], "work_files": [file_uid], "work_links": [], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_file_delete(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        file_uid = str(body.get("file_uid") or "").strip()
        if not file_uid:
            raise ValueError("file_uid is required")
        payload = load_work_files_payload(self.server.work_files_path)
        record_map = payload["work_files"]
        current_record = record_map.get(file_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"file_uid not found: {file_uid}")
        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "record changed since loaded", "file_uid": file_uid, "current_record_hash": current_hash}, allowed)
            return
        validation_errors = validate_deleted_file_records(self.server.source_dir, file_uid)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_map = dict(record_map)
            del updated_map[file_uid]
            target_path = self.server.work_files_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            backup_paths = atomic_write_many({target_path: payload_for_map("work_files", updated_map)}, self.server.backups_dir)
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-file.delete"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-file.delete",
                    "status": "completed",
                    "summary": "Deleted 1 work file source record.",
                    "affected": {"works": [current_record.get("work_id")], "series": [], "work_details": [], "work_files": [file_uid], "work_links": [], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        response_payload: Dict[str, Any] = {
            "ok": True,
            "file_uid": file_uid,
            "work_id": current_record.get("work_id"),
            "deleted": True,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        elif backup_paths:
            response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_link_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        link_update = extract_work_link_update(body)
        work_id = slug_id(body.get("work_id", link_update.get("work_id")))
        source_records = records_from_json_source(self.server.source_dir)
        if work_id not in source_records.works:
            raise ValueError(f"parent work_id not found: {work_id}")
        url = str(link_update.get("url") or "").strip()
        label = str(link_update.get("label") or "").strip()
        if not url:
            raise ValueError("work link url is required")
        if not label:
            raise ValueError("work link label is required")
        payload = load_work_links_payload(self.server.work_links_path)
        record_map = payload["work_links"]
        used_uids = set(record_map.keys())
        fragment = safe_uid_fragment(label or url, "link")
        link_uid = unique_uid(f"{work_id}:{fragment}", used_uids)
        blank_record = {field: None for field in LINK_FIELDS}
        blank_record["link_uid"] = link_uid
        blank_record["work_id"] = work_id
        link_update = dict(link_update)
        link_update["link_uid"] = link_uid
        link_update["work_id"] = work_id
        if not normalize_status(link_update.get("status")):
            link_update["status"] = "draft"
        created_record = normalize_work_link_update(link_uid, blank_record, link_update)
        validation_errors = validate_created_link_records(self.server.source_dir, link_uid, created_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        target_path = self.server.work_links_path.resolve()
        if target_path not in self.server.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_records = dict(record_map)
            updated_records[link_uid] = created_record
            backup_paths = atomic_write_many({target_path: payload_for_map("work_links", updated_records)}, self.server.backups_dir)
        response_payload: Dict[str, Any] = {
            "ok": True,
            "link_uid": link_uid,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_record, created_record),
            "record_hash": record_hash(created_record),
            "record": created_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-link.create"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-link.create",
                    "status": "completed",
                    "summary": f"Created draft work link {link_uid}.",
                    "affected": {"works": [work_id], "series": [], "work_details": [], "work_files": [], "work_links": [link_uid], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_link_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_uid = str(body.get("link_uid") or "").strip()
        link_update = extract_work_link_update(body)
        if not requested_uid:
            requested_uid = str(link_update.get("link_uid") or "").strip()
        link_uid = requested_uid
        payload = load_work_links_payload(self.server.work_links_path)
        record_map = payload["work_links"]
        current_record = record_map.get(link_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"link_uid not found: {link_uid}")
        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "record changed since loaded", "link_uid": link_uid, "current_record_hash": current_hash}, allowed)
            return
        updated_record = normalize_work_link_update(link_uid, current_record, link_update)
        if not str(updated_record.get("url") or "").strip():
            raise ValueError("work link url is required")
        if not str(updated_record.get("label") or "").strip():
            raise ValueError("work link label is required")
        validation_errors = validate_updated_link_records(self.server.source_dir, link_uid, updated_record)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        fields_changed = changed_fields(current_record, updated_record)
        changed = bool(fields_changed)
        backup_paths: list[Path] = []
        if changed:
            updated_map = dict(record_map)
            updated_map[link_uid] = updated_record
            target_path = self.server.work_links_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: payload_for_map("work_links", updated_map)}, self.server.backups_dir)
        response_payload: Dict[str, Any] = {
            "ok": True,
            "link_uid": link_uid,
            "work_id": updated_record.get("work_id"),
            "changed": changed,
            "changed_fields": fields_changed,
            "record_hash": record_hash(updated_record),
            "record": updated_record,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-link.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-link.save",
                    "status": "completed",
                    "summary": "Saved 1 work link source record.",
                    "affected": {"works": [updated_record.get("work_id")], "series": [], "work_details": [], "work_files": [], "work_links": [link_uid], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_link_delete(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        link_uid = str(body.get("link_uid") or "").strip()
        if not link_uid:
            raise ValueError("link_uid is required")
        payload = load_work_links_payload(self.server.work_links_path)
        record_map = payload["work_links"]
        current_record = record_map.get(link_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"link_uid not found: {link_uid}")
        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "record changed since loaded", "link_uid": link_uid, "current_record_hash": current_hash}, allowed)
            return
        validation_errors = validate_deleted_link_records(self.server.source_dir, link_uid)
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            updated_map = dict(record_map)
            del updated_map[link_uid]
            target_path = self.server.work_links_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            backup_paths = atomic_write_many({target_path: payload_for_map("work_links", updated_map)}, self.server.backups_dir)
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "work-link.delete"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "work-link.delete",
                    "status": "completed",
                    "summary": "Deleted 1 work link source record.",
                    "affected": {"works": [current_record.get("work_id")], "series": [], "work_details": [], "work_files": [], "work_links": [link_uid], "moments": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        response_payload: Dict[str, Any] = {
            "ok": True,
            "link_uid": link_uid,
            "work_id": current_record.get("work_id"),
            "deleted": True,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        elif backup_paths:
            response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_series_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_series_id = body.get("series_id")
        series_update = extract_series_update(body)
        if requested_series_id is None:
            requested_series_id = series_update.get("series_id")
        series_id = normalize_series_id(requested_series_id)
        work_updates_request = extract_series_work_updates(body)

        series_payload = load_series_payload(self.server.series_path)
        series_map = series_payload["series"]
        current_series_record = series_map.get(series_id)
        if not isinstance(current_series_record, dict):
            raise ValueError(f"series_id not found: {series_id}")

        expected_hash = str(body.get("expected_record_hash") or "").strip()
        current_hash = record_hash(current_series_record)
        if expected_hash and expected_hash != current_hash:
            self._send_json(
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "error": "record changed since loaded",
                    "series_id": series_id,
                    "current_record_hash": current_hash,
                },
                allowed,
            )
            return

        works_payload = load_works_payload(self.server.works_path)
        works_map = works_payload["works"]
        updated_series_record = normalize_series_update(series_id, current_series_record, series_update)
        pending_work_updates: Dict[str, Dict[str, Any]] = {}
        changed_work_ids: list[str] = []

        for update in work_updates_request:
            work_id = update["work_id"]
            current_work_record = works_map.get(work_id)
            if not isinstance(current_work_record, dict):
                raise ValueError(f"work_id not found: {work_id}")
            expected_work_hash = update.get("expected_record_hash") or ""
            current_work_hash = record_hash(current_work_record)
            if expected_work_hash and expected_work_hash != current_work_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {
                        "ok": False,
                        "error": "work record changed since loaded",
                        "work_id": work_id,
                        "current_record_hash": current_work_hash,
                    },
                    allowed,
                )
                return
            updated_work_record = normalize_work_update(work_id, current_work_record, {"series_ids": update["series_ids"]})
            pending_work_updates[work_id] = updated_work_record
            if changed_fields(current_work_record, updated_work_record):
                changed_work_ids.append(work_id)

        validation_errors = validate_updated_series_records(
            self.server.source_dir,
            series_id,
            updated_series_record,
            pending_work_updates,
        )
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        series_changed_fields = changed_fields(current_series_record, updated_series_record)
        changed = bool(series_changed_fields or changed_work_ids)
        backup_paths: list[Path] = []
        response_work_records = []

        if changed:
            target_payloads: Dict[Path, Dict[str, Any]] = {}
            if series_changed_fields:
                updated_series = dict(series_map)
                updated_series[series_id] = updated_series_record
                target_payloads[self.server.series_path.resolve()] = payload_for_map("series", updated_series)
            if changed_work_ids:
                updated_works = dict(works_map)
                for work_id in changed_work_ids:
                    updated_works[work_id] = pending_work_updates[work_id]
                target_payloads[self.server.works_path.resolve()] = payload_for_map("works", updated_works)
            for target_path in target_payloads:
                if target_path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many(target_payloads, self.server.backups_dir)

        for work_id in changed_work_ids:
            response_work_records.append({"work_id": work_id, "record": pending_work_updates[work_id]})

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "changed": changed,
            "changed_fields": series_changed_fields,
            "changed_work_ids": changed_work_ids,
            "record_hash": record_hash(updated_series_record),
            "record": updated_series_record,
            "work_records": response_work_records,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_series_save",
            {
                "series_id": series_id,
                "changed": changed,
                "changed_fields": series_changed_fields,
                "changed_work_ids": changed_work_ids,
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "series.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "series.save",
                    "status": "completed",
                    "summary": f"Saved series {series_id} and {len(changed_work_ids)} member work records.",
                    "affected": {"works": changed_work_ids, "series": [series_id], "work_details": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_series_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_series_id = body.get("series_id")
        series_update = extract_series_update(body)
        if requested_series_id is None:
            requested_series_id = series_update.get("series_id")
        series_id = normalize_series_id(requested_series_id)
        work_updates_request = extract_series_work_updates(body)

        series_payload = load_series_payload(self.server.series_path)
        series_map = series_payload["series"]
        if isinstance(series_map.get(series_id), dict):
            raise ValueError(f"series_id already exists: {series_id}")

        works_payload = load_works_payload(self.server.works_path)
        works_map = works_payload["works"]

        blank_series_record = {field: None for field in SERIES_FIELDS}
        blank_series_record["series_id"] = series_id
        if not normalize_status(series_update.get("status")):
            series_update = dict(series_update)
            series_update["status"] = "draft"
        created_series_record = normalize_series_update(series_id, blank_series_record, series_update)
        if not str(created_series_record.get("title") or "").strip():
            raise ValueError("series title is required")

        pending_work_updates: Dict[str, Dict[str, Any]] = {}
        changed_work_ids: list[str] = []
        response_work_records = []
        for update in work_updates_request:
            work_id = update["work_id"]
            current_work_record = works_map.get(work_id)
            if not isinstance(current_work_record, dict):
                raise ValueError(f"work_id not found: {work_id}")
            expected_work_hash = update.get("expected_record_hash") or ""
            current_work_hash = record_hash(current_work_record)
            if expected_work_hash and expected_work_hash != current_work_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {
                        "ok": False,
                        "error": "work record changed since loaded",
                        "work_id": work_id,
                        "current_record_hash": current_work_hash,
                    },
                    allowed,
                )
                return
            updated_work_record = normalize_work_update(work_id, current_work_record, {"series_ids": update["series_ids"]})
            pending_work_updates[work_id] = updated_work_record
            if changed_fields(current_work_record, updated_work_record):
                changed_work_ids.append(work_id)

        validation_errors = validate_created_series_records(
            self.server.source_dir,
            series_id,
            created_series_record,
            pending_work_updates,
        )
        if validation_errors:
            raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

        target_payloads: Dict[Path, Dict[str, Any]] = {}
        updated_series = dict(series_map)
        updated_series[series_id] = created_series_record
        target_payloads[self.server.series_path.resolve()] = payload_for_map("series", updated_series)
        if changed_work_ids:
            updated_works = dict(works_map)
            for work_id in changed_work_ids:
                updated_works[work_id] = pending_work_updates[work_id]
            target_payloads[self.server.works_path.resolve()] = payload_for_map("works", updated_works)
        for target_path in target_payloads:
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")

        backup_paths: list[Path] = []
        if not self.server.dry_run:
            backup_paths = atomic_write_many(target_payloads, self.server.backups_dir)

        for work_id in changed_work_ids:
            response_work_records.append({"work_id": work_id, "record": pending_work_updates[work_id]})

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_series_record, created_series_record),
            "changed_work_ids": changed_work_ids,
            "record_hash": record_hash(created_series_record),
            "record": created_series_record,
            "work_records": response_work_records,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_series_create",
            {
                "series_id": series_id,
                "changed_fields": response_payload["changed_fields"],
                "changed_work_ids": changed_work_ids,
                "dry_run": self.server.dry_run,
            },
        )
        if not self.server.dry_run:
            self._refresh_lookup_payloads()
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "series.create"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "series.create",
                    "status": "completed",
                    "summary": f"Created draft series {series_id} and {len(changed_work_ids)} member work records.",
                    "affected": {"works": changed_work_ids, "series": [series_id], "work_details": []},
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = extract_import_mode(body)
        workbook_path = (self.server.repo_root / DEFAULT_IMPORT_WORKBOOK_PATH).resolve()
        plan = build_workbook_import_plan(self.server.source_dir, workbook_path, mode)
        response_payload: Dict[str, Any] = {
            "ok": True,
            "mode": mode,
            "preview": plan_to_response(plan, repo_root=self.server.repo_root),
        }
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_import_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        mode = extract_import_mode(body)
        workbook_path = (self.server.repo_root / DEFAULT_IMPORT_WORKBOOK_PATH).resolve()
        plan = build_workbook_import_plan(self.server.source_dir, workbook_path, mode)
        preview_payload = plan_to_response(plan, repo_root=self.server.repo_root)

        if plan.blocked_count > 0:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "import preview contains blocked rows",
                    "mode": mode,
                    "preview": preview_payload,
                },
                allowed,
            )
            return

        changed = plan.importable_count > 0
        target_kind = plan.target_kind
        backup_paths: list[Path] = []
        if changed and not self.server.dry_run:
            updated_records = apply_workbook_import_plan(self.server.source_dir, plan)
            if target_kind == "works":
                target_path = self.server.works_path.resolve()
                payloads_by_path = {target_path: payload_for_map("works", updated_records.works)}
            else:
                target_path = self.server.work_details_path.resolve()
                payloads_by_path = {self.server.work_details_path.resolve(): payload_for_map("work_details", updated_records.work_details)}
            for path in payloads_by_path:
                if path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
            backup_paths = atomic_write_many(payloads_by_path, self.server.backups_dir)
            self._refresh_lookup_payloads()

        response_payload: Dict[str, Any] = {
            "ok": True,
            "mode": mode,
            "changed": changed,
            "imported_count": plan.importable_count,
            "duplicate_count": plan.duplicate_count,
            "target_kind": target_kind,
            "preview": preview_payload,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_import_apply",
            {
                "mode": mode,
                "imported_count": plan.importable_count,
                "duplicate_count": plan.duplicate_count,
                "blocked_count": plan.blocked_count,
                "dry_run": self.server.dry_run,
            },
        )
        if not self.server.dry_run:
            now_utc = utc_now()
            operation = "import.works" if mode == IMPORT_MODE_WORKS else "import.work-details"
            summary_label = "work" if mode == IMPORT_MODE_WORKS else "work detail"
            duplicate_suffix = f"; {plan.duplicate_count} duplicate record(s) already existed" if plan.duplicate_count else ""
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, operation),
                    "time_utc": now_utc,
                    "kind": "source_import",
                    "operation": operation,
                    "status": "completed",
                    "summary": f"Imported {plan.importable_count} {summary_label} record(s) from workbook{duplicate_suffix}.",
                    "affected": {
                        "works": {"count": plan.importable_count} if mode == IMPORT_MODE_WORKS else {"count": 0},
                        "series": [],
                        "work_details": {"count": plan.importable_count} if mode == IMPORT_MODE_WORK_DETAILS else {"count": 0},
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body too large")

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _handle_build_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, series_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
        if work_id:
            scope = build_scope_for_work(self.server.source_dir, work_id, extra_series_ids=extra_series_ids)
        else:
            scope = build_scope_for_series(self.server.source_dir, series_id, extra_work_ids=extra_work_ids)
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "work_id": work_id,
                "series_id": series_id,
                "force": force,
                "build": scope,
            },
            allowed,
        )

    def _handle_build_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, series_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
        if work_id:
            result = run_scoped_build(
                self.server.repo_root,
                source_dir=self.server.source_dir,
                work_id=work_id,
                extra_series_ids=extra_series_ids,
                write=not self.server.dry_run,
                force=force,
                log_activity=not self.server.dry_run,
            )
        else:
            result = run_series_scoped_build(
                self.server.repo_root,
                source_dir=self.server.source_dir,
                series_id=series_id,
                extra_work_ids=extra_work_ids,
                write=not self.server.dry_run,
                force=force,
                log_activity=not self.server.dry_run,
            )
        payload: Dict[str, Any] = {
            "ok": result.get("status") == "completed",
            "work_id": work_id,
            "series_id": series_id,
            "force": force,
            "build": result.get("scope"),
            "steps": result.get("steps", []),
        }
        if self.server.dry_run:
            payload["dry_run"] = True
        if result.get("status") != "completed":
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "build.apply_failed"),
                        "time_utc": now_utc,
                        "kind": "build",
                        "operation": "build.apply",
                        "status": "failed",
                        "summary": f"Scoped rebuild failed for {'work ' + work_id if work_id else 'series ' + series_id}.",
                        "affected": {
                            "works": list((result.get("scope") or {}).get("work_ids", [])),
                            "series": list((result.get("scope") or {}).get("series_ids", [])),
                            "work_details": [],
                        },
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
            payload["error"] = str(result.get("error") or "Scoped JSON build failed.")
            payload["failed_step"] = result.get("failed_step")
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, payload, allowed)
            return
        if not self.server.dry_run:
            payload["completed_at_utc"] = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(payload["completed_at_utc"], "build.apply"),
                    "time_utc": payload["completed_at_utc"],
                    "kind": "build",
                    "operation": "build.apply",
                    "status": "completed",
                    "summary": f"Scoped rebuild completed for {'work ' + work_id if work_id else 'series ' + series_id}.",
                    "affected": {
                        "works": list((result.get("scope") or {}).get("work_ids", [])),
                        "series": list((result.get("scope") or {}).get("series_ids", [])),
                        "work_details": [],
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _handle_moment_import_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        moment_file, force = extract_moment_import_request(body)
        preview = preview_moment_source(self.server.repo_root, moment_file)
        payload: Dict[str, Any] = {
            "ok": True,
            "moment_file": preview.get("moment_file") or moment_file,
            "force": bool(force),
            "preview": preview,
        }
        if preview.get("valid"):
            scope = build_scope_for_moment(self.server.repo_root, moment_file, force=force)
            payload["build"] = scope
            payload["effective_force"] = bool(scope.get("effective_force"))
        else:
            payload["effective_force"] = bool(preview.get("effective_force"))
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _handle_moment_import_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        moment_file, force = extract_moment_import_request(body)
        preview = preview_moment_source(self.server.repo_root, moment_file)
        if not preview.get("valid"):
            errors = preview.get("errors") or []
            raise ValueError("; ".join(str(error) for error in errors) or "moment import preview failed")

        result = run_moment_scoped_build(
            self.server.repo_root,
            moment_file=moment_file,
            write=not self.server.dry_run,
            force=force,
            log_activity=not self.server.dry_run,
        )
        scope = result.get("scope") or {}
        effective_force = bool(scope.get("effective_force")) or bool(force)
        moment_ids = list(scope.get("moment_ids", []))
        moment_id = str(moment_ids[0] if moment_ids else preview.get("moment_id") or "").strip().lower()
        payload: Dict[str, Any] = {
            "ok": result.get("status") == "completed",
            "moment_file": preview.get("moment_file") or moment_file,
            "moment_id": moment_id,
            "force": bool(force),
            "effective_force": effective_force,
            "preview": preview,
            "build": scope,
            "steps": result.get("steps", []),
            "public_url": str(preview.get("public_url") or ""),
        }
        if self.server.dry_run:
            payload["dry_run"] = True
        if result.get("status") != "completed":
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "moment.import_failed"),
                        "time_utc": now_utc,
                        "kind": "moment",
                        "operation": "moment.import",
                        "status": "failed",
                        "summary": f"Moment import failed for {moment_id or preview.get('moment_file')}.",
                        "affected": {
                            "works": [],
                            "series": [],
                            "work_details": [],
                            "moments": [moment_id] if moment_id else [],
                        },
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
            payload["error"] = str(result.get("error") or "Scoped moment build failed.")
            payload["failed_step"] = result.get("failed_step")
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, payload, allowed)
            return
        if not self.server.dry_run:
            payload["completed_at_utc"] = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(payload["completed_at_utc"], "moment.import"),
                    "time_utc": payload["completed_at_utc"],
                    "kind": "moment",
                    "operation": "moment.import",
                    "status": "completed",
                    "summary": f"Moment import completed for {moment_id}.",
                    "affected": {
                        "works": [],
                        "series": [],
                        "work_details": [],
                        "moments": [moment_id] if moment_id else [],
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any], allowed: Optional[str] = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._write_cors_headers(allowed)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _write_cors_headers(self, allowed: Optional[str]) -> None:
        if allowed:
            self.send_header("Access-Control-Allow-Origin", allowed)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        print(f"[catalogue_write_server] {self.address_string()} - {fmt % args}")

    def _refresh_lookup_payloads(self) -> None:
        written = build_and_write_catalogue_lookup(self.server.source_dir, self.server.lookup_dir)
        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "written_count": len(written),
            },
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Localhost-only catalogue source write service.")
    parser.add_argument("--port", type=int, default=8788, help="Server port (default: 8788)")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Validate and respond without writing files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(args.repo_root)
    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    lookup_dir = (repo_root / DEFAULT_LOOKUP_DIR).resolve()
    works_path = (source_dir / SOURCE_FILES["works"]).resolve()
    work_details_path = (source_dir / SOURCE_FILES["work_details"]).resolve()
    series_path = (source_dir / SOURCE_FILES["series"]).resolve()
    work_files_path = (source_dir / SOURCE_FILES["work_files"]).resolve()
    work_links_path = (source_dir / SOURCE_FILES["work_links"]).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_paths = {
        (source_dir / filename).resolve()
        for kind, filename in SOURCE_FILES.items()
        if kind != "meta"
    }

    server = CatalogueWriteServer(
        ("127.0.0.1", args.port),
        Handler,
        repo_root=repo_root,
        source_dir=source_dir,
        lookup_dir=lookup_dir,
        works_path=works_path,
        work_details_path=work_details_path,
        series_path=series_path,
        work_files_path=work_files_path,
        work_links_path=work_links_path,
        allowed_write_paths=allowed_paths,
        backups_dir=backups_dir,
        dry_run=args.dry_run,
    )
    mode = "dry-run" if args.dry_run else "write"
    print(
        f"catalogue_write_server listening on http://127.0.0.1:{args.port} "
        f"(mode={mode}, source_dir={source_dir}, backups={backups_dir})"
    )
    server.log_event(
        "server_start",
        {
            "port": args.port,
            "mode": mode,
            "source_dir": str(source_dir.relative_to(repo_root)),
            "backups_dir": str(backups_dir.relative_to(repo_root)),
        },
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.log_event("server_stop", {"port": args.port})
        print("catalogue_write_server stopped")


if __name__ == "__main__":
    main()
