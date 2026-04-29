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
  POST /catalogue/publication-preview
  POST /catalogue/publication-apply
  POST /catalogue/work/create
  POST /catalogue/work/save
  POST /catalogue/work-detail/create
  POST /catalogue/work-detail/save
  POST /catalogue/import-preview
  POST /catalogue/import-apply
  POST /catalogue/series/create
  POST /catalogue/series/save
  POST /catalogue/moment/preview
  POST /catalogue/moment/save
  POST /catalogue/build-preview
  POST /catalogue/build-apply
  POST /catalogue/project-state-report

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
import subprocess
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional
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
    normalize_text,
    payload_for_map,
    records_from_json_source,
    safe_uid_fragment,
    slug_id,
    sort_record_map,
    unique_uid,
    validate_source_records,
)
from catalogue_activity import append_catalogue_activity  # noqa: E402
from catalogue_lookup import (  # noqa: E402
    DEFAULT_LOOKUP_DIR,
    build_and_write_catalogue_lookup,
    build_series_search_payload,
    build_series_lookup_payload,
    build_work_detail_search_payload,
    build_work_detail_lookup_payload,
    build_work_lookup_payload,
    build_work_search_payload,
    write_detail_lookup_payload,
    write_lookup_root_payload,
    write_series_lookup_payload,
    write_work_lookup_payload,
)
from catalogue_json_build import (  # noqa: E402
    CATALOGUE_MEDIA_STAGING_REL_DIR,
    build_search_command,
    build_local_media_plan,
    build_moment_readiness,
    build_scope_for_moment,
    build_scope_for_series,
    build_scope_for_work,
    preview_moment_source,
    run_moment_scoped_build,
    run_scoped_build,
    run_series_scoped_build,
)
from moment_sources import (  # noqa: E402
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
    has_front_matter_text,
    load_moment_metadata_records,
    moment_metadata_payload,
    normalize_moment_filename,
    normalize_moment_metadata_record,
    validate_moment_metadata_record,
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
from project_state_report import (  # noqa: E402
    DEFAULT_OUTPUT_REL_PATH,
    PROJECTS_BASE_DIR_ENV_NAME,
    build_project_state_report,
    resolve_projects_base_dir,
)
from script_logging import append_script_log  # noqa: E402
from series_ids import normalize_series_id, parse_series_ids  # noqa: E402


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")
CATALOGUE_PROSE_STAGING_REL_DIR = Path("var/docs/catalogue/import-staging")
CATALOGUE_PROSE_SOURCE_REL_DIR = Path("_docs_src_catalogue")
MAX_BODY_BYTES = 1024 * 1024
MAX_PROSE_MARKDOWN_BYTES = 1024 * 1024
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
PROSE_IMPORT_PREVIEW_PATH = "/catalogue/prose/import-preview"
PROSE_IMPORT_APPLY_PATH = "/catalogue/prose/import-apply"
MOMENT_IMPORT_PREVIEW_PATH = "/catalogue/moment/import-preview"
MOMENT_IMPORT_APPLY_PATH = "/catalogue/moment/import-apply"
MOMENT_PREVIEW_PATH = "/catalogue/moment/preview"
MOMENT_SAVE_PATH = "/catalogue/moment/save"
BULK_SAVE_PATH = "/catalogue/bulk-save"
DELETE_PREVIEW_PATH = "/catalogue/delete-preview"
DELETE_APPLY_PATH = "/catalogue/delete-apply"
PUBLICATION_PREVIEW_PATH = "/catalogue/publication-preview"
PUBLICATION_APPLY_PATH = "/catalogue/publication-apply"
PROJECT_STATE_REPORT_PATH = "/catalogue/project-state-report"

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

LOOKUP_INVALIDATION_SINGLE_RECORD = "single-record"
LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD = "targeted-multi-record"
LOOKUP_INVALIDATION_FULL = "full"

LOOKUP_INVALIDATION_PRIORITY = {
    LOOKUP_INVALIDATION_SINGLE_RECORD: 0,
    LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD: 1,
    LOOKUP_INVALIDATION_FULL: 2,
}

# Canonical invalidation registry for work-source fields.
# This is the source of truth for Task 1 and stays in code for now.
# A later task can externalize it to JSON/config once the dependency model stabilizes.
WORK_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "project_folder": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "project_filename": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "year": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "medium_type": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "medium_caption": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "duration": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "height_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "width_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "depth_cm": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "storage_location": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "work_prose_file": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "notes": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "provenance": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "artist": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "downloads": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "links": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": [
            "work_record",
            "work_search",
            "related_series_records",
            "related_work_detail_records",
            "related_work_file_records",
            "related_work_link_records",
        ],
    },
    "year_display": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
    "series_ids": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_record", "work_search", "related_series_records"],
    },
}

# Canonical invalidation registry for work-detail source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/work_details/<detail_uid>.json`,
# `assets/studio/data/catalogue_lookup/work_detail_search.json`, and the focused
# work lookup record where detail sections are embedded.
DETAIL_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "project_filename": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "height_px": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "width_px": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_detail_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "project_subfolder": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "related_work_records"],
    },
    "detail_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
    "detail_uid": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_detail_record", "work_detail_search", "related_work_records"],
    },
}

# Canonical invalidation registry for work-file source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/work_files/<file_uid>.json`
# and the focused work lookup record where work-file summaries are embedded.
WORK_FILE_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_file_record"],
    },
    "filename": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_file_record", "related_work_records"],
    },
    "label": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_file_record", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_file_record", "related_work_records"],
    },
    "work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_file_record", "related_work_records"],
    },
    "file_uid": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_file_record", "related_work_records"],
    },
}

# Canonical invalidation registry for work-link source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/work_links/<link_uid>.json`
# and the focused work lookup record where work-link summaries are embedded.
WORK_LINK_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["work_link_record"],
    },
    "url": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_link_record", "related_work_records"],
    },
    "label": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_link_record", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_link_record", "related_work_records"],
    },
    "work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_link_record", "related_work_records"],
    },
    "link_uid": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["work_link_record", "related_work_records"],
    },
}

# Canonical invalidation registry for series source fields.
# Derived artifacts come from `assets/studio/data/catalogue_lookup/series/<series_id>.json`,
# `assets/studio/data/catalogue_lookup/series_search.json`, and work lookup records where
# `series_summary` embeds the current series title.
SERIES_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "year": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "year_display": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "series_type": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "series_prose_file": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "notes": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "sort_fields": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["series_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search", "related_work_records"],
    },
    "status": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search"],
    },
    "primary_work_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search"],
    },
    "series_id": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["series_record", "series_search", "related_work_records"],
    },
}

# Canonical invalidation registry for moment-source fields.
# Moments are part of the catalogue surface, but their current derived artifacts are
# `assets/moments/index/<moment_id>.json`, `assets/data/moments_index.json`, and
# catalogue search entries built from `moments_index.json`, not Studio catalogue lookup payloads.
MOMENT_LOOKUP_INVALIDATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "status": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "published_date": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "image_alt": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "source_image_file": {
        "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
        "artifacts": ["moment_record"],
    },
    "title": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
    "date": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
    "date_display": {
        "class": LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD,
        "artifacts": ["moment_record", "moments_index", "catalogue_search"],
    },
}

LOOKUP_INVALIDATION_FULL_FALLBACK_OPERATIONS = {
    "catalogue.bulk_save",
    "catalogue.delete_apply",
    "catalogue.import_apply",
    "catalogue.work_create",
    "catalogue.work_detail_create",
    "catalogue.work_file_create",
    "catalogue.work_link_create",
    "catalogue.series_create",
    "catalogue.moment_save",
}

MOMENT_FIELDS = [
    "moment_id",
    "title",
    "status",
    "published_date",
    "date",
    "date_display",
    "source_image_file",
    "image_alt",
]


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


def lookup_invalidation_for_fields(
    changed_field_names: list[str],
    registry: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    changed = sorted({str(name).strip() for name in changed_field_names if str(name).strip()})
    if not changed:
        return {
            "class": LOOKUP_INVALIDATION_SINGLE_RECORD,
            "artifacts": [],
            "fields": [],
            "unknown_fields": [],
        }

    invalidation_class = LOOKUP_INVALIDATION_SINGLE_RECORD
    artifacts: set[str] = set()
    unknown_fields: list[str] = []

    for field_name in changed:
        entry = registry.get(field_name)
        if not entry:
            unknown_fields.append(field_name)
            invalidation_class = LOOKUP_INVALIDATION_FULL
            continue
        entry_class = str(entry.get("class") or LOOKUP_INVALIDATION_FULL)
        if LOOKUP_INVALIDATION_PRIORITY.get(entry_class, LOOKUP_INVALIDATION_PRIORITY[LOOKUP_INVALIDATION_FULL]) > LOOKUP_INVALIDATION_PRIORITY[invalidation_class]:
            invalidation_class = entry_class
        for artifact in entry.get("artifacts") or []:
            artifacts.add(str(artifact))

    if unknown_fields:
        artifacts.add("full_lookup_refresh")

    return {
        "class": invalidation_class,
        "artifacts": sorted(artifacts),
        "fields": changed,
        "unknown_fields": unknown_fields,
    }


def work_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, WORK_LOOKUP_INVALIDATION_REGISTRY)


def detail_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, DETAIL_LOOKUP_INVALIDATION_REGISTRY)


def work_file_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, WORK_FILE_LOOKUP_INVALIDATION_REGISTRY)


def work_link_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, WORK_LINK_LOOKUP_INVALIDATION_REGISTRY)


def series_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, SERIES_LOOKUP_INVALIDATION_REGISTRY)


def moment_lookup_invalidation_for_fields(changed_field_names: list[str]) -> Dict[str, Any]:
    return lookup_invalidation_for_fields(changed_field_names, MOMENT_LOOKUP_INVALIDATION_REGISTRY)


