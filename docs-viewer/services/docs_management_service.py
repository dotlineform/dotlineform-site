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
import docs_deploy_repo  # noqa: E402
import docs_management_document_target  # noqa: E402
import docs_management_draft  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_local_links  # noqa: E402
import docs_media_report  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_publish  # noqa: E402
import docs_pre_publish  # noqa: E402
import docs_project_state  # noqa: E402
import docs_missing_source_files  # noqa: E402
import docs_uncataloged_files  # noqa: E402
import docs_source_config_report  # noqa: E402
import docs_source_config_settings  # noqa: E402
import docs_static_html_export  # noqa: E402
import docs_staged_media_service  # noqa: E402
import docs_collection_lifecycle  # noqa: E402
import docs_catalogue_regeneration  # noqa: E402
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
    DocumentPlacementCommittedError,
    CollectionDocumentDeleteApplyError,
    execute_management_mutation_plan,
    handle_assign_field_group,
    handle_create,
    handle_delete_apply,
    handle_move,
    handle_collection_create_apply,
    handle_collection_delete_apply,
    handle_update_metadata,
)
from docs_management_read_service import (  # noqa: E402
    docs_api_query_value,
    docs_generated_read_payload,
    docs_management_get_payload as read_docs_management_get_payload,
)
from docs_management_source_service import detect_preferred_markdown_app, open_publication_ignore, open_source_doc, rebuild_source_body  # noqa: E402
from docs_workspace_config import load_docs_stage, require_document_authoring  # noqa: E402


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
) -> tuple[HTTPStatus, dict[str, object]]:
    if "scope" in body or "parent_scope" in body:
        raise ValueError("scope is retired; supply an explicit stage and optional collection")
    if "sub_scope" in body:
        raise ValueError("sub_scope is retired; use collection")
    if path in {routes.DEPLOY_REPO_PREVIEW_PATH, routes.DEPLOY_REPO_APPLY_PATH}:
        if body.get("stage") != "published":
            raise ValueError("Deploy Repo requires stage published")
    elif "stage" in body:
        selected = load_docs_stage(repo_root, body["stage"])
        if path in {routes.DOCS_MEDIA_REPORT_PATH, routes.BROKEN_LINKS_PATH, routes.OPEN_MEDIA_SOURCE_PATH}:
            pass
        elif path in {
            routes.PRE_PUBLISH_PREVIEW_PATH, routes.PRE_PUBLISH_APPLY_PATH,
            routes.PUBLISH_CONFIRM_PATH, routes.PUBLISH_APPLY_PATH,
        }:
            required_stage = "working" if path in {routes.PRE_PUBLISH_PREVIEW_PATH, routes.PRE_PUBLISH_APPLY_PATH} else "pre-publish"
            if selected.stage != required_stage:
                raise ValueError(f"This action requires stage {required_stage}")
        else:
            require_document_authoring(selected)
    if path == routes.PRE_PUBLISH_PREVIEW_PATH:
        return HTTPStatus.OK, docs_pre_publish.preview_pre_publish(repo_root, body)
    if path == routes.CATALOGUE_REGENERATE_PREVIEW_PATH:
        return HTTPStatus.OK, docs_catalogue_regeneration.preview_catalogue_regeneration(repo_root, body)
    if path == routes.CATALOGUE_REGENERATE_APPLY_PATH:
        if dry_run:
            raise ValueError("Catalogue Regenerate apply does not support dry_run")
        try:
            return HTTPStatus.OK, docs_catalogue_regeneration.apply_catalogue_regeneration(repo_root, body)
        except docs_catalogue_regeneration.CatalogueRegenerationConflict as error:
            return HTTPStatus.CONFLICT, {"ok": False, "error": str(error)}
        except docs_catalogue_regeneration.CatalogueRegenerationApplyError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.PRE_PUBLISH_APPLY_PATH:
        if dry_run:
            raise ValueError("Pre-publish apply does not support dry_run")
        return HTTPStatus.OK, docs_pre_publish.apply_pre_publish(repo_root, body)
    if path == routes.SET_DRAFT_PATH:
        try:
            return HTTPStatus.OK, docs_management_draft.set_draft(repo_root, body, dry_run=dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
    if path == routes.SOURCE_REBUILD_PATH:
        return HTTPStatus.OK, rebuild_source_body(repo_root, body, dry_run)
    if path == routes.OPEN_SOURCE_PATH:
        return HTTPStatus.OK, open_source_doc(repo_root, body, dry_run)
    if path == routes.OPEN_PUBLICATION_IGNORE_PATH:
        return HTTPStatus.OK, open_publication_ignore(repo_root, body, dry_run)
    if path == routes.OPEN_DIAGRAM_SOURCE_PATH:
        return HTTPStatus.OK, docs_diagram_source_service.open_diagram_source(repo_root, body, dry_run)
    if path == routes.OPEN_LOCAL_TARGET_PATH:
        return docs_local_links.open_local_target_response(repo_root, body, dry_run=dry_run)
    if path == routes.OPEN_MEDIA_SOURCE_PATH:
        return HTTPStatus.OK, docs_media_report.open_media_source(repo_root, body, dry_run=dry_run)
    if path == routes.BROKEN_LINKS_PATH:
        payload = handle_broken_links(repo_root, body)
        return HTTPStatus.OK, payload
    if path == routes.PROJECT_STATE_PATH:
        payload = docs_project_state.ProjectStateProducer(repo_root=repo_root).run()
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Project State refreshed."
        return HTTPStatus.OK, payload
    if path == routes.DOCS_MEDIA_REPORT_PATH:
        if set(body) != {"stage"}:
            raise ValueError("Docs Media request must contain only stage")
        report = docs_media_report.build_docs_media_report(
            repo_root,
            load_docs_stage(repo_root, body["stage"]),
        )
        return HTTPStatus.OK, {
            "ok": True,
            "dry_run": dry_run,
            "summary_text": "Docs Media refreshed.",
            "report": report,
        }
    if path == routes.UNCATALOGED_FILES_PATH:
        if body:
            raise ValueError("Uncataloged Files request must be empty")
        payload = docs_uncataloged_files.UncatalogedFilesProducer(repo_root=repo_root).run()
        payload["ok"] = True
        payload["dry_run"] = dry_run
        payload["summary_text"] = "Uncataloged Files refreshed."
        return HTTPStatus.OK, payload
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
        payload = docs_source_config_settings.apply_stage_settings_change(
            repo_root,
            changes,
            stage=body.get("stage"),
            dry_run=dry_run,
        )
        if payload.get("requires_rebuild") and not dry_run:
            payload["rebuild"] = write_rebuild.rebuild_stage_outputs(repo_root, include_search=False, stage=body.get("stage"))
        else:
            payload["rebuild"] = None
        if payload.get("changed") and not dry_run:
            log_event(
                repo_root,
                "docs_source_config_settings",
                {
                    "stage": body["stage"],
                    "fields": sorted(payload.get("changes", {}).keys()),
                    "source_config_path": payload.get("source_config_path", ""),
                },
            )
        payload["dry_run"] = dry_run
        return HTTPStatus.OK, payload
    if path == routes.IMPORT_SOURCE_PATH:
        payload = handle_import_source(repo_root, body, dry_run)
        return HTTPStatus.OK, payload
    if path == routes.STAGED_MEDIA_PREVIEW_PATH:
        return HTTPStatus.OK, docs_staged_media_service.preview_staged_media(repo_root, body)
    if path == routes.STAGED_MEDIA_APPLY_PATH:
        payload = docs_staged_media_service.apply_staged_media(repo_root, body, write=not dry_run)
        if not dry_run:
            log_event(
                repo_root,
                "docs-staged-media-publish",
                {
                    "stage": payload["stage"],
                    "media_kind": payload["media_kind"],
                    "staged_filename": payload["staged_filename"],
                    "media_identity": payload["media_identity"],
                    "publish_status": payload["publish"]["status"],
                },
            )
        return HTTPStatus.OK, payload
    if path == routes.UPDATE_METADATA_PATH:
        try:
            return HTTPStatus.OK, handle_update_metadata(repo_root, body, dry_run)
        except DocumentPlacementCommittedError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
    if path == routes.ASSIGN_FIELD_GROUP_PATH:
        try:
            return HTTPStatus.OK, handle_assign_field_group(repo_root, body, dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
    if path == routes.CREATE_PATH:
        try:
            return HTTPStatus.OK, handle_create(repo_root, body, dry_run)
        except DocumentCreateCommittedError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.REBUILD_PATH:
        payload = write_rebuild.rebuild_stage_outputs(
            repo_root,
            include_search=True,
            stage=body.get("stage"),
        )
        payload["summary_text"] = f"Docs and docs search rebuilt for {body['stage']}."
        return HTTPStatus.OK, payload
    if path == routes.MOVE_PATH:
        try:
            return HTTPStatus.OK, handle_move(repo_root, body, dry_run)
        except DocumentPlacementCommittedError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
    if path == routes.DELETE_PREVIEW_PATH:
        if "collection" in body:
            return (
                HTTPStatus.OK,
                mutations.plan_collection_delete_preview(repo_root, body),
            )
        doc_ids = mutations.require_delete_doc_ids(body.get("doc_ids"))
        return HTTPStatus.OK, mutations.plan_delete_preview(repo_root, doc_ids, stage=body.get("stage"))
    if path == routes.DELETE_APPLY_PATH:
        try:
            return HTTPStatus.OK, handle_delete_apply(repo_root, body, dry_run)
        except mutations.ManagedDocumentRevisionConflict as error:
            return HTTPStatus.CONFLICT, error.payload
        except CollectionDocumentDeleteApplyError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.COLLECTION_CREATE_PREVIEW_PATH:
        payload = docs_collection_lifecycle.plan_create_collection_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.COLLECTION_CREATE_APPLY_PATH:
        try:
            return HTTPStatus.OK, handle_collection_create_apply(repo_root, body, dry_run)
        except docs_collection_lifecycle.CollectionLifecycleApplyError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.COLLECTION_DELETE_PREVIEW_PATH:
        payload = docs_collection_lifecycle.plan_delete_collection_preview(repo_root, body)
        payload["dry_run"] = True
        return HTTPStatus.OK, payload
    if path == routes.COLLECTION_DELETE_APPLY_PATH:
        try:
            return HTTPStatus.OK, handle_collection_delete_apply(repo_root, body, dry_run)
        except docs_collection_lifecycle.CollectionLifecycleApplyError as error:
            return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload
    if path == routes.PUBLISH_CONFIRM_PATH:
        return HTTPStatus.OK, docs_publish.preview_publish(repo_root, body)
    if path == routes.PUBLISH_APPLY_PATH:
        if dry_run:
            raise ValueError("Publish apply does not support dry_run")
        return HTTPStatus.OK, docs_publish.apply_publish(repo_root, body)
    if path == routes.DEPLOY_REPO_PREVIEW_PATH:
        return HTTPStatus.OK, docs_deploy_repo.preview_deploy_repo(repo_root, body)
    if path == routes.DEPLOY_REPO_APPLY_PATH:
        if dry_run:
            raise ValueError("Deploy Repo apply does not support dry_run")
        return HTTPStatus.OK, docs_deploy_repo.apply_deploy_repo(repo_root, body)
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
