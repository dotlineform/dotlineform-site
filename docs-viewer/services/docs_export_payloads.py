#!/usr/bin/env python3
"""Payload and sidecar builders for Docs Viewer exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_export_common import OUTPUT_ROOT, RETURNED_PACKAGE_SCHEMA_VERSION, normalize_text
from docs_export_config import EXPORT_META_SCHEMA_VERSION, config_checksum, supports_return_import
from docs_export_selection import ExportContext


EXTERNAL_CONTEXT_SCHEMA_VERSION = "documents_external_context_v1"


def export_metadata(
    context: ExportContext,
    *,
    export_id: str,
    generated_at: str,
    selected: list[dict[str, Any]],
    counts: dict[str, int],
    target_format: str,
) -> dict[str, Any]:
    include = set(context.config.get("metadata", {}).get("include", []))
    config_id = normalize_text(context.config.get("id"))
    target = context.config.get("target") if isinstance(context.config.get("target"), dict) else {}
    record_shape = normalize_text(target.get("record_shape"))
    selected_doc_ids = [normalize_text(doc.get("doc_id")) for doc in selected]
    source_last_updated = {
        normalize_text(doc.get("doc_id")): normalize_text(doc.get("last_updated"))
        for doc in selected
    }
    metadata: dict[str, Any] = {
        "schema_version": EXPORT_META_SCHEMA_VERSION,
        "export_id": export_id,
        "app": "docs-viewer",
        "data_domain": context.data_domain,
        "adapter_id": "documents",
        "config_id": config_id,
        "profile_id": config_id,
        "scope": context.scope,
        "target_format": target_format,
        "record_shape": record_shape,
        "generated_at": generated_at,
        "supports_return_import": supports_return_import(context.config),
    }
    if context.content_format:
        metadata["content_format"] = context.content_format
    optional_values = {
        "config_checksum": config_checksum(context.config),
        "selected_doc_ids": selected_doc_ids,
        "source_last_updated": source_last_updated,
        "counts": counts,
    }
    metadata.update({key: value for key, value in optional_values.items() if key in include})
    return metadata


def resolve_output_path(
    repo_root: Path,
    config: dict[str, Any],
    data_domain: str,
    export_id: str,
    timestamp: str,
    target_format: str,
    output_root: Path | str | None = None,
) -> Path:
    output = config.get("output") if isinstance(config.get("output"), dict) else {}
    pattern = normalize_text(output.get("path_pattern"))
    if not pattern:
        raise ValueError(f"Export config {normalize_text(config.get('id'))} is missing output.path_pattern")
    relative = Path(
        pattern.format(
            data_domain=data_domain,
            timestamp=timestamp,
            export_id=export_id,
            profile_id=normalize_text(config.get("id")),
            config_id=normalize_text(config.get("id")),
        )
    )
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe export output path: {relative}")
    if target_format:
        relative = relative.with_suffix(f".{target_format}")
    allowed_root = Path(output_root) if output_root else OUTPUT_ROOT
    if relative.parts[:len(allowed_root.parts)] != allowed_root.parts:
        raise ValueError(f"Export output path must stay under {allowed_root}: {relative}")
    return repo_root / relative


def external_field_type(field: dict[str, Any]) -> str:
    output_path = normalize_text(field.get("output_path"))
    source = normalize_text(field.get("source"))
    if output_path in {"ancestors", "children"} or source in {"ancestors", "children"}:
        return "array<object>"
    if output_path in {"headings"}:
        return "array<string>"
    if source == "viewable" or output_path == "viewable":
        return "boolean"
    default = field.get("default")
    if isinstance(default, list):
        return "array"
    if isinstance(default, bool):
        return "boolean"
    if isinstance(default, (int, float)) and not isinstance(default, bool):
        return "number"
    if isinstance(default, dict):
        return "object"
    return "string"


def build_external_context(config: dict[str, Any], target_format: str, content_format: str = "") -> dict[str, Any]:
    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    record_shape = normalize_text(target.get("record_shape"))
    external_context = config.get("external_context") if isinstance(config.get("external_context"), dict) else {}
    field_descriptions = (
        external_context.get("field_descriptions")
        if isinstance(external_context.get("field_descriptions"), dict)
        else {}
    )
    if record_shape == "document_tree":
        record_container = "JSON object containing a nested docs tree"
        records_path = "docs"
    elif target_format == "jsonl":
        record_container = "JSONL header row followed by one JSON object per line"
        records_path = ""
    else:
        record_container = "JSON object containing a records array"
        records_path = "records"

    schema: list[dict[str, str]] = []
    for field in config.get("document_fields", []):
        if not isinstance(field, dict):
            continue
        output_path = normalize_text(field.get("output_path"))
        if not output_path:
            continue
        schema.append(
            {
                "field": output_path,
                "type": external_field_type(field),
                "description": normalize_text(field_descriptions.get(output_path)),
            }
        )
    if record_shape == "document_tree":
        schema.append(
            {
                "field": "children",
                "type": "array<object>",
                "description": "Nested child documents with doc_id, title, and optional children.",
            }
        )

    response_guidance = normalize_text(external_context.get("response_guidance"))
    if target_format == "jsonl":
        header_guidance = "Preserve the first JSONL line unchanged; it is an internal routing header."
        response_guidance = f"{response_guidance} {header_guidance}".strip()

    payload = {
        "schema_version": EXTERNAL_CONTEXT_SCHEMA_VERSION,
        "task": normalize_text(external_context.get("task")),
        "response_guidance": response_guidance,
    }
    if content_format:
        payload["content_format"] = content_format
    payload.update({
        "record_format": target_format,
        "record_container": record_container,
        "records_path": records_path,
        "record_schema": schema,
    })
    return payload


def build_export_payload(
    context: ExportContext,
    *,
    export_id: str,
    records: list[dict[str, Any]],
    target_format: str,
) -> dict[str, Any] | list[dict[str, Any]]:
    target = context.config.get("target", {})
    record_shape = normalize_text(target.get("record_shape"))
    if record_shape == "document_rows":
        if target_format == "json":
            payload = {
                "schema_version": RETURNED_PACKAGE_SCHEMA_VERSION,
                "export_id": export_id,
            }
            if context.content_format:
                payload["content_format"] = context.content_format
            payload["records"] = records
            return payload
        return records
    raise ValueError(f"Unsupported target.record_shape: {record_shape}")


def document_tree_node(
    doc: dict[str, Any],
    *,
    included_by_parent: dict[str, list[dict[str, Any]]],
    emitted_ids: set[str],
    active_ids: set[str] | None = None,
) -> dict[str, Any]:
    active = set(active_ids or set())
    doc_id = normalize_text(doc.get("doc_id"))
    active.add(doc_id)
    emitted_ids.add(doc_id)
    node: dict[str, Any] = {
        "doc_id": doc_id,
        "title": normalize_text(doc.get("title")),
    }
    children = [
        document_tree_node(
            child,
            included_by_parent=included_by_parent,
            emitted_ids=emitted_ids,
            active_ids=active,
        )
        for child in included_by_parent.get(doc_id, [])
        if normalize_text(child.get("doc_id")) not in active
        and normalize_text(child.get("doc_id")) not in emitted_ids
    ]
    if children:
        node["children"] = children
    return node


def build_document_tree_payload(
    *,
    export_id: str,
    docs: list[dict[str, Any]],
) -> dict[str, Any]:
    included_ids = {normalize_text(doc.get("doc_id")) for doc in docs}
    included_by_parent: dict[str, list[dict[str, Any]]] = {}
    for doc in docs:
        parent_id = normalize_text(doc.get("parent_id"))
        if parent_id not in included_ids:
            parent_id = ""
        included_by_parent.setdefault(parent_id, []).append(doc)

    emitted_ids: set[str] = set()
    tree = [
        document_tree_node(doc, included_by_parent=included_by_parent, emitted_ids=emitted_ids)
        for doc in included_by_parent.get("", [])
    ]
    for doc in docs:
        doc_id = normalize_text(doc.get("doc_id"))
        if doc_id not in emitted_ids:
            tree.append(document_tree_node(doc, included_by_parent=included_by_parent, emitted_ids=emitted_ids))
    return {
        "schema": "docs_data_sharing_document_tree_v1",
        "export_id": export_id,
        "docs": tree,
    }