def locked_first_pass_work_fields() -> set[str]:
    return {
        "published_date",
        "project_folder",
        "project_filename",
        "year",
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


def extract_build_request(body: Mapping[str, Any]) -> tuple[str, list[str], bool]:
    work_id = slug_id(body.get("work_id"))
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    force = bool(body.get("force"))
    return work_id, extra_series_ids, force


def normalize_moment_id_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("moment_id is required")
    return normalize_moment_filename(text if text.endswith(".md") else f"{text}.md")[:-3]


def extract_generic_build_request(body: Mapping[str, Any]) -> tuple[str, str, str, list[str], list[str], bool]:
    work_id = str(body.get("work_id") or "").strip()
    series_id = str(body.get("series_id") or "").strip()
    moment_value = str(body.get("moment_id") or body.get("moment_file") or "").strip()
    if sum(1 for value in (work_id, series_id, moment_value) if value) != 1:
        raise ValueError("build request must include exactly one of work_id, series_id, or moment_id")
    normalized_work_id = slug_id(work_id) if work_id else ""
    normalized_series_id = normalize_series_id(series_id) if series_id else ""
    normalized_moment_id = normalize_moment_id_value(moment_value) if moment_value else ""
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    extra_work_ids: list[str] = []
    for raw in body.get("extra_work_ids") or []:
        extra_work_ids.append(slug_id(raw))
    force = bool(body.get("force"))
    return normalized_work_id, normalized_series_id, normalized_moment_id, extra_series_ids, extra_work_ids, force


def extract_moment_import_request(body: Mapping[str, Any]) -> tuple[str, Dict[str, Any], bool]:
    moment_file = str(body.get("moment_file") or body.get("file") or "").strip()
    if not moment_file:
        raise ValueError("moment_file is required")
    metadata_value = body.get("metadata")
    metadata: Dict[str, Any] = dict(metadata_value) if isinstance(metadata_value, Mapping) else {}
    for key in ["title", "status", "published_date", "date", "date_display", "source_image_file", "image_file", "image_alt"]:
        if key in body and key not in metadata:
            metadata[key] = body.get(key)
    metadata["status"] = "draft"
    force = bool(body.get("force"))
    return moment_file, metadata, force


def normalize_prose_import_target(body: Mapping[str, Any]) -> tuple[str, str, str]:
    target_kind = str(body.get("target_kind") or body.get("kind") or "").strip().lower()
    if target_kind not in {"work", "series", "moment"}:
        raise ValueError("target_kind must be work, series, or moment")
    raw_id = body.get("target_id")
    if raw_id is None:
        raw_id = body.get("work_id") if target_kind == "work" else body.get("series_id") if target_kind == "series" else body.get("moment_id")
    target_id = slug_id(raw_id) if target_kind == "work" else normalize_series_id(raw_id) if target_kind == "series" else normalize_moment_id_value(raw_id)
    collection = "works" if target_kind == "work" else "series" if target_kind == "series" else "moments"
    return target_kind, target_id, collection


def ensure_direct_child(path: Path, allowed_parent: Path) -> None:
    if path.resolve().parent != allowed_parent.resolve():
        raise ValueError("write target is outside the allowlisted prose source root")


def validate_prose_import_target_exists(source_dir: Path, target_kind: str, target_id: str) -> None:
    records = records_from_json_source(source_dir)
    if target_kind == "work" and target_id not in records.works:
        raise ValueError(f"work_id not found: {target_id}")
    if target_kind == "series" and target_id not in records.series:
        raise ValueError(f"series_id not found: {target_id}")
    if target_kind == "moment":
        moments = load_moment_metadata_records(source_dir)
        if target_id not in moments:
            raise ValueError(f"moment_id not found: {target_id}")


def read_staged_prose_markdown(staging_path: Path) -> tuple[str, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not staging_path.exists():
        return "", [f"Missing staged Markdown file: {staging_path.name}"], warnings
    if not staging_path.is_file():
        return "", [f"Staged Markdown path is not a file: {staging_path.name}"], warnings
    try:
        size = staging_path.stat().st_size
    except OSError as exc:
        return "", [f"Could not stat staged Markdown file: {exc}"], warnings
    if size > MAX_PROSE_MARKDOWN_BYTES:
        errors.append(f"Staged Markdown file is larger than {MAX_PROSE_MARKDOWN_BYTES} bytes.")
    try:
        text = staging_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "", ["Staged Markdown file must be UTF-8 text."], warnings
    except OSError as exc:
        return "", [f"Could not read staged Markdown file: {exc}"], warnings
    if "\x00" in text:
        errors.append("Staged Markdown file contains a null byte.")
    if text.startswith("---\n") or text.startswith("---\r\n"):
        errors.append("Staged prose source files must not include front matter.")
    if not text.strip():
        warnings.append("Staged Markdown file is blank; importing it will publish blank optional prose after the generator lookup is updated.")
    return text, errors, warnings


def build_prose_import_preview(
    repo_root: Path,
    source_dir: Path,
    body: Mapping[str, Any],
) -> Dict[str, Any]:
    target_kind, target_id, collection = normalize_prose_import_target(body)
    validate_prose_import_target_exists(source_dir, target_kind, target_id)
    staging_path = repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / collection / f"{target_id}.md"
    target_path = repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / collection / f"{target_id}.md"
    text, errors, warnings = read_staged_prose_markdown(staging_path)
    target_exists = target_path.exists()
    target_text = ""
    if target_exists:
        try:
            target_text = target_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            warnings.append("Existing permanent prose file could not be read for content comparison.")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if not errors else ""
    target_hash = hashlib.sha256(target_text.encode("utf-8")).hexdigest() if target_text else ""
    changed = not target_exists or text != target_text
    return {
        "ok": True,
        "valid": not errors,
        "target_kind": target_kind,
        "target_id": target_id,
        "staging_path": str((CATALOGUE_PROSE_STAGING_REL_DIR / collection / f"{target_id}.md")).replace(os.sep, "/"),
        "target_path": str((CATALOGUE_PROSE_SOURCE_REL_DIR / collection / f"{target_id}.md")).replace(os.sep, "/"),
        "staging_exists": staging_path.exists(),
        "target_exists": target_exists,
        "overwrite_required": bool(target_exists and changed),
        "changed": changed,
        "byte_count": len(text.encode("utf-8")) if not errors else 0,
        "line_count": len(text.splitlines()) if not errors else 0,
        "content_sha256": content_hash,
        "target_sha256": target_hash,
        "errors": errors,
        "warnings": warnings,
    }


def atomic_write_text_no_backup(target_path: Path, text: str) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".tmp",
        dir=str(target_path.parent),
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_path, target_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


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


def extract_apply_build(body: Mapping[str, Any]) -> bool:
    return bool(body.get("apply_build"))


def extract_delete_request(body: Mapping[str, Any]) -> Dict[str, str]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "work_detail", "series", "moment"}:
        raise ValueError("delete kind must be work, work_detail, series, or moment")

    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "work_detail":
        record_id = normalize_detail_uid_value(body.get("detail_uid") or body.get("id"))
    elif kind == "series":
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    else:
        record_id = normalize_moment_id_value(body.get("moment_id") or body.get("id"))
    expected_record_hash = str(body.get("expected_record_hash") or "").strip()
    return {
        "kind": kind,
        "id": record_id,
        "expected_record_hash": expected_record_hash,
    }


def extract_publication_request(body: Mapping[str, Any]) -> Dict[str, Any]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "work_detail", "series", "moment"}:
        raise ValueError("publication kind must be work, work_detail, series, or moment")

    action = str(body.get("action") or "").strip().lower().replace("-", "_")
    if action not in {"publish", "unpublish", "save_published"}:
        raise ValueError("publication action must be publish, unpublish, or save_published")

    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "work_detail":
        record_id = normalize_detail_uid_value(body.get("detail_uid") or body.get("id"))
    elif kind == "series":
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    else:
        record_id = normalize_moment_id_value(body.get("moment_id") or body.get("id"))

    record_update: Dict[str, Any] = {}
    if action == "save_published":
        if kind == "work":
            record_update = extract_work_update(body)
        elif kind == "work_detail":
            record_update = extract_work_detail_update(body)
        elif kind == "series":
            record_update = extract_series_update(body)
        else:
            record_update = extract_moment_update(body)

    return {
        "kind": kind,
        "action": action,
        "id": record_id,
        "record_update": record_update,
        "expected_record_hash": str(body.get("expected_record_hash") or "").strip(),
        "extra_series_ids": normalize_series_ids_value(body.get("extra_series_ids")),
        "extra_work_ids": [slug_id(raw) for raw in body.get("extra_work_ids") or []],
        "force": bool(body.get("force")),
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


def extract_moment_update(body: Mapping[str, Any]) -> Dict[str, Any]:
    raw_record = body.get("record", body.get("moment"))
    if raw_record is None:
        raw_record = {field: body[field] for field in MOMENT_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in MOMENT_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one moment field")
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


def validate_series_save_record(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not normalize_text(record.get("year")):
        errors.append("series year is required")
    else:
        try:
            int(normalize_text(record.get("year")))
        except ValueError:
            errors.append("series year must be a whole number")
    if not normalize_text(record.get("year_display")):
        errors.append("series year_display is required")
    return errors


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


def normalize_moment_update(
    moment_id: str,
    current_record: Mapping[str, Any],
    update: Mapping[str, Any],
) -> Dict[str, Any]:
    merged = dict(current_record)
    merged.update(update)
    merged["moment_id"] = normalize_moment_id_value(merged.get("moment_id") or moment_id)
    if merged["moment_id"] != moment_id:
        raise ValueError("record.moment_id must match moment_id")
    return normalize_moment_metadata_record(moment_id, merged)


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in sorted(set(before.keys()) | set(after.keys())) if before.get(field) != after.get(field)]


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


def preview_work_delete(source_dir: Path, work_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
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
        and normalize_status(series_record.get("status")) == "published"
    )
    blockers: list[str] = []
    if primary_series_ids:
        blockers.append(
            "Work is primary_work_id for series: " + ", ".join(primary_series_ids) + ". Reassign those series before deleting the work."
        )
    affected = {
        "works": [work_id],
        "series": normalize_series_ids_value(work_record.get("series_ids")),
        "work_details": dependent_detail_ids,
        "work_files": dependent_file_ids,
        "work_links": dependent_link_ids,
    }
    cleanup = catalogue_delete_preview_cleanup(repo_root, "work", work_id, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "work",
        "id": work_id,
        "record": work_record,
        "blockers": blockers,
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete work {work_id}, {len(dependent_detail_ids)} detail record(s), {len(dependent_file_ids)} file record(s), {len(dependent_link_ids)} link record(s), and remove {cleanup_count} generated/media file(s).",
    }


def series_records_with_draft_primary_cleared(
    series_records: Mapping[str, Dict[str, Any]],
    work_id: str,
) -> tuple[Dict[str, Dict[str, Any]], list[str]]:
    updated_series: Dict[str, Dict[str, Any]] = {}
    changed_series_ids: list[str] = []
    for series_id, series_record in series_records.items():
        next_record = dict(series_record)
        if (
            str(next_record.get("primary_work_id") or "") == work_id
            and normalize_status(next_record.get("status")) != "published"
        ):
            next_record["primary_work_id"] = None
            changed_series_ids.append(series_id)
        updated_series[series_id] = next_record
    return updated_series, sorted(changed_series_ids)


def preview_work_detail_delete(source_dir: Path, detail_uid: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    detail_record = source_records.work_details.get(detail_uid)
    if not isinstance(detail_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")
    work_id = str(detail_record.get("work_id") or "")
    affected = {
        "works": [work_id] if work_id else [],
        "series": [],
        "work_details": [detail_uid],
        "work_files": [],
        "work_links": [],
    }
    cleanup = catalogue_delete_preview_cleanup(repo_root, "work_detail", detail_uid, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "work_detail",
        "id": detail_uid,
        "record": detail_record,
        "blockers": [],
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete work detail {detail_uid} and remove {cleanup_count} generated/media file(s).",
    }


def preview_series_delete(source_dir: Path, series_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    series_record = source_records.series.get(series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")
    member_work_ids = sorted(
        work_id
        for work_id, work_record in source_records.works.items()
        if series_id in normalize_series_ids_value(work_record.get("series_ids"))
    )
    affected = {
        "works": member_work_ids,
        "series": [series_id],
        "work_details": [],
        "work_files": [],
        "work_links": [],
    }
    cleanup = catalogue_delete_preview_cleanup(repo_root, "series", series_id, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "series",
        "id": series_id,
        "record": series_record,
        "blockers": [],
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete series {series_id}, remove it from {len(member_work_ids)} member work record(s), and remove {cleanup_count} generated/media file(s).",
    }


def preview_moment_delete(source_dir: Path, moment_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    moment_records = load_moment_metadata_records(source_dir)
    moment_record = moment_records.get(moment_id)
    if not isinstance(moment_record, dict):
        raise ValueError(f"moment_id not found: {moment_id}")
    cleanup = moment_delete_preview_cleanup(repo_root, moment_id) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "moment",
        "id": moment_id,
        "record": moment_record,
        "blockers": [],
        "affected": {
            "works": [],
            "series": [],
            "work_details": [],
            "work_files": [],
            "work_links": [],
            "moments": [moment_id],
        },
        "cleanup": cleanup,
        "summary": f"Delete moment {moment_id}, remove {cleanup_count} generated/media file(s), update the moments index, and rebuild catalogue search.",
    }


def validate_work_delete_records(source_dir: Path, work_id: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    updated_works = dict(source_records.works)
    updated_works.pop(work_id, None)
    updated_series, _changed_series_ids = series_records_with_draft_primary_cleared(source_records.series, work_id)
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
        series=sort_record_map(updated_series),
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


def validate_moment_delete_records(source_dir: Path, moment_id: str) -> list[str]:
    moment_records = load_moment_metadata_records(source_dir)
    moment_records.pop(moment_id, None)
    errors: list[str] = []
    for remaining_moment_id, moment_record in sorted(moment_records.items()):
        errors.extend(
            f"{remaining_moment_id}: {error}"
            for error in validate_updated_moment_record(remaining_moment_id, moment_record)
        )
    return errors


def build_delete_preview(source_dir: Path, kind: str, record_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    if kind == "work":
        preview = preview_work_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_work_delete_records(source_dir, record_id)
    elif kind == "work_detail":
        preview = preview_work_detail_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_work_detail_delete_records(source_dir, record_id)
    elif kind == "series":
        preview = preview_series_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_series_delete_records(source_dir, record_id)
    else:
        preview = preview_moment_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_moment_delete_records(source_dir, record_id)
    blockers = list(preview.get("blockers") or [])
    validation_errors = list(preview.get("validation_errors") or [])
    preview["blockers"] = blockers
    preview["blocked"] = bool(blockers or validation_errors)
    return preview


def publication_source_path_key(kind: str) -> str:
    if kind == "work":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["works"])
    if kind == "work_detail":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["work_details"])
    if kind == "series":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["series"])
    return str(DEFAULT_SOURCE_DIR / MOMENT_METADATA_FILENAME)


def publication_affected_for_record(source_dir: Path, kind: str, record_id: str) -> Dict[str, list[str]]:
    source_records = records_from_json_source(source_dir)
    affected: Dict[str, list[str]] = {
        "works": [],
        "series": [],
        "work_details": [],
        "work_files": [],
        "work_links": [],
        "moments": [],
    }
    if kind == "work":
        work_record = source_records.works.get(record_id)
        if not isinstance(work_record, dict):
            raise ValueError(f"work_id not found: {record_id}")
        affected["works"] = [record_id]
        affected["series"] = normalize_series_ids_value(work_record.get("series_ids"))
        affected["work_details"] = sorted(
            detail_uid
            for detail_uid, detail_record in source_records.work_details.items()
            if str(detail_record.get("work_id") or "") == record_id
        )
    elif kind == "work_detail":
        detail_record = source_records.work_details.get(record_id)
        if not isinstance(detail_record, dict):
            raise ValueError(f"detail_uid not found: {record_id}")
        work_id = str(detail_record.get("work_id") or "")
        affected["works"] = [work_id] if work_id else []
        affected["work_details"] = [record_id]
    elif kind == "series":
        series_record = source_records.series.get(record_id)
        if not isinstance(series_record, dict):
            raise ValueError(f"series_id not found: {record_id}")
        affected["series"] = [record_id]
        affected["works"] = sorted(
            work_id
            for work_id, work_record in source_records.works.items()
            if record_id in normalize_series_ids_value(work_record.get("series_ids"))
        )
    else:
        moment_records = load_moment_metadata_records(source_dir)
        if record_id not in moment_records:
            raise ValueError(f"moment_id not found: {record_id}")
        affected["moments"] = [record_id]
    return affected


def series_publish_bootstrap_work_records(source_dir: Path, series_id: str) -> Dict[str, Dict[str, Any]]:
    records = records_from_json_source(source_dir)
    promoted: Dict[str, Dict[str, Any]] = {}
    for work_id, work_record in records.works.items():
        if series_id not in normalize_series_ids_value(work_record.get("series_ids")):
            continue
        if normalize_status(work_record.get("status")) != "draft":
            continue
        promoted[work_id] = normalize_work_update(work_id, work_record, {"status": "published"})
    return promoted


def publication_bootstrap_work_records(
    source_dir: Path,
    kind: str,
    action: str,
    record_id: str,
    target_record: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    if kind != "series" or action != "publish":
        return {}
    if normalize_status(target_record.get("status")) != "published":
        return {}
    return series_publish_bootstrap_work_records(source_dir, record_id)


def current_publication_record(source_dir: Path, kind: str, record_id: str) -> Dict[str, Any]:
    if kind == "work":
        record = records_from_json_source(source_dir).works.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"work_id not found: {record_id}")
        return dict(record)
    if kind == "work_detail":
        record = records_from_json_source(source_dir).work_details.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"detail_uid not found: {record_id}")
        return dict(record)
    if kind == "series":
        record = records_from_json_source(source_dir).series.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"series_id not found: {record_id}")
        return dict(record)
    record = load_moment_metadata_records(source_dir).get(record_id)
    if not isinstance(record, dict):
        raise ValueError(f"moment_id not found: {record_id}")
    return normalize_moment_metadata_record(record_id, record)


def normalize_publication_record(
    source_dir: Path,
    kind: str,
    record_id: str,
    current_record: Mapping[str, Any],
    action: str,
    record_update: Mapping[str, Any],
) -> Dict[str, Any]:
    if action == "publish":
        update = {"status": "published"}
    elif action == "unpublish":
        update = {"status": "draft"}
    else:
        update = dict(record_update)
        requested_status = normalize_status(update.get("status")) if "status" in update else normalize_status(current_record.get("status"))
        current_status = normalize_status(current_record.get("status"))
        if requested_status != current_status:
            raise ValueError("save_published must not change publication status")

    if kind == "work":
        return normalize_work_update(record_id, current_record, update)
    if kind == "work_detail":
        return normalize_work_detail_update(record_id, current_record, update)
    if kind == "series":
        return normalize_series_update(record_id, current_record, update)
    return normalize_moment_update(record_id, current_record, update)


def validate_publication_target(
    source_dir: Path,
    kind: str,
    record_id: str,
    target_record: Dict[str, Any],
    *,
    work_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> list[str]:
    if kind == "work":
        return validate_updated_records(source_dir, record_id, target_record)
    if kind == "work_detail":
        return validate_updated_detail_records(source_dir, record_id, target_record)
    if kind == "series":
        errors = validate_series_save_record(target_record)
        errors.extend(validate_updated_series_records(source_dir, record_id, target_record, work_updates or {}))
        return errors
    return validate_updated_moment_record(record_id, target_record)


def publication_specific_blockers(
    source_dir: Path,
    repo_root: Path,
    kind: str,
    record_id: str,
    target_record: Mapping[str, Any],
    *,
    work_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> list[str]:
    if normalize_status(target_record.get("status")) != "published":
        return []

    records = records_from_json_source(source_dir)
    effective_works = dict(records.works)
    if work_updates:
        effective_works.update({work_id: dict(record) for work_id, record in work_updates.items()})
    if kind == "work":
        published_series_ids = [
            series_id
            for series_id in normalize_series_ids_value(target_record.get("series_ids"))
            if isinstance(records.series.get(series_id), dict)
            and normalize_status(records.series[series_id].get("status")) == "published"
        ]
        if not published_series_ids:
            return [f"work {record_id} must belong to a published series before publishing"]
        return []

    if kind == "work_detail":
        work_id = slug_id(target_record.get("work_id"))
        parent = effective_works.get(work_id)
        if not isinstance(parent, dict):
            return [f"parent work_id not found: {work_id}"]
        if normalize_status(parent.get("status")) != "published":
            return [f"parent work {work_id} must be published before publishing detail {record_id}"]
        return []

    if kind == "series":
        primary_work_id = str(target_record.get("primary_work_id") or "").strip()
        blockers: list[str] = []
        if not primary_work_id:
            blockers.append("series primary_work_id is required before publishing")
        primary = effective_works.get(primary_work_id)
        if primary_work_id and not isinstance(primary, dict):
            blockers.append(f"primary work_id not found: {primary_work_id}")
        elif isinstance(primary, dict):
            if normalize_status(primary.get("status")) != "published":
                blockers.append(f"primary work {primary_work_id} must be published before publishing series {record_id}")
            if record_id not in normalize_series_ids_value(primary.get("series_ids")):
                blockers.append(f"primary work {primary_work_id} must belong to series {record_id}")
        member_work_ids = [
            work_id
            for work_id, work_record in effective_works.items()
            if record_id in normalize_series_ids_value(work_record.get("series_ids"))
            and normalize_status(work_record.get("status")) == "published"
        ]
        if not member_work_ids:
            blockers.append("series must have at least one published member work before publishing")
        return blockers

    if kind == "moment":
        preview = preview_moment_source(repo_root, f"{record_id}.md", metadata=dict(target_record))
        if not preview.get("valid"):
            return [str(error) for error in preview.get("errors") or []] or ["moment source preview failed"]
    return []


def build_publication_build_impact(
    source_dir: Path,
    repo_root: Path,
    kind: str,
    record_id: str,
    target_record: Mapping[str, Any],
    *,
    action: str,
    extra_series_ids: list[str],
    extra_work_ids: list[str],
    force: bool,
) -> Dict[str, Any]:
    try:
        if kind == "work":
            build = build_scope_for_work(source_dir, record_id, extra_series_ids=extra_series_ids)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        elif kind == "work_detail":
            work_id = slug_id(target_record.get("work_id"))
            build = build_scope_for_work(source_dir, work_id, extra_series_ids=extra_series_ids, detail_uid=record_id)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        elif kind == "series":
            build = build_scope_for_series(source_dir, record_id, extra_work_ids=extra_work_ids)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        else:
            build = build_scope_for_moment(repo_root, f"{record_id}.md", metadata=dict(target_record), force=force)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        return {
            "type": "scoped_public_update",
            "available": True,
            "build": build,
        }
    except Exception as exc:  # noqa: BLE001
        payload = {
            "type": "scoped_public_update",
            "available": action == "publish",
            "build": {
                "work_ids": [record_id] if kind == "work" else [slug_id(target_record.get("work_id"))] if kind == "work_detail" else [],
                "series_ids": [record_id] if kind == "series" else [],
                "moment_ids": [record_id] if kind == "moment" else [],
                "rebuild_search": True,
                "search_scope": "catalogue",
                "refresh_published": True,
            },
        }
        if action == "publish":
            payload["pending_source_write"] = True
            payload["summary"] = "Scoped public update will be resolved after the source status is written."
        else:
            payload["error"] = str(exc)
        return payload


def build_publication_preview(source_dir: Path, repo_root: Path, request: Mapping[str, Any]) -> Dict[str, Any]:
    kind = str(request.get("kind") or "")
    action = str(request.get("action") or "")
    record_id = str(request.get("id") or "")
    current_record = current_publication_record(source_dir, kind, record_id)
    current_status = normalize_status(current_record.get("status")) or "draft"
    record_update = request.get("record_update") if isinstance(request.get("record_update"), Mapping) else {}
    blockers: list[str] = []

    if action == "publish" and current_status == "published":
        blockers.append("record is already published")
    elif action == "unpublish" and current_status != "published":
        blockers.append("record is not published")
    elif action == "save_published" and current_status != "published":
        blockers.append("save_published requires a published record")

    target_record = normalize_publication_record(source_dir, kind, record_id, current_record, action, record_update)
    target_status = normalize_status(target_record.get("status")) or "draft"
    changed = current_record != target_record
    changed_field_names = changed_fields(current_record, target_record)
    bootstrap_work_records = publication_bootstrap_work_records(source_dir, kind, action, record_id, target_record)
    bootstrap_work_ids = sorted(bootstrap_work_records)
    source_changed = changed or bool(bootstrap_work_records)
    validation_errors = validate_publication_target(source_dir, kind, record_id, target_record, work_updates=bootstrap_work_records)
    blockers.extend(validation_errors)
    blockers.extend(publication_specific_blockers(source_dir, repo_root, kind, record_id, target_record, work_updates=bootstrap_work_records))
    affected = publication_affected_for_record(source_dir, kind, record_id)
    impact: Dict[str, Any] = {
        "source": {
            "path": publication_source_path_key(kind),
            "will_write": source_changed,
            "changed_fields": changed_field_names,
            "bootstrap_publish_work_ids": bootstrap_work_ids,
        },
        "public": {},
    }
    if bootstrap_work_records:
        impact["source"]["additional_paths"] = [
            {
                "path": str(DEFAULT_SOURCE_DIR / SOURCE_FILES["works"]),
                "will_write": True,
                "changed_record_ids": bootstrap_work_ids,
            }
        ]

    if action == "unpublish":
        if kind == "moment":
            cleanup = moment_delete_preview_cleanup(repo_root, record_id)
        else:
            cleanup = catalogue_delete_preview_cleanup(repo_root, kind, record_id, affected)
        impact["public"] = {
            "type": "public_cleanup",
            "cleanup": cleanup,
        }
    else:
        impact["public"] = build_publication_build_impact(
            source_dir,
            repo_root,
            kind,
            record_id,
            target_record,
            action=action,
            extra_series_ids=list(request.get("extra_series_ids") or []),
            extra_work_ids=list(request.get("extra_work_ids") or []),
            force=bool(request.get("force")),
        )

    if action in {"publish", "save_published"} and not impact["public"].get("available", True):
        blockers.append(str(impact["public"].get("error") or "public update preview failed"))

    blocked = bool(blockers)
    return {
        "ok": True,
        "kind": kind,
        "id": record_id,
        "action": action,
        "allowed": not blocked,
        "blocked": blocked,
        "blockers": blockers,
        "validation_errors": validation_errors,
        "current_status": current_status,
        "target_status": target_status,
        "current_record_hash": record_hash(current_record),
        "target_record_hash": record_hash(target_record),
        "record": current_record,
        "target_record": target_record,
        "changed": changed,
        "source_changed": source_changed,
        "changed_fields": changed_field_names,
        "bootstrap_publish_work_ids": bootstrap_work_ids,
        "affected": affected,
        "impact": impact,
        "summary": f"{action.replace('_', ' ')} {kind} {record_id}: {current_status} -> {target_status}.",
    }


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


def validate_updated_moment_record(moment_id: str, moment_record: Dict[str, Any]) -> list[str]:
    errors = validate_moment_metadata_record(moment_record)
    normalized_id = normalize_moment_id_value(moment_record.get("moment_id") or moment_id)
    if normalized_id != moment_id:
        errors.append("record.moment_id must match moment_id")
    return errors


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


def load_moments_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    moments = payload.get("moments")
    if not isinstance(moments, dict):
        raise ValueError("moments source file must include a moments object")
    return payload


def canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize_for_hash(value[key]) for key in sorted(value.keys(), key=lambda item: str(item))}
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, float):
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return float(f"{value:.15g}")
    return value


def compute_payload_version(payload: Any) -> str:
    canonical = json.dumps(
        canonicalize_for_hash(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"blake2b-{hashlib.blake2b(canonical, digest_size=16).hexdigest()}"


def finalize_moments_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    moments_map = payload.get("moments")
    if not isinstance(moments_map, dict):
        raise ValueError("moments_index.json must include a moments object")
    schema = str((payload.get("header") or {}).get("schema") or "moments_index_v1")
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, "moments": moments_map}),
        "generated_at_utc": utc_now(),
        "count": len(moments_map),
    }
    return payload


def sorted_object_map(value: Mapping[str, Any]) -> Dict[str, Any]:
    return {str(key): value[key] for key in sorted(value.keys(), key=lambda item: str(item))}


def finalize_object_map_payload(payload: Dict[str, Any], map_key: str, default_schema: str) -> Dict[str, Any]:
    records_map = payload.get(map_key)
    if not isinstance(records_map, dict):
        raise ValueError(f"payload must include a {map_key} object")
    sorted_map = sorted_object_map(records_map)
    schema = str((payload.get("header") or {}).get("schema") or default_schema)
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, map_key: sorted_map}),
        "generated_at_utc": utc_now(),
        "count": len(sorted_map),
    }
    payload[map_key] = sorted_map
    return payload


