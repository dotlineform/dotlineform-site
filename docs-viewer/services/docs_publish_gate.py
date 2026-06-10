#!/usr/bin/env python3
"""Publish working public-scope Docs Viewer payloads to public snapshots."""

from __future__ import annotations

import filecmp
import shutil
from pathlib import Path
from typing import Any

from docs_scope_config import DocsScopeConfig, is_public_readonly_scope, load_docs_scope_configs


PUBLISH_SCHEMA_VERSION = "docs_publish_gate_v1"


def repo_relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes repo root: {path}") from exc


def normalize_scope(repo_root: Path, value: Any) -> tuple[str, DocsScopeConfig]:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError("scope is required")
    configs = load_docs_scope_configs(repo_root)
    config = configs.get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    if not is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ):
        raise ValueError(f"scope {scope!r} is not a public read-only scope")
    return scope, config


def validate_publish_paths(repo_root: Path, config: DocsScopeConfig) -> dict[str, Path]:
    paths = {
        "working_docs_root": (repo_root / config.output).resolve(),
        "working_search_index": (repo_root / config.search_output).resolve(),
        "published_docs_root": (repo_root / config.publish_output).resolve(),
        "published_search_index": (repo_root / config.publish_search_output).resolve(),
    }
    for label, path in paths.items():
        repo_relative(repo_root, path)
        if label.startswith("published_") and path.relative_to(repo_root.resolve()).parts[:2] == ("docs-viewer", "generated"):
            raise ValueError(f"{label} must not publish under docs-viewer/generated")
    if paths["working_docs_root"] == paths["published_docs_root"]:
        raise ValueError("working docs root and published docs root must be separate")
    if paths["working_search_index"] == paths["published_search_index"]:
        raise ValueError("working search index and published search index must be separate")
    if not paths["working_docs_root"].is_dir():
        raise FileNotFoundError(f"working docs output not found: {repo_relative(repo_root, paths['working_docs_root'])}")
    if not paths["working_search_index"].is_file():
        raise FileNotFoundError(f"working search output not found: {repo_relative(repo_root, paths['working_search_index'])}")
    return paths


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def docs_diff(repo_root: Path, working_root: Path, published_root: Path) -> dict[str, list[str]]:
    changed: list[str] = []
    removed: list[str] = []
    for source_path in iter_files(working_root):
        rel = source_path.relative_to(working_root)
        target_path = published_root / rel
        if not target_path.exists() or not filecmp.cmp(source_path, target_path, shallow=False):
            changed.append(repo_relative(repo_root, target_path))
    for target_path in iter_files(published_root):
        rel = target_path.relative_to(published_root)
        if not (working_root / rel).exists():
            removed.append(repo_relative(repo_root, target_path))
    return {"changed": changed, "removed": removed}


def search_diff(repo_root: Path, working_index: Path, published_index: Path) -> dict[str, list[str]]:
    if not published_index.exists() or not filecmp.cmp(working_index, published_index, shallow=False):
        return {"changed": [repo_relative(repo_root, published_index)], "removed": []}
    return {"changed": [], "removed": []}


def publish_status(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope, config = normalize_scope(repo_root, body.get("scope"))
    paths = validate_publish_paths(repo_root, config)
    docs = docs_diff(repo_root, paths["working_docs_root"], paths["published_docs_root"])
    search = search_diff(repo_root, paths["working_search_index"], paths["published_search_index"])
    changed = len(docs["changed"]) + len(search["changed"])
    removed = len(docs["removed"]) + len(search["removed"])
    return {
        "ok": True,
        "schema_version": PUBLISH_SCHEMA_VERSION,
        "action": "publish_docs",
        "operation": "status",
        "scope": scope,
        "changed_count": changed,
        "removed_count": removed,
        "up_to_date": changed == 0 and removed == 0,
        "paths": {key: repo_relative(repo_root, value) for key, value in paths.items()},
        "docs": docs,
        "search": search,
        "summary_text": f"Publish status for {scope}: {changed} changed, {removed} stale.",
    }


def publish_confirm(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    payload = publish_status(repo_root, body)
    payload["operation"] = "confirm"
    payload["summary_text"] = (
        f"Publish confirmation for {payload['scope']}: "
        f"{payload['changed_count']} changed, {payload['removed_count']} stale."
    )
    return payload


def copy_tree(source_root: Path, target_root: Path) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    for source_path in iter_files(source_root):
        rel = source_path.relative_to(source_root)
        target_path = target_root / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        copy_file_atomic(source_path, target_path)
    for target_path in reversed(iter_files(target_root)):
        rel = target_path.relative_to(target_root)
        if not (source_root / rel).exists():
            target_path.unlink()
    for directory in sorted((path for path in target_root.rglob("*") if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def copy_file_atomic(source_path: Path, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f".{target_path.name}.tmp")
    shutil.copy2(source_path, temp_path)
    temp_path.replace(target_path)


def publish_apply(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to publish docs")
    payload = publish_confirm(repo_root, body)
    _scope, config = normalize_scope(repo_root, payload["scope"])
    paths = validate_publish_paths(repo_root, config)
    copy_tree(paths["working_docs_root"], paths["published_docs_root"])
    copy_file_atomic(paths["working_search_index"], paths["published_search_index"])
    payload["operation"] = "apply"
    payload["applied"] = True
    payload["summary_text"] = (
        f"Published docs for {payload['scope']}: "
        f"{payload['changed_count']} changed, {payload['removed_count']} stale."
    )
    return payload
