#!/usr/bin/env python3
"""Shared Docs management service functions for local Studio and optional HTTP wrappers."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_logging import append_script_log  # noqa: E402
from docs_broken_links import audit_docs_broken_links  # noqa: E402
from studio import data_sharing_routes, data_sharing_service  # noqa: E402
import docs_activity  # noqa: E402
import docs_generated_reads  # noqa: E402
import docs_source_config_report  # noqa: E402
import docs_source_config_settings  # noqa: E402
import documents_data_sharing_adapter  # noqa: E402
from analytics import tags_data_sharing_adapter  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_scope_manifest  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_scope_config import DOCS_SCOPE_CONFIGS, SCOPE_ROOTS  # noqa: E402
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


def make_scope_lifecycle_backup(repo_root: Path, scope: str, operation: str) -> Path:
    bundle_dir = repo_root / BACKUPS_REL_DIR / f"{backup_stamp_now()}-{scope}-scope-{operation}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    candidates = [
        repo_root / docs_scope_manifest.MANIFEST_REL_PATH,
        repo_root / docs_scope_manifest.CONFIG_REL_PATH,
    ]
    files = []
    for path in candidates:
        record = {
            "path": relative_path(repo_root, path),
            "exists": path.exists(),
        }
        if path.exists() and path.is_file():
            shutil.copy2(path, bundle_dir / path.name)
            record["backup_name"] = path.name
        files.append(record)
    manifest = {
        "time_utc": utc_now(),
        "scope": scope,
        "operation": f"scope-{operation}",
        "files": files,
    }
    source_model.write_text_atomic(bundle_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return bundle_dir


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}&mode=manage"


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


def capability_scope_docs(repo_root: Path, scope: str, root: Path) -> list[Any]:
    if not root.exists():
        return []
    if scope in SCOPE_ROOTS:
        return source_model.load_scope_docs(repo_root, scope)

    docs = []
    for path in source_model.scope_markdown_paths(root, scope):
        front_matter, body = source_model.parse_source(path)
        doc_id = str(front_matter.get("doc_id") or path.stem).strip()
        title = str(front_matter.get("title") or source_model.humanize(doc_id or path.stem)).strip() or doc_id
        sort_order = front_matter.get("sort_order")
        if sort_order is not None:
            try:
                sort_order = int(sort_order)
            except (TypeError, ValueError):
                sort_order = None
        hidden = source_model.doc_is_hidden(front_matter)
        docs.append(
            source_model.ScopeDoc(
                scope=scope,
                path=path,
                source_text=path.read_text(encoding="utf-8"),
                front_matter=dict(front_matter),
                body=body,
                doc_id=doc_id,
                title=title,
                ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
                parent_id=str(front_matter.get("parent_id") or "").strip(),
                sort_order=sort_order,
                published=source_model.doc_is_published(front_matter),
                hidden=hidden,
                viewable=not hidden,
            )
        )
    return docs


def capabilities_payload(repo_root: Path) -> Dict[str, Any]:
    scopes: Dict[str, Any] = {}
    try:
        manifest = docs_scope_manifest.load_manifest(repo_root)
    except (FileNotFoundError, ValueError):
        manifest = {"scopes": []}
    manifest_scopes = docs_scope_manifest.manifest_scopes_by_id(manifest)
    try:
        scope_configs = docs_source_config_settings.load_docs_scope_configs(repo_root)
    except FileNotFoundError:
        scope_configs = DOCS_SCOPE_CONFIGS
    for scope in sorted(scope_configs):
        config = scope_configs[scope]
        root = repo_root / config.source
        scope_docs = capability_scope_docs(repo_root, scope, root)
        manifest_record = manifest_scopes.get(scope)
        scopes[scope] = {
            "available": root.exists(),
            "root": relative_path(repo_root, root),
            "archive_available": any(doc.doc_id == "archive" for doc in scope_docs),
            "generated_data_reads": (repo_root / config.output / "index.json").exists(),
            "generated_search_reads": (repo_root / "assets" / "data" / "search" / scope / "index.json").exists(),
            "count": len(scope_docs),
            "scope_lifecycle": {
                "manifest_recorded": manifest_record is not None,
                "owner": str((manifest_record or {}).get("owner") or ""),
                "created_by_tool": (manifest_record or {}).get("created_by_tool") is True,
                "delete_eligible": docs_scope_manifest.scope_delete_eligible(manifest_record),
            },
        }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_reads": True,
            "source_config_settings_reads": True,
            "source_config_settings_writes": True,
            "html_import": True,
            "docs_export": True,
            "library_import": True,
            "scope_lifecycle": {
                "manifest": True,
                "create_preview": True,
                "create_apply": True,
                "delete_preview": True,
                "delete_apply": True,
                "publishing_modes": list(docs_scope_manifest.PUBLISHING_MODES),
                "manifest_path": docs_scope_manifest.MANIFEST_REL_PATH.as_posix(),
            },
            "scopes": scopes,
        },
    }



def log_event(repo_root: Path, event: str, details: Dict[str, Any]) -> None:
    append_script_log(
        repo_root / "scripts" / "docs" / "docs_management_service.py",
        event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )


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


def documents_data_sharing_dependencies() -> documents_data_sharing_adapter.DocumentsDataSharingDependencies:
    return documents_data_sharing_adapter.DocumentsDataSharingDependencies(
        log_event=log_event,
        make_backup_bundle=make_backup_bundle,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def tags_data_sharing_dependencies() -> tags_data_sharing_adapter.TagsDataSharingDependencies:
    return tags_data_sharing_adapter.TagsDataSharingDependencies(
        log_event=log_event,
    )


DATA_SHARING_HANDLERS = {
    "documents": documents_data_sharing_adapter.handlers_for(documents_data_sharing_dependencies),
    "analytics.tags": tags_data_sharing_adapter.handlers_for(tags_data_sharing_dependencies),
}


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
            docs_doc_ids=plan.build_doc_ids,
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


def handle_normalize_order(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_normalize_order(repo_root, body), dry_run)


def handle_archive(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_archive(repo_root, body), dry_run)


def handle_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_delete_apply(repo_root, body), dry_run)


def handle_scope_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id"))
    docs_scope_manifest.require_confirmed(body)
    docs_scope_manifest.plan_create_scope_preview(repo_root, body)
    backup_dir = None if dry_run else make_scope_lifecycle_backup(repo_root, scope_id, "create")
    payload = docs_scope_manifest.apply_create_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_scope_outputs=write_rebuild.rebuild_scope_outputs,
    )
    payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
    if not dry_run:
        log_event(
            repo_root,
            "docs_scope_create_apply",
            {
                "scope": scope_id,
                "created_count": len(payload.get("created_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_scope_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id") or body.get("scope"))
    docs_scope_manifest.require_confirmed(body)
    preview = docs_scope_manifest.plan_delete_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "scope delete is not allowed")
    backup_dir = None if dry_run else make_scope_lifecycle_backup(repo_root, scope_id, "delete")
    payload = docs_scope_manifest.apply_delete_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_all_docs_outputs=write_rebuild.rebuild_all_docs_outputs,
    )
    payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
    if not dry_run:
        log_event(
            repo_root,
            "docs_scope_delete_apply",
            {
                "scope": scope_id,
                "deleted_count": len(payload.get("deleted_files", [])),
                "missing_count": len(payload.get("missing_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload



def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    scope = source_model.normalize_scope(docs_api_query_value(params, "scope"))

    if path in {routes.GENERATED_INDEX_PATH, routes.GENERATED_INDEX_ALT_PATH}:
        return docs_generated_reads.read_generated_docs_index(repo_root, scope)
    if path in {routes.GENERATED_SEARCH_PATH, routes.GENERATED_SEARCH_ALT_PATH}:
        return docs_generated_reads.read_generated_search_index(repo_root, scope)
    if path in {routes.GENERATED_PAYLOAD_PATH, routes.GENERATED_PAYLOAD_ALT_PATH}:
        doc_id = docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        return docs_generated_reads.read_generated_doc_payload(repo_root, scope, doc_id)
    if path == routes.GENERATED_DOCS_LOG_PATH:
        projection = docs_api_query_value(params, "projection") or "search-index"
        return docs_generated_reads.read_generated_docs_log_projection(repo_root, projection)
    if path in {routes.GENERATED_REFERENCES_PATH, routes.GENERATED_REFERENCES_ALT_PATH}:
        return docs_generated_reads.read_generated_references_index(repo_root, scope)
    if path in {routes.GENERATED_REFERENCE_TARGET_PATH, routes.GENERATED_REFERENCE_TARGET_ALT_PATH}:
        target_kind = docs_api_query_value(params, "target_kind")
        target_slug = docs_api_query_value(params, "target_slug")
        if not target_kind or not target_slug:
            raise ValueError("target_kind and target_slug are required")
        return docs_generated_reads.read_generated_reference_target(repo_root, scope, target_kind, target_slug)
    raise FileNotFoundError("Not found")


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]], *, dry_run: bool = False) -> dict[str, object]:
    if path == routes.HEALTH_PATH:
        return {"ok": True, "service": "docs_management", "dry_run": dry_run}
    if path == routes.CAPABILITIES_PATH:
        return capabilities_payload(repo_root)
    if path in {
        routes.GENERATED_INDEX_PATH,
        routes.GENERATED_INDEX_ALT_PATH,
        routes.GENERATED_PAYLOAD_PATH,
        routes.GENERATED_PAYLOAD_ALT_PATH,
        routes.GENERATED_SEARCH_PATH,
        routes.GENERATED_SEARCH_ALT_PATH,
        routes.GENERATED_DOCS_LOG_PATH,
        routes.GENERATED_REFERENCES_PATH,
        routes.GENERATED_REFERENCES_ALT_PATH,
        routes.GENERATED_REFERENCE_TARGET_PATH,
        routes.GENERATED_REFERENCE_TARGET_ALT_PATH,
    }:
        return docs_generated_read_payload(repo_root, path, params)
    if path == routes.SOURCE_CONFIG_PATH:
        return docs_source_config_report.build_source_config_report(repo_root)
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        return docs_source_config_settings.build_settings_contract(
            repo_root,
            docs_api_query_value(params, "scope"),
        )
    if path in {routes.IMPORT_SOURCE_FILES_PATH, routes.IMPORT_HTML_FILES_PATH}:
        return import_source_service.handle_import_source_files(repo_root)
    if path == data_sharing_routes.RETURNED_PACKAGES_PATH:
        return data_sharing_service.list_returned_packages(
            repo_root,
            docs_api_query_value(params, "data_domain"),
            DATA_SHARING_HANDLERS,
        )

    if docs_api_query_value(params, "scope"):
        source_model.normalize_scope(docs_api_query_value(params, "scope"))
    raise FileNotFoundError("Not found")


def docs_management_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    if path == routes.OPEN_SOURCE_PATH:
        return HTTPStatus.OK, open_source_doc(repo_root, body, dry_run)
    if path == routes.BROKEN_LINKS_PATH:
        payload = handle_broken_links(repo_root, body)
        docs_activity.maybe_attach_broken_links_activity(repo_root, body, payload)
        return HTTPStatus.OK, payload
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        scope = source_model.normalize_scope(body.get("scope"))
        changes = body.get("changes")
        payload = docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            scope,
            changes,
            dry_run=dry_run,
        )
        if payload.get("requires_rebuild") and not dry_run:
            payload["rebuild"] = write_rebuild.rebuild_scope_outputs(repo_root, scope, include_search=False)
        else:
            payload["rebuild"] = None
        if payload.get("changed") and not dry_run:
            log_event(
                repo_root,
                "docs_source_config_settings",
                {
                    "scope": scope,
                    "fields": sorted(payload.get("changes", {}).keys()),
                    "source_config_path": payload.get("source_config_path", ""),
                },
            )
        payload["dry_run"] = dry_run
        return HTTPStatus.OK, payload
    if path == data_sharing_routes.PREPARE_PATH:
        payload = data_sharing_service.prepare_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        docs_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path in {routes.IMPORT_SOURCE_PATH, routes.IMPORT_HTML_PATH}:
        payload = handle_import_source(repo_root, body, dry_run)
        docs_activity.maybe_attach_import_source_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK, payload
    if path == data_sharing_routes.REVIEW_PATH:
        payload = data_sharing_service.review_returned_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path == data_sharing_routes.APPLY_PATH:
        payload = data_sharing_service.apply_returned_changes(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        docs_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path == routes.UPDATE_METADATA_PATH:
        return HTTPStatus.OK, handle_update_metadata(repo_root, body, dry_run)
    if path == routes.UPDATE_VIEWABILITY_PATH:
        return HTTPStatus.OK, handle_update_viewability(repo_root, body, dry_run)
    if path == routes.UPDATE_VIEWABILITY_BULK_PATH:
        return HTTPStatus.OK, handle_update_viewability_bulk(repo_root, body, dry_run)
    if path == routes.CREATE_PATH:
        return HTTPStatus.OK, handle_create(repo_root, body, dry_run)
    if path == routes.REBUILD_PATH:
        scope = source_model.normalize_scope(body.get("scope"))
        payload = write_rebuild.rebuild_scope_outputs(repo_root, scope)
        payload["summary_text"] = f"Docs and docs search rebuilt for {scope}."
        return HTTPStatus.OK, payload
    if path == routes.MOVE_PATH:
        return HTTPStatus.OK, handle_move(repo_root, body, dry_run)
    if path == routes.NORMALIZE_ORDER_PATH:
        return HTTPStatus.OK, handle_normalize_order(repo_root, body, dry_run)
    if path == routes.ARCHIVE_PATH:
        return HTTPStatus.OK, handle_archive(repo_root, body, dry_run)
    if path == routes.DELETE_PREVIEW_PATH:
        scope = source_model.normalize_scope(body.get("scope"))
        doc_id = str(body.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError("doc_id is required")
        return HTTPStatus.OK, mutations.plan_delete_preview(repo_root, scope, doc_id)
    if path == routes.DELETE_APPLY_PATH:
        return HTTPStatus.OK, handle_delete_apply(repo_root, body, dry_run)
    if path == routes.SCOPE_CREATE_PREVIEW_PATH:
        payload = docs_scope_manifest.plan_create_scope_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.SCOPE_CREATE_APPLY_PATH:
        return HTTPStatus.OK, handle_scope_create_apply(repo_root, body, dry_run)
    if path == routes.SCOPE_DELETE_PREVIEW_PATH:
        payload = docs_scope_manifest.plan_delete_scope_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.SCOPE_DELETE_APPLY_PATH:
        return HTTPStatus.OK, handle_scope_delete_apply(repo_root, body, dry_run)

    raise FileNotFoundError("Not found")