def finalize_works_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "works", "works_index_v4")


def finalize_series_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "series", "series_index_v2")


def finalize_work_storage_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return finalize_object_map_payload(payload, "works", "work_storage_index_v1")


def work_record_detail_count(payload: Mapping[str, Any]) -> int:
    count = 0
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return count
    for section in sections:
        if not isinstance(section, dict):
            continue
        details = section.get("details")
        if isinstance(details, list):
            count += len(details)
    return count


def finalize_work_record_payload(payload: Dict[str, Any], work_id: str) -> Dict[str, Any]:
    work_record = payload.get("work")
    if not isinstance(work_record, dict):
        raise ValueError("work record payload must include a work object")
    sections = payload.get("sections")
    if not isinstance(sections, list):
        sections = []
        payload["sections"] = sections
    content_html = payload.get("content_html")
    payload["header"] = {
        "schema": str((payload.get("header") or {}).get("schema") or "work_record_v3"),
        "version": compute_payload_version(
            {
                "work": work_record,
                "sections": sections,
                "content_html": content_html,
            }
        ),
        "generated_at_utc": utc_now(),
        "work_id": work_id,
        "count": work_record_detail_count(payload),
    }
    return payload


def finalize_series_record_payload(payload: Dict[str, Any], series_id: str) -> Dict[str, Any]:
    series_record = payload.get("series")
    if not isinstance(series_record, dict):
        raise ValueError("series record payload must include a series object")
    works = series_record.get("works")
    payload["header"] = {
        "schema": str((payload.get("header") or {}).get("schema") or "series_record_v1"),
        "version": compute_payload_version(
            {
                "series": series_record,
                "content_html": payload.get("content_html"),
            }
        ),
        "generated_at_utc": utc_now(),
        "series_id": series_id,
        "count": len(works) if isinstance(works, list) else 0,
    }
    return payload


def finalize_recent_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    schema = str((payload.get("header") or {}).get("schema") or "recent_index_v1")
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, "entries": entries}),
        "generated_at_utc": utc_now(),
        "count": len(entries),
    }
    return payload


def collect_matching_paths(root: Path, patterns: Iterable[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()
    if not root.exists():
        return collected
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            collected.append(path)
    return collected


def unique_existing_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists() or not path.is_file():
            continue
        seen.add(resolved)
        out.append(path)
    return out


def collect_moment_repo_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_moments" / f"{moment_id}.md",
            repo_root / "assets" / "moments" / "index" / f"{moment_id}.json",
        ]
    )


def collect_moment_repo_media_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "moments" / "img", [f"{moment_id}-thumb-*.*"])


def collect_moment_staged_media_artifacts(repo_root: Path, moment_id: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "moments"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{moment_id}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{moment_id}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{moment_id}-thumb-*.*"]))
    return paths


def collect_moment_delete_cleanup(repo_root: Path, moment_id: str) -> Dict[str, Any]:
    repo_artifacts = collect_moment_repo_artifacts(repo_root, moment_id)
    repo_media = collect_moment_repo_media_artifacts(repo_root, moment_id)
    staged_media = collect_moment_staged_media_artifacts(repo_root, moment_id)
    delete_paths = unique_existing_paths([*repo_artifacts, *repo_media, *staged_media])
    return {
        "repo_artifacts": repo_artifacts,
        "repo_media": repo_media,
        "staged_media": staged_media,
        "delete_paths": delete_paths,
    }


def collect_work_repo_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_works" / f"{work_id}.md",
            repo_root / "assets" / "works" / "index" / f"{work_id}.json",
        ]
    )


def collect_work_repo_media_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "works" / "img", [f"{work_id}-thumb-*.*"])


