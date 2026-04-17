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
  POST /catalogue/work/save
  POST /catalogue/work-detail/save

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
    slug_id,
    sort_record_map,
    validate_source_records,
)
from catalogue_activity import append_catalogue_activity  # noqa: E402
from catalogue_json_build import build_scope_for_work, run_scoped_build  # noqa: E402
from catalogue_json_build import build_scope_for_series, run_series_scoped_build  # noqa: E402
from script_logging import append_script_log  # noqa: E402
from series_ids import normalize_series_id, parse_series_ids  # noqa: E402


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")
MAX_BODY_BYTES = 1024 * 1024
WORK_SAVE_PATH = "/catalogue/work/save"
DETAIL_SAVE_PATH = "/catalogue/work-detail/save"
SERIES_SAVE_PATH = "/catalogue/series/save"
BUILD_PREVIEW_PATH = "/catalogue/build-preview"
BUILD_APPLY_PATH = "/catalogue/build-apply"


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


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in after.keys() if before.get(field) != after.get(field)]


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
        works_path: Path,
        work_details_path: Path,
        series_path: Path,
        allowed_write_paths: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.source_dir = source_dir.resolve()
        self.works_path = works_path.resolve()
        self.work_details_path = work_details_path.resolve()
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
        if self.path not in {WORK_SAVE_PATH, DETAIL_SAVE_PATH, SERIES_SAVE_PATH, BUILD_PREVIEW_PATH, BUILD_APPLY_PATH}:
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
            if self.path == WORK_SAVE_PATH:
                self._handle_work_save(allowed)
                return
            if self.path == DETAIL_SAVE_PATH:
                self._handle_work_detail_save(allowed)
                return
            if self.path == SERIES_SAVE_PATH:
                self._handle_series_save(allowed)
                return
            if self.path == BUILD_PREVIEW_PATH:
                self._handle_build_preview(allowed)
                return
            if self.path == BUILD_APPLY_PATH:
                self._handle_build_apply(allowed)
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
                        "affected": {"works": [], "series": [], "work_details": []},
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
    works_path = (source_dir / SOURCE_FILES["works"]).resolve()
    work_details_path = (source_dir / SOURCE_FILES["work_details"]).resolve()
    series_path = (source_dir / SOURCE_FILES["series"]).resolve()
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
        works_path=works_path,
        work_details_path=work_details_path,
        series_path=series_path,
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
