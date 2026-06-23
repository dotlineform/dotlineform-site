from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .common import (
    CONFIG_REL_PATH,
    DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
    DocsScopeConfig,
    browser_path_for_repo_relative,
    is_public_readonly_scope,
    json_text,
    normalize_viewer_base_url,
    read_text,
    scope_uses_external_data,
    write_text,
)


def raw_scope_items(repo_root: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scopes = payload.get("scopes") if isinstance(payload, dict) else None
    if not isinstance(scopes, list):
        return {}
    return {
        str(item.get("scope_id") or "").strip().lower(): item
        for item in scopes if isinstance(item, dict)
    }


def browser_docs_index_tree_url(config: DocsScopeConfig) -> str:
    if scope_uses_external_data(config):
        return f"/docs/generated/index-tree?scope={quote(config.scope_id)}"
    output = config.publish_output if is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ) else config.output
    return f"{browser_path_for_repo_relative(output)}/index-tree.json"


def browser_docs_recently_added_url(config: DocsScopeConfig) -> str:
    if scope_uses_external_data(config):
        return f"/docs/generated/recently-added?scope={quote(config.scope_id)}"
    output = config.publish_output if is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ) else config.output
    return f"{browser_path_for_repo_relative(output)}/recently-added.json"


def browser_search_index_url(config: DocsScopeConfig) -> str:
    if scope_uses_external_data(config):
        return f"/docs/generated/search?scope={quote(config.scope_id)}"
    output = config.publish_search_output if is_public_readonly_scope(
        viewer_base_url=config.viewer_base_url,
        include_scope_param=config.include_scope_param,
    ) else config.search_output
    return browser_path_for_repo_relative(output)


def browser_search_policy_payload(config: DocsScopeConfig) -> dict[str, Any]:
    return {
        "domain": "docs_viewer",
        "schema": f"search_index_{config.scope_id}_v1",
        "index_url": browser_search_index_url(config),
        "targeted_policy": "record_update",
        "targeted_operations": ["create", "update", "delete"],
    }


def docs_viewer_settings_payload(repo_root: Path, scope_ids: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    settings = payload.get("docs_viewer") if isinstance(payload, dict) else None
    if not isinstance(settings, dict):
        return None
    settings = json.loads(json.dumps(settings))
    statuses = settings.get("ui_statuses_by_scope")
    if isinstance(statuses, dict):
        settings["ui_statuses_by_scope"] = {
            scope_id: value for scope_id, value in statuses.items() if scope_id in scope_ids
        }
    return settings


def browser_scope_record(repo_root: Path, raw_by_scope: dict[str, dict[str, Any]], config: DocsScopeConfig) -> dict[str, Any]:
    record = {
        "scope_id": config.scope_id,
        "scope_type": config.scope_type,
        "meta": str(raw_by_scope.get(config.scope_id, {}).get("meta") or "").strip(),
        "viewer_base_url": normalize_viewer_base_url(config.viewer_base_url),
        "include_scope_param": config.include_scope_param is True,
        "default_doc_id": config.default_doc_id,
        "media_path_prefix": config.media_path_prefix.as_posix(),
        "index_tree_url": browser_docs_index_tree_url(config),
        "recently_added_url": browser_docs_recently_added_url(config),
        "search_index_url": browser_search_index_url(config),
        "search": browser_search_policy_payload(config),
    }
    return record


def browser_scope_config_payload(repo_root: Path, configs: list[DocsScopeConfig]) -> dict[str, Any]:
    raw_by_scope = raw_scope_items(repo_root)
    scope_ids = [config.scope_id for config in configs]
    payload = {
        "schema_version": DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
        "default_scope_id": configs[0].scope_id if configs else "",
        "scopes": [browser_scope_record(repo_root, raw_by_scope, config) for config in configs],
    }
    settings = docs_viewer_settings_payload(repo_root, scope_ids)
    if settings:
        payload["docs_viewer"] = settings
    return payload


def write_browser_config(repo_root: Path, configs: list[DocsScopeConfig], *, path: Path, label: str) -> None:
    text = json_text(browser_scope_config_payload(repo_root, configs))
    target = repo_root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text(encoding="utf-8") == text:
        print(f"{label}: unchanged")
        return
    target.write_text(text, encoding="utf-8")
    print(f"{label}: wrote")


def public_readonly_configs(configs: list[DocsScopeConfig]) -> list[DocsScopeConfig]:
    return [
        config for config in configs
        if is_public_readonly_scope(
            viewer_base_url=config.viewer_base_url,
            include_scope_param=config.include_scope_param,
        )
    ]
