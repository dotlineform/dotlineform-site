#!/usr/bin/env python3
"""Sub-scope lifecycle preview and apply helpers for Docs Viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_lifecycle_paths import (
    delete_manifest_paths,
    load_json_object,
    path_record,
    render_json,
    resolve_lifecycle_record_path,
    write_text_atomic,
)
from docs_scope_config import (
    CONFIG_REL_PATH,
    DocsScopeConfig,
    document_source_path,
    load_docs_scope_configs,
    normalize_sub_scope_id,
    public_documents_path,
    published_documents_path,
    resolve_scope_path,
)
from docs_scope_manifest import (
    LIFECYCLE_APPLY_SCHEMA_VERSION,
    LIFECYCLE_PREVIEW_SCHEMA_VERSION,
    normalize_scope_id,
    normalize_title,
    require_confirmed,
)


def find_raw_scope_config(payload: dict[str, Any], scope_id: str) -> dict[str, Any]:
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    for item in scopes:
        if isinstance(item, dict) and str(item.get("scope_id") or "").strip() == scope_id:
            return item
    raise ValueError(f"scope_id {scope_id!r} is missing from docs scope config")


def append_path_text(value: Any, *children: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("sub-scope parent path is required")
    path = Path(text)
    for child in children:
        if child and child != ".":
            path /= child
    return path.as_posix()


def raw_location(container: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(container, dict):
        raise ValueError(f"{field} must be an object")
    location = container.get("location")
    if not isinstance(location, dict):
        raise ValueError(f"{field}.location must be an object")
    provider = str(location.get("provider") or "").strip()
    path = str(location.get("path") or "").strip()
    if not provider or not path:
        raise ValueError(f"{field}.location requires provider and path")
    return {"provider": provider, "path": path}


def child_location(container: Any, *children: str, field: str) -> dict[str, Any]:
    location = raw_location(container, field=field)
    location["path"] = append_path_text(location["path"], *children)
    return location


def planned_sub_scope_config_record(
    parent_config: DocsScopeConfig,
    raw_parent_config: dict[str, Any],
    sub_scope: str,
    title: str,
) -> dict[str, Any]:
    raw_source = raw_parent_config.get("source")
    if not isinstance(raw_source, dict):
        raise ValueError("parent source role must be an object")
    raw_published = raw_parent_config.get("published")
    if not isinstance(raw_published, dict):
        raise ValueError("parent published role must be an object")
    source_location = child_location(
        raw_source,
        str(raw_source.get("sub_scopes_path") or "."),
        sub_scope,
        field="parent source",
    )
    published_documents = raw_published.get("documents")
    published_search = raw_published.get("search")
    search_location = raw_location(published_search, field="parent published search")
    search_location["path"] = (
        Path(search_location["path"]).parent / sub_scope / "index.json"
    ).as_posix()
    raw_projection = raw_parent_config.get("public_projection")
    projection = None
    if parent_config.public_projection is not None:
        if not isinstance(raw_projection, dict):
            raise ValueError("parent public projection must be an object")
        projection = {
            "documents": {
                "location": child_location(
                    raw_projection.get("documents"),
                    sub_scope,
                    field="parent public documents",
                )
            },
            "search": None,
        }
    return {
        "sub_scope": sub_scope,
        "title": title,
        "source": {
            "location": source_location,
            "documents_path": ".",
            "build_media": {},
            "sub_scopes_path": ".",
        },
        "published": {
            "documents": {
                "location": child_location(
                    published_documents,
                    sub_scope,
                    field="parent published documents",
                )
            },
            "search": {"location": search_location},
            "media": {},
        },
        "public_projection": projection,
    }


def append_sub_scope_config(repo_root: Path, parent_scope: str, sub_scope_config: dict[str, Any]) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    payload = load_json_object(config_path, "docs scope config")
    if payload.get("schema_version") != "docs_scopes_v2":
        raise ValueError("docs scope config schema_version must be docs_scopes_v2")
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
    if payload.get("schema_version") != "docs_scopes_v2":
        raise ValueError("docs scope config schema_version must be docs_scopes_v2")
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


def sub_scope_storage_contract(
    parent_scope: str,
    sub_scope_config: dict[str, Any],
    *,
    public_static_assets: bool,
) -> dict[str, Any]:
    source = sub_scope_config.get("source")
    published = sub_scope_config.get("published")
    projection = sub_scope_config.get("public_projection")
    source_root = raw_location(source, field="planned sub-scope source")["path"]
    published_docs = raw_location(
        published.get("documents") if isinstance(published, dict) else None,
        field="planned sub-scope published documents",
    )["path"]
    public_docs = (
        raw_location(projection.get("documents"), field="planned sub-scope public documents")["path"]
        if isinstance(projection, dict)
        else published_docs
    )
    return {
        "publishing_mode": "parent_scope",
        "public_static_assets": public_static_assets,
        "access": "embedded_detail_documents",
        "source_root": source_root,
        "docs_output": published_docs,
        "publish_output": public_docs,
        "search_output": "",
        "summary": (
            f"Sub-scope under {parent_scope}: creates nested source and published payload roots. "
            "It does not create a top-level scope, default document, route, or scope selector entry."
        ),
    }


def sub_scope_path_records(repo_root: Path, parent_config: DocsScopeConfig, sub_scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_root = resolve_scope_path(
        repo_root,
        parent_config.source.location.path / parent_config.source.sub_scopes_path / sub_scope,
    )
    docs_output = resolve_scope_path(repo_root, published_documents_path(parent_config) / sub_scope)
    records = [
        path_record(repo_root, "sub_scope_source_root", source_root, action="create"),
        path_record(repo_root, "sub_scope_published_docs_root", docs_output, action="create"),
        path_record(repo_root, "sub_scope_published_docs_payload_root", docs_output / "by-id", action="create"),
    ]
    publish_records: list[dict[str, Any]] = []
    public_output = public_documents_path(parent_config)
    if public_output is not None:
        publish_output = resolve_scope_path(repo_root, public_output / sub_scope)
        publish_records.extend(
            [
                path_record(repo_root, "sub_scope_public_docs_root", publish_output, action="publish"),
                path_record(repo_root, "sub_scope_public_docs_payload_root", publish_output / "by-id", action="publish"),
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
    public_readonly = parent_config.public_projection is not None

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
    candidate_paths = [
        ("sub_scope_source_root", resolve_scope_path(repo_root, document_source_path(sub_scope_config))),
        ("sub_scope_published_docs_root", resolve_scope_path(repo_root, published_documents_path(sub_scope_config))),
    ]
    public_output = public_documents_path(sub_scope_config)
    if public_output is not None:
        candidate_paths.append(("sub_scope_public_docs_root", resolve_scope_path(repo_root, public_output)))

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
