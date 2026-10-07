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

import docs_diagram_source_service  # noqa: E402
import docs_management_document_target  # noqa: E402
import docs_management_draft  # noqa: E402
import docs_selected_documents  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_local_links  # noqa: E402
import docs_media_actions  # noqa: E402
import docs_media_metadata  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_publish  # noqa: E402
import docs_project_state  # noqa: E402
import docs_missing_source_files  # noqa: E402
import docs_uncataloged_files  # noqa: E402
import docs_folders_without_works  # noqa: E402
import docs_work_downloads  # noqa: E402
import docs_work_links  # noqa: E402
import docs_source_config_settings  # noqa: E402
import docs_static_html_export  # noqa: E402
import docs_source_media_service  # noqa: E402
from docs_source_media_upload import SourceMediaUpload  # noqa: E402
import docs_catalogue_regeneration  # noqa: E402
import docs_document_rebuild  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
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
    CollectionDocumentDeleteApplyError,
    execute_management_mutation_plan,
    handle_assign_field_group,
    handle_create,
    handle_delete_apply,
    handle_move,
)
from docs_management_read_service import (  # noqa: E402
    docs_api_query_value,
    docs_generated_read_payload,
    docs_management_get_payload as read_docs_management_get_payload,
)
from docs_management_source_service import detect_preferred_markdown_app, open_publication_ignore, open_recent_exclusions, open_source_doc, read_source_context, save_source_document  # noqa: E402
from docs_workspace_config import load_docs_working_config, require_document_authoring  # noqa: E402


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
    media_upload: SourceMediaUpload | None = None,
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
    if path == routes.CATALOGUE_REGENERATE_PATH:
        if dry_run:
            raise ValueError("Catalogue Regenerate does not support dry_run")
        try:
            return HTTPStatus.OK, docs_catalogue_regeneration.regenerate_catalogue(repo_root, body)
        except docs_catalogue_regeneration.CatalogueRegenerationError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.SET_DRAFT_PATH:
        try:
            return HTTPStatus.OK, docs_management_draft.set_draft(repo_root, body, dry_run=dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
    if path == routes.SET_SELECTED_PATH:
        return HTTPStatus.OK, docs_selected_documents.set_selected(repo_root, body, dry_run=dry_run)
    if path == routes.SOURCE_SAVE_PATH:
        return HTTPStatus.OK, save_source_document(repo_root, body, dry_run)
    if path == routes.SOURCE_CONTEXT_PATH:
        return HTTPStatus.OK, read_source_context(repo_root, body)
    if path == routes.OPEN_SOURCE_PATH:
        return HTTPStatus.OK, open_source_doc(repo_root, body, dry_run)
    if path == routes.OPEN_PUBLICATION_IGNORE_PATH:
        return HTTPStatus.OK, open_publication_ignore(repo_root, body, dry_run)
    if path == routes.OPEN_RECENT_EXCLUSIONS_PATH:
        return HTTPStatus.OK, open_recent_exclusions(repo_root, body, dry_run)
    if path == routes.OPEN_DIAGRAM_SOURCE_PATH:
        return HTTPStatus.OK, docs_diagram_source_service.open_diagram_source(repo_root, body, dry_run)
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
        payload = docs_project_state.ProjectStateProducer(repo_root=repo_root).run()
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Project State refreshed."
        return HTTPStatus.OK, payload
    if path == routes.UNCATALOGED_FILES_PATH:
        if body:
            raise ValueError("Uncataloged Files request must be empty")
        payload = docs_uncataloged_files.UncatalogedFilesProducer(repo_root=repo_root).run()
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
        payload = docs_missing_source_files.MissingSourceFilesProducer(repo_root=repo_root).run()
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Missing Source Files refreshed."
        return HTTPStatus.OK, payload
    if path == routes.SOURCE_CONFIG_SETTINGS_PATH:
        changes = body.get("changes")
        payload = docs_source_config_settings.apply_settings_change(
            repo_root,
            changes,
            dry_run=dry_run,
        )
        if payload.get("requires_rebuild") and not dry_run:
            payload["rebuild"] = write_rebuild.rebuild_working_outputs(repo_root, include_search=False)
        else:
            payload["rebuild"] = None
        if payload.get("changed") and not dry_run:
            log_event(
                repo_root,
                "docs_source_config_settings",
                {
                    "fields": sorted(payload.get("changes", {}).keys()),
                    "source_config_path": payload.get("source_config_path", ""),
                },
            )
        payload["dry_run"] = dry_run
        return HTTPStatus.OK, payload
    if path == routes.IMPORT_SOURCE_PATH:
        payload = handle_import_source(repo_root, body, dry_run)
        return HTTPStatus.OK, payload
    if path == routes.SOURCE_MEDIA_APPLY_PATH:
        if media_upload is None:
            raise ValueError("Source media requires a native file upload")
        payload = docs_source_media_service.apply_source_media(repo_root, body, media_upload, write=not dry_run)
        if not dry_run and not payload["requires_confirmation"]:
            log_event(
                repo_root,
                "docs-source-media-publish",
                {
                    "media_kind": payload["media_kind"],
                    "source_filename": payload["source_filename"],
                    "media_identity": payload["media_identity"],
                    "publish_status": payload["publish"]["status"],
                },
            )
        return HTTPStatus.OK, payload
    if path == routes.ASSIGN_FIELD_GROUP_PATH:
        try:
            return HTTPStatus.OK, handle_assign_field_group(repo_root, body, dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
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
    if path == routes.REBUILD_PATH:
        payload = write_rebuild.rebuild_working_outputs(
            repo_root,
            include_search=True,
        )
        payload["summary_text"] = "Docs and docs search rebuilt."
        return HTTPStatus.OK, payload
    if path == routes.MOVE_PATH:
        return HTTPStatus.OK, handle_move(repo_root, body, dry_run)
    if path == routes.DELETE_PREVIEW_PATH:
        if "collection" in body:
            if str(body.get("collection") or "").strip().lower() == "catalogue":
                raise ValueError("Catalogue documents are deleted through Regenerate")
            return (
                HTTPStatus.OK,
                mutations.plan_collection_delete_preview(repo_root, body),
            )
        doc_ids = mutations.require_delete_doc_ids(body.get("doc_ids"))
        return HTTPStatus.OK, mutations.plan_delete_preview(repo_root, doc_ids)
    if path == routes.DELETE_APPLY_PATH:
        if str(body.get("collection") or "").strip().lower() == "catalogue":
            raise ValueError("Catalogue documents are deleted through Regenerate")
        try:
            return HTTPStatus.OK, handle_delete_apply(repo_root, body, dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
        except CollectionDocumentDeleteApplyError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
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
