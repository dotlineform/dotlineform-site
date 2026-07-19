#!/usr/bin/env python3
"""Docs Viewer top-level scope creation planning and apply."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from docs_lifecycle_paths import path_record, write_text_atomic
from docs_media_storage import ensure_configured_scope_owned_media_directories
from docs_route_lifecycle import (
    append_public_route_record,
    normalize_route_path,
    public_route_record,
    readonly_route_text,
    route_file_for_public_path,
    route_registry_path_records,
)
from docs_scope_config import (
    CONFIG_REL_PATH,
    EXTERNAL_DATA_ROOT_MARKER,
    load_docs_scope_configs,
    resolve_external_data_root,
)
from docs_scope_external_validation import external_scope_id_sync_blocker
from docs_document_identity import (
    allocate_doc_id,
    current_doc_timestamp,
    doc_id_matches_added_date,
    is_immutable_doc_id,
)
from docs_scope_manifest import (
    LIFECYCLE_APPLY_SCHEMA_VERSION,
    LIFECYCLE_PREVIEW_SCHEMA_VERSION,
    LOCAL_EXTERNAL_MODE,
    MANIFEST_REL_PATH,
    PUBLIC_MODE,
    append_scope_config,
    append_scope_manifest_record,
    default_source_doc_text,
    load_manifest,
    local_published_docs_output_path,
    local_published_search_index_path,
    manifest_scopes_by_id,
    normalize_publishing_mode,
    normalize_scope_id,
    normalize_source_root,
    normalize_title,
    planned_external_source_root,
    planned_scope_config_record,
    planned_source_output_path,
    planned_storage_contract,
    public_projection_docs_output_path,
    public_projection_search_index_path,
    require_confirmed,
    validate_planned_storage_paths,
)

def apply_build_commands(preview: dict[str, Any], *, dry_run: bool) -> list[dict[str, Any]]:
    status = "planned" if dry_run else "completed"
    return [
        {
            **command,
            "status": status,
        }
        for command in preview.get("build_commands", [])
        if isinstance(command, dict)
    ]


def sync_public_publish_outputs(repo_root: Path, config: dict[str, Any], *, include_search: bool) -> None:
    docs_source = local_published_docs_output_path(repo_root, config)
    docs_target = public_projection_docs_output_path(repo_root, config)
    if docs_source.exists():
        shutil.copytree(docs_source, docs_target, dirs_exist_ok=True)
    if include_search:
        search_source = local_published_search_index_path(repo_root, config)
        search_target = public_projection_search_index_path(repo_root, config)
        if search_source.exists():
            search_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(search_source, search_target)


def apply_create_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_scope_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_create_scope_preview(repo_root, body)
    manifest = load_manifest(repo_root)
    scope_id = str(preview["scope_id"])
    source_root = planned_source_output_path(repo_root, preview["planned_scope_config"])
    raw_source = preview["planned_scope_config"]["source"]
    documents_root = source_root / str(raw_source["documents_path"])
    sub_scopes_root = source_root / str(raw_source["sub_scopes_path"])
    default_doc_path = documents_root / f"{preview['planned_scope_config']['default_doc_id']}.md"
    rebuild = None

    if not dry_run:
        source_root.mkdir(parents=True, exist_ok=False)
        documents_root.mkdir(exist_ok=False)
        sub_scopes_root.mkdir(exist_ok=False)
        write_text_atomic(
            default_doc_path,
            default_source_doc_text(
                str(preview["title"]),
                str(preview["planned_document_identity"]["doc_id"]),
                str(preview["planned_document_identity"]["added_date"]),
            ),
        )
        append_scope_config(repo_root, preview["planned_scope_config"])
        created_config = load_docs_scope_configs(repo_root)[scope_id]
        ensure_configured_scope_owned_media_directories(
            repo_root,
            {scope_id: created_config},
        )
        if preview["urls"]["public"]:
            route_path = route_file_for_public_path(repo_root, str(preview["urls"]["public"]))
            write_text_atomic(
                route_path,
                readonly_route_text(
                    str(preview["title"]),
                    scope_id,
                    str(preview["urls"]["public"]),
                ),
            )
            append_public_route_record(
                repo_root,
                public_route_record(
                    scope_id,
                    str(preview["urls"]["public"]),
                    title=str(preview["title"]),
                ),
            )
        append_scope_manifest_record(repo_root, preview, manifest)
        rebuild = rebuild_scope_outputs(
            repo_root,
            scope_id,
            include_search=True,
        )
        if preview["publishing_mode"] == PUBLIC_MODE:
            sync_public_publish_outputs(
                repo_root,
                preview["planned_scope_config"],
                include_search=True,
            )

    return {
        "ok": True,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "action": "create_scope",
        "operation": "apply",
        "scope_id": scope_id,
        "title": preview["title"],
        "publishing_mode": preview["publishing_mode"],
        "planned_document_identity": preview["planned_document_identity"],
        "storage_contract": preview.get("storage_contract", {}),
        "created_files": preview["created_files"],
        "publish_files": preview.get("publish_files", []),
        "changed_files": preview["changed_files"],
        "deleted_files": [],
        "missing_files": [],
        "build_commands": apply_build_commands(preview, dry_run=dry_run),
        "urls": preview["urls"],
        "rebuild": rebuild,
        "summary_text": (
            f"Created Docs Viewer scope {scope_id}."
            if not dry_run
            else f"Validated create apply for Docs Viewer scope {scope_id}."
        ),
        "dry_run": dry_run,
    }


def plan_create_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope_id = normalize_scope_id(body.get("scope_id"))
    title = normalize_title(body.get("title"))
    publishing_mode = normalize_publishing_mode(body.get("publishing_mode"))
    planned_identity = body.get("planned_document_identity")
    if planned_identity is None:
        added_date = current_doc_timestamp()
        default_doc_id = allocate_doc_id(added_date)
    else:
        if not isinstance(planned_identity, dict):
            raise ValueError("planned_document_identity must be an object")
        default_doc_id = str(planned_identity.get("doc_id") or "").strip()
        added_date = str(planned_identity.get("added_date") or "").strip()
        if not is_immutable_doc_id(default_doc_id):
            raise ValueError("planned_document_identity.doc_id must be an immutable document ID")
        if not doc_id_matches_added_date(default_doc_id, added_date):
            raise ValueError("planned_document_identity added_date must match its document ID timestamp")
    external_data_root = resolve_external_data_root() if publishing_mode == LOCAL_EXTERNAL_MODE else None
    if external_data_root is not None:
        sync_blocker = external_scope_id_sync_blocker(scope_id, external_data_root)
        if sync_blocker:
            raise ValueError(sync_blocker)
    source_root = (
        planned_external_source_root(scope_id, external_data_root)
        if external_data_root is not None
        else normalize_source_root(body.get("source_root"), scope_id)
    )
    public_route_path = normalize_route_path(body.get("public_route_path")) if publishing_mode == PUBLIC_MODE else ""
    planned_scope_config = planned_scope_config_record(
        scope_id,
        source_root,
        public_route_path,
        default_doc_id,
        publishing_mode,
        external_data_root,
    )
    validate_planned_storage_paths(scope_id, publishing_mode, planned_scope_config)

    existing_configs = load_docs_scope_configs(repo_root)
    if scope_id in existing_configs:
        raise ValueError(f"scope_id {scope_id!r} already exists")

    manifest = load_manifest(repo_root)
    if scope_id in manifest_scopes_by_id(manifest):
        raise ValueError(f"scope_id {scope_id!r} already exists in docs scope manifest")

    created_source_root = planned_source_output_path(repo_root, planned_scope_config)
    raw_source = planned_scope_config["source"]
    created_documents_root = created_source_root / str(raw_source["documents_path"])
    created_sub_scopes_root = created_source_root / str(raw_source["sub_scopes_path"])
    created_files = [
        path_record(repo_root, "source_root", created_source_root, action="create"),
        path_record(repo_root, "source_documents_root", created_documents_root, action="create"),
        path_record(repo_root, "default_source_doc", created_documents_root / f"{default_doc_id}.md", action="create"),
        path_record(repo_root, "source_sub_scopes_root", created_sub_scopes_root, action="create"),
    ]
    docs_output = local_published_docs_output_path(repo_root, planned_scope_config)
    raw_media = planned_scope_config["published"]["media"]
    for media_type, media in raw_media.items():
        location = media["location"]
        provider = str(location["provider"])
        if provider == "r2":
            continue
        media_path = (
            docs_output / "media" / media_type
            if provider == "external_local"
            else repo_root / str(location["path"])
        )
        created_files.append(
            path_record(repo_root, f"scope_media_{media_type}_root", media_path, action="create")
        )
        if provider == "repository":
            created_files.append(
                path_record(
                    repo_root,
                    f"scope_media_{media_type}_marker",
                    media_path / ".gitkeep",
                    action="create",
                )
            )
    changed_files = [
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
    ]
    if public_route_path:
        created_files.append(path_record(repo_root, "route_file", route_file_for_public_path(repo_root, public_route_path), action="create"))
        changed_files.extend(route_registry_path_records(repo_root, action="change"))
    created_files.append(path_record(repo_root, "published_docs_root", docs_output, action="create"))
    created_files.extend(
        [
            path_record(repo_root, "published_docs_index_tree", docs_output / "index-tree.json", action="create"),
            path_record(repo_root, "published_docs_recent", docs_output / "recent.json", action="create"),
            path_record(repo_root, "published_docs_payload_root", docs_output / "by-id", action="create"),
            path_record(
                repo_root,
                "published_search_index",
                local_published_search_index_path(repo_root, planned_scope_config),
                action="create",
            ),
        ]
    )

    publish_files: list[dict[str, Any]] = []
    if publishing_mode == PUBLIC_MODE:
        public_output = public_projection_docs_output_path(repo_root, planned_scope_config)
        publish_files.append(path_record(repo_root, "public_docs_root", public_output, action="publish"))
        publish_files.extend(
            [
                path_record(repo_root, "public_docs_index_tree", public_output / "index-tree.json", action="publish"),
                path_record(repo_root, "public_docs_recent", public_output / "recent.json", action="publish"),
                path_record(repo_root, "public_docs_payload_root", public_output / "by-id", action="publish"),
            ]
        )
        publish_files.append(
            path_record(
                repo_root,
                "public_search_index",
                public_projection_search_index_path(repo_root, planned_scope_config),
                action="publish",
            )
        )

    conflicts = [
        record["path"]
        for record in [*created_files, *publish_files]
        if record.get("exists")
    ]
    if conflicts:
        raise ValueError(f"scope creation would overwrite existing paths: {', '.join(conflicts)}")

    commands = []
    commands.append({"command": f"./docs-viewer/build/build_docs.py --scope {scope_id} --write", "status": "planned"})
    commands.append({"command": f"./docs-viewer/build/build_search.py --scope {scope_id} --write", "status": "planned"})

    management_url = f"/docs/?scope={scope_id}"
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "create_scope",
        "operation": "preview",
        "scope_id": scope_id,
        "title": title,
        "publishing_mode": publishing_mode,
        "external_data_root": EXTERNAL_DATA_ROOT_MARKER if external_data_root else "",
        "planned_document_identity": {
            "doc_id": default_doc_id,
            "added_date": added_date,
        },
        "planned_scope_config": planned_scope_config,
        "storage_contract": planned_storage_contract(
            {
                "publishing_mode": publishing_mode,
                "planned_scope_config": planned_scope_config,
                "external_data_root": EXTERNAL_DATA_ROOT_MARKER if external_data_root else "",
            }
        ),
        "created_files": created_files,
        "publish_files": publish_files,
        "changed_files": changed_files,
        "build_commands": commands,
        "urls": {
            "management": management_url,
            "public": public_route_path,
        },
        "warnings": [],
        "summary_text": f"Previewed new Docs Viewer scope {scope_id}.",
    }
