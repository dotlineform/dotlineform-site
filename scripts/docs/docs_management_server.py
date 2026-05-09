#!/usr/bin/env python3
"""
Localhost-only write service for shared Docs Viewer source docs.

Run:
  ./scripts/docs/docs_management_server.py
  ./scripts/docs/docs_management_server.py --port 8789
  ./scripts/docs/docs_management_server.py --repo-root /path/to/dotlineform-site
  ./scripts/docs/docs_management_server.py --dry-run

Endpoints:
  GET /health
  GET /capabilities
  GET /docs/import-source-files
  GET /docs/import-html-files
  GET /docs/import/files
  POST /docs/import-source
  POST /docs/import-html
  POST /docs/export
  POST /docs/import/preview
  POST /docs/import/apply
  POST /docs/rebuild
  POST /docs/broken-links
  POST /docs/open-source
  POST /docs/update-metadata
  POST /docs/update-viewability
  POST /docs/update-viewability-bulk
  POST /docs/create
  POST /docs/move
  POST /docs/restore-move
  POST /docs/archive
  POST /docs/delete-preview
  POST /docs/delete-apply

Security constraints:
  - Binds to 127.0.0.1 only.
  - CORS allows only http://localhost:* and http://127.0.0.1:*.
  - Writes only allowlisted Markdown docs under _docs/, _docs_library/, and _docs_analysis/.
  - Writes export artifacts only under the resolved adapter export root.
  - Writes import preview artifacts only under the resolved adapter preview root.
  - Creates timestamped backup bundles under var/docs/backups/.
  - Writes minimal local logs under var/docs/logs/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log  # noqa: E402
from docs_broken_links import audit_docs_broken_links  # noqa: E402
from docs_export import build_export, parse_doc_ids as parse_export_doc_ids  # noqa: E402
from export_import_adapters import AdapterResolution, resolve_adapter  # noqa: E402
import docs_activity  # noqa: E402
import docs_generated_reads  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_import import list_staged_import_files, parse_staged_import, render_markdown_previews  # noqa: E402
from docs_scope_config import SCOPE_ROOTS  # noqa: E402
from local_env import runtime_env  # noqa: E402


MAX_BODY_BYTES = 64 * 1024
BACKUPS_REL_DIR = Path("var/docs/backups")
LOGS_REL_DIR = Path("var/docs/logs")
DEFAULT_MARKDOWN_APP_ENV = "DOCS_MANAGEMENT_DEFAULT_MARKDOWN_APP"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


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


def detect_preferred_markdown_app() -> Optional[str]:
    configured = runtime_env().get(DEFAULT_MARKDOWN_APP_ENV, "").strip()
    if configured:
        return configured

    for app_name in ["MarkEdit", "Typora", "Marked 2", "Marked"]:
        if (Path("/Applications") / f"{app_name}.app").exists():
            return app_name
    return None


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


def normalize_summary(value: Any) -> str:
    return mutations.normalize_summary(value)


def make_backup_bundle(
    repo_root: Path,
    scope: str,
    operation: str,
    docs: list[source_model.ScopeDoc],
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": operation,
        "count": len(docs),
        "files": [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "path": relative_path(repo_root, doc.path),
                "filename": doc.path.name,
            }
            for doc in docs
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    for doc in docs:
        shutil.copy2(doc.path, bundle_dir / doc.path.name)
    return bundle_dir


def make_import_overwrite_backup(
    repo_root: Path,
    scope: str,
    target: source_model.ScopeDoc,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    bundle_name = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}-{scope}-import-overwrite-{source_model.slugify(target.doc_id)}"
    bundle_dir = repo_root / BACKUPS_REL_DIR / bundle_name
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": "import-overwrite",
        "count": 1,
        "files": [
            {
                "doc_id": target.doc_id,
                "title": target.title,
                "path": relative_path(repo_root, target.path),
                "filename": target.path.name,
            }
        ],
    }
    if metadata:
        manifest["metadata"] = metadata
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(target.path, bundle_dir / target.path.name)
    return bundle_dir


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    if scope == "studio":
        return f"/docs/?scope=studio&doc={doc_id}"
    if scope == "analysis":
        return f"/analysis/?doc={doc_id}&mode=manage"
    return f"/library/?doc={doc_id}&mode=manage"


def query_param(handler: BaseHTTPRequestHandler, name: str) -> str:
    parsed = urlparse(handler.path)
    values = parse_qs(parsed.query).get(name, [])
    return str(values[0] if values else "").strip()


def open_source_doc(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    editor = str(body.get("editor") or "default").strip().lower()
    if not doc_id:
        raise ValueError("doc_id is required")
    if editor not in {"default", "vscode"}:
        raise ValueError("editor must be `default` or `vscode`")

    docs = source_model.load_scope_docs(repo_root, scope)
    target = next((doc for doc in docs if doc.doc_id == doc_id), None)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")

    preferred_app = detect_preferred_markdown_app()

    if editor == "vscode":
        command = ["open", "-a", "Visual Studio Code", str(target.path)]
    else:
        if preferred_app:
            command = ["open", "-a", preferred_app, str(target.path)]
        else:
            command = ["open", str(target.path)]

    if not dry_run:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
            raise RuntimeError(f"open source failed: {detail}")
        log_event(
            repo_root,
            "docs-open-source",
            {
                "scope": scope,
                "doc_id": target.doc_id,
                "editor": editor,
                "preferred_app": preferred_app if editor == "default" else "",
                "path": relative_path(repo_root, target.path),
            },
        )

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "editor": editor,
        "preferred_app": preferred_app if editor == "default" else "",
        "path": relative_path(repo_root, target.path),
        "summary_text": f"Opened {target.doc_id} source.",
        "dry_run": dry_run,
    }


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    scopes: Dict[str, Any] = {}
    for scope in sorted(SCOPE_ROOTS.keys()):
        root = source_model.scope_root(repo_root, scope)
        scope_docs = source_model.load_scope_docs(repo_root, scope) if root.exists() else []
        scopes[scope] = {
            "available": root.exists(),
            "root": relative_path(repo_root, root),
            "archive_available": any(doc.doc_id == "archive" for doc in scope_docs),
            "generated_data_reads": docs_generated_reads.generated_scope_data_available(repo_root, scope),
            "generated_search_reads": docs_generated_reads.generated_search_data_available(repo_root, scope),
            "count": len(scope_docs),
        }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "html_import": True,
            "docs_export": True,
            "library_import": True,
            "scopes": scopes,
        },
    }


def parse_json_body(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    content_length = handler.headers.get("Content-Length", "").strip()
    try:
        length = int(content_length)
    except ValueError as exc:
        raise ValueError("Invalid Content-Length") from exc
    if length < 0 or length > MAX_BODY_BYTES:
        raise ValueError("Request body too large")
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    return payload


def write_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: Dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    origin = allowed_origin(handler.headers.get("Origin", ""))
    if origin:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def error_response(handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
    write_response(handler, status, {"ok": False, "error": message})


def log_event(repo_root: Path, event: str, details: Dict[str, Any]) -> None:
    append_script_log(__file__, event, details=details, repo_root=repo_root, log_dir_rel=LOGS_REL_DIR)


def handle_broken_links(repo_root: Path, body: Dict[str, Any]) -> Dict[str, Any]:
    scope = source_model.normalize_scope(body.get("scope"))
    payload = audit_docs_broken_links(repo_root, scope)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "scope": scope,
            "total": int(summary.get("total") or 0),
            "not_found": int(summary.get("not_found") or 0),
        },
    )
    return payload


def handle_docs_export(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    adapter = resolve_documents_adapter(repo_root, body.get("data_domain"), "export")
    scope = source_model.normalize_scope(adapter.scope)
    config_id = str(body.get("config_id") or "").strip()
    if not config_id:
        raise ValueError("config_id is required")

    raw_doc_ids = body.get("doc_ids", [])
    if raw_doc_ids is None:
        raw_doc_ids = []
    if not isinstance(raw_doc_ids, list):
        raise ValueError("doc_ids must be a list")
    doc_ids = parse_export_doc_ids([str(doc_id or "") for doc_id in raw_doc_ids])
    select_all = bool(body.get("select_all"))
    missing_summary_only = body.get("missing_summary_only")
    if missing_summary_only is not None and not isinstance(missing_summary_only, bool):
        raise ValueError("missing_summary_only must be true, false, or null")
    target_format = str(body.get("target_format") or "").strip()

    report = build_export(
        repo_root=repo_root,
        config_id=config_id,
        scope=scope,
        selected_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        write=not dry_run,
        config_path=adapter.config_path("export_configs_path").as_posix(),
        target_format=target_format or None,
        output_root=adapter.path("export_root"),
    )
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    log_event(
        repo_root,
        "docs-export",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "config_id": config_id,
            "dry_run": dry_run,
            "target_format": report.get("target_format", ""),
            "output_written": bool(report.get("output_written")),
            "selected": int(report.get("counts", {}).get("selected") or 0),
            "exported": int(report.get("counts", {}).get("exported") or 0),
            "skipped": int(report.get("counts", {}).get("skipped") or 0),
            "failed": int(report.get("counts", {}).get("failed") or 0),
            "truncated": int(report.get("counts", {}).get("truncated") or 0),
            "errors": int(report.get("issue_counts", {}).get("errors") or 0),
            "warnings": int(report.get("issue_counts", {}).get("warnings") or 0),
        },
    )
    if report.get("ok"):
        action = "Validated export" if dry_run else "Exported"
        suffix = " without writing." if dry_run else "."
        exported_count = int(report.get("counts", {}).get("exported") or 0)
        document_word = "document" if exported_count == 1 else "documents"
        report["summary_text"] = (
            f"{action} {exported_count} {document_word} "
            f"to {report.get('output_file', '')}{suffix}"
        )
    return report


def resolve_documents_adapter(repo_root: Path, data_domain: Any, operation: str) -> AdapterResolution:
    adapter = resolve_adapter(repo_root, data_domain=data_domain, operation=operation)
    if str(adapter.adapter.get("module") or "").strip() != "documents":
        raise ValueError(f"adapter {adapter.adapter_id!r} is not implemented by the documents service")
    return adapter


def handle_documents_import_files(repo_root: Path, data_domain: Any) -> Dict[str, Any]:
    adapter = resolve_documents_adapter(repo_root, data_domain, "import_files")
    scope = source_model.normalize_scope(adapter.scope)
    staging_root = adapter.path("staging_root")
    files = list_staged_import_files(repo_root, scope, staging_root=staging_root)
    log_event(
        repo_root,
        "docs-import-files",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "count": len(files),
        },
    )
    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staging_root": staging_root.as_posix(),
        "files": files,
    }


def handle_documents_import_preview(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    adapter = resolve_documents_adapter(repo_root, body.get("data_domain"), "import_preview")
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("staging_root"),
    )
    report = render_markdown_previews(
        repo_root=repo_root,
        scope=scope,
        report=report,
        write=not dry_run,
        preview_root=adapter.path("preview_root"),
    )
    report["data_domain"] = adapter.data_domain
    report["adapter_id"] = adapter.adapter_id
    log_event(
        repo_root,
        "docs-import-preview",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "preview_written": bool(report.get("preview_written")),
            "detected_import_type": str(report.get("detected_import_type") or ""),
            "records": int(report.get("counts", {}).get("records") or 0),
            "parsed_records": int(report.get("counts", {}).get("parsed_records") or 0),
            "malformed_records": int(report.get("counts", {}).get("malformed_records") or 0),
            "errors": int(report.get("counts", {}).get("errors") or 0),
            "warnings": int(report.get("counts", {}).get("warnings") or 0),
            "preview_files": [
                str(item.get("path") or "")
                for item in report.get("preview_files", [])
                if isinstance(item, dict) and item.get("path")
            ],
        },
    )
    if report.get("ok"):
        action = "Validated" if dry_run else "Generated"
        suffix = " without writing" if dry_run else ""
        preview_count = len(report.get("preview_files", []))
        preview_file_label = "preview file" if preview_count == 1 else "preview files"
        report["summary_text"] = (
            f"{action} {preview_count} {adapter.label} import {preview_file_label}{suffix}."
        )
    return report


def selected_import_record_indices(value: Any) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("record_indices must be a list")
    selected: list[int] = []
    seen: set[int] = set()
    for item in value:
        if isinstance(item, bool):
            raise ValueError("record_indices must contain integers")
        try:
            index = int(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("record_indices must contain integers") from exc
        if index < 0:
            raise ValueError("record_indices must contain zero or positive integers")
        if index not in seen:
            selected.append(index)
            seen.add(index)
    return selected


def summary_from_import_record(record: Dict[str, Any]) -> tuple[str, bool]:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    if "summary" not in metadata:
        return "", False
    return normalize_summary(metadata.get("summary")), True


def imported_parent_id(record: Dict[str, Any]) -> str:
    return str(record.get("parent_id") or "").strip()


def selected_import_records(
    report: Dict[str, Any],
    selected_indices: list[int],
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], list[tuple[int, Dict[str, Any], str]]]:
    records_by_index = {
        int(record.get("record_index")): record
        for record in report.get("records", [])
        if isinstance(record, dict) and isinstance(record.get("record_index"), int)
    }
    selected_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    selected_records: list[tuple[int, Dict[str, Any], str]] = []
    seen_doc_ids: set[str] = set()

    for record_index in selected_indices:
        record = records_by_index.get(record_index)
        if not record:
            skipped.append({"record_index": record_index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        doc_id = str(record.get("doc_id") or "").strip()
        selected_rows.append({"record_index": record_index, "doc_id": doc_id})
        if not doc_id:
            skipped.append({"record_index": record_index, "reason": "missing_doc_id", "message": "selected record has no doc_id"})
            continue
        if doc_id in seen_doc_ids:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "duplicate_doc_id", "message": "selected doc_id was already planned"})
            continue
        seen_doc_ids.add(doc_id)
        selected_records.append((record_index, record, doc_id))

    return selected_rows, skipped, selected_records


def handle_documents_import_summary_apply(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: AdapterResolution,
) -> Dict[str, Any]:
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")
    selected_indices = selected_import_record_indices(body.get("record_indices", []))
    if not selected_indices:
        raise ValueError("record_indices must include at least one selected record")
    confirmed = bool(body.get("confirm"))

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("staging_root"),
    )
    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    selected_rows, skipped, selected_records = selected_import_records(report, selected_indices)
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected_records:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        summary, has_summary = summary_from_import_record(record)
        if not has_summary or not summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_summary", "message": "selected record has no proposed summary"})
            continue
        current_summary = normalize_summary(target.front_matter.get("summary"))
        if summary == current_summary:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "unchanged", "message": "proposed summary matches current source summary"})
            continue

        timestamp = source_model.current_doc_timestamp()
        updated_front_matter = dict(target.front_matter)
        updated_front_matter["added_date"] = str(
            updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
        ).strip()
        updated_front_matter["last_updated"] = timestamp
        updated_front_matter["summary"] = summary
        rewritten_sources[doc_id] = source_model.format_source(updated_front_matter, target.body)
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_summary": current_summary,
                "to_summary": summary,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    backup_dir = None
    rebuild = None
    if ok and confirmed and updates and not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "documents-summary-apply",
            rewrite_docs,
            {
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": [item["doc_id"] for item in updates],
            },
        )
        rebuild = write_rebuild.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [doc.path for doc in rewrite_docs],
            lambda: [source_model.write_text_atomic(doc.path, rewritten_sources[doc.doc_id]) for doc in rewrite_docs],
            suppression_reason="docs-import-summary-apply",
            search_doc_ids=[item["doc_id"] for item in updates],
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staged_filename": staged_filename,
        "operation": "summary_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "updates": len(updates),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "summary_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {adapter.label} summary update(s){suffix}."
    log_event(
        repo_root,
        "docs-import-summary-apply",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            "updates": len(updates),
            "skipped": len(skipped),
            "errors": error_count,
            "written": bool(payload["summary_apply_written"]),
        },
    )
    return payload


def handle_documents_import_hierarchy_apply(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    adapter: AdapterResolution,
) -> Dict[str, Any]:
    scope = source_model.normalize_scope(adapter.scope)
    staged_filename = str(body.get("staged_filename") or body.get("file") or "").strip()
    if not staged_filename:
        raise ValueError("staged_filename is required")
    selected_indices = selected_import_record_indices(body.get("record_indices", []))
    if not selected_indices:
        raise ValueError("record_indices must include at least one selected record")
    confirmed = bool(body.get("confirm"))

    report = parse_staged_import(
        repo_root=repo_root,
        scope=scope,
        staged_file=staged_filename,
        staging_root=adapter.path("staging_root"),
    )
    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    selected_rows, skipped, selected_records = selected_import_records(report, selected_indices)
    errors: list[Dict[str, Any]] = []
    warnings: list[Dict[str, Any]] = []
    updates: list[Dict[str, Any]] = []
    unchanged: list[Dict[str, Any]] = []
    rewrite_docs: list[source_model.ScopeDoc] = []
    rewritten_sources: dict[str, str] = {}

    for record_index, record, doc_id in selected_records:
        target = docs_by_id.get(doc_id)
        if target is None:
            errors.append({"record_index": record_index, "doc_id": doc_id, "reason": "missing_target_doc", "message": f"target Library source doc does not exist: {doc_id}"})
            continue
        parent_id = imported_parent_id(record)
        if parent_id == doc_id:
            skipped.append({"record_index": record_index, "doc_id": doc_id, "reason": "self_parent_id", "message": "selected record parent_id points to itself"})
            continue
        if parent_id and parent_id not in docs_by_id:
            warnings.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "reason": "unknown_parent_id", "message": f"parent_id is not a current Library source doc and will render at root level: {parent_id}"})
        if parent_id == target.parent_id:
            unchanged.append({"record_index": record_index, "doc_id": doc_id, "parent_id": parent_id, "message": "proposed parent_id matches current source parent_id"})
            continue

        timestamp = source_model.current_doc_timestamp()
        updated_front_matter = dict(target.front_matter)
        updated_front_matter["added_date"] = str(
            updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
        ).strip()
        updated_front_matter["last_updated"] = timestamp
        updated_front_matter["parent_id"] = parent_id
        rewritten_sources[doc_id] = source_model.format_source(updated_front_matter, target.body)
        rewrite_docs.append(target)
        updates.append(
            {
                "record_index": record_index,
                "doc_id": doc_id,
                "path": relative_path(repo_root, target.path),
                "from_parent_id": target.parent_id,
                "to_parent_id": parent_id,
                "sort_order": target.sort_order,
            }
        )

    warning_count = len(warnings) + len(skipped)
    error_count = len(errors)
    ok = bool(report.get("ok")) and error_count == 0
    backup_dir = None
    rebuild = None
    if ok and confirmed and updates and not dry_run:
        backup_dir = make_backup_bundle(
            repo_root,
            scope,
            "documents-hierarchy-apply",
            rewrite_docs,
            {
                "staged_filename": staged_filename,
                "record_indices": selected_indices,
                "updated_doc_ids": [item["doc_id"] for item in updates],
            },
        )
        rebuild = write_rebuild.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [doc.path for doc in rewrite_docs],
            lambda: [source_model.write_text_atomic(doc.path, rewritten_sources[doc.doc_id]) for doc in rewrite_docs],
            suppression_reason="docs-import-hierarchy-apply",
            search_doc_ids=[item["doc_id"] for item in updates],
        )

    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": scope,
        "staged_filename": staged_filename,
        "operation": "hierarchy_apply",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "input_ok": bool(report.get("ok")),
        "detected_import_type": report.get("detected_import_type", ""),
        "selected_records": selected_rows,
        "updates": updates,
        "unchanged": unchanged,
        "skipped": skipped,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "selected": len(selected_indices),
            "changed": len(updates),
            "updates": len(updates),
            "unchanged": len(unchanged),
            "skipped": len(skipped),
            "errors": error_count,
            "warnings": warning_count,
        },
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "hierarchy_apply_written": bool(ok and confirmed and updates and not dry_run),
        "requires_confirmation": bool(ok and updates and not confirmed),
    }
    action = "Validated" if not confirmed or dry_run else "Updated"
    suffix = " without writing" if not confirmed or dry_run else ""
    payload["summary_text"] = f"{action} {len(updates)} {adapter.label} hierarchy change(s){suffix}."
    log_event(
        repo_root,
        "docs-import-hierarchy-apply",
        {
            "data_domain": adapter.data_domain,
            "adapter_id": adapter.adapter_id,
            "scope": scope,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "confirmed": confirmed,
            "changed": len(updates),
            "unchanged": len(unchanged),
            "skipped": len(skipped),
            "warnings": len(warnings),
            "errors": error_count,
            "written": bool(payload["hierarchy_apply_written"]),
        },
    )
    return payload


def handle_documents_import_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    operation = str(body.get("operation") or "").strip()
    if operation not in {"summary_apply", "hierarchy_apply"}:
        raise ValueError("operation must be summary_apply or hierarchy_apply")
    adapter = resolve_documents_adapter(repo_root, body.get("data_domain"), operation)
    if operation == "summary_apply":
        return handle_documents_import_summary_apply(repo_root, body, dry_run, adapter)
    return handle_documents_import_hierarchy_apply(repo_root, body, dry_run, adapter)


def import_source_dependencies() -> import_source_service.ImportSourceDependencies:
    return import_source_service.ImportSourceDependencies(
        log_event=log_event,
        make_backup_bundle=make_backup_bundle,
        make_import_overwrite_backup=make_import_overwrite_backup,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def handle_import_source(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return import_source_service.handle_import_source(repo_root, body, dry_run, import_source_dependencies())


def execute_management_mutation_plan(repo_root: Path, plan: mutations.ManagementMutationPlan, dry_run: bool) -> Dict[str, Any]:
    payload = dict(plan.response)
    backup_dir = None
    rebuild = None

    if not dry_run and plan.has_source_changes:
        if plan.backup_operation:
            backup_dir = make_backup_bundle(
                repo_root,
                plan.scope,
                plan.backup_operation,
                list(plan.backup_docs),
                plan.backup_metadata,
            )

        def write_operation() -> None:
            for source_write in plan.source_writes:
                source_model.write_text_atomic(source_write.path, source_write.text)
            for source_delete in plan.source_deletes:
                source_delete.path.unlink()

        rebuild = write_rebuild.perform_source_write_and_rebuild(
            repo_root,
            plan.scope,
            plan.changed_paths,
            write_operation,
            suppression_reason=plan.suppression_reason or "docs-management",
            search_doc_ids=plan.search_doc_ids,
        )
        if plan.log_event_name:
            log_event(repo_root, plan.log_event_name, plan.log_details)

    if plan.include_write_result_keys:
        payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
        payload["rebuild"] = rebuild
    payload["dry_run"] = dry_run
    return payload


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_create(repo_root, body), dry_run)


def handle_update_metadata(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_metadata(repo_root, body), dry_run)


def handle_update_viewability_bulk(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_viewability_bulk(repo_root, body), dry_run)


def handle_update_viewability(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_viewability(repo_root, body), dry_run)


def handle_move(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_move(repo_root, body), dry_run)


def handle_restore_move(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_restore_move(repo_root, body), dry_run)


def handle_archive(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_archive(repo_root, body), dry_run)


def handle_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_delete_apply(repo_root, body), dry_run)


class DocsManagementHandler(BaseHTTPRequestHandler):
    server_version = "DocsManagementServer/0.1"

    GET_HANDLERS: Dict[str, str] = {
        routes.HEALTH_PATH: "_handle_health_get",
        routes.CAPABILITIES_PATH: "_handle_capabilities_get",
        routes.GENERATED_INDEX_PATH: "_handle_generated_index_get",
        routes.GENERATED_INDEX_ALT_PATH: "_handle_generated_index_get",
        routes.GENERATED_PAYLOAD_PATH: "_handle_generated_payload_get",
        routes.GENERATED_PAYLOAD_ALT_PATH: "_handle_generated_payload_get",
        routes.GENERATED_SEARCH_PATH: "_handle_generated_search_get",
        routes.GENERATED_SEARCH_ALT_PATH: "_handle_generated_search_get",
        routes.IMPORT_SOURCE_FILES_PATH: "_handle_import_source_files_get",
        routes.IMPORT_HTML_FILES_PATH: "_handle_import_source_files_get",
        routes.IMPORT_FILES_PATH: "_handle_import_files_get",
    }

    POST_HANDLERS: Dict[str, str] = {
        routes.OPEN_SOURCE_PATH: "_handle_open_source_post",
        routes.BROKEN_LINKS_PATH: "_handle_broken_links_post",
        routes.EXPORT_PATH: "_handle_export_post",
        routes.IMPORT_SOURCE_PATH: "_handle_import_source_post",
        routes.IMPORT_HTML_PATH: "_handle_import_source_post",
        routes.IMPORT_PREVIEW_PATH: "_handle_import_preview_post",
        routes.IMPORT_APPLY_PATH: "_handle_import_apply_post",
        routes.UPDATE_METADATA_PATH: "_handle_update_metadata_post",
        routes.UPDATE_VIEWABILITY_PATH: "_handle_update_viewability_post",
        routes.UPDATE_VIEWABILITY_BULK_PATH: "_handle_update_viewability_bulk_post",
        routes.CREATE_PATH: "_handle_create_post",
        routes.REBUILD_PATH: "_handle_rebuild_post",
        routes.MOVE_PATH: "_handle_move_post",
        routes.RESTORE_MOVE_PATH: "_handle_restore_move_post",
        routes.ARCHIVE_PATH: "_handle_archive_post",
        routes.DELETE_PREVIEW_PATH: "_handle_delete_preview_post",
        routes.DELETE_APPLY_PATH: "_handle_delete_apply_post",
    }

    @property
    def app(self) -> Dict[str, Any]:
        return getattr(self.server, "app_state")  # type: ignore[attr-defined]

    def _request_path(self) -> str:
        return urlparse(self.path).path

    def do_OPTIONS(self) -> None:  # noqa: N802
        request_path = self._request_path()
        if request_path not in routes.OPTIONS_PATHS:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return
        origin = allowed_origin(self.headers.get("Origin", ""))
        if not origin:
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_health_get(self) -> None:
        write_response(
            self,
            HTTPStatus.OK,
            {
                "ok": True,
                "service": "docs_management",
                "dry_run": self.app["dry_run"],
            },
        )

    def _handle_capabilities_get(self) -> None:
        write_response(self, HTTPStatus.OK, capabilities_payload(self.app["repo_root"]))

    def _handle_generated_index_get(self) -> None:
        scope = source_model.normalize_scope(query_param(self, "scope"))
        payload = docs_generated_reads.read_generated_docs_index(self.app["repo_root"], scope)
        write_response(self, HTTPStatus.OK, payload)

    def _handle_generated_payload_get(self) -> None:
        scope = source_model.normalize_scope(query_param(self, "scope"))
        doc_id = query_param(self, "doc_id") or query_param(self, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        payload = docs_generated_reads.read_generated_doc_payload(self.app["repo_root"], scope, doc_id)
        write_response(self, HTTPStatus.OK, payload)

    def _handle_generated_search_get(self) -> None:
        scope = source_model.normalize_scope(query_param(self, "scope"))
        payload = docs_generated_reads.read_generated_search_index(self.app["repo_root"], scope)
        write_response(self, HTTPStatus.OK, payload)

    def _handle_import_source_files_get(self) -> None:
        write_response(self, HTTPStatus.OK, import_source_service.handle_import_source_files(self.app["repo_root"]))

    def _handle_import_files_get(self) -> None:
        data_domain = query_param(self, "data_domain")
        write_response(self, HTTPStatus.OK, handle_documents_import_files(self.app["repo_root"], data_domain))

    def do_GET(self) -> None:  # noqa: N802
        try:
            request_path = self._request_path()
            handler_name = self.GET_HANDLERS.get(request_path)
            if handler_name:
                getattr(self, handler_name)()
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def _handle_open_source_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, open_source_doc(repo_root, body, dry_run)

    def _handle_broken_links_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        payload = handle_broken_links(repo_root, body)
        docs_activity.maybe_attach_broken_links_activity(repo_root, body, payload)
        return HTTPStatus.OK, payload

    def _handle_export_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        payload = handle_docs_export(repo_root, body, dry_run)
        docs_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload

    def _handle_import_source_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        payload = handle_import_source(repo_root, body, dry_run)
        docs_activity.maybe_attach_import_source_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK, payload

    def _handle_import_preview_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        payload = handle_documents_import_preview(repo_root, body, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload

    def _handle_import_apply_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        payload = handle_documents_import_apply(repo_root, body, dry_run)
        docs_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload

    def _handle_update_metadata_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_update_metadata(repo_root, body, dry_run)

    def _handle_update_viewability_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_update_viewability(repo_root, body, dry_run)

    def _handle_update_viewability_bulk_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_update_viewability_bulk(repo_root, body, dry_run)

    def _handle_create_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_create(repo_root, body, dry_run)

    def _handle_rebuild_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        scope = source_model.normalize_scope(body.get("scope"))
        payload = write_rebuild.rebuild_scope_outputs(repo_root, scope)
        payload["summary_text"] = f"Docs and docs search rebuilt for {scope}."
        return HTTPStatus.OK, payload

    def _handle_move_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_move(repo_root, body, dry_run)

    def _handle_restore_move_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_restore_move(repo_root, body, dry_run)

    def _handle_archive_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_archive(repo_root, body, dry_run)

    def _handle_delete_preview_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        scope = source_model.normalize_scope(body.get("scope"))
        doc_id = str(body.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError("doc_id is required")
        return HTTPStatus.OK, mutations.plan_delete_preview(repo_root, scope, doc_id)

    def _handle_delete_apply_post(self, repo_root: Path, body: Dict[str, Any], dry_run: bool) -> tuple[HTTPStatus, Dict[str, Any]]:
        return HTTPStatus.OK, handle_delete_apply(repo_root, body, dry_run)

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "")
        if origin and not allowed_origin(origin):
            error_response(self, HTTPStatus.FORBIDDEN, "Origin not allowed")
            return

        try:
            body = parse_json_body(self)
            repo_root = self.app["repo_root"]
            dry_run = self.app["dry_run"]
            handler_name = self.POST_HANDLERS.get(self._request_path())
            if handler_name:
                status, payload = getattr(self, handler_name)(repo_root, body, dry_run)
                write_response(self, status, payload)
                return
            error_response(self, HTTPStatus.NOT_FOUND, "Not found")
        except FileNotFoundError as error:
            error_response(self, HTTPStatus.NOT_FOUND, str(error))
        except ValueError as error:
            error_response(self, HTTPStatus.BAD_REQUEST, str(error))
        except RuntimeError as error:
            error_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, str(error))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the localhost docs-management server.")
    parser.add_argument("--port", type=int, default=8789, help="Port to bind. Default: 8789")
    parser.add_argument("--repo-root", default="", help="Explicit repo root")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write files")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = detect_repo_root(args.repo_root)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DocsManagementHandler)
    server.app_state = {  # type: ignore[attr-defined]
        "repo_root": repo_root,
        "dry_run": bool(args.dry_run),
    }
    print(f"Docs Management Server listening on http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Docs Management Server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
