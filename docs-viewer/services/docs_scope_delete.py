#!/usr/bin/env python3
"""Docs Viewer top-level scope deletion planning and apply."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from docs_lifecycle_paths import (
    delete_manifest_paths,
    path_record,
    resolve_manifest_path,
)
from docs_route_lifecycle import (
    manage_default_route_ids_for_scope,
    remove_public_route_record,
    route_registry_path_records,
)
from docs_scope_config import (
    CONFIG_REL_PATH,
    load_docs_scope_configs,
    resolve_external_data_marker_path,
)
from docs_scope_manifest import (
    LIFECYCLE_APPLY_SCHEMA_VERSION,
    LIFECYCLE_PREVIEW_SCHEMA_VERSION,
    MANIFEST_REL_PATH,
    SCOPE_DELETE_CHANGE_KINDS,
    load_manifest,
    manifest_scopes_by_id,
    normalize_scope_id,
    remove_scope_config,
    remove_scope_manifest_record,
    require_confirmed,
    scope_delete_eligible,
)

def manifest_delete_path_records(repo_root: Path, record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    delete_files = []
    missing_files = []
    recorded_paths: set[tuple[str, str]] = set()
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    external_root_text = str(metadata.get("external_data_root") or "").strip()
    external_data_root = (
        resolve_external_data_marker_path(external_root_text, field="external_data_root")
        if external_root_text
        else None
    )
    for file_record in record.get("files", []):
        if not isinstance(file_record, dict):
            continue
        kind = str(file_record.get("kind") or "file").strip() or "file"
        if kind in SCOPE_DELETE_CHANGE_KINDS:
            continue
        path_text = str(file_record.get("path") or "").strip()
        if not path_text:
            continue
        path = resolve_manifest_path(
            repo_root,
            path_text,
            field="manifest file path",
            external_data_root=external_data_root,
        )

        def append_planned_path(planned_kind: str, planned_path: Path) -> None:
            key = (planned_kind, planned_path.as_posix())
            if key in recorded_paths:
                return
            recorded_paths.add(key)
            planned = path_record(repo_root, planned_kind, planned_path, action="delete")
            if planned_path.exists():
                delete_files.append(planned)
            else:
                missing_files.append(planned)

        append_planned_path(kind, path)
        if kind in {"published_search_index", "public_search_index"} and path.parent.exists():
            append_planned_path(kind.removesuffix("_index") + "_root", path.parent)
    return delete_files, missing_files


def apply_delete_build_commands(repo_root: Path, scope_id: str, *, dry_run: bool) -> list[dict[str, Any]]:
    status = "planned" if dry_run else "completed"
    remaining_scope_ids = [
        config_scope_id
        for config_scope_id in sorted(load_docs_scope_configs(repo_root))
        if config_scope_id != scope_id
    ]
    commands = [
        {
            "command": "./docs-viewer/build/build_docs.py --write",
            "status": status,
        },
    ]
    commands.extend(
        {
            "command": f"./docs-viewer/build/build_search.py --scope {remaining_scope_id} --write",
            "status": status,
        }
        for remaining_scope_id in remaining_scope_ids
    )
    return commands


def apply_delete_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_all_docs_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_delete_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "scope delete is not allowed")

    scope_id = str(preview["scope_id"])
    fallback_scope_id = next(
        (configured_scope_id for configured_scope_id in load_docs_scope_configs(repo_root) if configured_scope_id != scope_id),
        "",
    )
    manifest = load_manifest(repo_root)
    rebuild = None
    if not dry_run:
        delete_manifest_paths(repo_root, preview["delete_files"])
        remove_scope_config(repo_root, scope_id)
        if str(preview.get("scope_type") or "").strip() == "public":
            remove_public_route_record(repo_root, scope_id)
        remove_scope_manifest_record(repo_root, scope_id, manifest)
        rebuild = rebuild_all_docs_outputs(repo_root)

    return {
        "ok": True,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "action": "delete_scope",
        "operation": "apply",
        "scope_id": scope_id,
        "fallback_scope_id": fallback_scope_id,
        "created_files": [],
        "changed_files": preview["changed_files"],
        "deleted_files": preview["delete_files"],
        "missing_files": preview["missing_files"],
        "build_commands": apply_delete_build_commands(repo_root, scope_id, dry_run=dry_run),
        "urls": {
            "management": "/docs/",
            "public": "",
        },
        "rebuild": rebuild,
        "summary_text": (
            f"Deleted Docs Viewer scope {scope_id}."
            if not dry_run
            else f"Validated delete apply for Docs Viewer scope {scope_id}."
        ),
        "dry_run": dry_run,
    }


def plan_delete_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope_id = normalize_scope_id(body.get("scope_id") or body.get("scope"))
    manifest = load_manifest(repo_root)
    record = manifest_scopes_by_id(manifest).get(scope_id)
    if record is None:
        return {
            "ok": True,
            "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
            "action": "delete_scope",
            "operation": "preview",
            "scope_id": scope_id,
            "allowed": False,
            "blockers": ["scope is not recorded in the docs scope manifest"],
            "delete_files": [],
            "missing_files": [],
            "changed_files": [],
            "build_commands": [],
        }
    if not scope_delete_eligible(record):
        return {
            "ok": True,
            "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
            "action": "delete_scope",
            "operation": "preview",
            "scope_id": scope_id,
            "allowed": False,
            "blockers": ["scope is system-owned or was not created by the scope lifecycle tool"],
            "delete_files": [],
            "missing_files": [],
            "changed_files": [],
            "build_commands": [],
        }

    protected_manage_routes = manage_default_route_ids_for_scope(repo_root, scope_id)
    if protected_manage_routes:
        return {
            "ok": True,
            "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
            "action": "delete_scope",
            "operation": "preview",
            "scope_id": scope_id,
            "allowed": False,
            "blockers": [
                "scope is the default scope for management route(s): "
                + ", ".join(protected_manage_routes)
            ],
            "delete_files": [],
            "missing_files": [],
            "changed_files": [],
            "build_commands": [],
        }

    delete_files, missing_files = manifest_delete_path_records(repo_root, record)

    changed_files = [
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
    ]
    if str(record.get("scope_type") or "").strip() == "public":
        changed_files.extend(route_registry_path_records(repo_root, action="change"))

    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "delete_scope",
        "operation": "preview",
        "scope_id": scope_id,
        "allowed": True,
        "blockers": [],
        "delete_files": delete_files,
        "missing_files": missing_files,
        "scope_type": str(record.get("scope_type") or "").strip(),
        "changed_files": changed_files,
        "build_commands": apply_delete_build_commands(repo_root, scope_id, dry_run=True),
        "summary_text": f"Previewed deletion for Docs Viewer scope {scope_id}.",
    }
