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
from script_logging import append_script_log  # noqa: E402
from series_ids import normalize_series_id, parse_series_ids  # noqa: E402


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")
MAX_BODY_BYTES = 1024 * 1024
WORK_SAVE_PATH = "/catalogue/work/save"
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


def extract_build_request(body: Mapping[str, Any]) -> tuple[str, list[str], bool]:
    work_id = slug_id(body.get("work_id"))
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    force = bool(body.get("force"))
    return work_id, extra_series_ids, force


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


def changed_fields(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[str]:
    return [field for field in WORK_FIELDS if before.get(field) != after.get(field)]


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


def load_works_payload(path: Path) -> Dict[str, Any]:
    payload = load_json_file(path)
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("works source file must include a works object")
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
        allowed_write_paths: set[Path],
        backups_dir: Path,
        dry_run: bool,
    ):
        super().__init__(server_address, handler_cls)
        self.repo_root = repo_root.resolve()
        self.source_dir = source_dir.resolve()
        self.works_path = works_path.resolve()
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
        if self.path not in {WORK_SAVE_PATH, BUILD_PREVIEW_PATH, BUILD_APPLY_PATH}:
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
        work_id, extra_series_ids, force = extract_build_request(body)
        scope = build_scope_for_work(self.server.source_dir, work_id, extra_series_ids=extra_series_ids)
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "work_id": work_id,
                "force": force,
                "build": scope,
            },
            allowed,
        )

    def _handle_build_apply(self, allowed: Optional[str]) -> None:
        body = self._read_json_body()
        work_id, extra_series_ids, force = extract_build_request(body)
        result = run_scoped_build(
            self.server.repo_root,
            source_dir=self.server.source_dir,
            work_id=work_id,
            extra_series_ids=extra_series_ids,
            write=not self.server.dry_run,
            force=force,
            log_activity=not self.server.dry_run,
        )
        payload: Dict[str, Any] = {
            "ok": result.get("status") == "completed",
            "work_id": work_id,
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
                        "summary": f"Scoped rebuild failed for work {work_id}.",
                        "affected": {
                            "works": [work_id],
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
                    "summary": f"Scoped rebuild completed for work {work_id}.",
                    "affected": {
                        "works": [work_id],
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
