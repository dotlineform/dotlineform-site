#!/usr/bin/env python3
"""Docs management route dispatcher for Local Studio."""

from __future__ import annotations

import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

import docs_activity  # noqa: E402
import docs_import_source_service as import_source_service  # noqa: E402
import docs_management_mutations as mutations  # noqa: E402
import docs_management_routes as routes  # noqa: E402
import docs_scope_manifest  # noqa: E402
import docs_source_config_report  # noqa: E402
import docs_source_config_settings  # noqa: E402
import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_management_broken_links_service import handle_broken_links  # noqa: E402
from docs_management_capabilities_service import capabilities_payload  # noqa: E402
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
    viewer_url_for,
)
from docs_management_import_service import handle_import_source, import_source_dependencies  # noqa: E402
from docs_management_mutation_service import (  # noqa: E402
    execute_management_mutation_plan,
    handle_create,
    handle_delete_apply,
    handle_move,
    handle_scope_create_apply,
    handle_scope_delete_apply,
    handle_update_metadata,
    handle_update_viewability,
    handle_update_viewability_bulk,
)
from docs_management_read_service import (  # noqa: E402
    docs_api_query_value,
    docs_generated_read_payload,
    docs_management_get_payload,
)
from docs_management_source_service import detect_preferred_markdown_app, open_source_doc  # noqa: E402


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
    if path in {routes.IMPORT_SOURCE_PATH, routes.IMPORT_HTML_PATH}:
        payload = handle_import_source(repo_root, body, dry_run)
        docs_activity.maybe_attach_import_source_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK, payload
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
