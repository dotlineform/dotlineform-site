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

from docs_scope_config import CONFIG_REL_PATH, DocsScopeConfig, load_docs_scope_configs, safe_relative_path


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
LOCAL_UNCOMMITTED_MODE = "local_uncommitted"
PUBLISHING_MODES = (PUBLIC_MODE, LOCAL_COMMITTED_MODE, LOCAL_UNCOMMITTED_MODE)
SCOPE_DELETE_CHANGE_KINDS = {"scope_config", "scope_manifest"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_relative(repo_root: Path, path: Path) -> str:
    resolved_root = repo_root.resolve()
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def path_record(repo_root: Path, kind: str, path: Path, *, action: str = "track") -> dict[str, Any]:
    return {
        "kind": kind,
        "path": repo_relative(repo_root, path),
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
        return repo_root / config.search_output
    return repo_root / safe_relative_path(config.get("search_output"), field="planned_scope_config.search_output")


def route_file_for_config(repo_root: Path, config: DocsScopeConfig) -> Path:
    route_base = config.viewer_base_url.strip("/")
    route_rel = Path(route_base) / "index.md" if route_base else Path("index.md")
    return repo_root / route_rel


def route_is_readonly(route_path: Path) -> bool:
    if not route_path.exists() or not route_path.is_file():
        return False
    try:
        return "docs_viewer_readonly_route.html" in route_path.read_text(encoding="utf-8")
    except OSError:
        return False


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
    candidate = repo_root / config.source / f"{config.default_doc_id}.md"
    if candidate.exists():
        return path_record(repo_root, "default_source_doc", candidate)
    return None


def backfilled_scope_record(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    source_root = repo_root / config.source
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
    files.extend(
        [
            path_record(repo_root, "generated_docs_root", repo_root / config.output),
            path_record(repo_root, "generated_docs_index", repo_root / config.output / "index.json"),
            path_record(repo_root, "generated_docs_payload_root", repo_root / config.output / "by-id"),
            path_record(repo_root, "generated_search_index", generated_search_index_path(repo_root, config)),
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
    return bool(record and record.get("user_created") is True and record.get("created_by_tool") is True)


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
    route_rel = Path(public_route_path.strip("/")) / "index.md"
    return repo_root / route_rel


def bool_value(payload: dict[str, Any], key: str, default: bool) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    raise ValueError(f"{key} must be a boolean")


def require_confirmed(body: dict[str, Any]) -> None:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to apply scope lifecycle changes")


def planned_docs_output(scope_id: str, publishing_mode: str) -> Path:
    if publishing_mode == PUBLIC_MODE:
        return Path("assets/data/docs/scopes") / scope_id
    return Path("docs-viewer/generated/docs") / scope_id


def planned_search_output(scope_id: str, publishing_mode: str) -> Path:
    if publishing_mode == PUBLIC_MODE:
        return Path("assets/data/search") / scope_id / "index.json"
    return Path("docs-viewer/generated/search") / scope_id / "index.json"


def planned_scope_type(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public"
    if publishing_mode == LOCAL_UNCOMMITTED_MODE:
        return "local_uncommitted"
    return "local"


def planned_scope_meta(publishing_mode: str) -> str:
    if publishing_mode == PUBLIC_MODE:
        return "public scope"
    if publishing_mode == LOCAL_UNCOMMITTED_MODE:
        return "local only"
    return "local management"


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_planned_storage_paths(scope_id: str, publishing_mode: str, config: dict[str, Any]) -> None:
    docs_output = safe_relative_path(config.get("output"), field="planned_scope_config.output")
    search_output = safe_relative_path(config.get("search_output"), field="planned_scope_config.search_output")
    if publishing_mode == PUBLIC_MODE:
        return
    if path_is_relative_to(docs_output, Path("assets/data/docs/scopes")):
        raise ValueError(
            f"committed manage-mode scope {scope_id!r} must not write generated docs under assets/data/docs/scopes"
        )
    if path_is_relative_to(search_output, Path("assets/data/search")):
        raise ValueError(
            f"committed manage-mode scope {scope_id!r} must not write generated search under assets/data/search"
        )


def planned_scope_config_record(
    scope_id: str,
    source_root: Path,
    public_route_path: str,
    default_doc_id: str,
    publishing_mode: str,
) -> dict[str, Any]:
    viewer_base_url = public_route_path or "/docs/"
    return {
        "scope_id": scope_id,
        "scope_type": planned_scope_type(publishing_mode),
        "meta": planned_scope_meta(publishing_mode),
        "source": source_root.as_posix(),
        "media_path_prefix": f"docs/{scope_id}",
        "output": planned_docs_output(scope_id, publishing_mode).as_posix(),
        "search_output": planned_search_output(scope_id, publishing_mode).as_posix(),
        "viewer_base_url": viewer_base_url,
        "include_scope_param": public_route_path == "",
        "default_doc_id": default_doc_id,
        "allow_nested_source": False,
        "non_loadable_doc_ids": [],
        "manage_only_tree_root_ids": [],
        "show_updated_date": True,
        "allow_unresolved_parent_ids": False,
        "import_media_storage": {
            "storage_mode": "staging_manual",
            "repo_assets_path_prefix": f"assets/docs/{scope_id}",
            "repo_assets_public_path_prefix": f"/assets/docs/{scope_id}",
        },
    }


def planned_storage_contract(preview: dict[str, Any]) -> dict[str, Any]:
    publishing_mode = str(preview["publishing_mode"])
    config = preview["planned_scope_config"]
    docs_output = str(config["output"])
    search_output = str(config["search_output"])
    if publishing_mode == PUBLIC_MODE:
        summary = (
            "Public read-only scope: generated docs and search payloads are public static assets under assets/ "
            "and a public route is created."
        )
        access = "public_readonly_route_and_local_manage"
        public_static_assets = True
    elif publishing_mode == LOCAL_COMMITTED_MODE:
        summary = (
            "Committed manage-mode scope: generated docs and search payloads are tracked non-public Docs Viewer "
            "runtime data under docs-viewer/generated/ and no public route is created."
        )
        access = "local_manage_only"
        public_static_assets = False
    else:
        summary = (
            "Uncommitted manage-mode scope: generated docs and search payloads use the non-public "
            "docs-viewer/generated/ path shape for local preview and no public route is created."
        )
        access = "local_manage_only"
        public_static_assets = False
    return {
        "publishing_mode": publishing_mode,
        "public_static_assets": public_static_assets,
        "access": access,
        "docs_output": docs_output,
        "search_output": search_output,
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


def readonly_route_text(title: str, scope_id: str, public_route_path: str) -> str:
    route_section = public_route_path.strip("/").split("/", 1)[0] or scope_id
    search_label = f"search {title.lower()}"
    return "\n".join(
        [
            "---",
            "layout: default",
            f"title: {json.dumps(title, ensure_ascii=False)}",
            f"section: {route_section}",
            f"permalink: {public_route_path}",
            "---",
            "",
            "{% include docs_viewer_readonly_route.html",
            f"  search_placeholder={json.dumps(search_label, ensure_ascii=False)}",
            f"  search_aria_label={json.dumps('Search ' + title, ensure_ascii=False)}",
            "%}",
            "",
        ]
    )


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


def manifest_file_records_for_created_scope(repo_root: Path, preview: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in [*preview.get("created_files", []), *preview.get("changed_files", [])]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind == "scope_manifest":
            continue
        path_text = str(item.get("path") or "").strip()
        if not kind or not path_text:
            continue
        path = repo_root / safe_relative_path(path_text, field="created scope file path")
        records.append(path_record(repo_root, kind, path, action="track"))
    return records


def created_scope_manifest_record(repo_root: Path, preview: dict[str, Any]) -> dict[str, Any]:
    publishing_mode = str(preview["publishing_mode"])
    scope_type = "public" if publishing_mode == PUBLIC_MODE else "local"
    repo_status = "untracked" if publishing_mode == LOCAL_UNCOMMITTED_MODE else "tracked"
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
    source_root = repo_root / preview["planned_scope_config"]["source"]
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
                readonly_route_text(str(preview["title"]), scope_id, str(preview["urls"]["public"])),
            )
        append_scope_manifest_record(repo_root, preview, manifest)
        if preview["write_generated_outputs"]:
            rebuild = rebuild_scope_outputs(
                repo_root,
                scope_id,
                include_search=preview["build_inline_search"],
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
    for file_record in record.get("files", []):
        if not isinstance(file_record, dict):
            continue
        kind = str(file_record.get("kind") or "file").strip() or "file"
        if kind in SCOPE_DELETE_CHANGE_KINDS:
            continue
        path_text = str(file_record.get("path") or "").strip()
        if not path_text:
            continue
        path = repo_root / safe_relative_path(path_text, field="manifest file path")
        planned = path_record(repo_root, kind, path, action="delete")
        if path.exists():
            delete_files.append(planned)
        else:
            missing_files.append(planned)
    return delete_files, missing_files


def delete_path_sort_key(repo_root: Path, record: dict[str, Any]) -> tuple[int, str]:
    path = repo_root / safe_relative_path(record.get("path"), field="delete file path")
    return (-len(path.parts), path.as_posix())


def delete_manifest_paths(repo_root: Path, delete_files: list[dict[str, Any]]) -> None:
    for record in sorted(delete_files, key=lambda item: delete_path_sort_key(repo_root, item)):
        path = repo_root / safe_relative_path(record.get("path"), field="delete file path")
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
            "management": "/docs/?mode=manage",
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


def plan_create_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope_id = normalize_scope_id(body.get("scope_id"))
    title = normalize_title(body.get("title"))
    publishing_mode = normalize_publishing_mode(body.get("publishing_mode"))
    default_doc_id = normalize_doc_id(body.get("default_doc_id"))
    source_root = normalize_source_root(body.get("source_root"), scope_id)
    build_inline_search = bool_value(body, "build_inline_search", True)
    write_generated_outputs = bool_value(body, "write_generated_outputs", True)
    public_route_path = normalize_route_path(body.get("public_route_path")) if publishing_mode == PUBLIC_MODE else ""
    planned_scope_config = planned_scope_config_record(
        scope_id,
        source_root,
        public_route_path,
        default_doc_id,
        publishing_mode,
    )
    validate_planned_storage_paths(scope_id, publishing_mode, planned_scope_config)

    existing_configs = load_docs_scope_configs(repo_root)
    if scope_id in existing_configs:
        raise ValueError(f"scope_id {scope_id!r} already exists")

    manifest = load_manifest(repo_root)
    if scope_id in manifest_scopes_by_id(manifest):
        raise ValueError(f"scope_id {scope_id!r} already exists in docs scope manifest")

    created_files = [
        path_record(repo_root, "source_root", repo_root / source_root, action="create"),
        path_record(repo_root, "default_source_doc", repo_root / source_root / f"{default_doc_id}.md", action="create"),
    ]
    changed_files = [
        path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
        path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
    ]
    if public_route_path:
        created_files.append(path_record(repo_root, "route_file", route_file_for_public_path(repo_root, public_route_path), action="create"))
    if write_generated_outputs:
        docs_output = repo_root / safe_relative_path(
            planned_scope_config["output"],
            field="planned_scope_config.output",
        )
        created_files.extend(
            [
                path_record(repo_root, "generated_docs_root", docs_output, action="create"),
                path_record(repo_root, "generated_docs_index", docs_output / "index.json", action="create"),
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

    conflicts = [record["path"] for record in created_files if record.get("exists")]
    if conflicts:
        raise ValueError(f"scope creation would overwrite existing paths: {', '.join(conflicts)}")

    commands = []
    if write_generated_outputs:
        commands.append({"command": f"./docs-viewer/build/build_docs.py --scope {scope_id} --write", "status": "planned"})
        if build_inline_search:
            commands.append({"command": f"./docs-viewer/build/build_search.py --scope {scope_id} --write", "status": "planned"})

    management_url = f"/docs/?scope={scope_id}&mode=manage"
    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "create_scope",
        "operation": "preview",
        "scope_id": scope_id,
        "title": title,
        "publishing_mode": publishing_mode,
        "build_inline_search": build_inline_search,
        "write_generated_outputs": write_generated_outputs,
        "planned_scope_config": planned_scope_config,
        "storage_contract": planned_storage_contract(
            {
                "publishing_mode": publishing_mode,
                "planned_scope_config": planned_scope_config,
            }
        ),
        "created_files": created_files,
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

    delete_files, missing_files = manifest_delete_path_records(repo_root, record)

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
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
            path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
        ],
        "build_commands": apply_delete_build_commands(repo_root, scope_id, dry_run=True),
        "summary_text": f"Previewed deletion for Docs Viewer scope {scope_id}.",
    }
