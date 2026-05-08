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
  GET /catalogue/read?key=<studio_config_data_key>[&record_id=<id>]

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only http://localhost:* and http://127.0.0.1:*.
  - Writes only allowlisted canonical catalogue source files.
  - Creates backups under var/studio/catalogue/backups/.
  - Writes minimal local logs under var/studio/catalogue/logs/.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional
from urllib.parse import parse_qs, urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from catalogue_source import (  # noqa: E402
    DEFAULT_SOURCE_DIR,
    DETAIL_FIELDS,
    DETAIL_TEXT_FIELDS,
    SERIES_FIELDS,
    SERIES_TEXT_FIELDS,
    SOURCE_FILES,
    WORK_FIELDS,
    WORK_TEXT_FIELDS,
    CatalogueSourceRecords,
    load_json_file,
    next_detail_section_id,
    normalize_detail_uid_value,
    normalize_source_record,
    normalize_status,
    normalize_series_ids_value,
    normalize_text,
    payload_for_map,
    records_from_json_source,
    slug_id,
    sort_record_map,
    validate_source_records,
    validate_work_detail_media_section_record,
    validate_work_detail_section_metadata_consistency,
)
from studio_activity import append_studio_activity  # noqa: E402
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
import catalogue_invalidation as invalidation  # noqa: E402
from catalogue_json_build import (  # noqa: E402
    build_search_command,
    build_local_media_plan,
    build_moment_readiness,
    build_field_plan_for_scope,
    build_scope_for_moment,
    build_scope_for_series,
    build_scope_for_work,
    preview_moment_source,
    run_scoped_build_scope,
)
from catalogue_field_registry import (  # noqa: E402
    apply_field_build_plan_to_scope,
    field_aware_build_plan,
    full_fallback_build_plan,
    load_catalogue_field_registry,
)
from moment_sources import (  # noqa: E402
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
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
from series_ids import normalize_series_id  # noqa: E402
import catalogue_activity as activity  # noqa: E402
import catalogue_cleanup  # noqa: E402
import catalogue_routes as routes  # noqa: E402
import catalogue_transactions as transactions  # noqa: E402


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")
CATALOGUE_PROSE_STAGING_REL_DIR = Path("var/docs/catalogue/import-staging")
CATALOGUE_PROSE_SOURCE_REL_DIR = Path("_docs_src_catalogue")
STUDIO_ACTIVITY_FEED_REL_PATH = Path("assets/studio/data/activity_log.json")
MAX_BODY_BYTES = 1024 * 1024
MAX_PROSE_MARKDOWN_BYTES = 1024 * 1024

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
    "notes",
    "provenance",
    "artist",
}

BULK_DETAIL_EDITABLE_FIELDS = {
    "details_subfolder",
    "section_title",
    "sort_order",
    "project_filename",
    "title",
    "status",
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


def load_activity_feed(repo_root: Path, rel_path: Path, schema: str) -> Dict[str, Any]:
    path = repo_root / rel_path
    if not path.exists():
        return {"header": {"schema": schema, "count": 0}, "entries": []}
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        raise ValueError(f"activity feed must be a JSON object: {rel_path}")
    if not isinstance(payload.get("entries"), list):
        payload = dict(payload)
        payload["entries"] = []
    return payload


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
        "set_fields": set_fields,
        "series_operation": series_operation,
    }


def extract_apply_build(body: Mapping[str, Any]) -> bool:
    return bool(body.get("apply_build"))


def extract_changed_field_names(body: Mapping[str, Any]) -> list[str]:
    raw = body.get("changed_fields")
    if raw is None:
        raw = body.get("fields")
    if raw is None:
        return []
    raw_values = raw if isinstance(raw, list) else [raw]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        for part in str(value or "").split(","):
            field = part.strip()
            if not field or field in seen:
                continue
            seen.add(field)
            out.append(field)
    return out


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
    return {
        "kind": kind,
        "id": record_id,
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
        unknown = sorted(str(key) for key in raw.keys() if str(key) not in {"work_id", "series_ids"})
        if unknown:
            raise ValueError(f"work_updates entry contains unsupported fields: {', '.join(unknown)}")
        work_id = slug_id(raw.get("work_id"))
        series_ids = normalize_series_ids_value(raw.get("series_ids"))
        updates.append(
            {
                "work_id": work_id,
                "series_ids": series_ids,
            }
        )
    return updates


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
    errors: list[str] = []
    source_records = records_from_json_source(source_dir)
    if work_updates:
        for work_id, work_record in work_updates.items():
            source_records.works[work_id] = work_record
    if detail_updates:
        for detail_uid, detail_record in detail_updates.items():
            errors.extend(validate_work_detail_media_section_record(detail_uid, detail_record))
            source_records.work_details[detail_uid] = detail_record
        errors.extend(validate_work_detail_section_metadata_consistency(source_records.work_details))
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    errors.extend(validate_source_records(normalized_records))
    return sorted(dict.fromkeys(errors))


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
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "work", work_id, affected) if repo_root is not None else {}
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
        "summary": f"Delete work {work_id}, {len(dependent_detail_ids)} detail record(s), and remove {cleanup_count} generated/media file(s).",
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
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "work_detail", detail_uid, affected) if repo_root is not None else {}
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
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "series", series_id, affected) if repo_root is not None else {}
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
    cleanup = catalogue_cleanup.moment_delete_preview_cleanup(repo_root, moment_id) if repo_root is not None else {}
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
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(updated_works),
        work_details=sort_record_map(updated_work_details),
        series=sort_record_map(updated_series),
    )
    return validate_source_records(normalized_records)


def validate_work_detail_delete_records(source_dir: Path, detail_uid: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_details.pop(detail_uid, None)
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
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
            cleanup = catalogue_cleanup.moment_delete_preview_cleanup(repo_root, record_id)
        else:
            cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, kind, record_id, affected)
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
    )
    return validate_source_records(normalized_records)


def validate_created_work_records(source_dir: Path, work_id: str, work_record: Dict[str, Any]) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.works[work_id] = work_record
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=source_records.series,
    )
    return validate_source_records(normalized_records)


def validate_updated_detail_records(source_dir: Path, detail_uid: str, detail_record: Dict[str, Any]) -> list[str]:
    errors = validate_work_detail_media_section_record(detail_uid, detail_record)
    source_records = records_from_json_source(source_dir)
    source_records.work_details[detail_uid] = detail_record
    errors.extend(validate_work_detail_section_metadata_consistency(source_records.work_details))
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    errors.extend(validate_source_records(normalized_records))
    return sorted(dict.fromkeys(errors))


def validate_created_detail_records(source_dir: Path, detail_uid: str, detail_record: Dict[str, Any]) -> list[str]:
    errors = validate_work_detail_media_section_record(detail_uid, detail_record)
    source_records = records_from_json_source(source_dir)
    source_records.work_details[detail_uid] = detail_record
    errors.extend(validate_work_detail_section_metadata_consistency(source_records.work_details))
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    errors.extend(validate_source_records(normalized_records))
    return sorted(dict.fromkeys(errors))


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


