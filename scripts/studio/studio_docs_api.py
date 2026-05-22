"""Docs Viewer API adapters for the local Studio app server."""

from __future__ import annotations

from http import HTTPStatus
import importlib.util
import sys
from pathlib import Path
from typing import Any


_docs_management_server_modules: dict[Path, object] = {}


def load_docs_management_server_module(repo_root: Path):
    repo_root = repo_root.resolve()
    if repo_root in _docs_management_server_modules:
        return _docs_management_server_modules[repo_root]

    scripts_dir = repo_root / "scripts"
    docs_dir = scripts_dir / "docs"
    for path in (docs_dir, scripts_dir):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    module_path = docs_dir / "docs_management_server.py"
    spec = importlib.util.spec_from_file_location("docs_management_server", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _docs_management_server_modules[repo_root] = module
    return module


def disabled_docs_capabilities_payload() -> dict[str, object]:
    scopes = {
        scope_id: {
            "available": False,
            "root": "",
            "archive_available": False,
            "generated_data_reads": False,
            "generated_search_reads": False,
            "count": 0,
            "scope_lifecycle": {
                "manifest_recorded": False,
                "owner": "",
                "created_by_tool": False,
                "delete_eligible": False,
            },
        }
        for scope_id in ("analysis", "library", "studio")
    }
    return {
        "ok": True,
        "capabilities": {
            "docs_management": False,
            "generated_data_reads": False,
            "source_config_reads": False,
            "source_config_settings_reads": False,
            "source_config_settings_writes": False,
            "html_import": False,
            "docs_export": False,
            "library_import": False,
            "scope_lifecycle": {
                "manifest": False,
                "create_preview": False,
                "create_apply": False,
                "delete_preview": False,
                "delete_apply": False,
                "publishing_modes": [],
                "manifest_path": "",
            },
            "scopes": scopes,
        },
    }


def docs_capabilities_payload(repo_root: Path) -> dict[str, object]:
    try:
        payload = load_docs_management_server_module(repo_root).capabilities_payload(repo_root)
    except Exception:
        return disabled_docs_capabilities_payload()

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        return disabled_docs_capabilities_payload()

    return payload


def docs_api_query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def docs_allowed_origin(repo_root: Path, origin: str) -> str:
    return load_docs_management_server_module(repo_root).allowed_origin(origin) or ""


def docs_generated_read_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    module = load_docs_management_server_module(repo_root)
    generated_reads = module.docs_generated_reads
    source_model = module.source_model
    scope = source_model.normalize_scope(docs_api_query_value(params, "scope"))

    if path in {"/docs/index", "/docs/generated/index"}:
        return generated_reads.read_generated_docs_index(repo_root, scope)
    if path in {"/docs/search", "/docs/generated/search"}:
        return generated_reads.read_generated_search_index(repo_root, scope)
    if path in {"/docs/doc", "/docs/generated/payload"}:
        doc_id = docs_api_query_value(params, "doc_id") or docs_api_query_value(params, "doc")
        if not doc_id:
            raise ValueError("doc_id is required")
        return generated_reads.read_generated_doc_payload(repo_root, scope, doc_id)
    if path == "/docs/generated/docs-log":
        projection = docs_api_query_value(params, "projection") or "search-index"
        return generated_reads.read_generated_docs_log_projection(repo_root, projection)
    if path in {"/docs/references", "/docs/generated/references"}:
        return generated_reads.read_generated_references_index(repo_root, scope)
    if path in {"/docs/reference-target", "/docs/generated/reference-target"}:
        target_kind = docs_api_query_value(params, "target_kind")
        target_slug = docs_api_query_value(params, "target_slug")
        if not target_kind or not target_slug:
            raise ValueError("target_kind and target_slug are required")
        return generated_reads.read_generated_reference_target(repo_root, scope, target_kind, target_slug)
    raise FileNotFoundError("Not found")


def docs_management_get_payload(repo_root: Path, path: str, params: dict[str, list[str]]) -> dict[str, object]:
    module = load_docs_management_server_module(repo_root)
    routes = module.routes
    source_model = module.source_model

    if path == routes.HEALTH_PATH:
        return {"ok": True, "service": "docs_management", "dry_run": False}
    if path == routes.CAPABILITIES_PATH:
        return docs_capabilities_payload(repo_root)
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
        return module.docs_source_config_report.build_source_config_report(repo_root)
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        return module.docs_source_config_settings.build_settings_contract(
            repo_root,
            docs_api_query_value(params, "scope"),
        )
    if path in {routes.IMPORT_SOURCE_FILES_PATH, routes.IMPORT_HTML_FILES_PATH}:
        return module.import_source_service.handle_import_source_files(repo_root)
    if path == module.data_sharing_routes.RETURNED_PACKAGES_PATH:
        return module.data_sharing_service.list_returned_packages(
            repo_root,
            docs_api_query_value(params, "data_domain"),
            module.DATA_SHARING_HANDLERS,
        )

    # Validate unknown normalized docs scopes consistently when a caller supplies one.
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
    module = load_docs_management_server_module(repo_root)
    routes = module.routes

    if path == routes.OPEN_SOURCE_PATH:
        return HTTPStatus.OK, module.open_source_doc(repo_root, body, dry_run)
    if path == routes.BROKEN_LINKS_PATH:
        payload = module.handle_broken_links(repo_root, body)
        module.docs_activity.maybe_attach_broken_links_activity(repo_root, body, payload)
        return HTTPStatus.OK, payload
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        scope = module.source_model.normalize_scope(body.get("scope"))
        changes = body.get("changes")
        payload = module.docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            scope,
            changes,
            dry_run=dry_run,
        )
        if payload.get("requires_rebuild") and not dry_run:
            payload["rebuild"] = module.write_rebuild.rebuild_scope_outputs(repo_root, scope, include_search=False)
        else:
            payload["rebuild"] = None
        if payload.get("changed") and not dry_run:
            module.log_event(
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
    if path == module.data_sharing_routes.PREPARE_PATH:
        payload = module.data_sharing_service.prepare_package(
            repo_root,
            body,
            dry_run,
            module.DATA_SHARING_HANDLERS,
        )
        module.docs_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path in {routes.IMPORT_SOURCE_PATH, routes.IMPORT_HTML_PATH}:
        payload = module.handle_import_source(repo_root, body, dry_run)
        module.docs_activity.maybe_attach_import_source_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK, payload
    if path == module.data_sharing_routes.REVIEW_PATH:
        payload = module.data_sharing_service.review_returned_package(
            repo_root,
            body,
            dry_run,
            module.DATA_SHARING_HANDLERS,
        )
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path == module.data_sharing_routes.APPLY_PATH:
        payload = module.data_sharing_service.apply_returned_changes(
            repo_root,
            body,
            dry_run,
            module.DATA_SHARING_HANDLERS,
        )
        module.docs_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if path == routes.UPDATE_METADATA_PATH:
        return HTTPStatus.OK, module.handle_update_metadata(repo_root, body, dry_run)
    if path == routes.UPDATE_VIEWABILITY_PATH:
        return HTTPStatus.OK, module.handle_update_viewability(repo_root, body, dry_run)
    if path == routes.UPDATE_VIEWABILITY_BULK_PATH:
        return HTTPStatus.OK, module.handle_update_viewability_bulk(repo_root, body, dry_run)
    if path == routes.CREATE_PATH:
        return HTTPStatus.OK, module.handle_create(repo_root, body, dry_run)
    if path == routes.REBUILD_PATH:
        scope = module.source_model.normalize_scope(body.get("scope"))
        payload = module.write_rebuild.rebuild_scope_outputs(repo_root, scope)
        payload["summary_text"] = f"Docs and docs search rebuilt for {scope}."
        return HTTPStatus.OK, payload
    if path == routes.MOVE_PATH:
        return HTTPStatus.OK, module.handle_move(repo_root, body, dry_run)
    if path == routes.NORMALIZE_ORDER_PATH:
        return HTTPStatus.OK, module.handle_normalize_order(repo_root, body, dry_run)
    if path == routes.ARCHIVE_PATH:
        return HTTPStatus.OK, module.handle_archive(repo_root, body, dry_run)
    if path == routes.DELETE_PREVIEW_PATH:
        scope = module.source_model.normalize_scope(body.get("scope"))
        doc_id = str(body.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError("doc_id is required")
        return HTTPStatus.OK, module.mutations.plan_delete_preview(repo_root, scope, doc_id)
    if path == routes.DELETE_APPLY_PATH:
        return HTTPStatus.OK, module.handle_delete_apply(repo_root, body, dry_run)
    if path == routes.SCOPE_CREATE_PREVIEW_PATH:
        payload = module.docs_scope_manifest.plan_create_scope_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.SCOPE_CREATE_APPLY_PATH:
        return HTTPStatus.OK, module.handle_scope_create_apply(repo_root, body, dry_run)
    if path == routes.SCOPE_DELETE_PREVIEW_PATH:
        payload = module.docs_scope_manifest.plan_delete_scope_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.SCOPE_DELETE_APPLY_PATH:
        return HTTPStatus.OK, module.handle_scope_delete_apply(repo_root, body, dry_run)

    raise FileNotFoundError("Not found")
