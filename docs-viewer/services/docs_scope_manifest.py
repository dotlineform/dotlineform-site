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
    EXTERNAL_DATA_ROOT_MARKER,
    PUBLIC_DOCS_OUTPUT_ROOT,
    PUBLIC_SEARCH_OUTPUT_ROOT,
    DocsScopeConfig,
    load_docs_scope_configs,
    resolve_external_data_marker_path,
    resolve_scope_path,
    safe_relative_path,
    safe_scope_data_path,
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
    route_is_readonly,
)


MANIFEST_REL_PATH = Path("docs-viewer/config/scopes/docs_scope_manifest.json")
SCHEMA_VERSION = "docs_scope_manifest_v1"
LIFECYCLE_PREVIEW_SCHEMA_VERSION = "docs_scope_lifecycle_preview_v1"
LIFECYCLE_APPLY_SCHEMA_VERSION = "docs_scope_lifecycle_apply_v1"
TOOL_ID = "docs-viewer-scope-lifecycle"
SAFE_SCOPE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PUBLIC_MODE = "public_readonly"
LOCAL_COMMITTED_MODE = "local_committed"
LOCAL_EXTERNAL_MODE = "local_external"
PUBLISHING_MODES = (PUBLIC_MODE, LOCAL_EXTERNAL_MODE, LOCAL_COMMITTED_MODE)
SCOPE_DELETE_CHANGE_KINDS = {"scope_config", "scope_manifest", "route_config", "public_route_config"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generated_search_index_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return resolve_scope_path(repo_root, config.search_output)
    return resolve_scope_path(
        repo_root,
        safe_scope_data_path(config.get("search_output"), field="planned_scope_config.search_output", allow_external=True),
    )


def published_docs_output_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return repo_root / config.publish_output
    return repo_root / safe_relative_path(config.get("publish_output"), field="planned_scope_config.publish_output")


def published_search_index_path(repo_root: Path, config: DocsScopeConfig | dict[str, Any]) -> Path:
    if isinstance(config, DocsScopeConfig):
        return repo_root / config.publish_search_output
    return repo_root / safe_relative_path(config.get("publish_search_output"), field="planned_scope_config.publish_search_output")


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
    candidate = resolve_scope_path(repo_root, config.source) / f"{config.default_doc_id}.md"
    if candidate.exists():
        return path_record(repo_root, "default_source_doc", candidate)
    return None


def backfilled_scope_record(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    source_root = resolve_scope_path(repo_root, config.source)
    route_path = route_file_for_config(repo_root, config)
    readonly_route = route_is_readonly(route_path)
    scope_type = "public" if readonly_route else "local"
    repo_status = "tracked" if scope_type == "public" else git_path_status(repo_root, source_root)
    files = [
        path_record(repo_root, "source_root", source_root),
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH),
    ]
    default_doc = default_source_doc_record(repo_root, config)
    if default_doc is not None:
        files.append(default_doc)
    if route_path.exists():
        files.append(path_record(repo_root, "route_file", route_path))
    docs_output = resolve_scope_path(repo_root, config.output)
    files.append(path_record(repo_root, "generated_docs_root", docs_output))
    files.extend(
        [
            path_record(repo_root, "generated_docs_index_tree", docs_output / "index-tree.json"),
            path_record(repo_root, "generated_docs_recent", docs_output / "recent.json"),
            path_record(repo_root, "generated_docs_payload_root", docs_output / "by-id"),
            path_record(repo_root, "generated_search_index", generated_search_index_path(repo_root, config)),
        ]
    )
    if scope_type == "public":
        files.extend(
            [
                path_record(repo_root, "published_docs_root", repo_root / config.publish_output),
                path_record(repo_root, "published_docs_index_tree", repo_root / config.publish_output / "index-tree.json"),
                path_record(repo_root, "published_docs_recent", repo_root / config.publish_output / "recent.json"),
                path_record(repo_root, "published_docs_payload_root", repo_root / config.publish_output / "by-id"),
                path_record(repo_root, "published_search_index", published_search_index_path(repo_root, config)),
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


def normalize_source_root(value: Any, scope_id: str) -> Path:
    source_root = safe_relative_path(value, field="source_root")
    expected = Path("docs-viewer/source") / scope_id
    if source_root != expected:
        raise ValueError(f"source_root must be {expected.as_posix()}")
    return source_root


def bool_value(payload: dict[str, Any], key: str, default: bool) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    raise ValueError(f"{key} must be a boolean")


def require_confirmed(body: dict[str, Any]) -> None:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to apply scope lifecycle changes")


def planned_external_source_root(scope_id: str, external_data_root: Path) -> Path:
    return external_data_root / "source" / scope_id


def planned_external_source_root_marker(scope_id: str) -> Path:
    return Path(EXTERNAL_DATA_ROOT_MARKER) / "source" / scope_id


def planned_external_docs_output_marker(scope_id: str) -> Path:
    return Path(EXTERNAL_DATA_ROOT_MARKER) / "generated" / "docs" / scope_id


def planned_external_search_output_marker(scope_id: str) -> Path:
    return Path(EXTERNAL_DATA_ROOT_MARKER) / "generated" / "search" / scope_id / "index.json"


def planned_docs_output(scope_id: str, publishing_mode: str, external_data_root: Path | None = None) -> Path:
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        if external_data_root is None:
            raise ValueError("external_data_root is required for external local scopes")
        return external_data_root / "generated" / "docs" / scope_id
    return Path("docs-viewer/generated/docs") / scope_id


def planned_search_output(scope_id: str, publishing_mode: str, external_data_root: Path | None = None) -> Path:
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        if external_data_root is None:
            raise ValueError("external_data_root is required for external local scopes")
        return external_data_root / "generated" / "search" / scope_id / "index.json"
    return Path("docs-viewer/generated/search") / scope_id / "index.json"


def planned_publish_output(scope_id: str, publishing_mode: str) -> Path:
    if publishing_mode == PUBLIC_MODE:
        return PUBLIC_DOCS_OUTPUT_ROOT / scope_id
    return planned_docs_output(scope_id, publishing_mode)


def planned_publish_search_output(scope_id: str, publishing_mode: str) -> Path:
    if publishing_mode == PUBLIC_MODE:
        return PUBLIC_SEARCH_OUTPUT_ROOT / scope_id / "index.json"
    return planned_search_output(scope_id, publishing_mode)


def planned_scope_type(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public"
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        return "local_external"
    return "local"


def planned_scope_meta(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public scope"
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        return "external local"
    return "local management"


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_planned_storage_paths(scope_id: str, publishing_mode: str, config: dict[str, Any]) -> None:
    allow_external = publishing_mode == LOCAL_EXTERNAL_MODE
    docs_output = safe_scope_data_path(
        config.get("output"),
        field="planned_scope_config.output",
        allow_external=allow_external,
    )
    search_output = safe_scope_data_path(
        config.get("search_output"),
        field="planned_scope_config.search_output",
        allow_external=allow_external,
    )
    if publishing_mode == PUBLIC_MODE:
        publish_output = safe_relative_path(config.get("publish_output"), field="planned_scope_config.publish_output")
        publish_search_output = safe_relative_path(
            config.get("publish_search_output"),
            field="planned_scope_config.publish_search_output",
        )
        if path_is_relative_to(docs_output, PUBLIC_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must write working generated docs under docs-viewer/generated/docs"
            )
        if path_is_relative_to(search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must write working generated search under docs-viewer/generated/search"
            )
        if not path_is_relative_to(publish_output, PUBLIC_DOCS_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must publish docs under site/assets/data/docs/scopes"
            )
        if not path_is_relative_to(publish_search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
            raise ValueError(
                f"public scope {scope_id!r} must publish search under site/assets/data/search"
            )
        return
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        source_root = safe_scope_data_path(
            config.get("source"),
            field="planned_scope_config.source",
            allow_external=True,
        )
        if not source_root.is_absolute() or not docs_output.is_absolute() or not search_output.is_absolute():
            raise ValueError(f"external local scope {scope_id!r} must use external source and generated paths")
        return
    if path_is_relative_to(docs_output, PUBLIC_DOCS_OUTPUT_ROOT):
        raise ValueError(
            f"local tracked scope {scope_id!r} must not write generated docs under site/assets/data/docs/scopes"
        )
    if path_is_relative_to(search_output, PUBLIC_SEARCH_OUTPUT_ROOT):
        raise ValueError(
            f"local tracked scope {scope_id!r} must not write generated search under site/assets/data/search"
        )


def planned_scope_config_record(
    scope_id: str,
    source_root: Path,
    public_route_path: str,
    default_doc_id: str,
    publishing_mode: str,
    external_data_root: Path | None = None,
) -> dict[str, Any]:
    viewer_base_url = public_route_path or "/docs/"
    if publishing_mode == PUBLIC_MODE:
        import_media_storage = {"storage_mode": "r2_upload"}
    elif publishing_mode == LOCAL_EXTERNAL_MODE:
        import_media_storage = {"storage_mode": "external_assets"}
    else:
        import_media_storage = {
            "storage_mode": "repo_assets",
            "repo_assets_path_prefix": (source_root / "media").as_posix(),
            "repo_assets_public_path_prefix": f"/docs/media/{scope_id}",
        }
    record = {
        "scope_id": scope_id,
        "scope_type": planned_scope_type(publishing_mode),
        "meta": planned_scope_meta(publishing_mode),
        "source": (
            planned_external_source_root_marker(scope_id)
            if publishing_mode == LOCAL_EXTERNAL_MODE
            else source_root
        ).as_posix(),
        "media_path_prefix": f"docs/{scope_id}",
        "output": (
            planned_external_docs_output_marker(scope_id)
            if publishing_mode == LOCAL_EXTERNAL_MODE
            else planned_docs_output(scope_id, publishing_mode)
        ).as_posix(),
        "search_output": (
            planned_external_search_output_marker(scope_id)
            if publishing_mode == LOCAL_EXTERNAL_MODE
            else planned_search_output(scope_id, publishing_mode)
        ).as_posix(),
        "viewer_base_url": viewer_base_url,
        "include_scope_param": public_route_path == "",
        "default_doc_id": default_doc_id,
        "non_loadable_doc_ids": [],
        "manage_only_tree_root_ids": [],
        "allow_unresolved_parent_ids": False,
        "import_media_storage": import_media_storage,
    }
    if publishing_mode == LOCAL_EXTERNAL_MODE:
        record["external_data_root"] = EXTERNAL_DATA_ROOT_MARKER
    if publishing_mode != LOCAL_EXTERNAL_MODE:
        record["publish_output"] = planned_publish_output(scope_id, publishing_mode).as_posix()
        record["publish_search_output"] = planned_publish_search_output(scope_id, publishing_mode).as_posix()
    return record


def planned_storage_contract(preview: dict[str, Any]) -> dict[str, Any]:
    publishing_mode = str(preview["publishing_mode"])
    config = preview["planned_scope_config"]
    docs_output = str(config["output"])
    search_output = str(config["search_output"])
    publish_output = str(config.get("publish_output") or docs_output)
    publish_search_output = str(config.get("publish_search_output") or search_output)
    if publishing_mode == PUBLIC_MODE:
        summary = (
            "Public read-only scope: generated docs and search payloads are working local outputs under "
            "docs-viewer/generated/ until Publish docs syncs them to public static assets under assets/."
        )
        access = "public_readonly_route_and_local_manage"
        public_static_assets = True
    elif publishing_mode == LOCAL_COMMITTED_MODE:
        summary = (
            "Local tracked scope: generated docs and search payloads are tracked non-public Docs Viewer "
            "runtime data under docs-viewer/generated/ and no public route is created."
        )
        access = "local_manage_only"
        public_static_assets = False
    else:
        summary = ""
        access = "local_manage_only"
        public_static_assets = False
    return {
        "publishing_mode": publishing_mode,
        "public_static_assets": public_static_assets,
        "access": access,
        "source_root": str(config.get("source") or ""),
        "docs_output": docs_output,
        "search_output": search_output,
        "publish_output": publish_output,
        "publish_search_output": publish_search_output,
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
    if payload.get("schema_version") != "docs_scopes_v1":
        raise ValueError("docs scope config schema_version must be docs_scopes_v1")
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
    if payload.get("schema_version") != "docs_scopes_v1":
        raise ValueError("docs scope config schema_version must be docs_scopes_v1")
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
    docs_viewer_settings = payload.get("docs_viewer")
    if isinstance(docs_viewer_settings, dict):
        statuses_by_scope = docs_viewer_settings.get("ui_statuses_by_scope")
        if isinstance(statuses_by_scope, dict):
            statuses_by_scope.pop(scope_id, None)
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
    repo_status = "external" if publishing_mode == LOCAL_EXTERNAL_MODE else "tracked"
    now = utc_now()
    return {
        "scope_id": preview["scope_id"],
        "scope_type": scope_type,
        "owner": "user",
        "user_created": True,
        "created_by_tool": True,
        "tool_id": TOOL_ID,
        "repo_status_at_creation": repo_status,
        "created_at": now,
        "updated_at": now,
        "files": manifest_file_records_for_created_scope(repo_root, preview),
        "metadata": {
            "backfilled": False,
            "viewer_base_url": preview["planned_scope_config"]["viewer_base_url"],
            "default_doc_id": preview["planned_scope_config"]["default_doc_id"],
            "publishing_mode": publishing_mode,
            "external_data_root": EXTERNAL_DATA_ROOT_MARKER if publishing_mode == LOCAL_EXTERNAL_MODE else "",
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
