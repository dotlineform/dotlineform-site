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
    public_documents_path,
    public_search_path,
    published_documents_path,
    published_search_path,
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


def browser_docs_index_tree_url(config: DocsScopeConfig, *, published: bool = False) -> str:
    if scope_uses_external_data(config):
        return f"/docs/index-tree?scope={quote(config.scope_id)}"
    output = public_documents_path(config) if published else published_documents_path(config)
    output = output or published_documents_path(config)
    return f"{browser_path_for_repo_relative(output)}/index-tree.json"


def browser_docs_recent_url(config: DocsScopeConfig, *, published: bool = False) -> str:
    if scope_uses_external_data(config):
        return f"/docs/recent?scope={quote(config.scope_id)}"
    output = public_documents_path(config) if published else published_documents_path(config)
    output = output or published_documents_path(config)
    return f"{browser_path_for_repo_relative(output)}/recent.json"


def browser_search_index_url(config: DocsScopeConfig, *, published: bool = False) -> str:
    if scope_uses_external_data(config):
        return f"/docs/search?scope={quote(config.scope_id)}"
    output = public_search_path(config) if published else published_search_path(config)
    output = output or published_search_path(config)
    return browser_path_for_repo_relative(output)


def browser_search_policy_payload(config: DocsScopeConfig, *, published: bool = False) -> dict[str, Any]:
    return {
        "domain": "docs_viewer",
        "schema": f"search_index_{config.scope_id}_v1",
        "index_url": browser_search_index_url(config, published=published),
        "targeted_policy": "record_update",
        "targeted_operations": ["create", "update", "delete"],
    }


def browser_sub_scope_output_url_base(config: DocsScopeConfig, sub_scope: Any) -> str:
    if scope_uses_external_data(config):
        return f"/docs/published/external/{quote(config.scope_id)}/{quote(sub_scope.sub_scope)}"
    output = public_documents_path(sub_scope) or published_documents_path(sub_scope)
    return browser_path_for_repo_relative(output)


def browser_sub_scope_records(config: DocsScopeConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for sub_scope in config.sub_scopes:
        output_base = browser_sub_scope_output_url_base(config, sub_scope)
        records.append(
            {
                "sub_scope": sub_scope.sub_scope,
                "title": sub_scope.title,
                "manifest_url": f"{output_base}/manifest.json",
                "by_id_url_base": f"{output_base}/by-id",
            }
        )
    return records


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


def browser_scope_record(
    repo_root: Path,
    raw_by_scope: dict[str, dict[str, Any]],
    config: DocsScopeConfig,
    *,
    published: bool = False,
) -> dict[str, Any]:
    record = {
        "scope_id": config.scope_id,
        "scope_type": config.scope_type,
        "meta": str(raw_by_scope.get(config.scope_id, {}).get("meta") or "").strip(),
        "viewer_base_url": normalize_viewer_base_url(config.viewer_base_url),
        "include_scope_param": config.include_scope_param is True,
        "default_doc_id": config.default_doc_id,
        "media": {
            media_type: {
                "reference_prefix": media.reference_prefix.as_posix(),
                "served_path_prefix": media.served_path_prefix,
            }
            for media_type, media in sorted(config.published.media.items())
        },
        "index_tree_url": browser_docs_index_tree_url(config, published=published),
        "recent_url": browser_docs_recent_url(config, published=published),
        "search_index_url": browser_search_index_url(config, published=published),
        "search": browser_search_policy_payload(config, published=published),
    }
    sub_scopes = browser_sub_scope_records(config)
    if sub_scopes:
        record["sub_scopes"] = sub_scopes
    return record


def browser_scope_config_payload(
    repo_root: Path,
    configs: list[DocsScopeConfig],
    *,
    published: bool = False,
) -> dict[str, Any]:
    raw_by_scope = raw_scope_items(repo_root)
    scope_ids = [config.scope_id for config in configs]
    payload = {
        "schema_version": DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
        "default_scope_id": configs[0].scope_id if configs else "",
        "scopes": [
            browser_scope_record(repo_root, raw_by_scope, config, published=published)
            for config in configs
        ],
    }
    settings = docs_viewer_settings_payload(repo_root, scope_ids)
    if settings:
        payload["docs_viewer"] = settings
    return payload


def patched_browser_scope_config_payload(
    repo_root: Path,
    configs: list[DocsScopeConfig],
    *,
    existing: dict[str, Any] | None,
    published: bool,
    replace_scope_ids: list[str],
) -> dict[str, Any]:
    replacement_payload = browser_scope_config_payload(repo_root, configs, published=published)
    replacement_by_scope = {
        str(record.get("scope_id") or "").strip().lower(): record
        for record in replacement_payload["scopes"]
        if isinstance(record, dict) and str(record.get("scope_id") or "").strip()
    }
    replaced = {
        str(scope_id or "").strip().lower()
        for scope_id in replace_scope_ids
    }
    existing_scopes = existing.get("scopes") if isinstance(existing, dict) else None
    retained_by_scope = (
        {
            str(record.get("scope_id") or "").strip().lower(): record
            for record in existing_scopes
            if isinstance(record, dict) and str(record.get("scope_id") or "").strip()
        }
        if isinstance(existing_scopes, list)
        else {}
    )
    for scope_id in replaced:
        retained_by_scope.pop(scope_id, None)
    retained_by_scope.update(replacement_by_scope)

    raw_scope_order = list(raw_scope_items(repo_root))
    ordered_scope_ids = [
        scope_id for scope_id in raw_scope_order
        if scope_id in retained_by_scope
    ]
    ordered_scope_ids.extend(
        scope_id for scope_id in retained_by_scope
        if scope_id not in ordered_scope_ids
    )
    scopes = [retained_by_scope[scope_id] for scope_id in ordered_scope_ids]
    existing_default = (
        str(existing.get("default_scope_id") or "").strip().lower()
        if isinstance(existing, dict)
        else ""
    )
    default_scope_id = (
        existing_default
        if existing_default in retained_by_scope
        else ordered_scope_ids[0] if ordered_scope_ids else ""
    )
    payload: dict[str, Any] = {
        "schema_version": DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
        "default_scope_id": default_scope_id,
        "scopes": scopes,
    }
    settings = docs_viewer_settings_payload(repo_root, ordered_scope_ids)
    if settings:
        payload["docs_viewer"] = settings
    elif isinstance(existing, dict) and isinstance(existing.get("docs_viewer"), dict):
        payload["docs_viewer"] = existing["docs_viewer"]
    return payload


def write_browser_config(
    repo_root: Path,
    configs: list[DocsScopeConfig],
    *,
    path: Path,
    label: str,
    published: bool = False,
    replace_scope_ids: list[str] | None = None,
) -> None:
    target = repo_root / path
    existing: dict[str, Any] | None = None
    if replace_scope_ids is not None and target.exists():
        try:
            parsed = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            parsed = None
        existing = parsed if isinstance(parsed, dict) else None
    payload = (
        patched_browser_scope_config_payload(
            repo_root,
            configs,
            existing=existing,
            published=published,
            replace_scope_ids=replace_scope_ids,
        )
        if replace_scope_ids is not None
        else browser_scope_config_payload(repo_root, configs, published=published)
    )
    text = json_text(payload)
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
