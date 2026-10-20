#!/usr/bin/env python3
"""Docs management route dispatcher for Local Studio."""

from __future__ import annotations

import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

import docs_management_document_target  # noqa: E402
import docs_management_draft  # noqa: E402
import docs_selected_documents  # noqa: E402
import docs_document_thumbnails  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_import_doc  # noqa: E402
import docs_local_links  # noqa: E402
import docs_media_actions  # noqa: E402
import docs_media_metadata  # noqa: E402
import docs_management_position  # noqa: E402
import docs_management_delete  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_publish  # noqa: E402
import docs_project_state  # noqa: E402
import docs_missing_source_files  # noqa: E402
import docs_uncataloged_files  # noqa: E402
import docs_folders_without_works  # noqa: E402
import docs_work_downloads  # noqa: E402
import docs_work_links  # noqa: E402
import docs_static_html_export  # noqa: E402
import docs_source_media_service  # noqa: E402
from docs_source_media_upload import SourceMediaUpload  # noqa: E402
import docs_catalogue_regeneration  # noqa: E402
import docs_document_rebuild  # noqa: E402
import docs_generated_reads  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
import docs_discovery_refresh  # noqa: E402
import docs_workspace_links  # noqa: E402
from docs_management_broken_links_service import handle_broken_links  # noqa: E402
from docs_management_capabilities_service import capabilities_payload as build_capabilities_payload  # noqa: E402
from docs_management_context import (  # noqa: E402
    DEFAULT_MARKDOWN_APP_ENV,
    LOGS_REL_DIR,
    MAX_BODY_BYTES,
    allowed_origin,
    detect_repo_root,
    find_repo_root,
    log_event,
    relative_path,
    utc_now,
)
from docs_management_import_service import handle_import_source, import_source_dependencies  # noqa: E402
from docs_management_mutation_service import (  # noqa: E402
    DocumentCreateCommittedError,
    handle_create,
)
from docs_management_read_service import (  # noqa: E402
    docs_api_query_value,
    docs_generated_read_payload,
    docs_management_get_payload as read_docs_management_get_payload,
)
from docs_management_source_service import detect_preferred_markdown_app, open_publication_ignore, open_recent_exclusions, open_source_doc, save_source_document  # noqa: E402
from docs_workspace_config import load_docs_working_config, load_docs_workspace_config, require_document_authoring, select_workspace_stage  # noqa: E402


def capabilities_payload(repo_root: Path) -> dict[str, object]:
    return build_capabilities_payload(repo_root)


def docs_management_get_payload(
    repo_root: Path,
    path: str,
    params: dict[str, list[str]],
) -> dict[str, object]:
    return read_docs_management_get_payload(repo_root, path, params)


