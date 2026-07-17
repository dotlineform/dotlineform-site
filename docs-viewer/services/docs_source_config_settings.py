#!/usr/bin/env python3
"""Docs Viewer source config settings contract and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_scope_config import CONFIG_REL_PATH, document_source_path, load_docs_scope_configs, resolve_scope_path
import docs_source_model as source_model


SCHEMA_VERSION = "docs_source_config_settings_v1"


@dataclass(frozen=True)
class EditableScopeField:
    field: str
    value_type: str
    source_path: str
    generated_path: str
    requires_rebuild: bool
    description: str


EDITABLE_SCOPE_FIELDS: dict[str, EditableScopeField] = {
    "default_doc_id": EditableScopeField(
        field="default_doc_id",
        value_type="string",
        source_path=f"{CONFIG_REL_PATH.as_posix()} scopes[].default_doc_id",
        generated_path="docs-viewer/config/defaults/docs-viewer-config.json scopes[].default_doc_id",
        requires_rebuild=True,
        description="Default document id opened for this scope when no document is requested. Leave blank to use the first loadable document.",
    ),
}

BLOCKED_SCOPE_FIELDS = {
    "scope_id": "Scope identity controls route and published-artifact ownership.",
    "scope_type": "Scope type controls availability labeling and should be guarded with route ownership.",
    "source": "Canonical source roles and locations are install-time config and require manual review.",
    "published": "Published artifact roles and locations are install-time config and affect builders and imports.",
    "public_projection": "Public projections are install-time config and affect publication and public routes.",
    "viewer_base_url": "Route bases are install-time config and affect public URLs.",
    "include_scope_param": "Route parameter behavior is part of the portable route contract.",
    "non_loadable_doc_ids": "Tree loading behavior depends on published docs structure.",
    "manage_only_tree_root_ids": "Manage-only tree behavior depends on published docs structure.",
    "allow_unresolved_parent_ids": "Parent validation policy affects source validation.",
    "sub_scopes": "Sub-scope roles and locations are managed through the scope lifecycle workflow.",
}

DEFERRED_GLOBAL_FIELDS = {
    "recent_limit": "Global Docs Viewer setting; deferred until the settings UI supports global fields.",
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
    if contract.value_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"Source config field {field} must be a string")
        return value.strip()
    raise ValueError(f"Source config field {field} has unsupported value type: {contract.value_type}")


def _field_current_value(config: Any, contract: EditableScopeField) -> Any:
    return getattr(config, contract.field)


def _scope_field_payload(config: Any, contract: EditableScopeField) -> dict[str, Any]:
    return {
        "field": contract.field,
        "type": contract.value_type,
        "current_value": _field_current_value(config, contract),
        "editable": True,
        "source_path": contract.source_path,
        "generated_path": contract.generated_path,
        "requires_rebuild": contract.requires_rebuild,
        "description": contract.description,
        "warnings": [],
    }


def _scope_payload(config: Any) -> dict[str, Any]:
    return {
        "scope_id": config.scope_id,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "fields": [
            _scope_field_payload(config, contract)
            for contract in sorted(EDITABLE_SCOPE_FIELDS.values(), key=lambda item: item.field)
        ],
    }


def _validate_default_doc_id(repo_root: Path, config: Any, value: str) -> list[str]:
    if not value:
        return []
    root = resolve_scope_path(repo_root, document_source_path(config))
    if not root.exists():
        raise ValueError(
            f"missing source root for scope {config.scope_id}: {document_source_path(config).as_posix()}"
        )
    docs = []
    for path in sorted(root.glob("*.md")):
        front_matter, _body = source_model.parse_source(path)
        doc_id = str(front_matter.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError(f"missing required doc_id in {path.relative_to(root).as_posix()}")
        docs.append(
            source_model.ScopeDoc(
                scope=config.scope_id,
                path=path,
                source_text=path.read_text(encoding="utf-8"),
                front_matter=dict(front_matter),
                body="",
                doc_id=doc_id,
                title=str(front_matter.get("title") or path.stem).strip(),
                ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
                parent_id=str(front_matter.get("parent_id") or "").strip(),
                viewable=source_model.doc_is_viewable(front_matter),
            )
        )
    docs_by_id = {doc.doc_id: doc for doc in docs}
    doc = docs_by_id.get(value)
    if doc is None:
        raise ValueError(f"default_doc_id must match a document in scope {config.scope_id}: {value}")
    if value in set(config.non_loadable_doc_ids):
        raise ValueError(f"default_doc_id must be loadable in scope {config.scope_id}: {value}")
    if doc.viewable is False:
        return ["Default doc id points at a non-viewable document; public routes may hide it."]
    return []


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

    config = configs[normalized_scope]
    validated_changes: dict[str, Any] = {}
    rejected_fields: list[dict[str, str]] = []
    warnings: list[str] = []
    affected_artifacts: set[str] = set()

    for field, raw_value in sorted(changes.items()):
        if field in BLOCKED_SCOPE_FIELDS:
            rejected_fields.append({"field": field, "reason": BLOCKED_SCOPE_FIELDS[field]})
            continue
        if field in DEFERRED_GLOBAL_FIELDS:
            rejected_fields.append({"field": field, "reason": DEFERRED_GLOBAL_FIELDS[field]})
            continue
        contract = EDITABLE_SCOPE_FIELDS.get(field)
        value = _validate_field_value(field, raw_value)
        field_warnings: list[str] = []
        if field == "default_doc_id":
            field_warnings = _validate_default_doc_id(repo_root, config, value)
        current_value = _field_current_value(config, contract)
        changed = current_value != value
        if changed and contract.requires_rebuild:
            affected_artifacts.add(contract.generated_path)
        warnings.extend(field_warnings)
        validated_changes[field] = {
            "current_value": current_value,
            "proposed_value": value,
            "changed": changed,
            "requires_rebuild": changed and contract.requires_rebuild,
            "source_path": contract.source_path,
            "generated_path": contract.generated_path,
            "warnings": field_warnings,
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
        "warnings": warnings,
        "requires_rebuild": any(item["requires_rebuild"] for item in validated_changes.values()),
        "affected_artifacts": sorted(affected_artifacts),
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
