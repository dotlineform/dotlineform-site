#!/usr/bin/env python3
"""Docs Viewer scope ownership manifest and shared lifecycle policy."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from docs_scope_config import (
    CONFIG_REL_PATH,
    DEFAULT_DOCS_SEARCH_FIELDS,
    EXTERNAL_DATA_ROOT_MARKER,
    GENERATED_DOCUMENTS_PATH,
    GENERATED_SEARCH_PATH,
    EXTERNAL_LOCAL_PROVIDER,
    PUBLISHED_DOCUMENTS_PATH,
    PUBLISHED_SEARCH_PATH,
    PUBLIC_DOCS_OUTPUT_ROOT,
    PUBLIC_SEARCH_OUTPUT_ROOT,
    SCHEMA_VERSION as SCOPE_CONFIG_SCHEMA_VERSION,
    SCOPE_SOURCE_PATH,
    SCOPE_LIFECYCLE_TOOL_ID,
    DocsScopeConfig,
    document_source_path,
    generated_documents_path,
    generated_search_path,
    load_docs_scope_configs,
    public_documents_path,
    public_search_path,
    published_documents_path,
    published_search_path,
    resolve_external_data_marker_path,
    resolve_external_data_root,
    resolve_location_path,
    resolve_scope_path,
    safe_scope_data_path,
    source_container_path,
)
from docs_lifecycle_paths import (
    load_json_object,
    path_record,
    render_json,
    repo_relative,
    resolve_manifest_path,
    write_text_atomic,
)
from docs_route_lifecycle import (
    route_file_for_config,
)


MANIFEST_REL_PATH = Path("docs-viewer/config/scopes/docs_scope_manifest.json")
SCHEMA_VERSION = "docs_scope_manifest_v1"
LIFECYCLE_PREVIEW_SCHEMA_VERSION = "docs_scope_lifecycle_preview_v1"
LIFECYCLE_APPLY_SCHEMA_VERSION = "docs_scope_lifecycle_apply_v1"
TOOL_ID = SCOPE_LIFECYCLE_TOOL_ID
SAFE_SCOPE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PUBLIC_MODE = "public_readonly"
LOCAL_MANAGE_MODE = "local_manage"
PUBLISHING_MODES = (PUBLIC_MODE, LOCAL_MANAGE_MODE)
SCOPE_DELETE_CHANGE_KINDS = {"scope_config", "scope_manifest", "route_config", "public_route_config"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _planned_location_path(raw: Any, *, field: str, allow_external: bool) -> Path:
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    provider = str(raw.get("provider") or "").strip()
    return safe_scope_data_path(
        raw.get("path"),
        field=f"{field}.path",
        allow_external=allow_external and provider == "external_local",
    )


def _planned_role_location(config: dict[str, Any], *keys: str) -> Any:
    value: Any = config
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def planned_scope_root_path(config: dict[str, Any]) -> Path:
    return _planned_location_path(
        config.get("scope_root"),
        field="planned_scope_config.scope_root",
        allow_external=True,
    )


def local_scope_root_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    path = config.scope_root.path if isinstance(config, DocsScopeConfig) else planned_scope_root_path(config)
    return resolve_scope_path(repo_root, path)


def local_published_search_index_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return resolve_scope_path(repo_root, published_search_path(config))
    return resolve_scope_path(repo_root, planned_scope_root_path(config) / PUBLISHED_SEARCH_PATH)


def local_published_docs_output_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return resolve_scope_path(repo_root, published_documents_path(config))
    return resolve_scope_path(repo_root, planned_scope_root_path(config) / PUBLISHED_DOCUMENTS_PATH)


def local_generated_search_index_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return resolve_scope_path(repo_root, generated_search_path(config))
    return resolve_scope_path(repo_root, planned_scope_root_path(config) / GENERATED_SEARCH_PATH)


def local_generated_docs_output_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return resolve_scope_path(repo_root, generated_documents_path(config))
    return resolve_scope_path(repo_root, planned_scope_root_path(config) / GENERATED_DOCUMENTS_PATH)


def planned_source_output_path(repo_root: Path, config: dict[str, Any]) -> Path:
    return resolve_scope_path(repo_root, planned_scope_root_path(config) / SCOPE_SOURCE_PATH)


def public_projection_docs_output_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        path = public_documents_path(config)
        if path is None:
            raise ValueError(f"scope {config.scope_id!r} has no public document projection")
        return repo_root / path
    return repo_root / _planned_location_path(
        _planned_role_location(config, "public_projection", "documents", "location"),
        field="planned_scope_config.public_projection.documents.location",
        allow_external=False,
    )


def public_projection_search_index_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        path = public_search_path(config)
        if path is None:
            raise ValueError(f"scope {config.scope_id!r} has no public search projection")
        return repo_root / path
    return repo_root / _planned_location_path(
        _planned_role_location(config, "public_projection", "search", "location"),
        field="planned_scope_config.public_projection.search.location",
        allow_external=False,
    )


def git_path_status(repo_root: Path, path: Path) -> str:
    if not (repo_root / ".git").exists():
        return "unknown"
    rel_path = repo_relative(repo_root, path)
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return "tracked" if completed.returncode == 0 else "untracked"


def default_source_doc_record(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any] | None:
    if not config.default_doc_id:
        return None
    candidate = resolve_scope_path(repo_root, document_source_path(config)) / f"{config.default_doc_id}.md"
    if candidate.exists():
        return path_record(repo_root, "default_source_doc", candidate)
    return None


def backfilled_scope_record(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    scope_root = resolve_scope_path(repo_root, config.scope_root.path)
    source_root = resolve_scope_path(repo_root, source_container_path(config))
    source_documents_root = resolve_scope_path(repo_root, document_source_path(config))
    source_sub_scopes_root = resolve_scope_path(
        repo_root,
        source_container_path(config) / config.source.sub_scopes_path,
    )
    route_path = route_file_for_config(repo_root, config)
    scope_type = "public" if config.public_projection is not None else "local"
    repo_status = (
        "external"
        if config.scope_root.provider == EXTERNAL_LOCAL_PROVIDER
        else git_path_status(repo_root, source_root)
    )
    files = [
        path_record(repo_root, "scope_root", scope_root),
        path_record(repo_root, "source_root", source_root),
        path_record(repo_root, "source_documents_root", source_documents_root),
        path_record(repo_root, "source_sub_scopes_root", source_sub_scopes_root),
        path_record(repo_root, "source_media_root", resolve_location_path(repo_root, config.media.source_location)),
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH),
    ]
    default_doc = default_source_doc_record(repo_root, config)
    if default_doc is not None:
        files.append(default_doc)
    if route_path.exists():
        files.append(path_record(repo_root, "route_file", route_path))
    docs_output = resolve_scope_path(repo_root, generated_documents_path(config))
    files.append(path_record(repo_root, "generated_docs_root", docs_output))
    files.extend(
        [
            path_record(repo_root, "generated_docs_index_tree", docs_output / "index-tree.json"),
            path_record(repo_root, "generated_docs_recent", docs_output / "recent.json"),
            path_record(repo_root, "generated_docs_payload_root", docs_output / "by-id"),
            path_record(repo_root, "generated_search_index", local_generated_search_index_path(repo_root, config)),
            path_record(repo_root, "published_docs_root", local_published_docs_output_path(repo_root, config)),
            path_record(repo_root, "published_search_index", local_published_search_index_path(repo_root, config)),
        ]
    )
    if config.public_projection is not None:
        files.extend(
            [
                path_record(repo_root, "public_docs_root", public_projection_docs_output_path(repo_root, config)),
                path_record(repo_root, "public_docs_index_tree", public_projection_docs_output_path(repo_root, config) / "index-tree.json"),
                path_record(repo_root, "public_docs_recent", public_projection_docs_output_path(repo_root, config) / "recent.json"),
                path_record(repo_root, "public_docs_payload_root", public_projection_docs_output_path(repo_root, config) / "by-id"),
                path_record(repo_root, "public_search_index", public_projection_search_index_path(repo_root, config)),
            ]
        )
    return {
        "scope_id": config.scope_id,
        "scope_type": scope_type,
        "owner": "system",
        "user_created": False,
        "created_by_tool": False,
        "tool_id": "",
        "repo_status_at_creation": repo_status,
        "created_at": "",
        "updated_at": utc_now(),
        "files": files,
        "metadata": {
            "backfilled": True,
            "viewer_base_url": config.viewer_base_url,
            "default_doc_id": config.default_doc_id,
        },
    }


def build_backfilled_manifest(repo_root: Path) -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_id": TOOL_ID,
        "updated_at": utc_now(),
        "scopes": [backfilled_scope_record(repo_root, configs[scope]) for scope in sorted(configs)],
    }


def load_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = repo_root / MANIFEST_REL_PATH
    if not manifest_path.exists():
        return build_backfilled_manifest(repo_root)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"docs scope manifest is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("docs scope manifest must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"docs scope manifest schema_version must be {SCHEMA_VERSION}")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope manifest scopes must be an array")
    return payload


def manifest_scopes_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scopes: dict[str, dict[str, Any]] = {}
    for item in manifest.get("scopes", []):
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip()
        if scope_id:
            scopes[scope_id] = item
    return scopes


def reconcile_scope_manifest(
    repo_root: Path,
    *,
    write: bool = False,
) -> dict[str, Any]:
    """Refresh config-derived scope paths without replacing lifecycle ownership."""

    current = load_manifest(repo_root)
    current_by_id = manifest_scopes_by_id(current)
    configs = load_docs_scope_configs(repo_root)
    reconciled_at = utc_now()
    records: list[dict[str, Any]] = []
    for scope_id in sorted(configs):
        fresh = backfilled_scope_record(repo_root, configs[scope_id])
        existing = current_by_id.get(scope_id)
        if existing is None:
            records.append(fresh)
            continue
        metadata = dict(existing.get("metadata") or {})
        metadata.update(fresh["metadata"])
        metadata["backfilled"] = bool(
            (existing.get("metadata") or {}).get("backfilled", True)
        )
        metadata["publishing_mode"] = (
            PUBLIC_MODE
            if configs[scope_id].public_projection is not None
            else LOCAL_MANAGE_MODE
        )
        if configs[scope_id].scope_root.provider == EXTERNAL_LOCAL_PROVIDER:
            metadata["external_data_root"] = EXTERNAL_DATA_ROOT_MARKER
        else:
            metadata.pop("external_data_root", None)
        records.append(
            {
                **fresh,
                "owner": existing.get("owner", fresh["owner"]),
                "user_created": existing.get("user_created", fresh["user_created"]),
                "created_by_tool": existing.get("created_by_tool", fresh["created_by_tool"]),
                "tool_id": existing.get("tool_id", fresh["tool_id"]),
                "repo_status_at_creation": existing.get(
                    "repo_status_at_creation",
                    fresh["repo_status_at_creation"],
                ),
                "created_at": existing.get("created_at", fresh["created_at"]),
                "updated_at": reconciled_at,
                "metadata": metadata,
            }
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool_id": str(current.get("tool_id") or TOOL_ID),
        "updated_at": reconciled_at,
        "scopes": records,
    }
    if write:
        write_text_atomic(repo_root / MANIFEST_REL_PATH, render_json(payload))
    return payload


def scope_delete_eligible(record: dict[str, Any] | None) -> bool:
    return bool(
        record
        and record.get("user_created") is True
        and record.get("created_by_tool") is True
    )


def normalize_scope_id(value: Any) -> str:
    scope_id = str(value or "").strip().lower()
    if not scope_id:
        raise ValueError("scope_id is required")
    if not SAFE_SCOPE_ID_PATTERN.match(scope_id):
        raise ValueError("scope_id must use lowercase letters, numbers, and single hyphen separators")
    return scope_id


def normalize_title(value: Any) -> str:
    title = re.sub(r"\s+", " ", str(value or "")).strip()
    if not title:
        raise ValueError("title is required")
    return title


def normalize_publishing_mode(value: Any) -> str:
    mode = str(value or "").strip().lower()
    if mode not in PUBLISHING_MODES:
        raise ValueError(f"publishing_mode must be one of: {', '.join(PUBLISHING_MODES)}")
    return mode


def bool_value(payload: dict[str, Any], key: str, default: bool) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    raise ValueError(f"{key} must be a boolean")


def require_confirmed(body: dict[str, Any]) -> None:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to apply scope lifecycle changes")


def planned_external_scope_root(scope_id: str, external_data_root: Path) -> Path:
    return external_data_root / "scopes" / scope_id


def planned_external_scope_root_marker(scope_id: str) -> Path:
    return Path(EXTERNAL_DATA_ROOT_MARKER) / "scopes" / scope_id


def planned_public_docs_projection(scope_id: str) -> Path:
    return PUBLIC_DOCS_OUTPUT_ROOT / scope_id


def planned_public_search_projection(scope_id: str) -> Path:
    return PUBLIC_SEARCH_OUTPUT_ROOT / scope_id / "index.json"


def planned_scope_type(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public"
    return "local"


def planned_scope_meta(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public scope"
    return "local management"


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_planned_storage_paths(scope_id: str, publishing_mode: str, config: dict[str, Any]) -> None:
    scope_root = planned_scope_root_path(config)
    expected_scope_root = resolve_external_data_root() / "scopes" / scope_id
    if scope_root != expected_scope_root:
        raise ValueError(
            f"scope {scope_id!r} must use {EXTERNAL_DATA_ROOT_MARKER}/scopes/{scope_id}"
        )
    if publishing_mode == PUBLIC_MODE:
        publish_output = _planned_location_path(
            _planned_role_location(config, "public_projection", "documents", "location"),
            field="planned_scope_config.public_projection.documents.location",
            allow_external=False,
        )
        publish_search_output = _planned_location_path(
            _planned_role_location(config, "public_projection", "search", "location"),
            field="planned_scope_config.public_projection.search.location",
            allow_external=False,
        )
        if not path_is_relative_to(publish_output, PUBLIC_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must publish docs under site/assets/data/docs/scopes"
            )
        if not path_is_relative_to(publish_search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must publish search under site/assets/data/search"
            )
    elif config.get("public_projection") is not None:
        raise ValueError(f"local scope {scope_id!r} must not configure a public projection")


def planned_scope_config_record(
    scope_id: str,
    scope_root: Path,
    public_route_path: str,
    default_doc_id: str,
    publishing_mode: str,
    external_data_root: Path | None = None,
) -> dict[str, Any]:
    viewer_base_url = public_route_path or "/docs/"
    del scope_root, external_data_root
    scope_root_path = planned_external_scope_root_marker(scope_id).as_posix()
    media_types: dict[str, Any] = {}
    public_media: dict[str, Any] = {}
    for media_type in ("img", "svg", "files"):
        media_types[media_type] = {"build_inputs": []}
        if publishing_mode == PUBLIC_MODE:
            if media_type == "svg":
                media_provider = "repository"
                media_path = f"{planned_public_docs_projection(scope_id).as_posix()}/media/svg"
                served_path = f"/assets/data/docs/scopes/{scope_id}/media/svg"
            else:
                media_provider = "r2"
                media_path = f"docs/{scope_id}/{media_type}"
                served_path = f"https://media.dotlineform.com/docs/{scope_id}/{media_type}"
            public_media[media_type] = {
                "location": {"provider": media_provider, "path": media_path},
                "served_path_prefix": served_path,
            }
    record = {
        "scope_id": scope_id,
        "scope_type": planned_scope_type(publishing_mode),
        "meta": planned_scope_meta(publishing_mode),
        "scope_root": {"provider": EXTERNAL_LOCAL_PROVIDER, "path": scope_root_path},
        "source": {},
        "search_fields": list(DEFAULT_DOCS_SEARCH_FIELDS),
        "media": {
            "types": media_types,
            "build_sources": {},
        },
        "generated": {},
        "published": {},
        "public_projection": (
            {
                "documents": {
                    "location": {
                        "provider": "repository",
                        "path": planned_public_docs_projection(scope_id).as_posix(),
                    }
                },
                "search": {
                    "location": {
                        "provider": "repository",
                        "path": planned_public_search_projection(scope_id).as_posix(),
                    }
                },
                "media": public_media,
            }
            if publishing_mode == PUBLIC_MODE
            else None
        ),
        "viewer_base_url": viewer_base_url,
        "include_scope_param": public_route_path == "",
        "default_doc_id": default_doc_id,
        "non_loadable_doc_ids": [],
        "manage_only_tree_root_ids": [],
        "allow_unresolved_parent_ids": False,
        "sub_scopes": [],
    }
    return record


def planned_storage_contract(preview: dict[str, Any]) -> dict[str, Any]:
    publishing_mode = str(preview["publishing_mode"])
    config = preview["planned_scope_config"]
    scope_root = str(_planned_role_location(config, "scope_root", "path") or "")
    source_root = (Path(scope_root) / SCOPE_SOURCE_PATH).as_posix()
    docs_output = (Path(scope_root) / GENERATED_DOCUMENTS_PATH).as_posix()
    search_output = (Path(scope_root) / GENERATED_SEARCH_PATH).as_posix()
    media_root = (Path(scope_root) / SCOPE_SOURCE_PATH / "media").as_posix()
    publish_output = (Path(scope_root) / PUBLISHED_DOCUMENTS_PATH).as_posix()
    publish_search_output = (Path(scope_root) / PUBLISHED_SEARCH_PATH).as_posix()
    deploy_output = str(
        _planned_role_location(config, "public_projection", "documents", "location", "path") or ""
    )
    deploy_search_output = str(
        _planned_role_location(config, "public_projection", "search", "location", "path") or ""
    )
    if publishing_mode == PUBLIC_MODE:
        summary = (
            "Public read-only route: source, generated, and published lifecycle folders share one "
            "external scope root; deployment remains a separate operation."
        )
        access = "public_readonly_route_and_local_manage"
        public_static_assets = True
    else:
        summary = (
            "Local Manage scope: source, generated, and published lifecycle folders share one "
            "external scope root and no public route is created."
        )
        access = "local_manage_only"
        public_static_assets = False
    return {
        "publishing_mode": publishing_mode,
        "public_static_assets": public_static_assets,
        "access": access,
        "scope_root": scope_root,
        "source_root": source_root,
        "docs_output": docs_output,
        "search_output": search_output,
        "media_root": media_root,
        "publish_output": publish_output,
        "publish_search_output": publish_search_output,
        "deploy_output": deploy_output,
        "deploy_search_output": deploy_search_output,
        "summary": summary,
    }


def default_source_doc_text(title: str, default_doc_id: str, added_date: str) -> str:
    return "\n".join(
        [
            "---",
            f"doc_id: {default_doc_id}",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            f"added_date: {json.dumps(added_date)}",
            f"last_updated: {json.dumps(added_date)}",
            "ui_status: draft",
            "---",
            f"# {title}",
            "",
            f"Start writing {title} docs here.",
            "",
        ]
    )


def append_scope_config(repo_root: Path, scope_config: dict[str, Any]) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != SCOPE_CONFIG_SCHEMA_VERSION:
        raise ValueError(f"docs scope config schema_version must be {SCOPE_CONFIG_SCHEMA_VERSION}")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    scope_id = str(scope_config.get("scope_id") or "").strip()
    if any(isinstance(item, dict) and item.get("scope_id") == scope_id for item in scopes):
        raise ValueError(f"scope_id {scope_id!r} already exists")
    scopes.append(scope_config)
    write_text_atomic(config_path, render_json(payload))


def remove_scope_config(repo_root: Path, scope_id: str) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != SCOPE_CONFIG_SCHEMA_VERSION:
        raise ValueError(f"docs scope config schema_version must be {SCOPE_CONFIG_SCHEMA_VERSION}")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    retained = [
        item
        for item in scopes
        if not (isinstance(item, dict) and str(item.get("scope_id") or "").strip() == scope_id)
    ]
    if len(retained) == len(scopes):
        raise ValueError(f"scope_id {scope_id!r} is missing from docs scope config")
    payload["scopes"] = retained
    write_text_atomic(config_path, render_json(payload))


def manifest_file_records_for_created_scope(repo_root: Path, preview: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    external_data_root = (
        resolve_external_data_marker_path(preview.get("external_data_root"), field="external_data_root")
        if preview.get("external_data_root")
        else None
    )
    for item in [*preview.get("created_files", []), *preview.get("publish_files", []), *preview.get("changed_files", [])]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind == "scope_manifest":
            continue
        path_text = str(item.get("path") or "").strip()
        if not kind or not path_text:
            continue
        path = resolve_manifest_path(
            repo_root,
            path_text,
            field="created scope file path",
            external_data_root=external_data_root,
        )
        records.append(path_record(repo_root, kind, path, action="track"))
    return records


def created_scope_manifest_record(repo_root: Path, preview: dict[str, Any]) -> dict[str, Any]:
    publishing_mode = str(preview["publishing_mode"])
    scope_type = "public" if publishing_mode == PUBLIC_MODE else "local"
    now = utc_now()
    return {
        "scope_id": preview["scope_id"],
        "scope_type": scope_type,
        "owner": "user",
        "user_created": True,
        "created_by_tool": True,
        "tool_id": TOOL_ID,
        "repo_status_at_creation": "external",
        "created_at": now,
        "updated_at": now,
        "files": manifest_file_records_for_created_scope(repo_root, preview),
        "metadata": {
            "backfilled": False,
            "viewer_base_url": preview["planned_scope_config"]["viewer_base_url"],
            "default_doc_id": preview["planned_scope_config"]["default_doc_id"],
            "publishing_mode": publishing_mode,
            "external_data_root": EXTERNAL_DATA_ROOT_MARKER,
        },
    }


def append_scope_manifest_record(repo_root: Path, preview: dict[str, Any], manifest: dict[str, Any] | None = None) -> None:
    if manifest is None:
        manifest = load_manifest(repo_root)
    scopes = manifest.setdefault("scopes", [])
    if not isinstance(scopes, list):
        raise ValueError("docs scope manifest scopes must be an array")
    scope_id = str(preview["scope_id"])
    if scope_id in manifest_scopes_by_id(manifest):
        raise ValueError(f"scope_id {scope_id!r} already exists in docs scope manifest")
    scopes.append(created_scope_manifest_record(repo_root, preview))
    manifest["updated_at"] = utc_now()
    write_text_atomic(repo_root / MANIFEST_REL_PATH, render_json(manifest))

def remove_scope_manifest_record(repo_root: Path, scope_id: str, manifest: dict[str, Any] | None = None) -> None:
    if manifest is None:
        manifest = load_manifest(repo_root)
    scopes = manifest.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope manifest scopes must be an array")
    retained = [
        item
        for item in scopes
        if not (isinstance(item, dict) and str(item.get("scope_id") or "").strip() == scope_id)
    ]
    if len(retained) == len(scopes):
        raise ValueError(f"scope_id {scope_id!r} is missing from docs scope manifest")
    manifest["scopes"] = retained
    manifest["updated_at"] = utc_now()
    write_text_atomic(repo_root / MANIFEST_REL_PATH, render_json(manifest))