def docs_management_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
    media_uploads: list[SourceMediaUpload] | None = None,
    document_upload: docs_import_doc.ImportDocUpload | None = None,
) -> tuple[HTTPStatus, dict[str, object]]:
    if path == routes.PUBLISH_PATH:
        if dry_run:
            raise ValueError("Publish does not support dry_run")
        payload = docs_publish.publish_docs(repo_root, body)
        return (HTTPStatus.OK if payload["complete"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if "stage" in body:
        raise ValueError("stage is retired from Docs requests")
    if "scope" in body or "parent_scope" in body:
        raise ValueError("scope is retired; use an optional collection")
    if "sub_scope" in body:
        raise ValueError("sub_scope is retired; use collection")
    if path == routes.GENERATED_WORKSPACE_LINKS_PATH:
        if body:
            raise ValueError("Links refresh requires an empty request object")
        if dry_run:
            raise ValueError("Links refresh does not support dry_run")
        workspace = load_docs_workspace_config(repo_root)
        config = select_workspace_stage(workspace, "working")
        require_document_authoring(config)
        return HTTPStatus.OK, docs_workspace_links.write_workspace_links(config, report_path=workspace.links_report.path)
    if path == routes.CATALOGUE_REGENERATE_PATH:
        if dry_run:
            raise ValueError("Catalogue Regenerate does not support dry_run")
        try:
            return HTTPStatus.OK, docs_catalogue_regeneration.regenerate_catalogue(repo_root, body)
        except docs_catalogue_regeneration.CatalogueRegenerationError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.SET_DRAFT_PATH:
        payload = docs_management_draft.set_draft(repo_root, body, dry_run=dry_run)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.SET_SELECTED_PATH:
        return HTTPStatus.OK, docs_selected_documents.set_selected(repo_root, body, dry_run=dry_run)
    if path == routes.THUMBNAIL_PATH:
        if dry_run:
            raise ValueError("Thumb does not support dry_run")
        return HTTPStatus.OK, docs_document_thumbnails.set_document_thumbnail(repo_root, body)
    if path == routes.SOURCE_SAVE_PATH:
        if media_uploads is None:
            raise ValueError("Source Save requires its multipart upload envelope")
        payload = save_source_document(repo_root, body, dry_run, media_uploads=media_uploads)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.OPEN_SOURCE_PATH:
        return HTTPStatus.OK, open_source_doc(repo_root, body, dry_run)
    if path == routes.OPEN_PUBLICATION_IGNORE_PATH:
        return HTTPStatus.OK, open_publication_ignore(repo_root, body, dry_run)
    if path == routes.OPEN_RECENT_EXCLUSIONS_PATH:
        return HTTPStatus.OK, open_recent_exclusions(repo_root, body, dry_run)
    if path == routes.OPEN_LOCAL_TARGET_PATH:
        return docs_local_links.open_local_target_response(repo_root, body, dry_run=dry_run)
    if path == routes.OPEN_MEDIA_SOURCE_PATH:
        return HTTPStatus.OK, docs_media_actions.open_media_source(repo_root, body, dry_run=dry_run)
    if path == routes.OPEN_WORK_DOWNLOAD_PATH:
        return HTTPStatus.OK, docs_work_downloads.open_work_download(repo_root, body, dry_run=dry_run)
    if path == routes.WORK_DOWNLOADS_PATH:
        if body:
            raise ValueError("Work Downloads request must be empty")
        return HTTPStatus.OK, docs_work_downloads.work_downloads_report(repo_root)
    if path == routes.WORK_LINKS_PATH:
        if body:
            raise ValueError("Work Links request must be empty")
        return HTTPStatus.OK, docs_work_links.work_links_report(repo_root)
    if path == routes.MEDIA_REFRESH_PATH:
        if not isinstance(body, dict) or body:
            raise ValueError("Docs Media refresh requires an empty request object")
        if dry_run:
            raise ValueError("Docs Media refresh does not support dry_run")
        return HTTPStatus.OK, docs_media_metadata.refresh_media_metadata(repo_root)
    if path == routes.BROKEN_LINKS_PATH:
        if dry_run:
            raise ValueError("Broken Links refresh does not support dry_run")
        payload = handle_broken_links(repo_root, body)
        return HTTPStatus.OK, payload
    if path == routes.PROJECT_STATE_PATH:
        if body:
            raise ValueError("Projects refresh requires an empty request object")
        if dry_run:
            raise ValueError("Projects refresh does not support dry_run")
        return HTTPStatus.OK, docs_project_state.refresh_project_state_metadata(repo_root)
    if path == routes.UNCATALOGED_FILES_PATH:
        if body:
            raise ValueError("Uncataloged Files request must be empty")
        payload = docs_uncataloged_files.uncataloged_files_report(repo_root)
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Uncataloged Files refreshed."
        return HTTPStatus.OK, payload
    if path == routes.FOLDERS_WITHOUT_WORKS_PATH:
        if body:
            raise ValueError("Folders Without Works request must be empty")
        return HTTPStatus.OK, docs_folders_without_works.folders_without_works_report(repo_root)
    if path == routes.MISSING_SOURCE_FILES_PATH:
        if body:
            raise ValueError("Missing Source Files request must be empty")
        payload = docs_missing_source_files.missing_source_files_report(repo_root)
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Missing Source Files refreshed."
        return HTTPStatus.OK, payload
    if path == routes.IMPORT_SOURCE_PATH:
        payload = handle_import_source(repo_root, body, dry_run)
        return HTTPStatus.OK, payload
    if path == routes.IMPORT_DOC_PATH:
        if dry_run or document_upload is None:
            raise ValueError("Import doc requires its native upload envelope and does not support dry_run")
        return HTTPStatus.OK, docs_import_doc.import_doc(repo_root, body, document_upload)
    if path == routes.SOURCE_MEDIA_PREPARE_PATH:
        return HTTPStatus.OK, docs_source_media_service.prepare_source_media_identity(repo_root, body)
    if path == routes.CREATE_PATH:
        if str(body.get("collection") or "").strip().lower() == "catalogue":
            raise ValueError("Catalogue documents are created through Regenerate")
        try:
            return HTTPStatus.OK, handle_create(repo_root, body, dry_run)
        except DocumentCreateCommittedError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.REBUILD_DOCUMENT_PATH:
        if dry_run:
            raise ValueError("Rebuild document does not support dry_run")
        return HTTPStatus.OK, docs_document_rebuild.rebuild_document(repo_root, body)
    if path == routes.REFRESH_DISCOVERY_PATH:
        if body:
            raise ValueError("Refresh Search and Recent requires an empty request object")
        if dry_run:
            raise ValueError("Refresh Search and Recent does not support dry_run")
        payload = docs_discovery_refresh.refresh_search_and_recent(repo_root)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.MOVE_PATH:
        payload = docs_management_position.position_document(repo_root, body, dry_run=dry_run)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.ORDER_CHILDREN_PATH:
        payload = docs_management_position.order_document_children(repo_root, body, dry_run=dry_run)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.DELETE_PATH:
        payload = docs_management_delete.delete_documents(repo_root, body, dry_run=dry_run)
        return (HTTPStatus.OK if payload["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR), payload
    if path == routes.STATIC_HTML_EXPORT_PREVIEW_PATH:
        return HTTPStatus.OK, docs_static_html_export.preview_static_html_export(repo_root, body)
    if path == routes.STATIC_HTML_EXPORT_APPLY_PATH:
        if dry_run:
            raise ValueError("static HTML snapshot apply does not support dry_run")
        try:
            return HTTPStatus.OK, docs_static_html_export.apply_static_html_snapshot(repo_root, body)
        except docs_static_html_export.StaticHtmlSnapshotApplyConflict as error:
            return HTTPStatus.CONFLICT, error.payload

    raise FileNotFoundError("Not found")
