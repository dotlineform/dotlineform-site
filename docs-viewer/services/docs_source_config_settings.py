#!/usr/bin/env python3
"""Docs Viewer source config settings contract and validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_workspace_config import CONFIG_REL_PATH, document_source_path, load_docs_workspace_config, load_docs_stage, resolve_workspace_path, select_workspace_stage, require_document_authoring
import docs_source_model as source_model


SCHEMA_VERSION = "docs_source_config_settings_v2"


@dataclass(frozen=True)
class EditableStageField:
    field: str
    value_type: str
    source_path: str
    generated_path: str
    requires_rebuild: bool
    description: str


EDITABLE_STAGE_FIELDS: dict[str, EditableStageField] = {
    "default_doc_id": EditableStageField(
        field="default_doc_id",
        value_type="string",
        source_path=f"{CONFIG_REL_PATH.as_posix()} stages.<stage>.default_doc_id",
        generated_path="docs-viewer/config/defaults/docs-viewer-config.json stages[].default_doc_id",
        requires_rebuild=True,
        description="Default document id opened for this stage when no document is requested. Leave blank to use the first loadable document.",
    ),
}

BLOCKED_STAGE_FIELDS = {
    "source": "Canonical source roles and locations are install-time config and require manual review.",
    "preview": "Preview artifact roles and locations are install-time config and affect builders and imports.",
    "public_projection": "Public projections are install-time config and affect publication and public routes.",
    "viewer_base_url": "Route bases are install-time config and affect public URLs.",
    "non_loadable_doc_ids": "Tree loading behavior depends on published docs structure.",
    "manage_only_tree_root_ids": "Manage-only tree behavior depends on published docs structure.",
    "allow_unresolved_parent_ids": "Parent validation policy affects source validation.",
    "collections": "Collection roles and locations are managed through the collection lifecycle workflow.",
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
    contract = EDITABLE_STAGE_FIELDS.get(field)
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


def _field_current_value(config: Any, contract: EditableStageField) -> Any:
    return getattr(config, contract.field)


def _stage_field_payload(config: Any, contract: EditableStageField) -> dict[str, Any]:
    return {
        "field": contract.field,
        "type": contract.value_type,
        "current_value": _field_current_value(config, contract),
        "editable": config.stage == "working",
        "source_path": (
            f"{CONFIG_REL_PATH.as_posix()} preview.{contract.field}"
            if config.stage == "preview" else contract.source_path.replace("<stage>", config.stage)
        ),
        "generated_path": contract.generated_path,
        "requires_rebuild": contract.requires_rebuild,
        "description": contract.description,
        "warnings": [],
    }


def _stage_payload(config: Any) -> dict[str, Any]:
    return {
        "stage": config.stage,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "fields": [
            _stage_field_payload(config, contract)
            for contract in sorted(EDITABLE_STAGE_FIELDS.values(), key=lambda item: item.field)
        ],
    }


def _validate_default_doc_id(repo_root: Path, config: Any, value: str) -> list[str]:
    if not value:
        return []
    root = resolve_workspace_path(repo_root, document_source_path(config))
    if not root.exists():
        raise ValueError(
            f"missing source root for stage {config.stage}: {document_source_path(config).as_posix()}"
        )
    docs = source_model.load_stage_docs_for_config(repo_root, config)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    doc = docs_by_id.get(value)
    if doc is None:
        raise ValueError(f"default_doc_id must match a document in stage {config.stage}: {value}")
    if value in set(config.non_loadable_doc_ids):
        raise ValueError(f"default_doc_id must be loadable in stage {config.stage}: {value}")
    return []


def build_settings_contract(repo_root: Path, *, stage: str | None = None) -> dict[str, Any]:
    workspace = load_docs_workspace_config(repo_root)
    selected_stages = (select_workspace_stage(workspace, stage),) if stage is not None else workspace.stages
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "source_config_path": CONFIG_REL_PATH.as_posix(),
        "editable_stage_fields": [
            {
                "field": contract.field,
                "type": contract.value_type,
                "source_path": contract.source_path,
                "generated_path": contract.generated_path,
                "requires_rebuild": contract.requires_rebuild,
                "description": contract.description,
            }
            for contract in sorted(EDITABLE_STAGE_FIELDS.values(), key=lambda item: item.field)
        ],
        "blocked_stage_fields": [
            {"field": field, "reason": reason}
            for field, reason in sorted(BLOCKED_STAGE_FIELDS.items())
        ],
        "deferred_global_fields": [
            {"field": field, "reason": reason}
            for field, reason in sorted(DEFERRED_GLOBAL_FIELDS.items())
        ],
        "stages": [_stage_payload(config) for config in selected_stages],
    }


def validate_stage_settings_change(repo_root: Path, changes: dict[str, Any], *, stage: str) -> dict[str, Any]:
    if not isinstance(changes, dict) or not changes:
        raise ValueError("changes must be a non-empty JSON object")
    config = load_docs_stage(repo_root, stage)
    require_document_authoring(config)
    validated_changes: dict[str, Any] = {}
    rejected_fields: list[dict[str, str]] = []
    warnings: list[str] = []
    affected_artifacts: set[str] = set()

    for field, raw_value in sorted(changes.items()):
        if field in BLOCKED_STAGE_FIELDS:
            rejected_fields.append({"field": field, "reason": BLOCKED_STAGE_FIELDS[field]})
            continue
        if field in DEFERRED_GLOBAL_FIELDS:
            rejected_fields.append({"field": field, "reason": DEFERRED_GLOBAL_FIELDS[field]})
            continue
        contract = EDITABLE_STAGE_FIELDS.get(field)
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
        "stage": config.stage,
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


def apply_stage_settings_change(repo_root: Path, changes: dict[str, Any], *, stage: str, dry_run: bool = False) -> dict[str, Any]:
    validation = validate_stage_settings_change(repo_root, changes, stage=stage)
    changed_fields = {
        field: detail["proposed_value"]
        for field, detail in validation["changes"].items()
        if detail["changed"]
    }
    if changed_fields and not dry_run:
        config_path = repo_root / CONFIG_REL_PATH
        payload = _load_json(config_path, CONFIG_REL_PATH.as_posix())
        raw_stages = payload.get("stages")
        if not isinstance(raw_stages, dict) or not isinstance(raw_stages.get(stage), dict):
            raise ValueError(f"Docs stage is not configured: {stage}")
        raw_stages[stage].update(changed_fields)

        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        _write_text_atomic(config_path, rendered)
        load_docs_workspace_config(repo_root)

    return {
        **validation,
        "changed": bool(changed_fields),
    }
