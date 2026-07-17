#!/usr/bin/env python3
"""External-local Docs Viewer scope rename planning and apply."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from docs_lifecycle_paths import (
    load_json_object,
    path_record,
    render_json,
    write_text_atomic,
)
from docs_scope_config import (
    CONFIG_REL_PATH,
    EXTERNAL_DATA_ROOT_MARKER,
    LOCAL_EXTERNAL_SCOPE_TYPE,
    load_docs_scope_configs,
    path_label,
    resolve_external_data_root,
)
from docs_scope_external_validation import external_scope_id_sync_blocker
from docs_scope_manifest import (
    LIFECYCLE_APPLY_SCHEMA_VERSION,
    LIFECYCLE_PREVIEW_SCHEMA_VERSION,
    MANIFEST_REL_PATH,
    load_manifest,
    manifest_scopes_by_id,
    normalize_scope_id,
    require_confirmed,
    scope_delete_eligible,
    utc_now,
)


LINK_REWRITE_WARNING = (
    "Links containing the old scope id are not rewritten; review same-scope and "
    "cross-scope links after the rename."
)


def scope_rename_eligible(config: Any, manifest_record: dict[str, Any] | None) -> bool:
    return bool(
        config
        and config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE
        and scope_delete_eligible(manifest_record)
        and str((manifest_record or {}).get("repo_status_at_creation") or "") == "external"
    )


def external_scope_roots(external_root: Path, scope_id: str) -> dict[str, Path]:
    return {
        "source_root": external_root / "source" / scope_id,
        "generated_docs_root": external_root / "generated" / "docs" / scope_id,
        "generated_search_root": external_root / "generated" / "search" / scope_id,
    }


def expected_config_paths(scope_id: str) -> dict[str, str]:
    return {
        "source": f"{EXTERNAL_DATA_ROOT_MARKER}/source/{scope_id}",
        "media_path_prefix": f"docs/{scope_id}",
        "output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/docs/{scope_id}",
        "search_output": f"{EXTERNAL_DATA_ROOT_MARKER}/generated/search/{scope_id}/index.json",
    }


def _renamed_config_path(value: Any, old_prefix: str, new_prefix: str) -> str:
    text = str(value or "").strip()
    if text == old_prefix:
        return new_prefix
    if text.startswith(old_prefix + "/"):
        return new_prefix + text[len(old_prefix):]
    return text


def _path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _move_records(
    repo_root: Path,
    old_roots: dict[str, Path],
    new_roots: dict[str, Path],
) -> list[dict[str, Any]]:
    return [
        {
            "kind": kind,
            "from": path_label(repo_root, old_roots[kind]),
            "to": path_label(repo_root, new_roots[kind]),
            "exists": _path_present(old_roots[kind]),
        }
        for kind in old_roots
    ]


def _build_commands(scope_id: str, *, dry_run: bool) -> list[dict[str, str]]:
    status = "planned" if dry_run else "completed"
    return [
        {
            "command": f"./docs-viewer/build/build_docs.py --scope {scope_id} --write",
            "status": status,
        },
        {
            "command": f"./docs-viewer/build/build_search.py --scope {scope_id} --write",
            "status": status,
        },
    ]


def plan_rename_scope_preview(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    old_scope_id = normalize_scope_id(body.get("scope_id") or body.get("old_scope_id"))
    new_scope_id = normalize_scope_id(body.get("new_scope_id"))
    configs = load_docs_scope_configs(repo_root)
    manifest = load_manifest(repo_root)
    manifest_records = manifest_scopes_by_id(manifest)
    config = configs.get(old_scope_id)
    manifest_record = manifest_records.get(old_scope_id)
    blockers: list[str] = []

    if old_scope_id == new_scope_id:
        blockers.append("new scope id must differ from the current scope id")
    if config is None:
        blockers.append("scope is not present in the Docs Viewer scope config")
    elif not scope_rename_eligible(config, manifest_record):
        blockers.append("only user-created external-local scopes can be renamed")
    if new_scope_id in configs:
        blockers.append(f"scope_id {new_scope_id!r} already exists")
    if new_scope_id in manifest_records:
        blockers.append(f"scope_id {new_scope_id!r} already exists in the docs scope manifest")
    raw_config = load_json_object(repo_root / CONFIG_REL_PATH, "docs scope config")
    settings = raw_config.get("docs_viewer")
    statuses = settings.get("ui_statuses_by_scope") if isinstance(settings, dict) else None
    if isinstance(statuses, dict) and new_scope_id in statuses and old_scope_id != new_scope_id:
        blockers.append(f"ui statuses already exist for scope {new_scope_id!r}")

    old_roots: dict[str, Path] = {}
    new_roots: dict[str, Path] = {}
    if config is not None and config.scope_type == LOCAL_EXTERNAL_SCOPE_TYPE:
        external_root = resolve_external_data_root()
        sync_blocker = external_scope_id_sync_blocker(new_scope_id, external_root)
        if sync_blocker:
            blockers.append(sync_blocker)
        old_roots = external_scope_roots(external_root, old_scope_id)
        new_roots = external_scope_roots(external_root, new_scope_id)
        configured_paths = {
            "source_root": config.source,
            "generated_docs_root": config.output,
            "generated_search_root": config.search_output.parent,
        }
        for kind, configured_path in configured_paths.items():
            if configured_path.resolve() != old_roots[kind].resolve():
                blockers.append(f"configured {kind.replace('_', ' ')} does not match the lifecycle-owned external path")
        if not _path_present(old_roots["source_root"]):
            blockers.append("external source root does not exist")
        for kind, target in new_roots.items():
            if _path_present(target):
                blockers.append(f"rename target already exists: {kind.replace('_', ' ')}")

    return {
        "ok": True,
        "schema_version": LIFECYCLE_PREVIEW_SCHEMA_VERSION,
        "action": "rename_scope",
        "operation": "preview",
        "scope_id": old_scope_id,
        "new_scope_id": new_scope_id,
        "scope_type": LOCAL_EXTERNAL_SCOPE_TYPE,
        "allowed": not blockers,
        "blockers": blockers,
        "warnings": [LINK_REWRITE_WARNING],
        "move_paths": _move_records(repo_root, old_roots, new_roots) if old_roots else [],
        "changed_files": [
            path_record(repo_root, "scope_config", repo_root / CONFIG_REL_PATH, action="change"),
            path_record(repo_root, "scope_manifest", repo_root / MANIFEST_REL_PATH, action="change"),
        ],
        "build_commands": _build_commands(new_scope_id, dry_run=True),
        "urls": {
            "management": f"/docs/?scope={new_scope_id}",
            "public": "",
        },
        "summary_text": f"Ready to rename Docs Viewer scope {old_scope_id} to {new_scope_id}.",
        "dry_run": True,
    }


def _renamed_scope_config_payload(
    repo_root: Path,
    old_scope_id: str,
    new_scope_id: str,
) -> dict[str, Any]:
    payload = load_json_object(repo_root / CONFIG_REL_PATH, "docs scope config")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("docs scope config scopes must be an array")
    target = next(
        (
            item
            for item in scopes
            if isinstance(item, dict) and str(item.get("scope_id") or "").strip() == old_scope_id
        ),
        None,
    )
    if target is None:
        raise ValueError(f"scope_id {old_scope_id!r} is missing from docs scope config")
    target["scope_id"] = new_scope_id
    old_paths = expected_config_paths(old_scope_id)
    new_paths = expected_config_paths(new_scope_id)
    target.update(new_paths)
    sub_scopes = target.get("sub_scopes")
    if isinstance(sub_scopes, list):
        for sub_scope in sub_scopes:
            if not isinstance(sub_scope, dict):
                continue
            sub_scope["source"] = _renamed_config_path(
                sub_scope.get("source"), old_paths["source"], new_paths["source"]
            )
            for key in ("output", "publish_output"):
                sub_scope[key] = _renamed_config_path(
                    sub_scope.get(key), old_paths["output"], new_paths["output"]
                )

    settings = payload.get("docs_viewer")
    if isinstance(settings, dict):
        statuses = settings.get("ui_statuses_by_scope")
        if isinstance(statuses, dict) and old_scope_id in statuses:
            if new_scope_id in statuses:
                raise ValueError(f"ui statuses already exist for scope {new_scope_id!r}")
            statuses[new_scope_id] = statuses.pop(old_scope_id)
    return payload


def _renamed_external_path(
    value: Any,
    root_pairs: list[tuple[Path, Path]],
) -> str:
    text = str(value or "").strip()
    path = Path(text)
    if not text or not path.is_absolute():
        return text
    for old_root, new_root in root_pairs:
        try:
            relative = path.relative_to(old_root)
        except ValueError:
            continue
        return (new_root / relative).as_posix()
    return text


def _renamed_manifest_payload(
    repo_root: Path,
    old_scope_id: str,
    new_scope_id: str,
    old_roots: dict[str, Path],
    new_roots: dict[str, Path],
) -> dict[str, Any]:
    manifest = copy.deepcopy(load_manifest(repo_root))
    record = manifest_scopes_by_id(manifest).get(old_scope_id)
    if record is None:
        raise ValueError(f"scope_id {old_scope_id!r} is missing from docs scope manifest")
    record["scope_id"] = new_scope_id
    record["updated_at"] = utc_now()
    root_pairs = [(old_roots[kind], new_roots[kind]) for kind in old_roots]
    for file_record in record.get("files", []):
        if not isinstance(file_record, dict):
            continue
        file_record["path"] = _renamed_external_path(file_record.get("path"), root_pairs)
    manifest["updated_at"] = utc_now()
    return manifest


def _move_external_roots(
    old_roots: dict[str, Path],
    new_roots: dict[str, Path],
) -> list[dict[str, str]]:
    moved: list[dict[str, str]] = []
    for kind in ("generated_docs_root", "generated_search_root", "source_root"):
        source = old_roots[kind]
        target = new_roots[kind]
        if not _path_present(source):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        moved.append({"kind": kind, "from": source.as_posix(), "to": target.as_posix()})
    return moved


def apply_rename_scope(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool,
    rebuild_scope_outputs: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    require_confirmed(body)
    preview = plan_rename_scope_preview(repo_root, body)
    if not preview["allowed"]:
        raise ValueError("; ".join(preview["blockers"]) or "scope rename is not allowed")

    old_scope_id = str(preview["scope_id"])
    new_scope_id = str(preview["new_scope_id"])
    external_root = resolve_external_data_root()
    old_roots = external_scope_roots(external_root, old_scope_id)
    new_roots = external_scope_roots(external_root, new_scope_id)
    config_payload = _renamed_scope_config_payload(repo_root, old_scope_id, new_scope_id)
    manifest_payload = _renamed_manifest_payload(
        repo_root,
        old_scope_id,
        new_scope_id,
        old_roots,
        new_roots,
    )
    moved_paths: list[dict[str, str]] = []
    rebuild = None

    if not dry_run:
        moved_paths = _move_external_roots(old_roots, new_roots)
        write_text_atomic(repo_root / CONFIG_REL_PATH, render_json(config_payload))
        write_text_atomic(repo_root / MANIFEST_REL_PATH, render_json(manifest_payload))
        rebuild = rebuild_scope_outputs(repo_root, new_scope_id, include_search=True)

    return {
        **preview,
        "schema_version": LIFECYCLE_APPLY_SCHEMA_VERSION,
        "operation": "apply",
        "move_paths": moved_paths if not dry_run else preview["move_paths"],
        "build_commands": _build_commands(new_scope_id, dry_run=dry_run),
        "rebuild": rebuild,
        "summary_text": (
            f"Renamed Docs Viewer scope {old_scope_id} to {new_scope_id}."
            if not dry_run
            else f"Validated rename apply for Docs Viewer scope {old_scope_id}."
        ),
        "dry_run": dry_run,
    }


__all__ = [
    "LINK_REWRITE_WARNING",
    "apply_rename_scope",
    "plan_rename_scope_preview",
    "scope_rename_eligible",
]
