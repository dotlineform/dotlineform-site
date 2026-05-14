#!/usr/bin/env python3
"""Docs Viewer source config settings contract and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_scope_config import CONFIG_REL_PATH, DocsScopeConfig, load_docs_scope_configs


SCHEMA_VERSION = "docs_source_config_settings_v1"


@dataclass(frozen=True)
class ScopeSettingField:
    field: str
    value_type: str
    source_path: str
    generated_path: str
    requires_rebuild: bool
    description: str


EDITABLE_SCOPE_FIELDS = {
    "show_updated_date": ScopeSettingField(
        field="show_updated_date",
        value_type="boolean",
        source_path="scopes[].show_updated_date",
        generated_path="viewer_options.show_updated_date",
        requires_rebuild=True,
        description="Show updated-date metadata in the Docs Viewer for this scope.",
    ),
}

BLOCKED_SCOPE_FIELDS = {
    "scope_id": "Scope identity controls route and generated-data ownership.",
    "source": "Source roots are install-time config and require manual review.",
    "media_path_prefix": "Media prefixes are install-time config and affect imports.",
    "output": "Generated output roots are install-time config and affect build artifacts.",
    "viewer_base_url": "Route bases are install-time config and affect public URLs.",
    "include_scope_param": "Route parameter behavior is part of the portable route contract.",
    "default_doc_id": "Default documents affect route behavior and should be guarded separately.",
    "allow_nested_source": "Nested source behavior affects source discovery and validation.",
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


def _read_viewer_options(repo_root: Path, config: DocsScopeConfig) -> tuple[dict[str, Any], list[str]]:
    index_path = repo_root / config.output / "index.json"
    payload = _load_json(index_path, f"generated docs index for {config.scope_id}")
    if not payload:
        return {}, [f"Generated docs index is missing: {(config.output / 'index.json').as_posix()}"]
    viewer_options = payload.get("viewer_options")
    if viewer_options is None:
        return {}, ["Generated docs index has no viewer_options object."]
    if not isinstance(viewer_options, dict):
        return {}, ["Generated docs index viewer_options is not an object."]
    return viewer_options, []


def _current_scope_value(config: DocsScopeConfig, field: str) -> Any:
    if field == "show_updated_date":
        return config.show_updated_date
    raise ValueError(f"Unsupported editable source config field: {field}")


def _validate_field_value(field: str, value: Any) -> Any:
    contract = EDITABLE_SCOPE_FIELDS.get(field)
    if contract is None:
        raise ValueError(f"Source config field is not editable through settings: {field}")
    if contract.value_type == "boolean":
        if type(value) is not bool:
            raise ValueError(f"Source config field {field} must be a boolean")
        return value
    raise ValueError(f"Source config field {field} has unsupported value type: {contract.value_type}")


def _field_warnings(
    *,
    field: str,
    current_value: Any,
    proposed_value: Any,
    viewer_options: dict[str, Any],
    viewer_option_warnings: list[str],
) -> list[str]:
    warnings = list(viewer_option_warnings)
    generated_value = viewer_options.get(EDITABLE_SCOPE_FIELDS[field].generated_path.split(".")[-1])
    if type(generated_value) is bool:
        if generated_value != current_value:
            warnings.append(
                f"Generated {EDITABLE_SCOPE_FIELDS[field].generated_path} does not match source config; rebuild is needed."
            )
        if generated_value != proposed_value:
            warnings.append(
                f"Saving {field} requires rebuilding the generated docs index before the browser reflects the change."
            )
    elif not viewer_option_warnings:
        warnings.append(f"Generated {EDITABLE_SCOPE_FIELDS[field].generated_path} is missing or invalid.")
    return warnings


def _affected_artifacts(config: DocsScopeConfig, field: str) -> list[str]:
    if field == "show_updated_date":
        return [(config.output / "index.json").as_posix()]
    return []


def _scope_payload(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    viewer_options, viewer_option_warnings = _read_viewer_options(repo_root, config)
    fields: list[dict[str, Any]] = []
    for field_name, contract in sorted(EDITABLE_SCOPE_FIELDS.items()):
        current_value = _current_scope_value(config, field_name)
        generated_value = viewer_options.get(contract.generated_path.split(".")[-1])
        fields.append(
            {
                "field": field_name,
                "editable": True,
                "type": contract.value_type,
                "current_value": current_value,
                "generated_value": generated_value if type(generated_value) is bool else None,
                "source_path": contract.source_path,
                "generated_path": contract.generated_path,
                "requires_rebuild": contract.requires_rebuild,
                "affected_artifacts": _affected_artifacts(config, field_name),
                "description": contract.description,
                "warnings": _field_warnings(
                    field=field_name,
                    current_value=current_value,
                    proposed_value=current_value,
                    viewer_options=viewer_options,
                    viewer_option_warnings=viewer_option_warnings,
                ),
            }
        )

    return {
        "scope_id": config.scope_id,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "fields": fields,
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
        "scopes": [_scope_payload(repo_root, configs[item]) for item in scope_ids],
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

    config = configs[normalized_scope]
    viewer_options, viewer_option_warnings = _read_viewer_options(repo_root, config)
    validated_changes: dict[str, Any] = {}
    rejected_fields: list[dict[str, str]] = []
    warnings: list[str] = []
    affected_artifacts: list[str] = []

    for field, raw_value in sorted(changes.items()):
        if field in BLOCKED_SCOPE_FIELDS:
            rejected_fields.append({"field": field, "reason": BLOCKED_SCOPE_FIELDS[field]})
            continue
        if field in DEFERRED_GLOBAL_FIELDS:
            rejected_fields.append({"field": field, "reason": DEFERRED_GLOBAL_FIELDS[field]})
            continue
        value = _validate_field_value(field, raw_value)
        current_value = _current_scope_value(config, field)
        validated_changes[field] = {
            "current_value": current_value,
            "proposed_value": value,
            "changed": value != current_value,
        }
        warnings.extend(
            _field_warnings(
                field=field,
                current_value=current_value,
                proposed_value=value,
                viewer_options=viewer_options,
                viewer_option_warnings=viewer_option_warnings,
            )
        )
        affected_artifacts.extend(_affected_artifacts(config, field))

    if rejected_fields:
        rejected = ", ".join(item["field"] for item in rejected_fields)
        raise ValueError(f"Source config fields are not editable through settings: {rejected}")

    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "scope_id": normalized_scope,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "changes": validated_changes,
        "warnings": sorted(set(warnings)),
        "requires_rebuild": any(item["changed"] for item in validated_changes.values()),
        "affected_artifacts": sorted(set(affected_artifacts)),
    }