def collect_work_staged_media_artifacts(repo_root: Path, work_id: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "works"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{work_id}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{work_id}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{work_id}-thumb-*.*"]))
    return paths


def collect_detail_repo_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    return unique_existing_paths([repo_root / "_work_details" / f"{detail_uid}.md"])


def collect_detail_repo_media_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    return collect_matching_paths(repo_root / "assets" / "work_details" / "img", [f"{detail_uid}-thumb-*.*"])


def collect_detail_staged_media_artifacts(repo_root: Path, detail_uid: str) -> list[Path]:
    staging_root = repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "work_details"
    paths: list[Path] = []
    paths.extend(collect_matching_paths(staging_root / "make_srcset_images", [f"{detail_uid}.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "primary", [f"{detail_uid}-primary-*.*"]))
    paths.extend(collect_matching_paths(staging_root / "srcset_images" / "thumb", [f"{detail_uid}-thumb-*.*"]))
    return paths


def collect_series_repo_artifacts(repo_root: Path, series_id: str) -> list[Path]:
    return unique_existing_paths(
        [
            repo_root / "_series" / f"{series_id}.md",
            repo_root / "assets" / "series" / "index" / f"{series_id}.json",
        ]
    )


def path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def existing_repo_paths(repo_root: Path, rel_paths: Iterable[Path]) -> list[Path]:
    return unique_existing_paths(repo_root / rel_path for rel_path in rel_paths)


def rel_path_for_preview(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root)) if path_is_under(path, repo_root) else path.name


def collect_catalogue_delete_cleanup(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[str, Any]:
    repo_artifacts: list[Path] = []
    repo_media: list[Path] = []
    staged_media: list[Path] = []
    public_json_updates: list[Path] = []
    studio_json_updates: list[Path] = []
    rebuild_search = False

    work_ids = [slug_id(value) for value in affected.get("works") or [] if str(value or "").strip()]
    detail_uids = [normalize_detail_uid_value(value) for value in affected.get("work_details") or [] if str(value or "").strip()]
    series_ids = [normalize_series_id(value) for value in affected.get("series") or [] if str(value or "").strip()]

    if kind == "work":
        repo_artifacts.extend(collect_work_repo_artifacts(repo_root, record_id))
        repo_media.extend(collect_work_repo_media_artifacts(repo_root, record_id))
        staged_media.extend(collect_work_staged_media_artifacts(repo_root, record_id))
        for detail_uid in detail_uids:
            repo_artifacts.extend(collect_detail_repo_artifacts(repo_root, detail_uid))
            repo_media.extend(collect_detail_repo_media_artifacts(repo_root, detail_uid))
            staged_media.extend(collect_detail_staged_media_artifacts(repo_root, detail_uid))
        public_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/data/works_index.json"),
                    Path("assets/data/series_index.json"),
                    Path("assets/data/recent_index.json"),
                ],
            )
        )
        public_json_updates.extend(
            existing_repo_paths(repo_root, [Path("assets/series/index") / f"{series_id}.json" for series_id in series_ids])
        )
        studio_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/studio/data/work_storage_index.json"),
                    Path("assets/studio/data/tag_assignments.json"),
                ],
            )
        )
        rebuild_search = True
    elif kind == "work_detail":
        repo_artifacts.extend(collect_detail_repo_artifacts(repo_root, record_id))
        repo_media.extend(collect_detail_repo_media_artifacts(repo_root, record_id))
        staged_media.extend(collect_detail_staged_media_artifacts(repo_root, record_id))
        public_json_updates.extend(existing_repo_paths(repo_root, [Path("assets/works/index") / f"{work_id}.json" for work_id in work_ids]))
    elif kind == "series":
        repo_artifacts.extend(collect_series_repo_artifacts(repo_root, record_id))
        public_json_updates.extend(
            existing_repo_paths(
                repo_root,
                [
                    Path("assets/data/series_index.json"),
                    Path("assets/data/works_index.json"),
                    Path("assets/data/recent_index.json"),
                ],
            )
        )
        public_json_updates.extend(
            existing_repo_paths(repo_root, [Path("assets/works/index") / f"{work_id}.json" for work_id in work_ids])
        )
        studio_json_updates.extend(existing_repo_paths(repo_root, [Path("assets/studio/data/tag_assignments.json")]))
        rebuild_search = True
    else:
        raise ValueError(f"unsupported catalogue cleanup kind: {kind}")

    return {
        "repo_artifacts": unique_existing_paths(repo_artifacts),
        "repo_media": unique_existing_paths(repo_media),
        "staged_media": unique_existing_paths(staged_media),
        "public_json_updates": unique_existing_paths(public_json_updates),
        "studio_json_updates": unique_existing_paths(studio_json_updates),
        "delete_paths": unique_existing_paths([*repo_artifacts, *repo_media, *staged_media]),
        "catalogue_search": rebuild_search,
    }


def ensure_moment_delete_cleanup_scope(repo_root: Path, cleanup: Mapping[str, Any]) -> None:
    roots = [
        repo_root / "_moments",
        repo_root / "assets" / "moments" / "index",
        repo_root / "assets" / "moments" / "img",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "moments",
    ]
    for raw_path in cleanup.get("delete_paths") or []:
        path = Path(raw_path)
        if not any(path_is_under(path, root) for root in roots):
            raise ValueError(f"delete target is outside allowlisted moment cleanup roots: {path.name}")


