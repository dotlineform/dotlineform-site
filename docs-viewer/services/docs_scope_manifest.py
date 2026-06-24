#!/usr/bin/env python3
"""Docs Viewer scope ownership manifest and lifecycle preview helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from docs_scope_config import (
    CONFIG_REL_PATH,
    EXTERNAL_DATA_ROOT_MARKER,
    PUBLIC_DOCS_OUTPUT_ROOT,
    PUBLIC_SEARCH_OUTPUT_ROOT,
    DocsScopeConfig,
    default_repo_root,
    is_public_readonly_scope,
    load_docs_scope_configs,
    normalize_sub_scope_id,
    path_label,
    resolve_external_data_marker_path,
    resolve_external_data_root,
    resolve_scope_path,
    safe_relative_path,
    safe_scope_data_path,
)


MANIFEST_REL_PATH = Path("docs-viewer/config/scopes/docs_scope_manifest.json")
SCHEMA_VERSION = "docs_scope_manifest_v1"
LIFECYCLE_PREVIEW_SCHEMA_VERSION = "docs_scope_lifecycle_preview_v1"
LIFECYCLE_APPLY_SCHEMA_VERSION = "docs_scope_lifecycle_apply_v1"
TOOL_ID = "docs-viewer-scope-lifecycle"
SAFE_SCOPE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
SAFE_DOC_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SAFE_ROUTE_PART_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PUBLIC_MODE = "public_readonly"
LOCAL_COMMITTED_MODE = "local_committed"
LOCAL_EXTERNAL_MODE = "local_external"
PUBLISHING_MODES = (PUBLIC_MODE, LOCAL_EXTERNAL_MODE, LOCAL_COMMITTED_MODE)
SCOPE_DELETE_CHANGE_KINDS = {"scope_config", "scope_manifest", "route_config", "public_route_config"}
PUBLIC_ROUTE_TEMPLATE_REL_PATH = Path("docs-viewer/templates/public-route/index.html")
ROUTE_CONFIG_REL_PATH = Path("docs-viewer/config/routes/docs-viewer-routes.json")
DOCS_MANAGEMENT_ROUTE_PATH = "/docs/"
PUBLIC_ROUTE_CONFIG_REL_PATHS = (
    Path("site/docs-viewer/config/routes/docs-viewer-public-routes.json"),
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_route_path(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return f"/{text.strip('/')}/"


def repo_relative(repo_root: Path, path: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def path_location(repo_root: Path, path: Path) -> str:
    try:
        path.resolve().relative_to(repo_root.resolve())
        return "repo"
    except ValueError:
        return "external"


def path_record(repo_root: Path, kind: str, path: Path, *, action: str = "track") -> dict[str, Any]:
    location = path_location(repo_root, path)
    return {
        "kind": kind,
        "path": path_label(repo_root, path),
        "location": location,
        "action": action,
        "exists": path.exists(),
    }


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(path)


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


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


def route_file_for_config(repo_root: Path, config: DocsScopeConfig) -> Path:
    route_base = config.viewer_base_url.strip("/")
    if config.scope_type == "public" or (not config.include_scope_param and route_base and config.viewer_base_url != "/docs/"):
        return repo_root / "site" / route_base / "index.html"
    route_rel = Path(route_base) / "index.md" if route_base else Path("index.md")
    return repo_root / route_rel


def route_is_readonly(route_path: Path) -> bool:
    if not route_path.exists() or not route_path.is_file():
        return False
    try:
        text = route_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "docs_viewer_readonly_route.html" in text or 'data-route-config-url="/docs-viewer/config/routes/docs-viewer-public-routes.json"' in text


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
            path_record(repo_root, "generated_docs_recently_added", docs_output / "recently-added.json"),
            path_record(repo_root, "generated_docs_payload_root", docs_output / "by-id"),
            path_record(repo_root, "generated_search_index", generated_search_index_path(repo_root, config)),
        ]
    )
    if scope_type == "public":
        files.extend(
            [
                path_record(repo_root, "published_docs_root", repo_root / config.publish_output),
                path_record(repo_root, "published_docs_index_tree", repo_root / config.publish_output / "index-tree.json"),
                path_record(repo_root, "published_docs_recently_added", repo_root / config.publish_output / "recently-added.json"),
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


def normalize_doc_id(value: Any) -> str:
    doc_id = str(value or "").strip().lower()
    if not doc_id:
        raise ValueError("default_doc_id is required")
    if not SAFE_DOC_ID_PATTERN.match(doc_id):
        raise ValueError("default_doc_id must use lowercase letters, numbers, and hyphens")
    return doc_id


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


def normalize_route_path(value: Any) -> str:
    route = str(value or "").strip()
    if not route:
        raise ValueError("public_route_path is required for public read-only scopes")
    if not route.startswith("/"):
        route = f"/{route}"
    if not route.endswith("/"):
        route = f"{route}/"
    route_parts = [part for part in route.strip("/").split("/") if part]
    if not route_parts:
        raise ValueError("public_route_path must include a route segment")
    if any(part in {".", ".."} or not SAFE_ROUTE_PART_PATTERN.match(part) for part in route_parts):
        raise ValueError("public_route_path must use lowercase route segments with hyphens")
    return "/" + "/".join(route_parts) + "/"


def route_file_for_public_path(repo_root: Path, public_route_path: str) -> Path:
    route_rel = Path(public_route_path.strip("/")) / "index.html"
    return repo_root / "site" / route_rel


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
        "show_updated_date": True,
        "allow_unresolved_parent_ids": False,
        "import_media_storage": {
            "storage_mode": "staging_manual",
            "repo_assets_path_prefix": f"site/assets/docs/{scope_id}",
            "repo_assets_public_path_prefix": f"/assets/docs/{scope_id}",
        },
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


def default_source_doc_text(title: str, default_doc_id: str) -> str:
    today = utc_now()[:10]
    return "\n".join(
        [
            "---",
            f"doc_id: {default_doc_id}",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            f"added_date: {today}",
            f"last_updated: {today}",
            "ui_status: draft",
            "---",
            f"# {title}",
            "",
            f"Start writing {title} docs here.",
            "",
        ]
    )


def readonly_route_text(title: str, scope_id: str, public_route_path: str, *, enable_search: bool = True) -> str:
    del title, scope_id, public_route_path, enable_search
    return (default_repo_root() / PUBLIC_ROUTE_TEMPLATE_REL_PATH).read_text(encoding="utf-8")


def public_route_body_class(scope_id: str, public_route_path: str) -> str:
    route_section = public_route_path.strip("/").split("/", 1)[0] or scope_id
    return route_section


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


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


def find_raw_scope_config(payload: dict[str, Any], scope_id: str) -> dict[str, Any]:
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    for item in scopes:
        if isinstance(item, dict) and str(item.get("scope_id") or "").strip() == scope_id:
            return item
    raise ValueError(f"scope_id {scope_id!r} is missing from docs scope config")


def append_path_text(value: Any, child: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("sub-scope parent path is required")
    return (Path(text) / child).as_posix()


def resolve_lifecycle_record_path(repo_root: Path, value: Any, *, field: str) -> Path:
    text = str(value or "").strip()
    if Path(text).is_absolute():
        return safe_scope_data_path(text, field=field, allow_external=True)
    return repo_root / safe_relative_path(text, field=field)


def planned_sub_scope_config_record(
    parent_config: DocsScopeConfig,
    raw_parent_config: dict[str, Any],
    sub_scope: str,
    title: str,
) -> dict[str, Any]:
    public_readonly = is_public_readonly_scope(
        viewer_base_url=parent_config.viewer_base_url,
        include_scope_param=parent_config.include_scope_param,
    )
    publish_parent = raw_parent_config.get("publish_output") if public_readonly else raw_parent_config.get("output")
    return {
        "sub_scope": sub_scope,
        "title": title,
        "source": append_path_text(raw_parent_config.get("source"), sub_scope),
        "output": append_path_text(raw_parent_config.get("output"), sub_scope),
        "publish_output": append_path_text(publish_parent, sub_scope),
    }


def append_sub_scope_config(repo_root: Path, parent_scope: str, sub_scope_config: dict[str, Any]) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != "docs_scopes_v1":
        raise ValueError("docs scope config schema_version must be docs_scopes_v1")
    parent_record = find_raw_scope_config(payload, parent_scope)
    sub_scopes = parent_record.setdefault("sub_scopes", [])
    if not isinstance(sub_scopes, list):
        raise ValueError(f"scope_id {parent_scope!r} sub_scopes must be an array")
    sub_scope = str(sub_scope_config.get("sub_scope") or "").strip()
    if any(isinstance(item, dict) and str(item.get("sub_scope") or "").strip() == sub_scope for item in sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in scope {parent_scope!r}")
    sub_scopes.append(sub_scope_config)
    write_text_atomic(config_path, render_json(payload))


def remove_sub_scope_config(repo_root: Path, parent_scope: str, sub_scope: str) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != "docs_scopes_v1":
        raise ValueError("docs scope config schema_version must be docs_scopes_v1")
    parent_record = find_raw_scope_config(payload, parent_scope)
    sub_scopes = parent_record.get("sub_scopes")
    if not isinstance(sub_scopes, list):
        raise ValueError(f"sub_scope {sub_scope!r} is missing from scope {parent_scope!r}")
    retained = [
        item
        for item in sub_scopes
        if not (isinstance(item, dict) and str(item.get("sub_scope") or "").strip() == sub_scope)
    ]
    if len(retained) == len(sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} is missing from scope {parent_scope!r}")
    if retained:
        parent_record["sub_scopes"] = retained
    else:
        parent_record.pop("sub_scopes", None)
    write_text_atomic(config_path, render_json(payload))


def public_route_record(
    scope_id: str,
    public_route_path: str,
    default_doc_id: str,
    *,
    build_inline_search: bool,
    title: str,
) -> dict[str, Any]:
    search_label = f"search {title.lower()}"
    return {
        "schema_version": "docs_viewer_route_config_v1",
        "route_id": scope_id,
        "route_path": public_route_path,
        "default_scope_id": scope_id,
        "default_doc_id": default_doc_id,
        "include_scope_param": False,
        "allow_scope_query": False,
        "viewer_base_url": public_route_path,
        "generated_base_url": "",
        "access": {
            "allow_scope_query": False,
            "management_base_url": "",
        },
        "docs_paths": {
            "index_tree_url": f"/assets/data/docs/scopes/{scope_id}/index-tree.json",
            "recently_added_url": f"/assets/data/docs/scopes/{scope_id}/recently-added.json",
            "search_index_url": f"/assets/data/search/{scope_id}/index.json" if build_inline_search else "",
        },
        "config_urls": {
            "docs_viewer": "/docs-viewer/config/defaults/docs-viewer-public-config.json",
            "ui_text": "/docs-viewer/config/ui-text/public.json",
        },
        "panels": {
            "index": {"enabled": True, "default_state": "normal"},
            "main": {"enabled": True, "default_view": "rendered-document"},
            "info": {"enabled": True, "default_view": "metadata-info"},
        },
        "ui": {
            "route_shell": {
                "page_title": f"{title} | dotlineform",
                "body_class": public_route_body_class(scope_id, public_route_path),
            },
            "viewer_search": {
                "enabled": build_inline_search,
                "placeholder": search_label,
                "aria_label": f"Search {title}",
            },
        },
        "hosted_views": {
            "records": [],
        },
    }


def route_registry_path_records(repo_root: Path, *, action: str) -> list[dict[str, Any]]:
    return [
        path_record(repo_root, "route_config", repo_root / ROUTE_CONFIG_REL_PATH, action=action),
        *[
            path_record(repo_root, "public_route_config", repo_root / rel_path, action=action)
            for rel_path in PUBLIC_ROUTE_CONFIG_REL_PATHS
        ],
    ]


def load_route_registry(path: Path, label: str) -> dict[str, Any]:
    payload = load_json_object(path, label)
    if payload.get("schema_version") != "docs_viewer_route_config_registry_v1":
        raise ValueError(f"{label} schema_version must be docs_viewer_route_config_registry_v1")
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise ValueError(f"{label} routes must be an array")
    return payload


def write_route_registry(path: Path, payload: dict[str, Any]) -> None:
    write_text_atomic(path, render_json(payload))


def append_public_route_record(repo_root: Path, route_record: dict[str, Any]) -> None:
    route_id = str(route_record.get("route_id") or "").strip()
    for rel_path in (ROUTE_CONFIG_REL_PATH, *PUBLIC_ROUTE_CONFIG_REL_PATHS):
        path = repo_root / rel_path
        payload = load_route_registry(path, rel_path.as_posix())
        routes = payload["routes"]
        if any(isinstance(item, dict) and str(item.get("route_id") or "").strip() == route_id for item in routes):
            raise ValueError(f"route_id {route_id!r} already exists in {rel_path.as_posix()}")
        routes.append(route_record)
        write_route_registry(path, payload)


def remove_public_route_record(repo_root: Path, scope_id: str) -> None:
    for rel_path in (ROUTE_CONFIG_REL_PATH, *PUBLIC_ROUTE_CONFIG_REL_PATHS):
        path = repo_root / rel_path
        payload = load_route_registry(path, rel_path.as_posix())
        routes = payload["routes"]
        retained = [
            item
            for item in routes
            if not (
                isinstance(item, dict)
                and (
                    str(item.get("route_id") or "").strip() == scope_id
                    or str(item.get("default_scope_id") or "").strip() == scope_id
                )
            )
        ]
        if len(retained) != len(routes):
            payload["routes"] = retained
            write_route_registry(path, payload)


def manage_default_route_ids_for_scope(repo_root: Path, scope_id: str) -> list[str]:
    payload = load_route_registry(repo_root / ROUTE_CONFIG_REL_PATH, ROUTE_CONFIG_REL_PATH.as_posix())
    route_ids: list[str] = []
    for route in payload["routes"]:
        if not isinstance(route, dict):
            continue
        route_path = route.get("route_path") or route.get("viewer_base_url")
        if normalize_route_path(route_path) != DOCS_MANAGEMENT_ROUTE_PATH:
            continue
        if str(route.get("default_scope_id") or "").strip() != scope_id:
            continue
        route_id = str(route.get("route_id") or "").strip()
        route_ids.append(route_id or "(unnamed manage route)")
    return route_ids


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


def path_is_relative_to_path(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def resolve_manifest_path(
    repo_root: Path,
    value: Any,
    *,
    field: str,
    external_data_root: Path | None = None,
) -> Path:
    text = str(value or "").strip()
    if Path(text).is_absolute():
        path = safe_scope_data_path(text, field=field, allow_external=True).resolve()
        if external_data_root is None or not path_is_relative_to_path(path, external_data_root):
            raise ValueError(f"{field} external path must stay under external_data_root")
        return path
    return repo_root / safe_relative_path(text, field=field)


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
            "build_inline_search": preview["build_inline_search"],
            "write_generated_outputs": preview["write_generated_outputs"],
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
    docs_source = repo_root / safe_relative_path(config.get("output"), field="planned_scope_config.output")
    docs_target = repo_root / safe_relative_path(config.get("publish_output"), field="planned_scope_config.publish_output")
    if docs_source.exists():
        if docs_target.exists():
            shutil.rmtree(docs_target)
        shutil.copytree(docs_source, docs_target)
    if include_search:
        search_source = repo_root / safe_relative_path(
            config.get("search_output"),
            field="planned_scope_config.search_output",
        )
        search_target = repo_root / safe_relative_path(
            config.get("publish_search_output"),
            field="planned_scope_config.publish_search_output",
        )
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
    source_root = resolve_scope_path(
        repo_root,
        safe_scope_data_path(
            preview["planned_scope_config"]["source"],
            field="planned_scope_config.source",
            allow_external=preview["publishing_mode"] == LOCAL_EXTERNAL_MODE,
        ),
    )
    default_doc_path = source_root / f"{preview['planned_scope_config']['default_doc_id']}.md"
    rebuild = None

    if not dry_run:
        source_root.mkdir(parents=True, exist_ok=False)
        write_text_atomic(
            default_doc_path,
            default_source_doc_text(str(preview["title"]), str(preview["planned_scope_config"]["default_doc_id"])),
        )
        append_scope_config(repo_root, preview["planned_scope_config"])
        if preview["urls"]["public"]:
            route_path = route_file_for_public_path(repo_root, str(preview["urls"]["public"]))
            write_text_atomic(
                route_path,
                readonly_route_text(
                    str(preview["title"]),
                    scope_id,
                    str(preview["urls"]["public"]),
                    enable_search=bool(preview["build_inline_search"]),
                ),
            )
            append_public_route_record(
                repo_root,
                public_route_record(
                    scope_id,
                    str(preview["urls"]["public"]),
                    str(preview["planned_scope_config"]["default_doc_id"]),
                    build_inline_search=bool(preview["build_inline_search"]),
                    title=str(preview["title"]),
                ),
            )
        append_scope_manifest_record(repo_root, preview, manifest)
        if preview["write_generated_outputs"]:
            rebuild = rebuild_scope_outputs(
                repo_root,
                scope_id,
                include_search=preview["build_inline_search"],
            )
            if preview["publishing_mode"] == PUBLIC_MODE:
                sync_public_publish_outputs(
                    repo_root,
                    preview["planned_scope_config"],
                    include_search=bool(preview["build_inline_search"]),
                )

    return {
        "ok": True,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "action": "create_scope",
        "operation": "apply",
        "scope_id": scope_id,
        "title": preview["title"],
        "publishing_mode": preview["publishing_mode"],
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


def manifest_delete_path_records(repo_root: Path, record: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    delete_files = []
    missing_files = []
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
        planned = path_record(repo_root, kind, path, action="delete")
        if path.exists():
            delete_files.append(planned)
        else:
            missing_files.append(planned)
    return delete_files, missing_files


def delete_path_sort_key(repo_root: Path, record: dict[str, Any]) -> tuple[int, str]:
    path_text = str(record.get("path") or "")
    path = Path(path_text) if Path(path_text).is_absolute() else repo_root / safe_relative_path(path_text, field="delete file path")
    return (-len(path.parts), path.as_posix())


def delete_manifest_paths(repo_root: Path, delete_files: list[dict[str, Any]]) -> None:
    for record in sorted(delete_files, key=lambda item: delete_path_sort_key(repo_root, item)):
        path_text = str(record.get("path") or "")
        path = Path(path_text) if Path(path_text).is_absolute() else repo_root / safe_relative_path(path_text, field="delete file path")
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


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


def sub_scope_storage_contract(
    parent_scope: str,
    sub_scope_config: dict[str, Any],
    *,
    public_static_assets: bool,
) -> dict[str, Any]:
    return {
        "publishing_mode": "parent_scope",
        "public_static_assets": public_static_assets,
        "access": "embedded_detail_documents",
        "source_root": str(sub_scope_config.get("source") or ""),
        "docs_output": str(sub_scope_config.get("output") or ""),
        "publish_output": str(sub_scope_config.get("publish_output") or sub_scope_config.get("output") or ""),
        "search_output": "",
        "summary": (
            f"Sub-scope under {parent_scope}: creates nested source and generated payload roots. "
            "It does not create a top-level scope, default document, route, or scope selector entry."
        ),
    }


def sub_scope_path_records(repo_root: Path, parent_config: DocsScopeConfig, sub_scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public_readonly = is_public_readonly_scope(
        viewer_base_url=parent_config.viewer_base_url,
        include_scope_param=parent_config.include_scope_param,
    )
    source_root = resolve_scope_path(repo_root, parent_config.source / sub_scope)
    docs_output = resolve_scope_path(repo_root, parent_config.output / sub_scope)
    records = [
        path_record(repo_root, "sub_scope_source_root", source_root, action="create"),
        path_record(repo_root, "sub_scope_generated_docs_root", docs_output, action="create"),
        path_record(repo_root, "sub_scope_generated_docs_payload_root", docs_output / "by-id", action="create"),
    ]
    publish_records: list[dict[str, Any]] = []
    if public_readonly:
        publish_output = resolve_scope_path(repo_root, parent_config.publish_output / sub_scope)
        publish_records.extend(
            [
                path_record(repo_root, "sub_scope_published_docs_root", publish_output, action="publish"),
                path_record(repo_root, "sub_scope_published_docs_payload_root", publish_output / "by-id", action="publish"),
            ]
        )
    return records, publish_records


def plan_create_sub_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    parent_scope = normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    title = normalize_title(body.get("title"))
    configs = load_docs_scope_configs(repo_root)
    parent_config = configs.get(parent_scope)
    if parent_config is None:
        raise ValueError(f"parent scope {parent_scope!r} does not exist")
    if any(item.sub_scope == sub_scope for item in parent_config.sub_scopes):
        raise ValueError(f"sub_scope {sub_scope!r} already exists in scope {parent_scope!r}")

    config_payload = load_json_object(repo_root / CONFIG_REL_PATH, "docs scope config")
    raw_parent_config = find_raw_scope_config(config_payload, parent_scope)
    planned_sub_scope_config = planned_sub_scope_config_record(parent_config, raw_parent_config, sub_scope, title)
    created_files, publish_files = sub_scope_path_records(repo_root, parent_config, sub_scope)
    conflicts = [
        record["path"]
        for record in [*created_files, *publish_files]
        if record.get("exists")
    ]
    if conflicts:
        raise ValueError(f"sub-scope creation would overwrite existing paths: {', '.join(conflicts)}")
    public_readonly = is_public_readonly_scope(
        viewer_base_url=parent_config.viewer_base_url,
        include_scope_param=parent_config.include_scope_param,
    )

    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "create_sub_scope",
        "operation": "preview",
        "scope_id": parent_scope,
        "parent_scope": parent_scope,
        "sub_scope": sub_scope,
        "title": title,
        "planned_sub_scope_config": planned_sub_scope_config,
        "storage_contract": sub_scope_storage_contract(
            parent_scope,
            planned_sub_scope_config,
            public_static_assets=public_readonly,
        ),
        "created_files": created_files,
        "publish_files": publish_files,
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        ],
        "build_commands": [],
        "urls": {
            "management": f"/docs/?scope={parent_scope}",
            "public": "",
        },
        "warnings": [],
        "summary_text": f"Previewed new Docs Viewer sub-scope {parent_scope}/{sub_scope}.",
    }


def apply_create_sub_scope(repo_root: Path, body: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_create_sub_scope_preview(repo_root, body)
    if not dry_run:
        for record in [*preview["created_files"], *preview.get("publish_files", [])]:
            path = resolve_lifecycle_record_path(repo_root, record["path"], field="sub-scope created file path")
            path.mkdir(parents=True, exist_ok=False)
        append_sub_scope_config(repo_root, str(preview["parent_scope"]), preview["planned_sub_scope_config"])

    return {
        "ok": True,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "action": "create_sub_scope",
        "operation": "apply",
        "scope_id": preview["scope_id"],
        "parent_scope": preview["parent_scope"],
        "sub_scope": preview["sub_scope"],
        "title": preview["title"],
        "storage_contract": preview.get("storage_contract", {}),
        "created_files": preview["created_files"],
        "publish_files": preview.get("publish_files", []),
        "changed_files": preview["changed_files"],
        "deleted_files": [],
        "missing_files": [],
        "build_commands": [],
        "urls": preview["urls"],
        "summary_text": (
            f"Created Docs Viewer sub-scope {preview['parent_scope']}/{preview['sub_scope']}."
            if not dry_run
            else f"Validated create apply for Docs Viewer sub-scope {preview['parent_scope']}/{preview['sub_scope']}."
        ),
        "dry_run": dry_run,
    }


def sub_scope_delete_path_records(repo_root: Path, sub_scope_config: Any, parent_config: DocsScopeConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public_readonly = is_public_readonly_scope(
        viewer_base_url=parent_config.viewer_base_url,
        include_scope_param=parent_config.include_scope_param,
    )
    candidate_paths = [
        ("sub_scope_source_root", resolve_scope_path(repo_root, sub_scope_config.source)),
        ("sub_scope_generated_docs_root", resolve_scope_path(repo_root, sub_scope_config.output)),
    ]
    if public_readonly:
        candidate_paths.append(("sub_scope_published_docs_root", resolve_scope_path(repo_root, sub_scope_config.publish_output)))

    delete_files: list[dict[str, Any]] = []
    missing_files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for kind, path in candidate_paths:
        key = path.resolve().as_posix()
        if key in seen_paths:
            continue
        seen_paths.add(key)
        record = path_record(repo_root, kind, path, action="delete")
        if path.exists():
            delete_files.append(record)
        else:
            missing_files.append(record)
    return delete_files, missing_files


def plan_delete_sub_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    parent_scope = normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    configs = load_docs_scope_configs(repo_root)
    parent_config = configs.get(parent_scope)
    if parent_config is None:
        return {
            "ok": True,
            "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
            "action": "delete_sub_scope",
            "operation": "preview",
            "scope_id": parent_scope,
            "parent_scope": parent_scope,
            "sub_scope": sub_scope,
            "allowed": False,
            "blockers": [f"parent scope {parent_scope!r} does not exist"],
            "delete_files": [],
            "missing_files": [],
            "changed_files": [],
            "build_commands": [],
        }
    matching = [item for item in parent_config.sub_scopes if item.sub_scope == sub_scope]
    if not matching:
        return {
            "ok": True,
            "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
            "action": "delete_sub_scope",
            "operation": "preview",
            "scope_id": parent_scope,
            "parent_scope": parent_scope,
            "sub_scope": sub_scope,
            "allowed": False,
            "blockers": [f"sub_scope {sub_scope!r} is not configured in scope {parent_scope!r}"],
            "delete_files": [],
            "missing_files": [],
            "changed_files": [],
            "build_commands": [],
        }

    delete_files, missing_files = sub_scope_delete_path_records(repo_root, matching[0], parent_config)
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "delete_sub_scope",
        "operation": "preview",
        "scope_id": parent_scope,
        "parent_scope": parent_scope,
        "sub_scope": sub_scope,
        "title": matching[0].title,
        "allowed": True,
        "blockers": [],
        "delete_files": delete_files,
        "missing_files": missing_files,
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        ],
        "build_commands": [],
        "summary_text": f"Previewed deletion for Docs Viewer sub-scope {parent_scope}/{sub_scope}.",
    }


def apply_delete_sub_scope(repo_root: Path, body: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_delete_sub_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "sub-scope delete is not allowed")

    if not dry_run:
        delete_manifest_paths(repo_root, preview["delete_files"])
        remove_sub_scope_config(repo_root, str(preview["parent_scope"]), str(preview["sub_scope"]))

    return {
        "ok": True,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "action": "delete_sub_scope",
        "operation": "apply",
        "scope_id": preview["scope_id"],
        "parent_scope": preview["parent_scope"],
        "sub_scope": preview["sub_scope"],
        "created_files": [],
        "changed_files": preview["changed_files"],
        "deleted_files": preview["delete_files"],
        "missing_files": preview["missing_files"],
        "build_commands": [],
        "urls": {
            "management": f"/docs/?scope={preview['parent_scope']}",
            "public": "",
        },
        "summary_text": (
            f"Deleted Docs Viewer sub-scope {preview['parent_scope']}/{preview['sub_scope']}."
            if not dry_run
            else f"Validated delete apply for Docs Viewer sub-scope {preview['parent_scope']}/{preview['sub_scope']}."
        ),
        "dry_run": dry_run,
    }


def plan_create_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope_id = normalize_scope_id(body.get("scope_id"))
    title = normalize_title(body.get("title"))
    publishing_mode = normalize_publishing_mode(body.get("publishing_mode"))
    default_doc_id = normalize_doc_id(body.get("default_doc_id"))
    external_data_root = resolve_external_data_root() if publishing_mode == LOCAL_EXTERNAL_MODE else None
    source_root = (
        planned_external_source_root(scope_id, external_data_root)
        if external_data_root is not None
        else normalize_source_root(body.get("source_root"), scope_id)
    )
    build_inline_search = bool_value(body, "build_inline_search", True)
    write_generated_outputs = bool_value(body, "write_generated_outputs", True)
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

    created_source_root = resolve_scope_path(repo_root, source_root)
    created_files = [
        path_record(repo_root, "source_root", created_source_root, action="create"),
        path_record(repo_root, "default_source_doc", created_source_root / f"{default_doc_id}.md", action="create"),
    ]
    changed_files = [
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
    ]
    if public_route_path:
        created_files.append(path_record(repo_root, "route_file", route_file_for_public_path(repo_root, public_route_path), action="create"))
        changed_files.extend(route_registry_path_records(repo_root, action="change"))
    if write_generated_outputs:
        docs_output = resolve_scope_path(
            repo_root,
            safe_scope_data_path(
                planned_scope_config["output"],
                field="planned_scope_config.output",
                allow_external=publishing_mode == LOCAL_EXTERNAL_MODE,
            ),
        )
        created_files.append(path_record(repo_root, "generated_docs_root", docs_output, action="create"))
        created_files.extend(
            [
                path_record(repo_root, "generated_docs_index_tree", docs_output / "index-tree.json", action="create"),
                path_record(repo_root, "generated_docs_recently_added", docs_output / "recently-added.json", action="create"),
                path_record(repo_root, "generated_docs_payload_root", docs_output / "by-id", action="create"),
            ]
        )
        if build_inline_search:
            created_files.append(
                path_record(
                    repo_root,
                    "generated_search_index",
                    generated_search_index_path(repo_root, planned_scope_config),
                    action="create",
                )
            )

    publish_files: list[dict[str, Any]] = []
    if publishing_mode == PUBLIC_MODE:
        published_output = repo_root / safe_relative_path(
            planned_scope_config["publish_output"],
            field="planned_scope_config.publish_output",
        )
        publish_files.append(path_record(repo_root, "published_docs_root", published_output, action="publish"))
        publish_files.extend(
            [
                path_record(repo_root, "published_docs_index_tree", published_output / "index-tree.json", action="publish"),
                path_record(repo_root, "published_docs_recently_added", published_output / "recently-added.json", action="publish"),
                path_record(repo_root, "published_docs_payload_root", published_output / "by-id", action="publish"),
            ]
        )
        if build_inline_search:
            publish_files.append(
                path_record(
                    repo_root,
                    "published_search_index",
                    published_search_index_path(repo_root, planned_scope_config),
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
    if write_generated_outputs:
        commands.append({"command": f"./docs-viewer/build/build_docs.py --scope {scope_id} --write", "status": "planned"})
        if build_inline_search:
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
        "build_inline_search": build_inline_search,
        "write_generated_outputs": write_generated_outputs,
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
