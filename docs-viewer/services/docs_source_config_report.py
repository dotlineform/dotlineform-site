#!/usr/bin/env python3
"""Build browser-safe Docs Viewer source config report payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_scope_config import CONFIG_REL_PATH, DocsScopeConfig, load_docs_scope_configs, path_label, resolve_scope_path


BROWSER_CONFIG_REL_PATH = Path("docs-viewer/config/defaults/docs-viewer-config.json")
SCHEMA_VERSION = "docs_source_config_report_v1"


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _raw_scope_records(repo_root: Path) -> list[dict[str, Any]]:
    payload = _load_json(repo_root / CONFIG_REL_PATH, str(CONFIG_REL_PATH))
    raw_scopes = payload.get("scopes")
    if not isinstance(raw_scopes, list):
        raise ValueError(f"{CONFIG_REL_PATH} must contain a scopes array")
    return [item for item in raw_scopes if isinstance(item, dict)]


def _browser_scope_records(repo_root: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(repo_root / BROWSER_CONFIG_REL_PATH, str(BROWSER_CONFIG_REL_PATH))
    raw_scopes = payload.get("scopes")
    if not isinstance(raw_scopes, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for item in raw_scopes:
        if not isinstance(item, dict):
            continue
        scope_id = str(item.get("scope_id") or "").strip().lower()
        if scope_id:
            out[scope_id] = item
    return out


def _docs_viewer_source_settings(repo_root: Path) -> dict[str, Any]:
    payload = _load_json(repo_root / CONFIG_REL_PATH, str(CONFIG_REL_PATH))
    docs_viewer = payload.get("docs_viewer")
    return docs_viewer if isinstance(docs_viewer, dict) else {}


def _browser_docs_viewer_settings(repo_root: Path) -> dict[str, Any]:
    payload = _load_json(repo_root / BROWSER_CONFIG_REL_PATH, str(BROWSER_CONFIG_REL_PATH))
    docs_viewer = payload.get("docs_viewer")
    return docs_viewer if isinstance(docs_viewer, dict) else {}


def generated_docs_index_tree_path(repo_root: Path, config: DocsScopeConfig) -> Path:
    return resolve_scope_path(repo_root, config.output) / "index-tree.json"


def _read_viewer_options(repo_root: Path, config: DocsScopeConfig) -> tuple[dict[str, Any], list[str]]:
    index_tree_path = generated_docs_index_tree_path(repo_root, config)
    warnings: list[str] = []
    payload = _load_json(index_tree_path, f"generated docs index tree for {config.scope_id}")
    if not payload:
        warnings.append(f"Generated docs index tree is missing: {path_label(repo_root, index_tree_path)}")
        return {}, warnings
    viewer_options = payload.get("viewer_options")
    if viewer_options is None:
        warnings.append("Generated docs index tree has no viewer_options object.")
        return {}, warnings
    if not isinstance(viewer_options, dict):
        warnings.append("Generated docs index tree viewer_options is not an object.")
        return {}, warnings
    return viewer_options, warnings


def _scope_title(raw: dict[str, Any], scope_id: str) -> str:
    title = str(raw.get("title") or "").strip()
    if title:
        return title
    return scope_id.replace("_", " ").replace("-", " ").title()


def _safe_raw_subset(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "scope_id",
        "scope_type",
        "source",
        "media_path_prefix",
        "output",
        "search_output",
        "viewer_base_url",
        "include_scope_param",
        "default_doc_id",
        "non_loadable_doc_ids",
        "manage_only_tree_root_ids",
        "allow_unresolved_parent_ids",
        "import_media_storage",
        "sub_scopes",
    }
    return {key: raw[key] for key in sorted(allowed) if key in raw}


def build_source_config_report(repo_root: Path) -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root)
    raw_by_scope = {
        str(item.get("scope_id") or "").strip().lower(): item
        for item in _raw_scope_records(repo_root)
        if str(item.get("scope_id") or "").strip()
    }
    browser_by_scope = _browser_scope_records(repo_root)
    scopes: list[dict[str, Any]] = []

    for scope_id in sorted(configs):
        config = configs[scope_id]
        raw = raw_by_scope.get(scope_id, {})
        browser = browser_by_scope.get(scope_id, {})
        viewer_options, warnings = _read_viewer_options(repo_root, config)
        scopes.append(
            {
                "scope_id": scope_id,
                "title": _scope_title(raw, scope_id),
                "source_config": _safe_raw_subset(raw),
                "source_config_path": CONFIG_REL_PATH.as_posix(),
                "browser_config": browser,
                "browser_config_path": BROWSER_CONFIG_REL_PATH.as_posix(),
                "viewer_options": viewer_options,
                "generated": {
                    "docs_output": path_label(repo_root, config.output),
                    "docs_index_tree": path_label(repo_root, generated_docs_index_tree_path(repo_root, config)),
                    "recent": path_label(repo_root, resolve_scope_path(repo_root, config.output) / "recent.json"),
                    "docs_payload_root": path_label(repo_root, resolve_scope_path(repo_root, config.output) / "by-id"),
                    "search_index": path_label(repo_root, config.search_output),
                    "publish_output": config.publish_output.as_posix(),
                    "publish_search_index": config.publish_search_output.as_posix(),
                },
                "paths": {
                    "source_root": path_label(repo_root, config.source),
                    "media_path_prefix": config.media_path_prefix.as_posix(),
                    "route_base": config.viewer_base_url,
                },
                "warnings": warnings,
            }
        )

    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "browser_config_path": BROWSER_CONFIG_REL_PATH.as_posix(),
        "docs_viewer_source": _docs_viewer_source_settings(repo_root),
        "docs_viewer_browser": _browser_docs_viewer_settings(repo_root),
        "scopes": scopes,
    }