def ensure_catalogue_delete_cleanup_scope(repo_root: Path, cleanup: Mapping[str, Any]) -> None:
    delete_roots = [
        repo_root / "_works",
        repo_root / "_work_details",
        repo_root / "_series",
        repo_root / "assets" / "works" / "index",
        repo_root / "assets" / "series" / "index",
        repo_root / "assets" / "works" / "img",
        repo_root / "assets" / "work_details" / "img",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "works",
        repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / "work_details",
    ]
    update_roots = [
        repo_root / "assets" / "works" / "index",
        repo_root / "assets" / "series" / "index",
    ]
    update_paths = {
        (repo_root / "assets" / "data" / "works_index.json").resolve(),
        (repo_root / "assets" / "data" / "series_index.json").resolve(),
        (repo_root / "assets" / "data" / "recent_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "work_storage_index.json").resolve(),
        (repo_root / "assets" / "studio" / "data" / "tag_assignments.json").resolve(),
    }
    for raw_path in cleanup.get("delete_paths") or []:
        path = Path(raw_path)
        if not any(path_is_under(path, root) for root in delete_roots):
            raise ValueError(f"delete target is outside allowlisted catalogue cleanup roots: {path.name}")
    for key in ("public_json_updates", "studio_json_updates"):
        for raw_path in cleanup.get(key) or []:
            path = Path(raw_path)
            if path.resolve() in update_paths:
                continue
            if not any(path_is_under(path, root) for root in update_roots):
                raise ValueError(f"update target is outside allowlisted catalogue cleanup roots: {path.name}")


def catalogue_delete_preview_cleanup(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[str, Any]:
    cleanup = collect_catalogue_delete_cleanup(repo_root, kind, record_id, affected)
    return {
        "repo_artifacts": len(cleanup["repo_artifacts"]),
        "repo_media": len(cleanup["repo_media"]),
        "staged_media": len(cleanup["staged_media"]),
        "public_json_updates": [rel_path_for_preview(repo_root, path) for path in cleanup["public_json_updates"]],
        "studio_json_updates": [rel_path_for_preview(repo_root, path) for path in cleanup["studio_json_updates"]],
        "delete_paths": [rel_path_for_preview(repo_root, path) for path in cleanup["delete_paths"]],
        "catalogue_search": "assets/data/search/catalogue/index.json" if cleanup["catalogue_search"] else "",
    }


def remove_detail_from_work_record_payload(payload: Dict[str, Any], detail_uid: str) -> bool:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return False
    changed = False
    next_sections: list[Dict[str, Any]] = []
    for section in sections:
        if not isinstance(section, dict):
            next_sections.append(section)
            continue
        details = section.get("details")
        if not isinstance(details, list):
            next_sections.append(section)
            continue
        next_details = [
            detail
            for detail in details
            if not (isinstance(detail, dict) and str(detail.get("detail_uid") or "") == detail_uid)
        ]
        if len(next_details) != len(details):
            changed = True
        if next_details:
            next_section = dict(section)
            next_section["details"] = next_details
            next_sections.append(next_section)
    if changed:
        payload["sections"] = next_sections
    return changed


def remove_work_from_series_record_payload(payload: Dict[str, Any], series_id: str, work_id: str) -> bool:
    series_record = payload.get("series")
    if not isinstance(series_record, dict):
        return False
    works = series_record.get("works")
    if not isinstance(works, list):
        return False
    next_works = [str(value) for value in works if str(value) != work_id]
    if next_works == works:
        return False
    series_record["works"] = next_works
    return True


def remove_series_from_work_record_payload(payload: Dict[str, Any], work_id: str, series_id: str) -> bool:
    work_record = payload.get("work")
    if not isinstance(work_record, dict):
        return False
    series_ids = normalize_series_ids_value(work_record.get("series_ids"))
    if series_id not in series_ids:
        return False
    work_record["series_ids"] = [value for value in series_ids if value != series_id]
    return True


def update_recent_entries_for_work_delete(payload: Dict[str, Any], work_id: str, series_index_payload: Mapping[str, Any]) -> bool:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    series_map = series_index_payload.get("series")
    if not isinstance(series_map, dict):
        series_map = {}
    changed = False
    next_entries: list[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            next_entries.append(entry)
            continue
        kind = str(entry.get("kind") or "")
        target_id = str(entry.get("target_id") or "")
        if kind == "work" and target_id == work_id:
            changed = True
            continue
        if kind == "series":
            series_record = series_map.get(target_id)
            if isinstance(series_record, dict):
                works = [str(value) for value in series_record.get("works") or [] if str(value)]
                next_entry = dict(entry)
                next_entry["caption"] = f"{len(works)} work" if len(works) == 1 else f"{len(works)} works"
                if str(next_entry.get("thumb_id") or "") == work_id:
                    next_entry["thumb_id"] = str(series_record.get("primary_work_id") or (works[0] if works else ""))
                if next_entry != entry:
                    changed = True
                next_entries.append(next_entry)
                continue
        next_entries.append(entry)
    if changed:
        payload["entries"] = next_entries
    return changed


def update_recent_entries_for_series_delete(payload: Dict[str, Any], series_id: str) -> bool:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("recent_index.json must include an entries array")
    next_entries = [
        entry
        for entry in entries
        if not (isinstance(entry, dict) and str(entry.get("kind") or "") == "series" and str(entry.get("target_id") or "") == series_id)
    ]
    if len(next_entries) == len(entries):
        return False
    payload["entries"] = next_entries
    return True


def remove_work_overrides_from_tag_assignments(payload: Dict[str, Any], work_id: str) -> bool:
    series_map = payload.get("series")
    if not isinstance(series_map, dict):
        raise ValueError("tag_assignments.json must include a series object")
    changed = False
    now_utc = utc_now()
    for row in series_map.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works")
        if not isinstance(works, dict) or work_id not in works:
            continue
        del works[work_id]
        row["updated_at_utc"] = now_utc
        changed = True
    if changed:
        payload["updated_at_utc"] = now_utc
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"
    return changed


def remove_series_from_tag_assignments(payload: Dict[str, Any], series_id: str) -> bool:
    series_map = payload.get("series")
    if not isinstance(series_map, dict):
        raise ValueError("tag_assignments.json must include a series object")
    if series_id not in series_map:
        return False
    del series_map[series_id]
    payload["updated_at_utc"] = utc_now()
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"
    return True


def build_catalogue_delete_generated_payloads(
    repo_root: Path,
    kind: str,
    record_id: str,
    affected: Mapping[str, Any],
) -> Dict[Path, Dict[str, Any]]:
    payloads: Dict[Path, Dict[str, Any]] = {}

    def load_existing(rel_path: Path) -> tuple[Path, Dict[str, Any]] | None:
        path = (repo_root / rel_path).resolve()
        if not path.exists():
            return None
        return path, load_json_file(path)

    if kind == "work":
        works_index = load_existing(Path("assets/data/works_index.json"))
        if works_index is not None:
            path, payload = works_index
            works = payload.get("works")
            if isinstance(works, dict) and record_id in works:
                del works[record_id]
                payloads[path] = finalize_works_index_payload(payload)

        work_storage = load_existing(Path("assets/studio/data/work_storage_index.json"))
        if work_storage is not None:
            path, payload = work_storage
            works = payload.get("works")
            if isinstance(works, dict) and record_id in works:
                del works[record_id]
                payloads[path] = finalize_work_storage_index_payload(payload)

        series_index_payload: Dict[str, Any] | None = None
        series_index = load_existing(Path("assets/data/series_index.json"))
        if series_index is not None:
            path, payload = series_index
            series_map = payload.get("series")
            changed = False
            if isinstance(series_map, dict):
                for series_id in affected.get("series") or []:
                    series_record = series_map.get(str(series_id))
                    if not isinstance(series_record, dict):
                        continue
                    works = [str(value) for value in series_record.get("works") or [] if str(value) != record_id]
                    if works != series_record.get("works"):
                        series_record["works"] = works
                        changed = True
            if changed:
                payloads[path] = finalize_series_index_payload(payload)
            series_index_payload = payload

        for series_id in affected.get("series") or []:
            series_payload = load_existing(Path("assets/series/index") / f"{series_id}.json")
            if series_payload is None:
                continue
            path, payload = series_payload
            if remove_work_from_series_record_payload(payload, str(series_id), record_id):
                payloads[path] = finalize_series_record_payload(payload, str(series_id))

        recent_index = load_existing(Path("assets/data/recent_index.json"))
        if recent_index is not None:
            path, payload = recent_index
            if update_recent_entries_for_work_delete(payload, record_id, series_index_payload or {}):
                payloads[path] = finalize_recent_index_payload(payload)

        tag_assignments = load_existing(Path("assets/studio/data/tag_assignments.json"))
        if tag_assignments is not None:
            path, payload = tag_assignments
            if remove_work_overrides_from_tag_assignments(payload, record_id):
                payloads[path] = payload

    elif kind == "work_detail":
        for work_id in affected.get("works") or []:
            work_payload = load_existing(Path("assets/works/index") / f"{work_id}.json")
            if work_payload is None:
                continue
            path, payload = work_payload
            if remove_detail_from_work_record_payload(payload, record_id):
                payloads[path] = finalize_work_record_payload(payload, str(work_id))

    elif kind == "series":
        series_index = load_existing(Path("assets/data/series_index.json"))
        if series_index is not None:
            path, payload = series_index
            series_map = payload.get("series")
            if isinstance(series_map, dict) and record_id in series_map:
                del series_map[record_id]
                payloads[path] = finalize_series_index_payload(payload)

        works_index = load_existing(Path("assets/data/works_index.json"))
        if works_index is not None:
            path, payload = works_index
            works = payload.get("works")
            changed = False
            if isinstance(works, dict):
                for work_id in affected.get("works") or []:
                    work_record = works.get(str(work_id))
                    if not isinstance(work_record, dict):
                        continue
                    series_ids = normalize_series_ids_value(work_record.get("series_ids"))
                    if record_id in series_ids:
                        work_record["series_ids"] = [value for value in series_ids if value != record_id]
                        changed = True
            if changed:
                payloads[path] = finalize_works_index_payload(payload)

        for work_id in affected.get("works") or []:
            work_payload = load_existing(Path("assets/works/index") / f"{work_id}.json")
            if work_payload is None:
                continue
            path, payload = work_payload
            if remove_series_from_work_record_payload(payload, str(work_id), record_id):
                payloads[path] = finalize_work_record_payload(payload, str(work_id))

        recent_index = load_existing(Path("assets/data/recent_index.json"))
        if recent_index is not None:
            path, payload = recent_index
            if update_recent_entries_for_series_delete(payload, record_id):
                payloads[path] = finalize_recent_index_payload(payload)

        tag_assignments = load_existing(Path("assets/studio/data/tag_assignments.json"))
        if tag_assignments is not None:
            path, payload = tag_assignments
            if remove_series_from_tag_assignments(payload, record_id):
                payloads[path] = payload

    return payloads


def moment_delete_preview_cleanup(repo_root: Path, moment_id: str) -> Dict[str, Any]:
    cleanup = collect_moment_delete_cleanup(repo_root, moment_id)
    return {
        "repo_artifacts": len(cleanup["repo_artifacts"]),
        "repo_media": len(cleanup["repo_media"]),
        "staged_media": len(cleanup["staged_media"]),
        "delete_paths": [str(path.relative_to(repo_root)) if path_is_under(path, repo_root) else path.name for path in cleanup["delete_paths"]],
        "moments_index": "assets/data/moments_index.json",
        "catalogue_search": "assets/data/search/catalogue/index.json",
    }


def backup_transaction_paths(paths: Iterable[Path], backup_root: Path, repo_root: Path) -> Dict[Path, Path]:
    backups: Dict[Path, Path] = {}
    for path in unique_existing_paths(paths):
        resolved = path.resolve()
        if resolved in backups:
            continue
        try:
            rel_path = Path("repo") / resolved.relative_to(repo_root.resolve())
        except ValueError:
            rel_path = Path("external") / path.name
        backup_path = backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        backups[resolved] = backup_path
    return backups


def restore_transaction_paths(touched_paths: Iterable[Path], backups: Mapping[Path, Path]) -> None:
    for path in unique_paths(touched_paths):
        resolved = path.resolve()
        backup_path = backups.get(resolved)
        try:
            if backup_path and backup_path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, path)
            elif path.exists() and path.is_file():
                path.unlink()
        except OSError:
            pass


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(path)
    return out


def delete_existing_files(paths: Iterable[Path]) -> int:
    deleted = 0
    for path in unique_existing_paths(paths):
        path.unlink()
        deleted += 1
    return deleted


def run_catalogue_search_rebuild(repo_root: Path, *, write: bool) -> Dict[str, Any]:
    proc = subprocess.run(
        build_search_command(repo_root, write=write, force=False, env=os.environ.copy()),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-8:]) if proc.stdout else "",
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-8:]) if proc.stderr else "",
    }
    if proc.returncode != 0:
        detail = payload["stderr_tail"] or payload["stdout_tail"] or "catalogue search rebuild failed"
        raise RuntimeError(str(detail))
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
        series_path: Path,
        moments_path: Path,
        allowed_write_paths: set[Path],
        allowed_write_roots: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.source_dir = source_dir.resolve()
        self.lookup_dir = lookup_dir.resolve()
        self.works_path = works_path.resolve()
        self.work_details_path = work_details_path.resolve()
        self.series_path = series_path.resolve()
        self.moments_path = moments_path.resolve()
        self.allowed_write_paths = {path.resolve() for path in allowed_write_paths}
        self.allowed_write_roots = {path.resolve() for path in allowed_write_roots}
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
            PUBLICATION_PREVIEW_PATH,
            PUBLICATION_APPLY_PATH,
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
            PROSE_IMPORT_PREVIEW_PATH,
            PROSE_IMPORT_APPLY_PATH,
            MOMENT_IMPORT_PREVIEW_PATH,
            MOMENT_IMPORT_APPLY_PATH,
            MOMENT_PREVIEW_PATH,
            MOMENT_SAVE_PATH,
            PROJECT_STATE_REPORT_PATH,
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
            if self.path == PUBLICATION_PREVIEW_PATH:
                self._handle_publication_preview(allowed)
                return
            if self.path == PUBLICATION_APPLY_PATH:
                self._handle_publication_apply(allowed)
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
            if self.path == PROSE_IMPORT_PREVIEW_PATH:
                self._handle_prose_import_preview(allowed)
                return
            if self.path == PROSE_IMPORT_APPLY_PATH:
                self._handle_prose_import_apply(allowed)
                return
            if self.path == MOMENT_IMPORT_PREVIEW_PATH:
                self._handle_moment_import_preview(allowed)
                return
            if self.path == MOMENT_IMPORT_APPLY_PATH:
                self._handle_moment_import_apply(allowed)
                return
            if self.path == MOMENT_PREVIEW_PATH:
                self._handle_moment_preview(allowed)
                return
            if self.path == MOMENT_SAVE_PATH:
                self._handle_moment_save(allowed)
                return
            if self.path == PROJECT_STATE_REPORT_PATH:
                self._handle_project_state_report(allowed)
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
        requested_apply_build = extract_apply_build(body)
        requested_work_id = body.get("work_id")
        work_update = extract_work_update(body)
        if requested_work_id is None:
            requested_work_id = work_update.get("work_id")
        work_id = slug_id(requested_work_id)
        extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))

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
        apply_build = requested_apply_build and normalize_status(updated_record.get("status")) == "published"
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
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation = work_lookup_invalidation_for_fields(fields_changed)
            locked_fields = locked_first_pass_work_fields()
            use_single_record_lookup_refresh = (
                invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD
                and set(fields_changed).issubset(locked_fields)
            )
            lookup_refresh_payload = {
                "mode": "single-record" if use_single_record_lookup_refresh else (
                    "targeted-multi-record" if invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else "full"
                ),
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
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
                "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
                "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            refresh_result = self._refresh_lookup_payloads_for_work_change(
                work_id,
                fields_changed,
                current_record,
                updated_record,
            )
            response_payload["lookup_refresh"] = {
                "mode": refresh_result["mode"],
                "invalidation_class": refresh_result["invalidation_class"],
                "artifacts": refresh_result["artifacts"],
                "unknown_fields": refresh_result["unknown_fields"],
                "written_count": refresh_result["written_count"],
            }
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "work_not_published",
                "summary": "Work must be published before a public update can run.",
            }
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id=work_id,
                series_id="",
                extra_series_ids=extra_series_ids,
                extra_work_ids=[],
                detail_uid="",
                force=False,
            )
            response_payload["build"] = build_payload
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_bulk_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        apply_build = extract_apply_build(body)
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
                if normalize_status(updated_record.get("status")) == "published":
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
            response_payload["build_requested"] = bool(apply_build and changed and build_targets)
            if apply_build and changed and build_targets:
                response_payload["build"] = self._run_build_targets(response_payload["build_targets"])
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if apply_build and changed:
            response_payload["build"] = self._run_build_targets(response_payload["build_targets"])
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _publication_source_payload(self, kind: str, record_id: str, target_record: Mapping[str, Any]) -> tuple[Path, Dict[str, Any]]:
        if kind == "work":
            payload = load_works_payload(self.server.works_path)
            records = dict(payload["works"])
            records[record_id] = dict(target_record)
            return self.server.works_path.resolve(), payload_for_map("works", records)
        if kind == "work_detail":
            payload = load_work_details_payload(self.server.work_details_path)
            records = dict(payload["work_details"])
            records[record_id] = dict(target_record)
            return self.server.work_details_path.resolve(), payload_for_map("work_details", records)
        if kind == "series":
            payload = load_series_payload(self.server.series_path)
            records = dict(payload["series"])
            records[record_id] = dict(target_record)
            return self.server.series_path.resolve(), payload_for_map("series", records)
        payload = load_moments_payload(self.server.moments_path)
        records = dict(payload["moments"])
        records[record_id] = dict(target_record)
        return self.server.moments_path.resolve(), moment_metadata_payload(records)

    def _publication_source_payloads(self, kind: str, record_id: str, target_record: Mapping[str, Any], preview: Mapping[str, Any]) -> Dict[Path, Dict[str, Any]]:
        source_path, source_payload = self._publication_source_payload(kind, record_id, target_record)
        payloads: Dict[Path, Dict[str, Any]] = {source_path: source_payload}
        bootstrap_work_ids = [str(work_id) for work_id in preview.get("bootstrap_publish_work_ids") or []]
        if kind == "series" and bootstrap_work_ids:
            promoted = series_publish_bootstrap_work_records(self.server.source_dir, record_id)
            works_payload = load_works_payload(self.server.works_path)
            work_records = dict(works_payload["works"])
            for work_id in bootstrap_work_ids:
                if work_id not in promoted:
                    raise ValueError(f"bootstrap work {work_id} is no longer draft")
                work_records[work_id] = promoted[work_id]
            payloads[self.server.works_path.resolve()] = payload_for_map("works", work_records)
        return payloads

    def _run_publication_build(
        self,
        *,
        kind: str,
        record_id: str,
        target_record: Mapping[str, Any],
        extra_series_ids: list[str],
        extra_work_ids: list[str],
        force: bool,
    ) -> tuple[bool, Dict[str, Any]]:
        if self.server.dry_run:
            return True, {
                "ok": True,
                "dry_run": True,
                "would_run": True,
                "kind": kind,
                "id": record_id,
                "summary": "Dry-run publication apply would run the scoped public update after the source write.",
            }
        generated_backup_root = self.server.backups_dir / f"catalogue-public-update-{kind.replace('_', '-')}-{backup_stamp_now()}"
        affected = publication_affected_for_record(self.server.source_dir, kind, record_id)
        if kind == "moment":
            cleanup = collect_moment_delete_cleanup(self.server.repo_root, record_id)
            backup_candidates = [
                *cleanup["delete_paths"],
                self.server.repo_root / "assets" / "data" / "moments_index.json",
                self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json",
            ]
        else:
            cleanup = collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, affected)
            backup_candidates = [
                *cleanup["delete_paths"],
                *cleanup["public_json_updates"],
                *cleanup["studio_json_updates"],
                self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json",
            ]
        generated_backups = backup_transaction_paths(backup_candidates, generated_backup_root, self.server.repo_root)
        if kind == "work":
            success, payload = self._run_build_operation(work_id=record_id, series_id="", moment_id="", extra_series_ids=extra_series_ids, extra_work_ids=[], detail_uid="", force=force)
        elif kind == "work_detail":
            success, payload = self._run_build_operation(work_id=slug_id(target_record.get("work_id")), series_id="", moment_id="", extra_series_ids=extra_series_ids, extra_work_ids=[], detail_uid=record_id, force=force)
        elif kind == "series":
            success, payload = self._run_build_operation(work_id="", series_id=record_id, moment_id="", extra_series_ids=[], extra_work_ids=extra_work_ids, detail_uid="", force=force)
        else:
            success, payload = self._run_build_operation(work_id="", series_id="", moment_id=record_id, extra_series_ids=[], extra_work_ids=[], detail_uid="", force=force)
        payload["generated_backup_root"] = self.server.rel_path(generated_backup_root) if generated_backups else ""
        payload["generated_backups"] = [self.server.rel_path(path) for path in generated_backups.values()]
        return success, payload

    def _apply_publication_unpublish_cleanup(
        self,
        *,
        kind: str,
        record_id: str,
        target_record: Mapping[str, Any],
        preview: Mapping[str, Any],
    ) -> Dict[str, Any]:
        source_path, source_payload = self._publication_source_payload(kind, record_id, target_record)
        if source_path not in self.server.allowed_write_paths:
            raise ValueError("write target not allowlisted")

        if kind != "moment":
            affected = preview["affected"]
            cleanup = collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, affected)
            generated_payloads = build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, affected)
            cleanup_result = self._apply_catalogue_delete_transaction(
                backup_label=f"catalogue-unpublish-{kind.replace('_', '-')}",
                payloads={source_path: source_payload, **generated_payloads},
                cleanup=cleanup,
            )
            cleanup_result.pop("backup_paths", None)
            return cleanup_result

        cleanup = collect_moment_delete_cleanup(self.server.repo_root, record_id)
        ensure_moment_delete_cleanup_scope(self.server.repo_root, cleanup)
        moments_index_path = (self.server.repo_root / "assets" / "data" / "moments_index.json").resolve()
        search_index_path = (self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
        deleted_file_count = 0
        search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
        transaction_backup_root: Path | None = None
        if not self.server.dry_run:
            transaction_backup_root = self.server.backups_dir / f"catalogue-unpublish-moment-{backup_stamp_now()}"
            touched_paths = unique_paths([source_path, moments_index_path, search_index_path, *cleanup["delete_paths"]])
            transaction_backups = backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
            try:
                payloads: Dict[Path, Dict[str, Any]] = {source_path: source_payload}
                if moments_index_path.exists():
                    moments_index_payload = load_json_file(moments_index_path)
                    moments_map = moments_index_payload.get("moments")
                    if not isinstance(moments_map, dict):
                        raise ValueError("moments_index.json must include a moments object")
                    moments_map.pop(record_id, None)
                    payloads[moments_index_path] = finalize_moments_index_payload(moments_index_payload)
                atomic_write_many(payloads, self.server.backups_dir)
                deleted_file_count = delete_existing_files(cleanup["delete_paths"])
                search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
            except Exception:
                restore_transaction_paths(touched_paths, transaction_backups)
                raise

        return {
            "deleted_files": deleted_file_count,
            "would_delete_files": len(cleanup["delete_paths"]),
            "moments_index_updated": bool(not self.server.dry_run and moments_index_path.exists()),
            "would_update_moments_index": moments_index_path.exists(),
            "catalogue_search_rebuilt": bool(not self.server.dry_run and search_rebuild.get("ok")),
            "would_rebuild_catalogue_search": True,
            "search_exit_code": search_rebuild.get("exit_code"),
            "backup_root": self.server.rel_path(transaction_backup_root) if transaction_backup_root else "",
        }

    def _handle_publication_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_publication_request(body)
        preview = build_publication_preview(self.server.source_dir, self.server.repo_root, request)
        self._send_json(HTTPStatus.OK, {"ok": True, "preview": preview}, allowed)

    def _handle_publication_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_publication_request(body)
        preview = build_publication_preview(self.server.source_dir, self.server.repo_root, request)
        if preview.get("blocked"):
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "publication preview contains blockers", "preview": preview}, allowed)
            return

        expected_hash = str(request.get("expected_record_hash") or "").strip()
        current_hash = str(preview.get("current_record_hash") or "")
        if expected_hash and expected_hash != current_hash:
            self._send_json(HTTPStatus.CONFLICT, {"ok": False, "error": "record changed since loaded", "kind": request["kind"], "id": request["id"], "current_record_hash": current_hash}, allowed)
            return

        kind = str(request["kind"])
        action = str(request["action"])
        record_id = str(request["id"])
        target_record = dict(preview["target_record"])
        changed = bool(preview.get("changed"))
        source_changed = bool(preview.get("source_changed", changed))
        source_backups: list[Path] = []
        public_update: Dict[str, Any] = {"ok": True, "skipped": True}
        public_update_ok = True

        if action == "unpublish":
            public_update = self._apply_publication_unpublish_cleanup(kind=kind, record_id=record_id, target_record=target_record, preview=preview)
        else:
            if source_changed:
                source_payloads = self._publication_source_payloads(kind, record_id, target_record, preview)
                blocked_paths = [path for path in source_payloads if path not in self.server.allowed_write_paths]
                if blocked_paths:
                    raise ValueError("write target not allowlisted")
                if not self.server.dry_run:
                    source_backups = atomic_write_many(source_payloads, self.server.backups_dir)
                    self._refresh_lookup_payloads()
            public_update_ok, public_update = self._run_publication_build(
                kind=kind,
                record_id=record_id,
                target_record=target_record,
                extra_series_ids=list(request.get("extra_series_ids") or []),
                extra_work_ids=list(request.get("extra_work_ids") or []),
                force=bool(request.get("force")),
            )

        response_payload: Dict[str, Any] = {
            "ok": public_update_ok,
            "status": "completed" if public_update_ok else "public_update_failed",
            "kind": kind,
            "id": record_id,
            "action": action,
            "changed": changed,
            "source_changed": source_changed,
            "changed_fields": preview.get("changed_fields", []),
            "bootstrap_publish_work_ids": preview.get("bootstrap_publish_work_ids", []),
            "record": target_record,
            "record_hash": record_hash(target_record),
            "preview": preview,
            "source_saved": bool(source_changed and not self.server.dry_run) or bool(action == "unpublish" and not self.server.dry_run),
            "public_update": public_update,
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = source_changed or action == "unpublish"
        elif source_backups:
            response_payload["backups"] = [self.server.rel_path(path) for path in source_backups]
        if not self.server.dry_run:
            now_utc = utc_now()
            operation = f"{kind}.{action}"
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, operation),
                    "time_utc": now_utc,
                    "kind": "publication",
                    "operation": operation,
                    "status": "completed" if public_update_ok else "failed",
                    "summary": f"{action.replace('_', ' ').title()} {kind} {record_id}.",
                    "affected": preview.get("affected", {}),
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self._send_json(HTTPStatus.OK if public_update_ok else HTTPStatus.INTERNAL_SERVER_ERROR, response_payload, allowed)

    def _handle_delete_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_delete_request(body)
        preview = build_delete_preview(self.server.source_dir, request["kind"], request["id"], repo_root=self.server.repo_root)
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

    def _ensure_delete_payload_scope(self, payloads: Mapping[Path, Dict[str, Any]]) -> None:
        generated_roots = [
            self.server.repo_root / "assets" / "works" / "index",
            self.server.repo_root / "assets" / "series" / "index",
        ]
        generated_paths = {
            (self.server.repo_root / "assets" / "data" / "works_index.json").resolve(),
            (self.server.repo_root / "assets" / "data" / "series_index.json").resolve(),
            (self.server.repo_root / "assets" / "data" / "recent_index.json").resolve(),
            (self.server.repo_root / "assets" / "studio" / "data" / "work_storage_index.json").resolve(),
            (self.server.repo_root / "assets" / "studio" / "data" / "tag_assignments.json").resolve(),
        }
        for target_path in payloads:
            resolved = target_path.resolve()
            if resolved in self.server.allowed_write_paths:
                continue
            if resolved in generated_paths:
                continue
            if any(path_is_under(resolved, root) for root in generated_roots):
                continue
            raise ValueError("write target not allowlisted")

    def _apply_catalogue_delete_transaction(
        self,
        *,
        backup_label: str,
        payloads: Dict[Path, Dict[str, Any]],
        cleanup: Mapping[str, Any],
    ) -> Dict[str, Any]:
        ensure_catalogue_delete_cleanup_scope(self.server.repo_root, cleanup)
        self._ensure_delete_payload_scope(payloads)
        search_index_path = (self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
        rebuild_search = bool(cleanup.get("catalogue_search"))
        transaction_backup_root: Path | None = None
        deleted_file_count = 0
        search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
        transaction_backups: Dict[Path, Path] = {}
        backup_paths: list[Path] = []

        if not self.server.dry_run:
            transaction_backup_root = self.server.backups_dir / f"{backup_label}-{backup_stamp_now()}"
            touched_paths = unique_paths(
                [
                    *payloads.keys(),
                    *(cleanup.get("delete_paths") or []),
                    *([search_index_path] if rebuild_search else []),
                ]
            )
            transaction_backups = backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
            try:
                backup_paths = atomic_write_many(payloads, self.server.backups_dir)
                backup_paths.extend(transaction_backups.values())
                deleted_file_count = delete_existing_files(cleanup.get("delete_paths") or [])
                if rebuild_search:
                    search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
                self._refresh_lookup_payloads()
            except Exception:
                restore_transaction_paths(touched_paths, transaction_backups)
                raise

        return {
            "deleted_files": deleted_file_count,
            "would_delete_files": len(cleanup.get("delete_paths") or []),
            "updated_json_files": 0 if self.server.dry_run else len(payloads),
            "would_update_json_files": len(payloads),
            "catalogue_search_rebuilt": bool(not self.server.dry_run and rebuild_search and search_rebuild.get("ok")),
            "would_rebuild_catalogue_search": rebuild_search,
            "search_exit_code": search_rebuild.get("exit_code"),
            "backup_root": self.server.rel_path(transaction_backup_root) if transaction_backup_root else "",
            "backup_paths": backup_paths,
        }

    def _handle_delete_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        request = extract_delete_request(body)
        kind = request["kind"]
        record_id = request["id"]
        expected_hash = request["expected_record_hash"]
        preview = build_delete_preview(self.server.source_dir, kind, record_id, repo_root=self.server.repo_root)
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
            series_payload = load_series_payload(self.server.series_path)
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
            updated_series, changed_series_ids = series_records_with_draft_primary_cleared(series_payload["series"], record_id)
            cleanup = collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
            payloads = {
                self.server.works_path.resolve(): payload_for_map("works", updated_works),
                self.server.work_details_path.resolve(): payload_for_map("work_details", updated_details),
                **generated_payloads,
            }
            if changed_series_ids:
                payloads[self.server.series_path.resolve()] = payload_for_map("series", updated_series)
            cleanup_result = self._apply_catalogue_delete_transaction(
                backup_label="catalogue-delete-work",
                payloads=payloads,
                cleanup=cleanup,
            )
            backup_paths = cleanup_result.pop("backup_paths")
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
                "cleanup": cleanup_result,
            }
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "work.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "work.delete",
                        "status": "completed",
                        "summary": f"Deleted work {record_id}, dependent source records, generated artifacts, local media, and catalogue search record.",
                        "affected": {
                            **preview["affected"],
                            "series": sorted(set([*preview["affected"].get("series", []), *changed_series_ids])),
                        },
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
            cleanup = collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
            payloads = {
                self.server.work_details_path.resolve(): payload_for_map("work_details", updated_details),
                **generated_payloads,
            }
            cleanup_result = self._apply_catalogue_delete_transaction(
                backup_label="catalogue-delete-work-detail",
                payloads=payloads,
                cleanup=cleanup,
            )
            backup_paths = cleanup_result.pop("backup_paths")
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
                "cleanup": cleanup_result,
            }
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "work-detail.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "work-detail.delete",
                        "status": "completed",
                        "summary": f"Deleted work detail {record_id}, generated artifacts, and local media.",
                        "affected": preview["affected"],
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
        elif kind == "series":
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
            cleanup = collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
            payloads = {
                self.server.series_path.resolve(): payload_for_map("series", updated_series),
                self.server.works_path.resolve(): payload_for_map("works", updated_works),
                **generated_payloads,
            }
            cleanup_result = self._apply_catalogue_delete_transaction(
                backup_label="catalogue-delete-series",
                payloads=payloads,
                cleanup=cleanup,
            )
            backup_paths = cleanup_result.pop("backup_paths")
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
                "cleanup": cleanup_result,
            }
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "series.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "series.delete",
                        "status": "completed",
                        "summary": f"Deleted series {record_id}, generated artifacts, related index records, and catalogue search record.",
                        "affected": preview["affected"],
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
        else:
            moments_payload = load_moments_payload(self.server.moments_path)
            current_record = moments_payload["moments"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"moment_id not found: {record_id}")
            normalized_current = normalize_moment_metadata_record(record_id, current_record)
            current_hash = record_hash(normalized_current)
            if expected_hash and expected_hash != current_hash:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"ok": False, "error": "record changed since loaded", "moment_id": record_id, "current_record_hash": current_hash},
                    allowed,
                )
                return
            updated_moments = dict(moments_payload["moments"])
            del updated_moments[record_id]
            cleanup = collect_moment_delete_cleanup(self.server.repo_root, record_id)
            ensure_moment_delete_cleanup_scope(self.server.repo_root, cleanup)
            moments_index_path = (self.server.repo_root / "assets" / "data" / "moments_index.json").resolve()
            search_index_path = (self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
            allowed_generated_paths = {
                moments_index_path,
                search_index_path,
            }
            if moments_index_path not in allowed_generated_paths or search_index_path not in allowed_generated_paths:
                raise ValueError("generated write target not allowlisted")
            deleted_file_count = 0
            search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
            transaction_backup_root: Path | None = None
            if not self.server.dry_run:
                metadata_path = self.server.moments_path.resolve()
                if metadata_path not in self.server.allowed_write_paths:
                    raise ValueError("write target not allowlisted")
                transaction_backup_root = self.server.backups_dir / f"catalogue-delete-moment-{backup_stamp_now()}"
                touched_paths = unique_paths(
                    [
                        metadata_path,
                        moments_index_path,
                        search_index_path,
                        *cleanup["delete_paths"],
                    ]
                )
                transaction_backups = backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
                try:
                    payloads: Dict[Path, Dict[str, Any]] = {
                        metadata_path: moment_metadata_payload(updated_moments),
                    }
                    if moments_index_path.exists():
                        moments_index_payload = load_json_file(moments_index_path)
                        moments_map = moments_index_payload.get("moments")
                        if not isinstance(moments_map, dict):
                            raise ValueError("moments_index.json must include a moments object")
                        moments_map.pop(record_id, None)
                        payloads[moments_index_path] = finalize_moments_index_payload(moments_index_payload)
                    backup_paths = atomic_write_many(payloads, self.server.backups_dir)
                    backup_paths.extend(transaction_backups.values())
                    deleted_file_count = delete_existing_files(cleanup["delete_paths"])
                    search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
                except Exception:
                    restore_transaction_paths(touched_paths, transaction_backups)
                    raise
            response_payload = {
                "ok": True,
                "kind": kind,
                "id": record_id,
                "deleted": True,
                "preview": preview,
                "cleanup": {
                    "deleted_files": deleted_file_count,
                    "would_delete_files": len(cleanup["delete_paths"]),
                    "moments_index_updated": bool(not self.server.dry_run and moments_index_path.exists()),
                    "would_update_moments_index": moments_index_path.exists(),
                    "catalogue_search_rebuilt": bool(not self.server.dry_run and search_rebuild.get("ok")),
                    "would_rebuild_catalogue_search": True,
                    "search_exit_code": search_rebuild.get("exit_code"),
                    "backup_root": self.server.rel_path(transaction_backup_root) if transaction_backup_root else "",
                },
            }
            if not self.server.dry_run:
                now_utc = utc_now()
                self.server.append_activity(
                    {
                        "id": activity_id(now_utc, "moment.delete"),
                        "time_utc": now_utc,
                        "kind": "source_save",
                        "operation": "moment.delete",
                        "status": "completed",
                        "summary": f"Deleted moment {record_id}, generated artifacts, local media, and catalogue search record.",
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
        parent_work = source_records.works.get(work_id)
        if not isinstance(parent_work, dict):
            raise ValueError(f"parent work_id not found: {work_id}")
        if normalize_status(parent_work.get("status")) != "published":
            raise ValueError(f"parent work {work_id} must be published before adding work details")

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
        apply_build = extract_apply_build(body)
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
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation = detail_lookup_invalidation_for_fields(fields_changed)
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
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
                "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
                "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            refresh_result = self._refresh_lookup_payloads_for_detail_change(
                detail_uid,
                fields_changed,
                current_record,
                updated_record,
            )
            response_payload["lookup_refresh"] = {
                "mode": refresh_result["mode"],
                "invalidation_class": refresh_result["invalidation_class"],
                "artifacts": refresh_result["artifacts"],
                "unknown_fields": refresh_result["unknown_fields"],
                "written_count": refresh_result["written_count"],
            }
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id=work_id,
                series_id="",
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid=detail_uid,
                force=False,
            )
            response_payload["build"] = build_payload
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _send_retired_work_child_metadata_response(self, allowed: Optional[str]) -> None:
        self._send_json(
            HTTPStatus.GONE,
            {
                "ok": False,
                "error": "Work files and links are now work-owned metadata. Edit downloads and links through the work record.",
            },
            allowed,
        )

    def _handle_work_file_create(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)
        return
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
        self._send_retired_work_child_metadata_response(allowed)
        return
        body = self._read_json_body()
        apply_build = extract_apply_build(body)
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
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation = work_file_lookup_invalidation_for_fields(fields_changed)
            if slug_id(current_record.get("work_id")) != slug_id(updated_record.get("work_id")):
                invalidation = {
                    "class": LOOKUP_INVALIDATION_FULL,
                    "artifacts": ["full_lookup_refresh"],
                    "unknown_fields": [],
                }
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_file_save",
            {
                "file_uid": file_uid,
                "work_id": updated_record.get("work_id"),
                "changed": changed,
                "changed_fields": fields_changed,
                "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
                "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            refresh_result = self._refresh_lookup_payloads_for_work_file_change(
                file_uid,
                fields_changed,
                current_record,
                updated_record,
            )
            response_payload["lookup_refresh"] = {
                "mode": refresh_result["mode"],
                "invalidation_class": refresh_result["invalidation_class"],
                "artifacts": refresh_result["artifacts"],
                "unknown_fields": refresh_result["unknown_fields"],
                "written_count": refresh_result["written_count"],
            }
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id=slug_id(updated_record.get("work_id")),
                series_id="",
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid="",
                force=False,
            )
            response_payload["build"] = build_payload
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_file_delete(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)
        return
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
        self._send_retired_work_child_metadata_response(allowed)
        return
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
        self._send_retired_work_child_metadata_response(allowed)
        return
        body = self._read_json_body()
        apply_build = extract_apply_build(body)
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
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation = work_link_lookup_invalidation_for_fields(fields_changed)
            if slug_id(current_record.get("work_id")) != slug_id(updated_record.get("work_id")):
                invalidation = {
                    "class": LOOKUP_INVALIDATION_FULL,
                    "artifacts": ["full_lookup_refresh"],
                    "unknown_fields": [],
                }
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_work_link_save",
            {
                "link_uid": link_uid,
                "work_id": updated_record.get("work_id"),
                "changed": changed,
                "changed_fields": fields_changed,
                "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
                "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            refresh_result = self._refresh_lookup_payloads_for_work_link_change(
                link_uid,
                fields_changed,
                current_record,
                updated_record,
            )
            response_payload["lookup_refresh"] = {
                "mode": refresh_result["mode"],
                "invalidation_class": refresh_result["invalidation_class"],
                "artifacts": refresh_result["artifacts"],
                "unknown_fields": refresh_result["unknown_fields"],
                "written_count": refresh_result["written_count"],
            }
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id=slug_id(updated_record.get("work_id")),
                series_id="",
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid="",
                force=False,
            )
            response_payload["build"] = build_payload
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_link_delete(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)
        return
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
        requested_apply_build = extract_apply_build(body)
        requested_series_id = body.get("series_id")
        series_update = extract_series_update(body)
        if requested_series_id is None:
            requested_series_id = series_update.get("series_id")
        series_id = normalize_series_id(requested_series_id)
        work_updates_request = extract_series_work_updates(body)
        extra_work_ids = [slug_id(raw) for raw in body.get("extra_work_ids") or []]

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
        save_validation_errors = validate_series_save_record(updated_series_record)
        if save_validation_errors:
            raise ValueError("source validation failed: " + "; ".join(save_validation_errors))
        apply_build = requested_apply_build and normalize_status(updated_series_record.get("status")) == "published"
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
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation = series_lookup_invalidation_for_fields(series_changed_fields)
            if changed_work_ids:
                invalidation = {
                    "class": LOOKUP_INVALIDATION_FULL,
                    "artifacts": ["full_lookup_refresh"],
                    "unknown_fields": [],
                }
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
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
                "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
                "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            refresh_result = self._refresh_lookup_payloads_for_series_change(
                series_id,
                series_changed_fields,
                changed_work_ids,
                current_series_record,
                updated_series_record,
            )
            response_payload["lookup_refresh"] = {
                "mode": refresh_result["mode"],
                "invalidation_class": refresh_result["invalidation_class"],
                "artifacts": refresh_result["artifacts"],
                "unknown_fields": refresh_result["unknown_fields"],
                "written_count": refresh_result["written_count"],
            }
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
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "series_not_published",
                "summary": "Series must be published before a public update can run.",
            }
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id="",
                series_id=series_id,
                extra_series_ids=[],
                extra_work_ids=extra_work_ids,
                detail_uid="",
                force=False,
            )
            response_payload["build"] = build_payload
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
        save_validation_errors = validate_series_save_record(created_series_record)
        if save_validation_errors:
            raise ValueError("source validation failed: " + "; ".join(save_validation_errors))

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

    def _run_build_operation(
        self,
        *,
        work_id: str,
        series_id: str,
        moment_id: str = "",
        extra_series_ids: list[str],
        extra_work_ids: list[str],
        detail_uid: str,
        force: bool,
        media_only: bool = False,
    ) -> tuple[bool, Dict[str, Any]]:
        if work_id:
            result = run_scoped_build(
                self.server.repo_root,
                source_dir=self.server.source_dir,
                work_id=work_id,
                extra_series_ids=extra_series_ids,
                detail_uid=detail_uid,
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
                log_activity=not self.server.dry_run,
            )
        elif series_id:
            result = run_series_scoped_build(
                self.server.repo_root,
                source_dir=self.server.source_dir,
                series_id=series_id,
                extra_work_ids=extra_work_ids,
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
                log_activity=not self.server.dry_run,
            )
        else:
            result = run_moment_scoped_build(
                self.server.repo_root,
                moment_file=f"{moment_id}.md",
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
                log_activity=not self.server.dry_run,
            )

        payload: Dict[str, Any] = {
            "ok": result.get("status") == "completed",
            "work_id": work_id,
            "series_id": series_id,
            "moment_id": moment_id,
            "detail_uid": detail_uid,
            "force": force,
            "media_only": media_only,
            "build": result.get("scope"),
            "media": result.get("media"),
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
                        "operation": "media.refresh" if media_only else "build.apply",
                        "status": "failed",
                        "summary": f"{'Media refresh' if media_only else 'Scoped rebuild'} failed for {('work ' + work_id) if work_id else ('series ' + series_id) if series_id else ('moment ' + moment_id)}.",
                        "affected": {
                            "works": list((result.get("scope") or {}).get("work_ids", [])),
                            "series": list((result.get("scope") or {}).get("series_ids", [])),
                            "work_details": [],
                            "moments": list((result.get("scope") or {}).get("moment_ids", [])),
                        },
                        "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                    }
                )
            payload["error"] = str(result.get("error") or "Scoped JSON build failed.")
            payload["failed_step"] = result.get("failed_step")
            return False, payload

        if not self.server.dry_run:
            payload["completed_at_utc"] = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(payload["completed_at_utc"], "build.apply"),
                    "time_utc": payload["completed_at_utc"],
                    "kind": "build",
                    "operation": "media.refresh" if media_only else "build.apply",
                    "status": "completed",
                    "summary": f"{'Media refresh' if media_only else 'Scoped rebuild'} completed for {('work ' + work_id) if work_id else ('series ' + series_id) if series_id else ('moment ' + moment_id)}.",
                    "affected": {
                        "works": list((result.get("scope") or {}).get("work_ids", [])),
                        "series": list((result.get("scope") or {}).get("series_ids", [])),
                        "work_details": [],
                        "moments": list((result.get("scope") or {}).get("moment_ids", [])),
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        return True, payload

    def _run_build_targets(self, build_targets: list[Dict[str, Any]]) -> Dict[str, Any]:
        if not build_targets:
            return {
                "ok": True,
                "requested_count": 0,
                "completed_count": 0,
                "targets": [],
                "remaining_targets": [],
            }

        target_results: list[Dict[str, Any]] = []
        for index, target in enumerate(build_targets):
            work_id = slug_id(target.get("work_id"))
            extra_series_ids = normalize_series_ids_value(target.get("extra_series_ids"))
            success, payload = self._run_build_operation(
                work_id=work_id,
                series_id="",
                moment_id="",
                extra_series_ids=extra_series_ids,
                extra_work_ids=[],
                detail_uid="",
                force=False,
            )
            target_results.append(
                {
                    "work_id": work_id,
                    "extra_series_ids": extra_series_ids,
                    "ok": success,
                    "completed_at_utc": payload.get("completed_at_utc"),
                    "error": payload.get("error"),
                }
            )
            if not success:
                return {
                    "ok": False,
                    "requested_count": len(build_targets),
                    "completed_count": index,
                    "targets": target_results,
                    "remaining_targets": build_targets[index:],
                    "error": payload.get("error"),
                    "failed_step": payload.get("failed_step"),
                }

        return {
            "ok": True,
            "requested_count": len(build_targets),
            "completed_count": len(build_targets),
            "targets": target_results,
            "remaining_targets": [],
            "completed_at_utc": utc_now(),
        }

    def _handle_build_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, series_id, moment_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
        detail_uid = normalize_detail_uid_value(body.get("detail_uid")) if body.get("detail_uid") else ""
        media_only = bool(body.get("media_only"))
        if work_id:
            scope = build_scope_for_work(
                self.server.source_dir,
                work_id,
                extra_series_ids=extra_series_ids,
                detail_uid=detail_uid,
            )
        elif series_id:
            scope = build_scope_for_series(self.server.source_dir, series_id, extra_work_ids=extra_work_ids)
        else:
            scope = build_scope_for_moment(self.server.repo_root, f"{moment_id}.md", force=force)
        scope["media_only"] = media_only
        scope["local_media"] = build_local_media_plan(self.server.repo_root, scope=scope, force=force)
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "work_id": work_id,
                "series_id": series_id,
                "moment_id": moment_id,
                "detail_uid": detail_uid,
                "force": force,
                "media_only": media_only,
                "build": scope,
            },
            allowed,
        )

    def _handle_build_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, series_id, moment_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
        detail_uid = normalize_detail_uid_value(body.get("detail_uid")) if body.get("detail_uid") else ""
        media_only = bool(body.get("media_only"))
        success, payload = self._run_build_operation(
            work_id=work_id,
            series_id=series_id,
            moment_id=moment_id,
            extra_series_ids=extra_series_ids,
            extra_work_ids=extra_work_ids,
            detail_uid=detail_uid,
            force=force,
            media_only=media_only,
        )
        self._send_json(HTTPStatus.OK if success else HTTPStatus.INTERNAL_SERVER_ERROR, payload, allowed)

    def _handle_moment_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        moment_id = normalize_moment_id_value(body.get("moment_id") or body.get("moment_file"))
        moments_payload = load_moments_payload(self.server.moments_path)
        current_record = moments_payload["moments"].get(moment_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"moment_id not found: {moment_id}")
        normalized_record = normalize_moment_metadata_record(moment_id, current_record)
        preview = preview_moment_source(self.server.repo_root, f"{moment_id}.md", metadata=normalized_record)
        payload: Dict[str, Any] = {
            "ok": True,
            "moment_id": moment_id,
            "record": normalized_record,
            "record_hash": record_hash(normalized_record),
            "preview": preview,
            "readiness": build_moment_readiness(self.server.repo_root, f"{moment_id}.md", metadata=normalized_record),
        }
        if preview.get("valid"):
            scope = build_scope_for_moment(self.server.repo_root, f"{moment_id}.md", metadata=normalized_record)
            scope["local_media"] = build_local_media_plan(self.server.repo_root, scope=scope)
            payload["build"] = scope
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _handle_moment_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_apply_build = extract_apply_build(body)
        requested_moment_id = body.get("moment_id")
        moment_update = extract_moment_update(body)
        if requested_moment_id is None:
            requested_moment_id = moment_update.get("moment_id")
        moment_id = normalize_moment_id_value(requested_moment_id)

        moments_payload = load_moments_payload(self.server.moments_path)
        moments = moments_payload["moments"]
        current_record = moments.get(moment_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"moment_id not found: {moment_id}")

        expected_hash = str(body.get("expected_record_hash") or "").strip()
        normalized_current = normalize_moment_metadata_record(moment_id, current_record)
        current_hash = record_hash(normalized_current)
        if expected_hash and expected_hash != current_hash:
            self._send_json(
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "error": "record changed since loaded",
                    "moment_id": moment_id,
                    "current_record_hash": current_hash,
                },
                allowed,
            )
            return

        updated_record = normalize_moment_update(moment_id, normalized_current, moment_update)
        fields_changed = changed_fields(normalized_current, updated_record)
        validation_errors = validate_updated_moment_record(moment_id, updated_record)
        if validation_errors:
            raise ValueError("moment source validation failed: " + "; ".join(validation_errors[:20]))

        changed = bool(fields_changed)
        apply_build = requested_apply_build and normalize_status(updated_record.get("status")) == "published"
        backup_paths: list[Path] = []
        if changed:
            updated_moments = dict(moments)
            updated_moments[moment_id] = updated_record
            target_path = self.server.moments_path.resolve()
            if target_path not in self.server.allowed_write_paths:
                raise ValueError("write target not allowlisted")
            if not self.server.dry_run:
                backup_paths = atomic_write_many({target_path: moment_metadata_payload(updated_moments)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "moment_id": moment_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record_hash": record_hash(updated_record),
            "record": updated_record,
        }
        if changed:
            invalidation = moment_lookup_invalidation_for_fields(fields_changed)
            response_payload["lookup_refresh"] = {
                "mode": "moment-scoped-build",
                "invalidation_class": invalidation["class"],
                "artifacts": invalidation["artifacts"],
                "unknown_fields": invalidation["unknown_fields"],
            }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_moment_save",
            {
                "moment_id": moment_id,
                "changed": changed,
                "changed_fields": fields_changed,
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            now_utc = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(now_utc, "moment.save"),
                    "time_utc": now_utc,
                    "kind": "source_save",
                    "operation": "moment.save",
                    "status": "completed",
                    "summary": f"Saved moment source metadata for {moment_id}.",
                    "affected": {
                        "works": [],
                        "series": [],
                        "work_details": [],
                        "work_files": [],
                        "work_links": [],
                        "moments": [moment_id],
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "moment_not_published",
                "message": "Public moment update skipped because the saved moment is not published.",
            }
        if apply_build and changed:
            _build_success, build_payload = self._run_build_operation(
                work_id="",
                series_id="",
                moment_id=moment_id,
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid="",
                force=False,
            )
            response_payload["build"] = build_payload
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_prose_import_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        preview = build_prose_import_preview(self.server.repo_root, self.server.source_dir, body)
        self._send_json(HTTPStatus.OK, preview, allowed)

    def _handle_prose_import_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        preview = build_prose_import_preview(self.server.repo_root, self.server.source_dir, body)
        if not preview.get("valid"):
            errors = preview.get("errors") if isinstance(preview.get("errors"), list) else []
            raise ValueError("; ".join(str(error) for error in errors) or "prose import preview failed")
        if preview.get("overwrite_required") and not bool(body.get("confirm_overwrite")):
            self._send_json(
                HTTPStatus.CONFLICT,
                {"ok": False, "error": "overwrite confirmation required", "preview": preview},
                allowed,
            )
            return

        target_kind, target_id, collection = normalize_prose_import_target(body)
        staging_path = self.server.repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / collection / f"{target_id}.md"
        target_path = self.server.repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / collection / f"{target_id}.md"
        target_root = (self.server.repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / collection).resolve()
        if target_root not in self.server.allowed_write_roots:
            raise ValueError("prose source root is not allowlisted")
        ensure_direct_child(target_path, target_root)
        text, errors, _warnings = read_staged_prose_markdown(staging_path)
        if errors:
            raise ValueError("; ".join(errors))

        changed = bool(preview.get("changed"))
        if changed and not self.server.dry_run:
            atomic_write_text_no_backup(target_path, text)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "target_kind": target_kind,
            "target_id": target_id,
            "changed": changed,
            "staging_path": preview.get("staging_path"),
            "target_path": preview.get("target_path"),
            "target_exists": preview.get("target_exists"),
            "content_sha256": preview.get("content_sha256"),
            "warnings": preview.get("warnings", []),
        }
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["imported_at_utc"] = utc_now()
            self.server.append_activity(
                {
                    "id": activity_id(response_payload["imported_at_utc"], "prose.import"),
                    "time_utc": response_payload["imported_at_utc"],
                    "kind": "source_import",
                    "operation": "prose.import",
                    "status": "completed",
                    "summary": f"Imported {target_kind} prose source for {target_id}.",
                    "affected": {
                        "works": [target_id] if target_kind == "work" else [],
                        "series": [target_id] if target_kind == "series" else [],
                        "work_details": [],
                        "work_files": [],
                        "work_links": [],
                        "moments": [target_id] if target_kind == "moment" else [],
                    },
                    "log_ref": str((LOGS_REL_DIR / "catalogue_write_server.log")),
                }
            )
        self.server.log_event(
            "catalogue_prose_import_apply",
            {
                "target_kind": target_kind,
                "target_id": target_id,
                "changed": changed,
                "dry_run": self.server.dry_run,
            },
        )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_moment_import_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        moment_file, metadata, _force = extract_moment_import_request(body)
        preview = preview_moment_source(self.server.repo_root, moment_file, metadata=metadata, staged=True)
        payload: Dict[str, Any] = {
            "ok": True,
            "moment_file": preview.get("moment_file") or moment_file,
            "preview": preview,
            "build": {},
            "steps": [],
            "published": False,
        }
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _handle_moment_import_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        moment_file, metadata, _force = extract_moment_import_request(body)
        preview = preview_moment_source(self.server.repo_root, moment_file, metadata=metadata, staged=True)
        if not preview.get("valid"):
            errors = preview.get("errors") or []
            raise ValueError("; ".join(str(error) for error in errors) or "moment import preview failed")

        moment_filename = normalize_moment_filename(moment_file)
        moment_id_for_write = moment_filename[:-3]
        staging_path = self.server.repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / "moments" / moment_filename
        target_path = self.server.repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR / moment_filename
        target_root = (self.server.repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR).resolve()
        if target_root not in self.server.allowed_write_roots:
            raise ValueError("moment prose source root is not allowlisted")
        ensure_direct_child(target_path, target_root)
        text = staging_path.read_text(encoding="utf-8")
        if has_front_matter_text(text):
            raise ValueError("staged moment prose must be body-only Markdown without front matter")
        if not text.endswith("\n"):
            text += "\n"

        metadata_records = load_moment_metadata_records(self.server.source_dir)
        merged_metadata = normalize_moment_metadata_record(
            moment_id_for_write,
            {**metadata_records.get(moment_id_for_write, {}), **metadata, "moment_id": moment_id_for_write},
        )
        metadata_records[moment_id_for_write] = merged_metadata
        metadata_path = self.server.source_dir / MOMENT_METADATA_FILENAME
        target_payloads: Dict[Path, Dict[str, Any]] = {
            metadata_path: moment_metadata_payload(metadata_records),
        }
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            atomic_write_text_no_backup(target_path, text)
            backup_paths = atomic_write_many(target_payloads, self.server.backups_dir)

        moment_id = str(preview.get("moment_id") or moment_id_for_write).strip().lower()
        payload: Dict[str, Any] = {
            "ok": True,
            "moment_file": preview.get("moment_file") or moment_file,
            "moment_id": moment_id,
            "status": "draft",
            "published": False,
            "preview": preview,
            "build": {},
            "steps": [],
            "public_url": "",
            "metadata_path": str(preview.get("metadata_path") or ""),
            "target_path": str(preview.get("target_path") or ""),
        }
        if self.server.dry_run:
            payload["dry_run"] = True
        if backup_paths:
            payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
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

    def _handle_project_state_report(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        include_subfolders = bool(body.get("include_subfolders"))
        projects_base_dir = resolve_projects_base_dir()
        result = build_project_state_report(
            repo_root=self.server.repo_root,
            projects_base_dir=projects_base_dir,
            output_path=self.server.repo_root / DEFAULT_OUTPUT_REL_PATH,
            write=not self.server.dry_run,
            include_subfolders=include_subfolders,
        )
        payload = {
            "ok": True,
            "generated_at_utc": result["generated_at_utc"],
            "output_path": result["output_path"],
            "projects_root": result["projects_root_display"],
            "catalogue_source_path": result["catalogue_source_path"],
            "include_subfolders": result["include_subfolders"],
            "summary": result["summary"],
            "written": result["written"],
            "dry_run": self.server.dry_run,
        }
        self.server.log_event(
            "project_state_report",
            {
                "output_path": result["output_path"],
                "written": result["written"],
                "dry_run": self.server.dry_run,
                "include_subfolders": result["include_subfolders"],
                "projects_base_env": PROJECTS_BASE_DIR_ENV_NAME,
                "summary": result["summary"],
            },
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

    def _refresh_lookup_payload_for_work(self, work_id: str) -> Dict[str, Any]:
        source_records = records_from_json_source(self.server.source_dir)
        payload = build_work_lookup_payload(source_records, work_id)
        written_path = write_work_lookup_payload(self.server.lookup_dir, work_id, payload)
        result = {
            "mode": "single-record",
            "artifacts": ["work_record"],
            "written_count": 1,
            "written_paths": [self.server.rel_path(written_path)],
        }
        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "work_id": work_id,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads_for_work_change(
        self,
        work_id: str,
        fields_changed: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation = work_lookup_invalidation_for_fields(fields_changed)
        locked_fields = locked_first_pass_work_fields()
        artifacts = list(invalidation["artifacts"])
        use_single_record_lookup_refresh = (
            invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD
            and set(fields_changed).issubset(locked_fields)
        )
        if use_single_record_lookup_refresh:
            result = self._refresh_lookup_payload_for_work(work_id)
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation["unknown_fields"]
            return result

        if invalidation["class"] != LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation["unknown_fields"]
            return result

        source_records = records_from_json_source(self.server.source_dir)
        written_paths: list[str] = []

        if "work_record" in artifacts:
            written_paths.append(
                self.server.rel_path(
                    write_work_lookup_payload(
                        self.server.lookup_dir,
                        work_id,
                        build_work_lookup_payload(source_records, work_id),
                    )
                )
            )

        if "work_search" in artifacts:
            written_paths.append(
                self.server.rel_path(
                    write_lookup_root_payload(
                        self.server.lookup_dir,
                        "work_search.json",
                        build_work_search_payload(source_records),
                    )
                )
            )

        if "related_series_records" in artifacts:
            related_series_ids = set(normalize_series_ids_value(current_record.get("series_ids")))
            related_series_ids.update(normalize_series_ids_value(updated_record.get("series_ids")))
            for series_id in sorted(related_series_ids):
                written_paths.append(
                    self.server.rel_path(
                        write_series_lookup_payload(
                            self.server.lookup_dir,
                            series_id,
                            build_series_lookup_payload(source_records, series_id),
                        )
                    )
                )

        if "related_work_detail_records" in artifacts:
            for detail_uid, detail_record in source_records.work_details.items():
                if normalize_text(detail_record.get("work_id")) != work_id:
                    continue
                written_paths.append(
                    self.server.rel_path(
                        write_detail_lookup_payload(
                            self.server.lookup_dir,
                            detail_uid,
                            build_work_detail_lookup_payload(source_records, detail_uid),
                        )
                    )
                )

        if "related_work_file_records" in artifacts:
            for file_uid, file_record in source_records.work_files.items():
                if normalize_text(file_record.get("work_id")) != work_id:
                    continue
                written_paths.append(
                    self.server.rel_path(
                        write_work_file_lookup_payload(
                            self.server.lookup_dir,
                            file_uid,
                            build_work_file_lookup_payload(source_records, file_uid),
                        )
                    )
                )

        if "related_work_link_records" in artifacts:
            for link_uid, link_record in source_records.work_links.items():
                if normalize_text(link_record.get("work_id")) != work_id:
                    continue
                written_paths.append(
                    self.server.rel_path(
                        write_work_link_lookup_payload(
                            self.server.lookup_dir,
                            link_uid,
                            build_work_link_lookup_payload(source_records, link_uid),
                        )
                    )
                )

        result = {
            "mode": "targeted-multi-record",
            "artifacts": sorted(artifacts),
            "written_count": len(written_paths),
            "written_paths": written_paths,
            "invalidation_class": invalidation["class"],
            "unknown_fields": invalidation["unknown_fields"],
        }
        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "work_id": work_id,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads_for_detail_change(
        self,
        detail_uid: str,
        fields_changed: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation = detail_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation["artifacts"])
        if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_path = write_detail_lookup_payload(
                self.server.lookup_dir,
                detail_uid,
                build_work_detail_lookup_payload(source_records, detail_uid),
            )
            result = {
                "mode": "single-record",
                "artifacts": ["work_detail_record"],
                "written_count": 1,
                "written_paths": [self.server.rel_path(written_path)],
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation["unknown_fields"],
            }
        elif invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_paths: list[str] = []
            if "work_detail_record" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_detail_lookup_payload(
                            self.server.lookup_dir,
                            detail_uid,
                            build_work_detail_lookup_payload(source_records, detail_uid),
                        )
                    )
                )
            if "work_detail_search" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_lookup_root_payload(
                            self.server.lookup_dir,
                            "work_detail_search.json",
                            build_work_detail_search_payload(source_records),
                        )
                    )
                )
            if "related_work_records" in artifacts:
                work_id = slug_id(updated_record.get("work_id"))
                written_paths.append(
                    self.server.rel_path(
                        write_work_lookup_payload(
                            self.server.lookup_dir,
                            work_id,
                            build_work_lookup_payload(source_records, work_id),
                        )
                    )
                )
            result = {
                "mode": "targeted-multi-record",
                "artifacts": sorted(artifacts),
                "written_count": len(written_paths),
                "written_paths": written_paths,
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation["unknown_fields"],
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation["unknown_fields"]
            return result

        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "detail_uid": detail_uid,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads_for_work_file_change(
        self,
        file_uid: str,
        fields_changed: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation = work_file_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation["artifacts"])
        if slug_id(current_record.get("work_id")) != slug_id(updated_record.get("work_id")):
            invalidation = {
                "class": LOOKUP_INVALIDATION_FULL,
                "artifacts": ["full_lookup_refresh"],
                "unknown_fields": [],
            }
        if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_path = write_work_file_lookup_payload(
                self.server.lookup_dir,
                file_uid,
                build_work_file_lookup_payload(source_records, file_uid),
            )
            result = {
                "mode": "single-record",
                "artifacts": ["work_file_record"],
                "written_count": 1,
                "written_paths": [self.server.rel_path(written_path)],
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        elif invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_paths: list[str] = []
            if "work_file_record" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_work_file_lookup_payload(
                            self.server.lookup_dir,
                            file_uid,
                            build_work_file_lookup_payload(source_records, file_uid),
                        )
                    )
                )
            if "related_work_records" in artifacts:
                work_id = slug_id(updated_record.get("work_id"))
                written_paths.append(
                    self.server.rel_path(
                        write_work_lookup_payload(
                            self.server.lookup_dir,
                            work_id,
                            build_work_lookup_payload(source_records, work_id),
                        )
                    )
                )
            result = {
                "mode": "targeted-multi-record",
                "artifacts": sorted(artifacts),
                "written_count": len(written_paths),
                "written_paths": written_paths,
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation.get("unknown_fields", [])
            return result

        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "file_uid": file_uid,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads_for_work_link_change(
        self,
        link_uid: str,
        fields_changed: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation = work_link_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation["artifacts"])
        if slug_id(current_record.get("work_id")) != slug_id(updated_record.get("work_id")):
            invalidation = {
                "class": LOOKUP_INVALIDATION_FULL,
                "artifacts": ["full_lookup_refresh"],
                "unknown_fields": [],
            }
        if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_path = write_work_link_lookup_payload(
                self.server.lookup_dir,
                link_uid,
                build_work_link_lookup_payload(source_records, link_uid),
            )
            result = {
                "mode": "single-record",
                "artifacts": ["work_link_record"],
                "written_count": 1,
                "written_paths": [self.server.rel_path(written_path)],
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        elif invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_paths: list[str] = []
            if "work_link_record" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_work_link_lookup_payload(
                            self.server.lookup_dir,
                            link_uid,
                            build_work_link_lookup_payload(source_records, link_uid),
                        )
                    )
                )
            if "related_work_records" in artifacts:
                work_id = slug_id(updated_record.get("work_id"))
                written_paths.append(
                    self.server.rel_path(
                        write_work_lookup_payload(
                            self.server.lookup_dir,
                            work_id,
                            build_work_lookup_payload(source_records, work_id),
                        )
                    )
                )
            result = {
                "mode": "targeted-multi-record",
                "artifacts": sorted(artifacts),
                "written_count": len(written_paths),
                "written_paths": written_paths,
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation.get("unknown_fields", [])
            return result

        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "link_uid": link_uid,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads_for_series_change(
        self,
        series_id: str,
        fields_changed: list[str],
        changed_work_ids: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation = series_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation["artifacts"])
        if changed_work_ids:
            invalidation = {
                "class": LOOKUP_INVALIDATION_FULL,
                "artifacts": ["full_lookup_refresh"],
                "unknown_fields": [],
            }
        if invalidation["class"] == LOOKUP_INVALIDATION_SINGLE_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_path = write_series_lookup_payload(
                self.server.lookup_dir,
                series_id,
                build_series_lookup_payload(source_records, series_id),
            )
            result = {
                "mode": "single-record",
                "artifacts": ["series_record"],
                "written_count": 1,
                "written_paths": [self.server.rel_path(written_path)],
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        elif invalidation["class"] == LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            source_records = records_from_json_source(self.server.source_dir)
            written_paths: list[str] = []
            if "series_record" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_series_lookup_payload(
                            self.server.lookup_dir,
                            series_id,
                            build_series_lookup_payload(source_records, series_id),
                        )
                    )
                )
            if "series_search" in artifacts:
                written_paths.append(
                    self.server.rel_path(
                        write_lookup_root_payload(
                            self.server.lookup_dir,
                            "series_search.json",
                            build_series_search_payload(source_records),
                        )
                    )
                )
            if "related_work_records" in artifacts:
                for work_id, work_record in source_records.works.items():
                    series_ids = normalize_series_ids_value(work_record.get("series_ids"))
                    if series_id not in series_ids:
                        continue
                    written_paths.append(
                        self.server.rel_path(
                            write_work_lookup_payload(
                                self.server.lookup_dir,
                                work_id,
                                build_work_lookup_payload(source_records, work_id),
                            )
                        )
                    )
            result = {
                "mode": "targeted-multi-record",
                "artifacts": sorted(artifacts),
                "written_count": len(written_paths),
                "written_paths": written_paths,
                "invalidation_class": invalidation["class"],
                "unknown_fields": invalidation.get("unknown_fields", []),
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation["class"]
            result["unknown_fields"] = invalidation.get("unknown_fields", [])
            return result

        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "series_id": series_id,
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result

    def _refresh_lookup_payloads(self) -> Dict[str, Any]:
        written = build_and_write_catalogue_lookup(self.server.source_dir, self.server.lookup_dir)
        result = {
            "mode": "full",
            "artifacts": ["full_lookup_refresh"],
            "written_count": len(written),
            "written_paths": [self.server.rel_path(path) for path in written],
        }
        self.server.log_event(
            "catalogue_lookup_refresh",
            {
                "lookup_dir": self.server.rel_path(self.server.lookup_dir),
                "mode": result["mode"],
                "artifacts": result["artifacts"],
                "written_count": result["written_count"],
            },
        )
        return result


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
    moments_path = (source_dir / MOMENT_METADATA_FILENAME).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_paths = {
        (source_dir / filename).resolve()
        for kind, filename in SOURCE_FILES.items()
        if kind != "meta"
    }
    allowed_paths.add((source_dir / MOMENT_METADATA_FILENAME).resolve())
    allowed_write_roots = {
        (repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / "works").resolve(),
        (repo_root / CATALOGUE_PROSE_SOURCE_REL_DIR / "series").resolve(),
        (repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR).resolve(),
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
        moments_path=moments_path,
        allowed_write_paths=allowed_paths,
        allowed_write_roots=allowed_write_roots,
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
