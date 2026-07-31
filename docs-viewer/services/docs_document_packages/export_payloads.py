#!/usr/bin/env python3
"""Payload builders for document-package exports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_document_packages.export_common import RETURNED_PACKAGE_SCHEMA_VERSION, normalize_text
from docs_document_packages.export_config import (
    EXPORT_META_SCHEMA_VERSION,
    config_checksum,
    supports_docs_review,
)
from docs_document_packages.export_selection import ExportContext
from docs_document_packages.workspace import configured_workspace_paths, path_is_relative_to


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
        "supports_docs_review": supports_docs_review(context.config),
        "supports_return_import": context.supports_return_import,
    }
    if context.sub_scope:
        metadata["sub_scope"] = context.sub_scope
    if context.content_format:
        metadata["content_format"] = context.content_format
    optional_values = {
        "config_checksum": config_checksum(context.config),
        "selected_doc_ids": selected_doc_ids,
        "source_last_updated": source_last_updated,
        "counts": counts,
    }
    metadata.update({
        key: value
        for key, value in optional_values.items()
        if key in include or (context.sub_scope and key == "selected_doc_ids")
    })
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
    allowed_root = (
        Path(output_root) if output_root else configured_workspace_paths(repo_root).exports
    ).resolve()
    resolved = (allowed_root / relative).resolve()
    if not path_is_relative_to(resolved, allowed_root):
        raise ValueError(f"Export output path must stay under the configured outbound package root: {relative}")
    return resolved


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
