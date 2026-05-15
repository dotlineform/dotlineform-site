#!/usr/bin/env python3
"""Docs Viewer scope ownership manifest and lifecycle preview helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

from docs_scope_config import CONFIG_REL_PATH, DocsScopeConfig, load_docs_scope_configs, safe_relative_path


MANIFEST_REL_PATH = Path("scripts/docs/docs_scope_manifest.json")
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


def generated_search_index_path(repo_root: Path, scope_id: str) -> Path:
    return repo_root / "assets" / "data" / "search" / scope_id / "index.json"


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
            path_record(repo_root, "generated_search_index", generated_search_index_path(repo_root, config.scope_id)),
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
    if len(source_root.parts) != 1 or not source_root.name.startswith("_docs_"):
        raise ValueError("source_root must be a single allowlisted _docs_<scope> directory")
    if source_root.name != f"_docs_{scope_id}":
        raise ValueError(f"source_root must be _docs_{scope_id}")
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


def planned_scope_config_record(scope_id: str, source_root: Path, public_route_path: str, default_doc_id: str) -> dict[str, Any]:
    viewer_base_url = public_route_path or "/docs/"
    return {
        "scope_id": scope_id,
        "source": source_root.as_posix(),
        "media_path_prefix": f"docs/{scope_id}",
        "output": f"assets/data/docs/scopes/{scope_id}",
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
            "published: true",
            "hidden: false",
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


def plan_create_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope_id = normalize_scope_id(body.get("scope_id"))
    title = normalize_title(body.get("title"))
    publishing_mode = normalize_publishing_mode(body.get("publishing_mode"))
    default_doc_id = normalize_doc_id(body.get("default_doc_id"))
    source_root = normalize_source_root(body.get("source_root"), scope_id)
    build_inline_search = bool_value(body, "build_inline_search", True)
    write_generated_outputs = bool_value(body, "write_generated_outputs", True)
    public_route_path = normalize_route_path(body.get("public_route_path")) if publishing_mode == PUBLIC_MODE else ""

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
        docs_output = repo_root / "assets" / "data" / "docs" / "scopes" / scope_id
        created_files.extend(
            [
                path_record(repo_root, "generated_docs_root", docs_output, action="create"),
                path_record(repo_root, "generated_docs_index", docs_output / "index.json", action="create"),
                path_record(repo_root, "generated_docs_payload_root", docs_output / "by-id", action="create"),
            ]
        )
        if build_inline_search:
            created_files.append(path_record(repo_root, "generated_search_index", generated_search_index_path(repo_root, scope_id), action="create"))

    conflicts = [record["path"] for record in created_files if record.get("exists")]
    if conflicts:
        raise ValueError(f"scope creation would overwrite existing paths: {', '.join(conflicts)}")

    commands = []
    if write_generated_outputs:
        commands.append({"command": f"./scripts/build_docs.rb --scope {scope_id} --write", "status": "planned"})
        if build_inline_search:
            commands.append({"command": f"./scripts/build_search.rb --scope {scope_id} --write", "status": "planned"})

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
        "planned_scope_config": planned_scope_config_record(scope_id, source_root, public_route_path, default_doc_id),
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

    delete_files = []
    missing_files = []
    for file_record in record.get("files", []):
        if not isinstance(file_record, dict):
            continue
        path_text = str(file_record.get("path") or "").strip()
        if not path_text:
            continue
        path = repo_root / safe_relative_path(path_text, field="manifest file path")
        planned = path_record(repo_root, str(file_record.get("kind") or "file"), path, action="delete")
        if path.exists():
            delete_files.append(planned)
        else:
            missing_files.append(planned)

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
        "build_commands": [
            {"command": f"./scripts/build_docs.rb --scope {scope_id} --write", "status": "planned"},
            {"command": f"./scripts/build_search.rb --scope {scope_id} --write", "status": "planned"},
        ],
        "summary_text": f"Previewed deletion for Docs Viewer scope {scope_id}.",
    }