def load_moments_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    moments = payload.get("moments")
    if not isinstance(moments, dict):
        raise ValueError("moments source file must include a moments object")
    return payload


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
        self.field_registry = load_catalogue_field_registry(self.repo_root)

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

    def append_studio_activity(self, entries: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> None:
        try:
            append_studio_activity(self.repo_root, entries)
        except Exception:
            pass


class Handler(BaseHTTPRequestHandler):
    server: CatalogueWriteServer  # type: ignore[assignment]

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def do_OPTIONS(self) -> None:  # noqa: N802
        request_path = self._request_path()
        if request_path not in {
            routes.BULK_SAVE_PATH,
            routes.DELETE_PREVIEW_PATH,
            routes.DELETE_APPLY_PATH,
            routes.PUBLICATION_PREVIEW_PATH,
            routes.PUBLICATION_APPLY_PATH,
            routes.WORK_CREATE_PATH,
            routes.WORK_SAVE_PATH,
            routes.DETAIL_CREATE_PATH,
            routes.DETAIL_SAVE_PATH,
            routes.WORK_FILE_CREATE_PATH,
            routes.WORK_FILE_SAVE_PATH,
            routes.WORK_FILE_DELETE_PATH,
            routes.WORK_LINK_CREATE_PATH,
            routes.WORK_LINK_SAVE_PATH,
            routes.WORK_LINK_DELETE_PATH,
            routes.CATALOGUE_READ_PATH,
            routes.IMPORT_PREVIEW_PATH,
            routes.IMPORT_APPLY_PATH,
            routes.SERIES_SAVE_PATH,
            routes.SERIES_CREATE_PATH,
            routes.BUILD_PREVIEW_PATH,
            routes.BUILD_APPLY_PATH,
            routes.PROSE_IMPORT_PREVIEW_PATH,
            routes.PROSE_IMPORT_APPLY_PATH,
            routes.MOMENT_IMPORT_PREVIEW_PATH,
            routes.MOMENT_IMPORT_APPLY_PATH,
            routes.MOMENT_PREVIEW_PATH,
            routes.MOMENT_SAVE_PATH,
            routes.PROJECT_STATE_REPORT_PATH,
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

        request_path = self._request_path()
        if request_path == routes.CATALOGUE_READ_PATH:
            try:
                self._handle_catalogue_read(allowed)
            except ValueError as exc:
                self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "validation"})
                self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
            except Exception as exc:  # noqa: BLE001
                self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "internal"})
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)
            return

        if request_path != "/health":
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
                "time_utc": activity.utc_now(),
            },
            allowed,
        )

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        allowed = allowed_origin(origin)
        if origin and not allowed:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin not allowed"})
            return

        request_path = self._request_path()
        try:
            if request_path == routes.WORK_CREATE_PATH:
                self._handle_work_create(allowed)
                return
            if request_path == routes.BULK_SAVE_PATH:
                self._handle_bulk_save(allowed)
                return
            if request_path == routes.DELETE_PREVIEW_PATH:
                self._handle_delete_preview(allowed)
                return
            if request_path == routes.DELETE_APPLY_PATH:
                self._handle_delete_apply(allowed)
                return
            if request_path == routes.PUBLICATION_PREVIEW_PATH:
                self._handle_publication_preview(allowed)
                return
            if request_path == routes.PUBLICATION_APPLY_PATH:
                self._handle_publication_apply(allowed)
                return
            if request_path == routes.WORK_SAVE_PATH:
                self._handle_work_save(allowed)
                return
            if request_path == routes.DETAIL_CREATE_PATH:
                self._handle_work_detail_create(allowed)
                return
            if request_path == routes.DETAIL_SAVE_PATH:
                self._handle_work_detail_save(allowed)
                return
            if request_path == routes.WORK_FILE_CREATE_PATH:
                self._handle_work_file_create(allowed)
                return
            if request_path == routes.WORK_FILE_SAVE_PATH:
                self._handle_work_file_save(allowed)
                return
            if request_path == routes.WORK_FILE_DELETE_PATH:
                self._handle_work_file_delete(allowed)
                return
            if request_path == routes.WORK_LINK_CREATE_PATH:
                self._handle_work_link_create(allowed)
                return
            if request_path == routes.WORK_LINK_SAVE_PATH:
                self._handle_work_link_save(allowed)
                return
            if request_path == routes.WORK_LINK_DELETE_PATH:
                self._handle_work_link_delete(allowed)
                return
            if request_path == routes.IMPORT_PREVIEW_PATH:
                self._handle_import_preview(allowed)
                return
            if request_path == routes.IMPORT_APPLY_PATH:
                self._handle_import_apply(allowed)
                return
            if request_path == routes.SERIES_SAVE_PATH:
                self._handle_series_save(allowed)
                return
            if request_path == routes.SERIES_CREATE_PATH:
                self._handle_series_create(allowed)
                return
            if request_path == routes.BUILD_PREVIEW_PATH:
                self._handle_build_preview(allowed)
                return
            if request_path == routes.BUILD_APPLY_PATH:
                self._handle_build_apply(allowed)
                return
            if request_path == routes.PROSE_IMPORT_PREVIEW_PATH:
                self._handle_prose_import_preview(allowed)
                return
            if request_path == routes.PROSE_IMPORT_APPLY_PATH:
                self._handle_prose_import_apply(allowed)
                return
            if request_path == routes.MOMENT_IMPORT_PREVIEW_PATH:
                self._handle_moment_import_preview(allowed)
                return
            if request_path == routes.MOMENT_IMPORT_APPLY_PATH:
                self._handle_moment_import_apply(allowed)
                return
            if request_path == routes.MOMENT_PREVIEW_PATH:
                self._handle_moment_preview(allowed)
                return
            if request_path == routes.MOMENT_SAVE_PATH:
                self._handle_moment_save(allowed)
                return
            if request_path == routes.PROJECT_STATE_REPORT_PATH:
                self._handle_project_state_report(allowed)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"}, allowed)
        except ValueError as exc:
            self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "validation"})
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)}, allowed)
        except Exception as exc:  # noqa: BLE001
            self.server.log_event("request_error", {"path": request_path, "error": str(exc), "kind": "internal"})
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"internal error: {exc}"}, allowed)

    def _handle_catalogue_read(self, allowed: Optional[str]) -> None:
        query = parse_qs(urlparse(self.path).query)
        key = str((query.get("key") or [""])[0] or "").strip()
        record_id = str((query.get("record_id") or [""])[0] or "").strip()
        payload = self._catalogue_read_payload(key, record_id)
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _catalogue_read_payload(self, key: str, record_id: str = "") -> Dict[str, Any]:
        if key == "activity_log":
            return load_activity_feed(self.server.repo_root, STUDIO_ACTIVITY_FEED_REL_PATH, "studio_activity_log_v1")

        if key == "catalogue_works":
            return load_works_payload(self.server.works_path)
        if key == "catalogue_work_details":
            return load_work_details_payload(self.server.work_details_path)
        if key == "catalogue_series":
            return load_series_payload(self.server.series_path)
        if key == "catalogue_moments":
            return load_moments_payload(self.server.moments_path)

        if key in {
            "catalogue_lookup_work_search",
            "catalogue_lookup_series_search",
            "catalogue_lookup_work_detail_search",
            "catalogue_lookup_work_base",
            "catalogue_lookup_work_detail_base",
            "catalogue_lookup_series_base",
        }:
            source_records = records_from_json_source(self.server.source_dir)
            if key == "catalogue_lookup_work_search":
                return build_work_search_payload(source_records)
            if key == "catalogue_lookup_series_search":
                return build_series_search_payload(source_records)
            if key == "catalogue_lookup_work_detail_search":
                return build_work_detail_search_payload(source_records)
            if key == "catalogue_lookup_work_base":
                work_id = slug_id(record_id)
                if not work_id:
                    raise ValueError("record_id is required for work lookup reads")
                return build_work_lookup_payload(source_records, work_id)
            if key == "catalogue_lookup_work_detail_base":
                detail_uid = normalize_detail_uid_value(record_id)
                if not detail_uid:
                    raise ValueError("record_id is required for work detail lookup reads")
                return build_work_detail_lookup_payload(source_records, detail_uid)
            if key == "catalogue_lookup_series_base":
                series_id = normalize_series_id(record_id)
                if not series_id:
                    raise ValueError("record_id is required for series lookup reads")
                return build_series_lookup_payload(source_records, series_id)

        raise ValueError(f"unsupported catalogue read key: {key}")

    def _handle_work_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_apply_build = extract_apply_build(body)
        requested_work_id = body.get("work_id")
        work_update = extract_work_update(body)
        if requested_work_id is None:
            requested_work_id = work_update.get("work_id")
        work_id = slug_id(requested_work_id)
        extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_SAVE_WORK,
            record_id=work_id,
        )

        works_payload = load_works_payload(self.server.works_path)
        works = works_payload["works"]
        current_record = works.get(work_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"work_id not found: {work_id}")

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
                backup_paths = transactions.atomic_write_many({target_path: updated_payload}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "work_id": work_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record": updated_record,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        build_plan: Dict[str, Any] = {}
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation_result = invalidation.work_lookup_invalidation_for_fields(fields_changed)
            locked_fields = locked_first_pass_work_fields()
            use_single_record_lookup_refresh = (
                invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD
                and set(fields_changed).issubset(locked_fields)
            )
            lookup_refresh_payload = {
                "mode": "single-record" if use_single_record_lookup_refresh else (
                    "targeted-multi-record" if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else "full"
                ),
                "invalidation_class": invalidation_result["class"],
                "artifacts": invalidation_result["artifacts"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
            build_plan = field_aware_build_plan(
                self.server.field_registry,
                record_family="work",
                operation="metadata_update",
                changed_field_names=fields_changed,
                context={
                    "source_records": records_from_json_source(self.server.source_dir),
                    "current_record": current_record,
                    "updated_record": updated_record,
                },
            )
            response_payload["build_plan"] = build_plan
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = activity.utc_now()
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
                "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
                "activity_page_id": activity_context.get("page_id") if activity_context else "",
                "activity_action_id": activity_context.get("action_id") if activity_context else "",
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
            now_utc = activity.utc_now()
            if activity_context:
                related_series_ids = sorted(
                    {
                        *normalize_series_ids_value(current_record.get("series_ids")),
                        *normalize_series_ids_value(updated_record.get("series_ids")),
                    }
                )
                activity_rows = [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        status="completed",
                        record_groups={"works": [work_id], "series": [], "work_details": [], "moments": []},
                        detail_items=[
                            f"Saved canonical work record {work_id}",
                            f"Changed fields: {', '.join(fields_changed)}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": [work_id], "series": related_series_ids, "work_details": [], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for work {work_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ]
                activity.append_studio_activity_rows(self.server, response_payload, activity_rows)
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "work_not_published",
                "summary": "Work must be published before a public update can run.",
            }
        if apply_build and changed and not build_plan.get("build_required", True):
            response_payload["build_requested"] = False
            response_payload["build_skipped"] = {
                "reason": "no_public_build_artifacts",
                "summary": "Changed fields do not require public build artifacts.",
            }
        if apply_build and changed and build_plan.get("build_required", True):
            previous_series_ids = normalize_series_ids_value(current_record.get("series_ids"))
            next_series_ids = normalize_series_ids_value(updated_record.get("series_ids"))
            removed_series_ids = [series_id for series_id in previous_series_ids if series_id not in next_series_ids]
            _build_success, build_payload = self._run_build_operation(
                work_id=work_id,
                series_id="",
                extra_series_ids=normalize_series_ids_value([*extra_series_ids, *removed_series_ids]),
                extra_work_ids=[],
                detail_uid="",
                force=False,
                build_plan=build_plan,
            )
            response_payload["build"] = build_payload
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    activity.catalogue_build_studio_activity_rows(
                        activity.ACTIVITY_PROFILE_SAVE_WORK,
                        activity_context,
                        build_payload,
                        published_detail=f"Updated published work JSON for {work_id}",
                        search_detail=f"Rebuilt catalogue search for work {work_id}",
                        fallback_record_groups={"works": [work_id], "series": [], "work_details": [], "moments": []},
                    ),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_bulk_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        apply_build = extract_apply_build(body)
        request = extract_bulk_save_request(body)
        kind = request["kind"]
        selected_ids: list[str] = request["ids"]
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
                    backup_paths = transactions.atomic_write_many({target_path: payload_for_map("works", updated_works)}, self.server.backups_dir)

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
                response_payload["saved_at_utc"] = activity.utc_now()
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
                backup_paths = transactions.atomic_write_many({target_path: payload_for_map("work_details", updated_details)}, self.server.backups_dir)

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
            response_payload["saved_at_utc"] = activity.utc_now()
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
        generated_backup_root = self.server.backups_dir / f"catalogue-public-update-{kind.replace('_', '-')}-{transactions.backup_stamp_now()}"
        affected = publication_affected_for_record(self.server.source_dir, kind, record_id)
        if kind == "moment":
            cleanup = catalogue_cleanup.collect_moment_delete_cleanup(self.server.repo_root, record_id)
            backup_candidates = [
                *cleanup["delete_paths"],
                self.server.repo_root / "assets" / "data" / "moments_index.json",
                self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json",
            ]
        else:
            cleanup = catalogue_cleanup.collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, affected)
            backup_candidates = [
                *cleanup["delete_paths"],
                *cleanup["public_json_updates"],
                *cleanup["studio_json_updates"],
                self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json",
            ]
        generated_backups = transactions.backup_transaction_paths(backup_candidates, generated_backup_root, self.server.repo_root)
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
            cleanup = catalogue_cleanup.collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, affected)
            generated_payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, affected)
            cleanup_result = self._apply_catalogue_delete_transaction(
                backup_label=f"catalogue-unpublish-{kind.replace('_', '-')}",
                payloads={source_path: source_payload, **generated_payloads},
                cleanup=cleanup,
            )
            cleanup_result.pop("backup_paths", None)
            return cleanup_result

        cleanup = catalogue_cleanup.collect_moment_delete_cleanup(self.server.repo_root, record_id)
        catalogue_cleanup.ensure_moment_delete_cleanup_scope(self.server.repo_root, cleanup)
        moments_index_path = (self.server.repo_root / "assets" / "data" / "moments_index.json").resolve()
        search_index_path = (self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
        deleted_file_count = 0
        search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
        transaction_backup_root: Path | None = None
        if not self.server.dry_run:
            transaction_backup_root = self.server.backups_dir / f"catalogue-unpublish-moment-{transactions.backup_stamp_now()}"
            touched_paths = transactions.unique_paths([source_path, moments_index_path, search_index_path, *cleanup["delete_paths"]])
            transaction_backups = transactions.backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
            try:
                payloads: Dict[Path, Dict[str, Any]] = {source_path: source_payload}
                if moments_index_path.exists():
                    moments_index_payload = load_json_file(moments_index_path)
                    moments_map = moments_index_payload.get("moments")
                    if not isinstance(moments_map, dict):
                        raise ValueError("moments_index.json must include a moments object")
                    moments_map.pop(record_id, None)
                    payloads[moments_index_path] = catalogue_cleanup.finalize_moments_index_payload(moments_index_payload)
                transactions.atomic_write_many(payloads, self.server.backups_dir)
                deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup["delete_paths"])
                search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
            except Exception:
                transactions.restore_transaction_paths(touched_paths, transaction_backups)
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

        kind = str(request["kind"])
        action = str(request["action"])
        record_id = str(request["id"])
        activity_profile = activity.activity_profile_for_publication(kind, action) if action in {"publish", "unpublish"} else None
        activity_context = (
            activity.normalize_activity_context_for_profile(
                body.get("activity_context"),
                activity_profile,
                record_id=record_id,
            )
            if activity_profile is not None
            else {}
        )
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
                    source_backups = transactions.atomic_write_many(source_payloads, self.server.backups_dir)
                    if kind != "moment":
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
            "preview": preview,
            "source_saved": bool(source_changed and not self.server.dry_run) or bool(action == "unpublish" and not self.server.dry_run),
            "public_update": public_update,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = source_changed or action == "unpublish"
        elif source_backups:
            response_payload["backups"] = [self.server.rel_path(path) for path in source_backups]
        if not self.server.dry_run:
            now_utc = activity.utc_now()
            if activity_context and activity_profile is not None:
                record_groups = activity.activity_record_groups_from_affected(preview.get("affected"))
                activity_rows: list[Dict[str, Any]] = []
                if response_payload["source_saved"]:
                    activity_rows.extend(
                        activity.catalogue_source_write_activity_rows(
                            activity_profile,
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="save-canonical-data",
                            record_groups=record_groups,
                            detail_items=[
                                f"{action.replace('_', ' ').title()} {kind.replace('_', ' ')} {record_id}",
                                f"Changed fields: {', '.join(preview.get('changed_fields') or [])}",
                            ],
                        )
                    )
                if activity_profile.lookup_script_purpose_id and response_payload["source_saved"]:
                    activity_rows.append(
                        activity.catalogue_lookup_activity_row(
                            activity_context,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[f"Refreshed catalogue lookup data after {action.replace('_', ' ')} {kind.replace('_', ' ')} {record_id}"],
                        )
                    )
                if action == "publish":
                    activity_rows.extend(
                        activity.catalogue_build_studio_activity_rows(
                            activity_profile,
                            activity_context,
                            public_update,
                            published_detail=f"Updated published {kind.replace('_', ' ')} data for {record_id}",
                            search_detail=f"Rebuilt catalogue search for {kind.replace('_', ' ')} {record_id}",
                            fallback_record_groups=record_groups,
                        )
                    )
                elif action == "unpublish":
                    activity_rows.extend(
                        activity.catalogue_cleanup_activity_rows(
                            activity_context,
                            public_update,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[
                                f"Cleaned generated artifacts for {kind.replace('_', ' ')} {record_id}",
                                f"Deleted {public_update.get('deleted_files', 0)} generated/local file(s)",
                                f"Updated {public_update.get('updated_json_files', 0)} generated JSON file(s)",
                            ],
                        )
                    )
                activity.append_studio_activity_rows(self.server, response_payload, activity_rows)
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
            if any(catalogue_cleanup.path_is_under(resolved, root) for root in generated_roots):
                continue
            raise ValueError("write target not allowlisted")

    def _apply_catalogue_delete_transaction(
        self,
        *,
        backup_label: str,
        payloads: Dict[Path, Dict[str, Any]],
        cleanup: Mapping[str, Any],
    ) -> Dict[str, Any]:
        catalogue_cleanup.ensure_catalogue_delete_cleanup_scope(self.server.repo_root, cleanup)
        self._ensure_delete_payload_scope(payloads)
        search_index_path = (self.server.repo_root / "assets" / "data" / "search" / "catalogue" / "index.json").resolve()
        rebuild_search = bool(cleanup.get("catalogue_search"))
        transaction_backup_root: Path | None = None
        deleted_file_count = 0
        search_rebuild: Dict[str, Any] = {"ok": True, "exit_code": 0}
        transaction_backups: Dict[Path, Path] = {}
        backup_paths: list[Path] = []

        if not self.server.dry_run:
            transaction_backup_root = self.server.backups_dir / f"{backup_label}-{transactions.backup_stamp_now()}"
            touched_paths = transactions.unique_paths(
                [
                    *payloads.keys(),
                    *(cleanup.get("delete_paths") or []),
                    *([search_index_path] if rebuild_search else []),
                ]
            )
            transaction_backups = transactions.backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
            try:
                backup_paths = transactions.atomic_write_many(payloads, self.server.backups_dir)
                backup_paths.extend(transaction_backups.values())
                deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup.get("delete_paths") or [])
                if rebuild_search:
                    search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
                self._refresh_lookup_payloads()
            except Exception:
                transactions.restore_transaction_paths(touched_paths, transaction_backups)
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
        activity_profile = activity.activity_profile_for_delete(kind)
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity_profile,
            record_id=record_id,
        )
        activity_affected = preview["affected"]

        if kind == "work":
            works_payload = load_works_payload(self.server.works_path)
            details_payload = load_work_details_payload(self.server.work_details_path)
            series_payload = load_series_payload(self.server.series_path)
            current_record = works_payload["works"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"work_id not found: {record_id}")
            updated_works = dict(works_payload["works"])
            del updated_works[record_id]
            updated_details = {
                detail_uid: detail_record
                for detail_uid, detail_record in details_payload["work_details"].items()
                if str(detail_record.get("work_id") or "") != record_id
            }
            updated_series, changed_series_ids = series_records_with_draft_primary_cleared(series_payload["series"], record_id)
            cleanup = catalogue_cleanup.collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
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
            activity_affected = {
                **preview["affected"],
                "series": sorted(set([*preview["affected"].get("series", []), *changed_series_ids])),
            }
        elif kind == "work_detail":
            details_payload = load_work_details_payload(self.server.work_details_path)
            current_record = details_payload["work_details"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"detail_uid not found: {record_id}")
            updated_details = dict(details_payload["work_details"])
            del updated_details[record_id]
            cleanup = catalogue_cleanup.collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
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
        elif kind == "series":
            series_payload = load_series_payload(self.server.series_path)
            works_payload = load_works_payload(self.server.works_path)
            current_record = series_payload["series"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"series_id not found: {record_id}")
            updated_series = dict(series_payload["series"])
            del updated_series[record_id]
            updated_works = dict(works_payload["works"])
            for work_id in preview["affected"]["works"]:
                work_record = updated_works.get(work_id)
                if not isinstance(work_record, dict):
                    continue
                next_series_ids = [value for value in normalize_series_ids_value(work_record.get("series_ids")) if value != record_id]
                updated_works[work_id] = normalize_work_update(work_id, work_record, {"series_ids": next_series_ids})
            cleanup = catalogue_cleanup.collect_catalogue_delete_cleanup(self.server.repo_root, kind, record_id, preview["affected"])
            generated_payloads = catalogue_cleanup.build_catalogue_delete_generated_payloads(self.server.repo_root, kind, record_id, preview["affected"])
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
        else:
            moments_payload = load_moments_payload(self.server.moments_path)
            current_record = moments_payload["moments"].get(record_id)
            if not isinstance(current_record, dict):
                raise ValueError(f"moment_id not found: {record_id}")
            normalized_current = normalize_moment_metadata_record(record_id, current_record)
            updated_moments = dict(moments_payload["moments"])
            del updated_moments[record_id]
            cleanup = catalogue_cleanup.collect_moment_delete_cleanup(self.server.repo_root, record_id)
            catalogue_cleanup.ensure_moment_delete_cleanup_scope(self.server.repo_root, cleanup)
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
                transaction_backup_root = self.server.backups_dir / f"catalogue-delete-moment-{transactions.backup_stamp_now()}"
                touched_paths = transactions.unique_paths(
                    [
                        metadata_path,
                        moments_index_path,
                        search_index_path,
                        *cleanup["delete_paths"],
                    ]
                )
                transaction_backups = transactions.backup_transaction_paths(touched_paths, transaction_backup_root, self.server.repo_root)
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
                        payloads[moments_index_path] = catalogue_cleanup.finalize_moments_index_payload(moments_index_payload)
                    backup_paths = transactions.atomic_write_many(payloads, self.server.backups_dir)
                    backup_paths.extend(transaction_backups.values())
                    deleted_file_count = catalogue_cleanup.delete_existing_files(cleanup["delete_paths"])
                    search_rebuild = run_catalogue_search_rebuild(self.server.repo_root, write=True)
                except Exception:
                    transactions.restore_transaction_paths(touched_paths, transaction_backups)
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
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = activity.utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if activity_context:
            response_payload["activity_context"] = activity_context
        if activity_context and not self.server.dry_run:
            now_utc = activity.utc_now()
            cleanup_result = response_payload.get("cleanup") if isinstance(response_payload.get("cleanup"), Mapping) else {}
            updated_json_files = cleanup_result.get("updated_json_files")
            if updated_json_files is None and cleanup_result.get("moments_index_updated"):
                updated_json_files = 1
            record_groups = activity.activity_record_groups_from_affected(activity_affected)
            activity.append_studio_activity_rows(
                self.server,
                response_payload,
                activity.catalogue_delete_activity_rows(
                    activity_profile,
                    activity_context,
                    cleanup_result,
                    now_utc=now_utc,
                    record_groups=record_groups,
                    source_detail_items=[f"Deleted canonical {kind.replace('_', ' ')} source record {record_id}"],
                    cleanup_detail_items=[
                        f"Cleaned generated artifacts for deleted {kind.replace('_', ' ')} {record_id}",
                        f"Deleted {cleanup_result.get('deleted_files', 0)} generated/local file(s)",
                        f"Updated {updated_json_files or 0} generated JSON file(s)",
                    ],
                ),
            )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_work_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_work_id = body.get("work_id")
        work_update = extract_work_update(body)
        if requested_work_id is None:
            requested_work_id = work_update.get("work_id")
        work_id = slug_id(requested_work_id)
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_CREATE_WORK,
            record_id=work_id,
        )

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
            backup_paths = transactions.atomic_write_many({target_path: payload_for_map("works", updated_works)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_work_record, created_record),
            "record": created_record,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = activity.utc_now()
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
            refresh_result = self._refresh_lookup_payloads()
            response_payload["lookup_refresh"] = refresh_result
            now_utc = activity.utc_now()
            if activity_context:
                record_groups = activity.activity_record_groups(works=[work_id])
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    [
                        *activity.catalogue_source_write_activity_rows(
                            activity.ACTIVITY_PROFILE_CREATE_WORK,
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="save-canonical-data",
                            record_groups=record_groups,
                            detail_items=[
                                f"Created canonical draft work record {work_id}",
                                f"Changed fields: {', '.join(response_payload['changed_fields'])}",
                            ],
                        ),
                        activity.catalogue_lookup_activity_row(
                            activity_context,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[
                                f"Refreshed catalogue lookup data after creating work {work_id}",
                                f"Wrote {refresh_result['written_count']} lookup file(s)",
                            ],
                        ),
                    ],
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
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_CREATE_WORK_DETAIL,
            record_id=detail_uid,
        )

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
        if normalize_text(detail_update.get("section_id")):
            raise ValueError("record.section_id is generated by the server")
        if not normalize_text(detail_update.get("section_title")):
            raise ValueError("work detail section_title is required")
        detail_update["section_id"] = next_detail_section_id(work_id, work_details.values())
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
            backup_paths = transactions.atomic_write_many({target_path: payload_for_map("work_details", updated_details)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "detail_uid": detail_uid,
            "work_id": work_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_detail_record, created_record),
            "record": created_record,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = activity.utc_now()
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
            refresh_result = self._refresh_lookup_payloads()
            response_payload["lookup_refresh"] = refresh_result
            now_utc = activity.utc_now()
            if activity_context:
                record_groups = activity.activity_record_groups(works=[work_id], work_details=[detail_uid])
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    [
                        *activity.catalogue_source_write_activity_rows(
                            activity.ACTIVITY_PROFILE_CREATE_WORK_DETAIL,
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="save-canonical-data",
                            record_groups=record_groups,
                            detail_items=[
                                f"Created canonical draft work detail record {detail_uid}",
                                f"Changed fields: {', '.join(response_payload['changed_fields'])}",
                            ],
                        ),
                        activity.catalogue_lookup_activity_row(
                            activity_context,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[
                                f"Refreshed catalogue lookup data after creating work detail {detail_uid}",
                                f"Wrote {refresh_result['written_count']} lookup file(s)",
                            ],
                        ),
                    ],
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
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_SAVE_WORK_DETAIL,
            record_id=detail_uid,
        )

        details_payload = load_work_details_payload(self.server.work_details_path)
        work_details = details_payload["work_details"]
        current_record = work_details.get(detail_uid)
        if not isinstance(current_record, dict):
            raise ValueError(f"detail_uid not found: {detail_uid}")
        current_section_id = normalize_text(current_record.get("section_id"))
        requested_section_id = normalize_text(detail_update.get("section_id"))
        if requested_section_id and current_section_id and requested_section_id != current_section_id:
            raise ValueError("record.section_id is read-only")

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
                backup_paths = transactions.atomic_write_many({target_path: updated_payload}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "detail_uid": detail_uid,
            "work_id": work_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record": updated_record,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        build_plan: Dict[str, Any] = {}
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation_result = invalidation.detail_lookup_invalidation_for_fields(fields_changed)
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation_result["class"],
                "artifacts": invalidation_result["artifacts"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
            build_plan = field_aware_build_plan(
                self.server.field_registry,
                record_family="work_detail",
                operation="metadata_update",
                changed_field_names=fields_changed,
                context={
                    "source_records": source_records,
                    "current_record": current_record,
                    "updated_record": updated_record,
                },
            )
            response_payload["build_plan"] = build_plan
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = activity.utc_now()
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
                "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
                "activity_page_id": activity_context.get("page_id") if activity_context else "",
                "activity_action_id": activity_context.get("action_id") if activity_context else "",
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
            now_utc = activity.utc_now()
            if activity_context:
                activity_rows = [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        status="completed",
                        record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
                        detail_items=[
                            f"Saved canonical work detail record {detail_uid}",
                            f"Changed fields: {', '.join(fields_changed)}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for work detail {detail_uid}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ]
                activity.append_studio_activity_rows(self.server, response_payload, activity_rows)
        response_payload["build_requested"] = bool(apply_build and changed)
        if apply_build and changed and not build_plan.get("build_required", True):
            response_payload["build_requested"] = False
            response_payload["build_skipped"] = {
                "reason": "no_public_build_artifacts",
                "summary": "Changed fields do not require public build artifacts.",
            }
        if apply_build and changed and build_plan.get("build_required", True):
            _build_success, build_payload = self._run_build_operation(
                work_id=work_id,
                series_id="",
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid=detail_uid,
                force=False,
                build_plan=build_plan,
            )
            response_payload["build"] = build_payload
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    activity.catalogue_build_studio_activity_rows(
                        activity.ACTIVITY_PROFILE_SAVE_WORK_DETAIL,
                        activity_context,
                        build_payload,
                        published_detail=f"Updated published parent work JSON for detail {detail_uid}",
                        search_detail=f"Rebuilt catalogue search for work detail {detail_uid}",
                        fallback_record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
                    ),
                )
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

    def _handle_work_file_save(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)

    def _handle_work_file_delete(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)

    def _handle_work_link_create(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)

    def _handle_work_link_save(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)

    def _handle_work_link_delete(self, allowed: Optional[str]) -> None:
        self._send_retired_work_child_metadata_response(allowed)

    def _handle_series_save(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_apply_build = extract_apply_build(body)
        requested_series_id = body.get("series_id")
        series_update = extract_series_update(body)
        if requested_series_id is None:
            requested_series_id = series_update.get("series_id")
        series_id = normalize_series_id(requested_series_id)
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_SAVE_SERIES,
            record_id=series_id,
        )
        work_updates_request = extract_series_work_updates(body)
        extra_work_ids = [slug_id(raw) for raw in body.get("extra_work_ids") or []]

        series_payload = load_series_payload(self.server.series_path)
        series_map = series_payload["series"]
        current_series_record = series_map.get(series_id)
        if not isinstance(current_series_record, dict):
            raise ValueError(f"series_id not found: {series_id}")

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
                backup_paths = transactions.atomic_write_many(target_payloads, self.server.backups_dir)

        for work_id in changed_work_ids:
            response_work_records.append({"work_id": work_id, "record": pending_work_updates[work_id]})

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "changed": changed,
            "changed_fields": series_changed_fields,
            "changed_work_ids": changed_work_ids,
            "record": updated_series_record,
            "work_records": response_work_records,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        build_plan: Dict[str, Any] = {}
        lookup_refresh_payload: Dict[str, Any] = {}
        if changed:
            invalidation_result = invalidation.series_lookup_invalidation_for_fields(series_changed_fields)
            if changed_work_ids:
                invalidation = {
                    "class": invalidation.LOOKUP_INVALIDATION_FULL,
                    "artifacts": ["full_lookup_refresh"],
                    "unknown_fields": [],
                }
            lookup_refresh_payload = {
                "mode": "targeted-multi-record" if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD else (
                    "single-record" if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD else "full"
                ),
                "invalidation_class": invalidation_result["class"],
                "artifacts": invalidation_result["artifacts"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
            response_payload["lookup_refresh"] = lookup_refresh_payload
            if changed_work_ids:
                build_plan = full_fallback_build_plan(
                    self.server.field_registry,
                    fields=[*series_changed_fields, "work.series_ids"],
                    fallback_reason="series_save_changed_member_works",
                    reason="Series save also changed member work records; use conservative fallback until cross-family saves are scoped explicitly.",
                    record_family="series",
                )
            else:
                build_plan = field_aware_build_plan(
                    self.server.field_registry,
                    record_family="series",
                    operation="metadata_update",
                    changed_field_names=series_changed_fields,
                    context={
                        "source_records": records_from_json_source(self.server.source_dir),
                        "current_record": current_series_record,
                        "updated_record": updated_series_record,
                    },
                )
            response_payload["build_plan"] = build_plan
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = activity.utc_now()
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
                "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
                "activity_page_id": activity_context.get("page_id") if activity_context else "",
                "activity_action_id": activity_context.get("action_id") if activity_context else "",
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
            now_utc = activity.utc_now()
            if activity_context:
                canonical_detail_items = [f"Saved canonical series record {series_id}"]
                if series_changed_fields:
                    canonical_detail_items.append(f"Changed series fields: {', '.join(series_changed_fields)}")
                if changed_work_ids:
                    canonical_detail_items.append(f"Saved {len(changed_work_ids)} member work record(s)")
                activity_rows = [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        status="completed",
                        record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
                        detail_items=canonical_detail_items,
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for series {series_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ]
                activity.append_studio_activity_rows(self.server, response_payload, activity_rows)
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "series_not_published",
                "summary": "Series must be published before a public update can run.",
            }
        if apply_build and changed and not build_plan.get("build_required", True):
            response_payload["build_requested"] = False
            response_payload["build_skipped"] = {
                "reason": "no_public_build_artifacts",
                "summary": "Changed fields do not require public build artifacts.",
            }
        if apply_build and changed and build_plan.get("build_required", True):
            _build_success, build_payload = self._run_build_operation(
                work_id="",
                series_id=series_id,
                extra_series_ids=[],
                extra_work_ids=extra_work_ids,
                detail_uid="",
                force=False,
                build_plan=build_plan,
            )
            response_payload["build"] = build_payload
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    activity.catalogue_build_studio_activity_rows(
                        activity.ACTIVITY_PROFILE_SAVE_SERIES,
                        activity_context,
                        build_payload,
                        published_detail=f"Updated published series/work JSON for series {series_id}",
                        search_detail=f"Rebuilt catalogue search for series {series_id}",
                        fallback_record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
                    ),
                )
        self._send_json(HTTPStatus.OK, response_payload, allowed)

    def _handle_series_create(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        requested_series_id = body.get("series_id")
        series_update = extract_series_update(body)
        if requested_series_id is None:
            requested_series_id = series_update.get("series_id")
        series_id = normalize_series_id(requested_series_id)
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_CREATE_SERIES,
            record_id=series_id,
        )
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
            backup_paths = transactions.atomic_write_many(target_payloads, self.server.backups_dir)

        for work_id in changed_work_ids:
            response_work_records.append({"work_id": work_id, "record": pending_work_updates[work_id]})

        response_payload: Dict[str, Any] = {
            "ok": True,
            "series_id": series_id,
            "created": True,
            "changed": True,
            "changed_fields": changed_fields(blank_series_record, created_series_record),
            "changed_work_ids": changed_work_ids,
            "record": created_series_record,
            "work_records": response_work_records,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = True
        else:
            response_payload["saved_at_utc"] = activity.utc_now()
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
            refresh_result = self._refresh_lookup_payloads()
            response_payload["lookup_refresh"] = refresh_result
            now_utc = activity.utc_now()
            if activity_context:
                record_groups = activity.activity_record_groups(works=changed_work_ids, series=[series_id])
                detail_items = [
                    f"Created canonical draft series record {series_id}",
                    f"Changed fields: {', '.join(response_payload['changed_fields'])}",
                ]
                if changed_work_ids:
                    detail_items.append(f"Saved {len(changed_work_ids)} member work record(s)")
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    [
                        *activity.catalogue_source_write_activity_rows(
                            activity.ACTIVITY_PROFILE_CREATE_SERIES,
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="save-canonical-data",
                            record_groups=record_groups,
                            detail_items=detail_items,
                        ),
                        activity.catalogue_lookup_activity_row(
                            activity_context,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[
                                f"Refreshed catalogue lookup data after creating series {series_id}",
                                f"Wrote {refresh_result['written_count']} lookup file(s)",
                            ],
                        ),
                    ],
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
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS,
            record_id=mode,
        )
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
            backup_paths = transactions.atomic_write_many(payloads_by_path, self.server.backups_dir)
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
        if activity_context:
            response_payload["activity_context"] = activity_context
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = activity.utc_now()
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
            now_utc = activity.utc_now()
            if activity_context:
                imported_ids = sorted(plan.importable_records.keys())
                record_groups = activity.activity_record_groups(
                    works=imported_ids if mode == IMPORT_MODE_WORKS else [],
                    work_details=imported_ids if mode == IMPORT_MODE_WORK_DETAILS else [],
                )
                detail_label = "work" if mode == IMPORT_MODE_WORKS else "work detail"
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    [
                        activity.studio_activity_entry(
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="import-source-data",
                            status="completed",
                            record_groups=record_groups,
                            detail_items=[
                                f"Imported {plan.importable_count} {detail_label} record(s) from workbook",
                                f"{plan.duplicate_count} duplicate record(s) already existed",
                                f"Candidate rows reviewed: {plan.total_candidate_rows}",
                            ],
                            source_refs=[
                                {"kind": "source", "path": str(DEFAULT_IMPORT_WORKBOOK_PATH)},
                                *activity.catalogue_log_source_ref(),
                            ],
                        ),
                        activity.catalogue_lookup_activity_row(
                            activity_context,
                            now_utc=now_utc,
                            record_groups=record_groups,
                            detail_items=[f"Refreshed catalogue lookup data after workbook {detail_label} import"],
                        ),
                    ],
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
        build_plan: Optional[Mapping[str, Any]] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        if work_id:
            scope = build_scope_for_work(
                self.server.source_dir,
                work_id,
                extra_series_ids=extra_series_ids,
                detail_uid=detail_uid,
            )
            if build_plan:
                apply_field_build_plan_to_scope(scope, build_plan)
            result = run_scoped_build_scope(
                self.server.repo_root,
                scope=scope,
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
            )
        elif series_id:
            scope = build_scope_for_series(self.server.source_dir, series_id, extra_work_ids=extra_work_ids)
            if build_plan:
                apply_field_build_plan_to_scope(scope, build_plan)
            result = run_scoped_build_scope(
                self.server.repo_root,
                scope=scope,
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
            )
        else:
            scope = build_scope_for_moment(self.server.repo_root, f"{moment_id}.md", force=force)
            if build_plan:
                apply_field_build_plan_to_scope(scope, build_plan)
            result = run_scoped_build_scope(
                self.server.repo_root,
                scope=scope,
                write=not self.server.dry_run,
                force=force,
                media_only=media_only,
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
            "field_plan": dict(build_plan) if build_plan else None,
            "media": result.get("media"),
            "steps": result.get("steps", []),
        }
        if self.server.dry_run:
            payload["dry_run"] = True

        if result.get("status") != "completed":
            payload["error"] = str(result.get("error") or "Scoped JSON build failed.")
            payload["failed_step"] = result.get("failed_step")
            return False, payload

        if not self.server.dry_run:
            payload["completed_at_utc"] = activity.utc_now()
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
            "completed_at_utc": activity.utc_now(),
        }

    def _handle_build_preview(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, series_id, moment_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
        detail_uid = normalize_detail_uid_value(body.get("detail_uid")) if body.get("detail_uid") else ""
        media_only = bool(body.get("media_only"))
        changed_fields = extract_changed_field_names(body)
        record_family = str(body.get("record_family") or body.get("family") or "").strip()
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
        if changed_fields:
            build_plan = build_field_plan_for_scope(
                self.server.repo_root,
                self.server.source_dir,
                scope,
                changed_fields=changed_fields,
                record_family=record_family,
            )
            apply_field_build_plan_to_scope(scope, build_plan)
        scope["media_only"] = media_only
        scope["local_media"] = (
            build_local_media_plan(self.server.repo_root, scope=scope, force=force)
            if bool(scope.get("generate_local_media", True))
            else {"tasks": [], "counts": {"pending": 0, "current": 0, "blocked": 0, "unavailable": 0}}
        )
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
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_SAVE_MOMENT,
            record_id=moment_id,
        )

        moments_payload = load_moments_payload(self.server.moments_path)
        moments = moments_payload["moments"]
        current_record = moments.get(moment_id)
        if not isinstance(current_record, dict):
            raise ValueError(f"moment_id not found: {moment_id}")

        normalized_current = normalize_moment_metadata_record(moment_id, current_record)
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
                backup_paths = transactions.atomic_write_many({target_path: moment_metadata_payload(updated_moments)}, self.server.backups_dir)

        response_payload: Dict[str, Any] = {
            "ok": True,
            "moment_id": moment_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "record": updated_record,
        }
        if activity_context:
            response_payload["activity_context"] = activity_context
        build_plan: Dict[str, Any] = {}
        if changed:
            invalidation_result = invalidation.moment_build_invalidation_for_fields(fields_changed)
            response_payload["moment_build_invalidation"] = {
                "mode": "moment-scoped-build",
                "invalidation_class": invalidation_result["class"],
                "artifacts": invalidation_result["artifacts"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
            build_plan = field_aware_build_plan(
                self.server.field_registry,
                record_family="moment",
                operation="metadata_update",
                changed_field_names=fields_changed,
                context={
                    "current_record": normalized_current,
                    "updated_record": updated_record,
                },
            )
            response_payload["build_plan"] = build_plan
        if self.server.dry_run:
            response_payload["dry_run"] = True
            response_payload["would_write"] = changed
        elif changed:
            response_payload["saved_at_utc"] = activity.utc_now()
            if backup_paths:
                response_payload["backups"] = [self.server.rel_path(path) for path in backup_paths]

        self.server.log_event(
            "catalogue_moment_save",
            {
                "moment_id": moment_id,
                "changed": changed,
                "changed_fields": fields_changed,
                "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
                "activity_page_id": activity_context.get("page_id") if activity_context else "",
                "activity_action_id": activity_context.get("action_id") if activity_context else "",
                "dry_run": self.server.dry_run,
            },
        )
        if changed and not self.server.dry_run:
            now_utc = activity.utc_now()
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    [
                        activity.studio_activity_entry(
                            activity_context,
                            now_utc=now_utc,
                            script_purpose_id="save-canonical-data",
                            status="completed",
                            record_groups={"works": [], "series": [], "work_details": [], "moments": [moment_id]},
                            detail_items=[
                                f"Saved canonical moment record {moment_id}",
                                f"Changed fields: {', '.join(fields_changed)}",
                            ],
                            source_refs=activity.catalogue_log_source_ref(),
                        )
                    ],
                )
        response_payload["build_requested"] = bool(apply_build and changed)
        if requested_apply_build and changed and not apply_build:
            response_payload["build_skipped"] = {
                "reason": "moment_not_published",
                "message": "Public moment update skipped because the saved moment is not published.",
            }
        if apply_build and changed and not build_plan.get("build_required", True):
            response_payload["build_requested"] = False
            response_payload["build_skipped"] = {
                "reason": "no_public_build_artifacts",
                "message": "Changed fields do not require public build artifacts.",
            }
        if apply_build and changed and build_plan.get("build_required", True):
            _build_success, build_payload = self._run_build_operation(
                work_id="",
                series_id="",
                moment_id=moment_id,
                extra_series_ids=[],
                extra_work_ids=[],
                detail_uid="",
                force=False,
                build_plan=build_plan,
            )
            response_payload["build"] = build_payload
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    response_payload,
                    activity.catalogue_build_studio_activity_rows(
                        activity.ACTIVITY_PROFILE_SAVE_MOMENT,
                        activity_context,
                        build_payload,
                        published_detail=f"Updated published moment JSON for {moment_id}",
                        search_detail=f"Rebuilt catalogue search for moment {moment_id}",
                        fallback_record_groups={"works": [], "series": [], "work_details": [], "moments": [moment_id]},
                    ),
                )
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
            response_payload["imported_at_utc"] = activity.utc_now()
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
        moment_id = str(preview.get("moment_id") or moment_id_for_write).strip().lower()
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_IMPORT_MOMENT,
            record_id=moment_id,
        )
        backup_paths: list[Path] = []
        if not self.server.dry_run:
            atomic_write_text_no_backup(target_path, text)
            backup_paths = transactions.atomic_write_many(target_payloads, self.server.backups_dir)

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
        if activity_context:
            payload["activity_context"] = activity_context
        if self.server.dry_run:
            payload["dry_run"] = True
        if backup_paths:
            payload["backups"] = [self.server.rel_path(path) for path in backup_paths]
        if not self.server.dry_run:
            payload["completed_at_utc"] = activity.utc_now()
            if activity_context:
                activity.append_studio_activity_rows(
                    self.server,
                    payload,
                    [
                        activity.studio_activity_entry(
                            activity_context,
                            now_utc=payload["completed_at_utc"],
                            script_purpose_id="import-source-data",
                            status="completed",
                            record_groups=activity.activity_record_groups(moments=[moment_id]),
                            detail_items=[
                                f"Imported draft moment source {moment_id}",
                                f"Wrote body-only moment prose to {self.server.rel_path(target_path)}",
                                f"Saved canonical moment metadata for {moment_id}",
                            ],
                            source_refs=activity.catalogue_log_source_ref(),
                        )
                    ],
                )
        self._send_json(HTTPStatus.OK, payload, allowed)

    def _handle_project_state_report(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        include_subfolders = bool(body.get("include_subfolders"))
        activity_context = activity.normalize_activity_context_for_profile(
            body.get("activity_context"),
            activity.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT,
            record_id="project-state",
        )
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
        if activity_context:
            payload["activity_context"] = activity_context
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
        if activity_context and not self.server.dry_run and result["written"]:
            summary = result["summary"] if isinstance(result.get("summary"), Mapping) else {}
            activity.append_studio_activity_rows(
                self.server,
                payload,
                [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=str(result["generated_at_utc"]),
                        script_purpose_id="generate-report",
                        status="completed",
                        record_groups={
                            "works": [],
                            "series": [],
                            "work_details": [],
                            "moments": [],
                            "files": [str(result["output_path"])],
                        },
                        detail_items=[
                            f"Wrote project-state report to {result['output_path']}",
                            f"Source folders: {int(summary.get('source_folder_count') or 0)}",
                            f"Source images: {int(summary.get('source_image_count') or 0)}",
                            f"Unrepresented folders: {int(summary.get('unrepresented_folder_count') or 0)}",
                            f"Unrepresented images: {int(summary.get('unrepresented_image_count') or 0)}",
                        ],
                        source_refs=[
                            {"kind": "report", "path": str(result["output_path"])},
                            *activity.catalogue_log_source_ref(),
                        ],
                    )
                ],
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
        invalidation_result = invalidation.work_lookup_invalidation_for_fields(fields_changed)
        locked_fields = locked_first_pass_work_fields()
        artifacts = list(invalidation_result["artifacts"])
        use_single_record_lookup_refresh = (
            invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD
            and set(fields_changed).issubset(locked_fields)
        )
        if use_single_record_lookup_refresh:
            result = self._refresh_lookup_payload_for_work(work_id)
            result["invalidation_class"] = invalidation_result["class"]
            result["unknown_fields"] = invalidation_result["unknown_fields"]
            return result

        if invalidation_result["class"] != invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation_result["class"]
            result["unknown_fields"] = invalidation_result["unknown_fields"]
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

        result = {
            "mode": "targeted-multi-record",
            "artifacts": sorted(artifacts),
            "written_count": len(written_paths),
            "written_paths": written_paths,
            "invalidation_class": invalidation_result["class"],
            "unknown_fields": invalidation_result["unknown_fields"],
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
        invalidation_result = invalidation.detail_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation_result["artifacts"])
        if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD:
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
                "invalidation_class": invalidation_result["class"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
        elif invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
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
                "invalidation_class": invalidation_result["class"],
                "unknown_fields": invalidation_result["unknown_fields"],
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation_result["class"]
            result["unknown_fields"] = invalidation_result["unknown_fields"]
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

    def _refresh_lookup_payloads_for_series_change(
        self,
        series_id: str,
        fields_changed: list[str],
        changed_work_ids: list[str],
        current_record: Mapping[str, Any],
        updated_record: Mapping[str, Any],
    ) -> Dict[str, Any]:
        invalidation_result = invalidation.series_lookup_invalidation_for_fields(fields_changed)
        artifacts = list(invalidation_result["artifacts"])
        if changed_work_ids:
            invalidation = {
                "class": invalidation.LOOKUP_INVALIDATION_FULL,
                "artifacts": ["full_lookup_refresh"],
                "unknown_fields": [],
            }
        if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD:
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
                "invalidation_class": invalidation_result["class"],
                "unknown_fields": invalidation_result.get("unknown_fields", []),
            }
        elif invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
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
                "invalidation_class": invalidation_result["class"],
                "unknown_fields": invalidation_result.get("unknown_fields", []),
            }
        else:
            result = self._refresh_lookup_payloads()
            result["invalidation_class"] = invalidation_result["class"]
            result["unknown_fields"] = invalidation_result.get("unknown_fields", [])
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
