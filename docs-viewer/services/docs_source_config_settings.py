#!/usr/bin/env python3
"""Docs Viewer source config settings contract and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_scope_config import CONFIG_REL_PATH, load_docs_scope_configs


SCHEMA_VERSION = "docs_source_config_settings_v1"


EDITABLE_SCOPE_FIELDS: dict[str, Any] = {}

BLOCKED_SCOPE_FIELDS = {
    "scope_id": "Scope identity controls route and generated-data ownership.",
    "scope_type": "Scope type controls availability labeling and should be guarded with route ownership.",
    "source": "Source roots are install-time config and require manual review.",
    "media_path_prefix": "Media prefixes are install-time config and affect imports.",
    "output": "Generated output roots are install-time config and affect build artifacts.",
    "search_output": "Generated search output paths are install-time config and affect build artifacts.",
    "viewer_base_url": "Route bases are install-time config and affect public URLs.",
    "include_scope_param": "Route parameter behavior is part of the portable route contract.",
    "default_doc_id": "Default documents affect route behavior and should be guarded separately.",
    "non_loadable_doc_ids": "Tree loading behavior depends on generated docs structure.",
    "manage_only_tree_root_ids": "Manage-only tree behavior depends on generated docs structure.",
    "allow_unresolved_parent_ids": "Parent validation policy affects source validation.",
    "import_media_storage": "Import media storage affects local write destinations.",
}

DEFERRED_GLOBAL_FIELDS = {
    "recently_added_limit": "Global Docs Viewer setting; deferred until the settings UI supports global fields.",
}


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


def _validate_field_value(field: str, value: Any) -> Any:
    contract = EDITABLE_SCOPE_FIELDS.get(field)
    if contract is None:
        raise ValueError(f"Source config field is not editable through settings: {field}")
    if contract.value_type == "boolean":
        if type(value) is not bool:
            raise ValueError(f"Source config field {field} must be a boolean")
        return value
    raise ValueError(f"Source config field {field} has unsupported value type: {contract.value_type}")


def _scope_payload(config: Any) -> dict[str, Any]:
    return {
        "scope_id": config.scope_id,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "fields": [],
    }


def build_settings_contract(repo_root: Path, scope_id: str = "") -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root)
    requested_scope = str(scope_id or "").strip().lower()
    if requested_scope and requested_scope not in configs:
        raise ValueError(f"Docs scope is not configured: {requested_scope}")

    scope_ids = [requested_scope] if requested_scope else sorted(configs)
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "editable_scope_fields": [
            {
                "field": contract.field,
                "type": contract.value_type,
                "source_path": contract.source_path,
                "generated_path": contract.generated_path,
                "requires_rebuild": contract.requires_rebuild,
                "description": contract.description,
            }
            for contract in sorted(EDITABLE_SCOPE_FIELDS.values(), key=lambda item: item.field)
        ],
        "blocked_scope_fields": [
            {"field": field, "reason": reason}
            for field, reason in sorted(BLOCKED_SCOPE_FIELDS.items())
        ],
        "deferred_global_fields": [
            {"field": field, "reason": reason}
            for field, reason in sorted(DEFERRED_GLOBAL_FIELDS.items())
        ],
        "scopes": [_scope_payload(configs[item]) for item in scope_ids],
    }


def validate_scope_settings_change(repo_root: Path, scope_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(changes, dict):
        raise ValueError("changes must be a JSON object")
    configs = load_docs_scope_configs(repo_root)
    normalized_scope = str(scope_id or "").strip().lower()
    if not normalized_scope:
        raise ValueError("scope is required")
    if normalized_scope not in configs:
        raise ValueError(f"Docs scope is not configured: {normalized_scope}")
    if not changes:
        raise ValueError("At least one source config setting is required")

    validated_changes: dict[str, Any] = {}
    rejected_fields: list[dict[str, str]] = []

    for field, raw_value in sorted(changes.items()):
        if field in BLOCKED_SCOPE_FIELDS:
            rejected_fields.append({"field": field, "reason": BLOCKED_SCOPE_FIELDS[field]})
            continue
        if field in DEFERRED_GLOBAL_FIELDS:
            rejected_fields.append({"field": field, "reason": DEFERRED_GLOBAL_FIELDS[field]})
            continue
        value = _validate_field_value(field, raw_value)
        validated_changes[field] = {
            "current_value": value,
            "proposed_value": value,
            "changed": False,
        }

    if rejected_fields:
        rejected = ", ".join(item["field"] for item in rejected_fields)
        raise ValueError(f"Source config fields are not editable through settings: {rejected}")

    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "scope_id": normalized_scope,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "changes": validated_changes,
        "warnings": [],
        "requires_rebuild": any(item["changed"] for item in validated_changes.values()),
        "affected_artifacts": [],
    }


def _write_text_atomic(path: Path, text: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(text, encoding="utf-8")
    temp_path.replace(path)


def apply_scope_settings_change(repo_root: Path, scope_id: str, changes: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    validation = validate_scope_settings_change(repo_root, scope_id, changes)
    changed_fields = {
        field: detail["proposed_value"]
        for field, detail in validation["changes"].items()
        if detail["changed"]
    }
    if changed_fields and not dry_run:
        config_path = repo_root / CONFIG_REL_PATH
        payload = _load_json(config_path, CONFIG_REL_PATH.as_posix())
        raw_scopes = payload.get("scopes")
        if not isinstance(raw_scopes, list):
            raise ValueError("docs scope config scopes must be an array")

        updated = False
        for item in raw_scopes:
            if not isinstance(item, dict):
                continue
            if str(item.get("scope_id") or "").strip().lower() != validation["scope_id"]:
                continue
            for field, value in changed_fields.items():
                item[field] = value
            updated = True
            break
        if not updated:
            raise ValueError(f"Docs scope is not configured: {validation['scope_id']}")

        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        _write_text_atomic(config_path, rendered)
        load_docs_scope_configs(repo_root)

    return {
        **validation,
        "changed": bool(changed_fields),
    }
