#!/usr/bin/env python3
"""Source loading and document selection helpers for Docs Viewer exports."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from docs_data_sharing import source_metadata
from docs_export_common import normalize_text


SKIPPED_REASON_LABELS = {
    "has_summary": "already have summaries",
    "max_documents": "exceeded the configured maximum document count",
    "non_viewable": "are not viewable",
    "unknown_doc_id": "were not found",
}


@dataclasses.dataclass(frozen=True)
class ExportContext:
    repo_root: Path
    scope: str
    data_domain: str
    config: dict[str, Any]
    source_context: source_metadata.DataSharingDocsSourceContext
    docs: list[dict[str, Any]]
    docs_by_id: dict[str, dict[str, Any]]
    children_by_parent: dict[str, list[dict[str, Any]]]


def source_record_to_export_doc(record: source_metadata.DataSharingDocsSourceRecord) -> dict[str, Any]:
    return {
        "doc_id": record.doc_id,
        "scope": record.scope,
        "title": record.title,
        "published": record.published,
        "summary": record.summary,
        "added_date": record.added_date,
        "last_updated": record.last_updated,
        "parent_id": record.parent_id,
        "parent_title": record.parent_title,
        "viewable": record.viewable,
        "ui_status": record.ui_status,
        "source_path": record.source_path,
        "viewer_url": record.viewer_url,
        "content_text_length": record.content_text_length,
    }


def load_source_export_context(repo_root: Path, scope: str) -> tuple[source_metadata.DataSharingDocsSourceContext, list[dict[str, Any]]]:
    context = source_metadata.load_data_sharing_docs_source_context(repo_root, scope)
    return context, [source_record_to_export_doc(record) for record in context.records]


def build_children_by_parent(docs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    children: dict[str, list[dict[str, Any]]] = {}
    for doc in docs:
        parent_id = normalize_text(doc.get("parent_id"))
        children.setdefault(parent_id, []).append(doc)
    return children


def resolve_selected_doc_ids(selected_doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    resolved: list[str] = []
    for raw_doc_id in selected_doc_ids:
        doc_id = normalize_text(raw_doc_id)
        if not doc_id:
            continue
        if doc_id not in seen:
            seen.add(doc_id)
            resolved.append(doc_id)
    return resolved


def docs_in_source_order(context: ExportContext, doc_ids: list[str]) -> list[str]:
    selected_ids = set(doc_ids)
    return [
        normalize_text(doc.get("doc_id"))
        for doc in context.docs
        if normalize_text(doc.get("doc_id")) in selected_ids
    ]


def selected_docs(
    context: ExportContext,
    *,
    selected_doc_ids: list[str],
    select_all: bool,
    missing_summary_only: bool | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str], list[str]]:
    selection = context.config.get("selection", {})
    mode = normalize_text(selection.get("mode"))
    skipped: list[dict[str, str]] = []
    errors: list[str] = []
    warnings: list[str] = []

    if select_all and selected_doc_ids:
        warnings.append("selection: explicit doc_ids were ignored because select_all is true")
    if missing_summary_only and not selection.get("supports_missing_summary_only"):
        warnings.append("selection: missing_summary_only was ignored because the selected config does not support it")

    if mode == "all_matching" or select_all:
        requested_ids = [normalize_text(doc.get("doc_id")) for doc in context.docs]
    else:
        explicit_ids = resolve_selected_doc_ids(selected_doc_ids)
        requested_ids = docs_in_source_order(context, explicit_ids)
        unknown_ids = [doc_id for doc_id in explicit_ids if doc_id not in context.docs_by_id]
        skipped.extend({"doc_id": doc_id, "reason": "unknown_doc_id"} for doc_id in unknown_ids)
        if not explicit_ids:
            errors.append("explicit_doc_ids selection requires at least one --doc-id, --doc-ids, or --all")

    selected: list[dict[str, Any]] = []
    for doc_id in requested_ids:
        doc = context.docs_by_id.get(doc_id)
        if doc is None:
            skipped.append({"doc_id": doc_id, "reason": "unknown_doc_id"})
            continue
        if not selection.get("include_non_viewable") and doc.get("viewable") is False:
            skipped.append({"doc_id": doc_id, "reason": "non_viewable"})
            continue
        if effective_missing_summary_only(context.config, missing_summary_only) and normalize_text(doc.get("summary")):
            skipped.append({"doc_id": doc_id, "reason": "has_summary"})
            continue
        selected.append(doc)

    max_documents = context.config.get("limits", {}).get("max_documents")
    if isinstance(max_documents, int) and len(selected) > max_documents:
        for doc in selected[max_documents:]:
            skipped.append({"doc_id": normalize_text(doc.get("doc_id")), "reason": "max_documents"})
        selected = selected[:max_documents]

    unknown_ids = [item["doc_id"] for item in skipped if item.get("reason") == "unknown_doc_id"]
    if unknown_ids:
        errors.append(f"selection: unknown doc_id value(s): {', '.join(unknown_ids)}")
    if requested_ids and not selected:
        errors.append("selection: no exportable documents remain after applying filters")

    return selected, skipped, errors, warnings


def descendant_doc_ids(context: ExportContext, doc_id: str, active_ids: set[str] | None = None) -> set[str]:
    active = set(active_ids or set())
    if doc_id in active:
        return set()
    active.add(doc_id)
    descendants: set[str] = set()
    for child in context.children_by_parent.get(doc_id, []):
        child_id = normalize_text(child.get("doc_id"))
        if not child_id or child_id in descendants:
            continue
        descendants.add(child_id)
        descendants.update(descendant_doc_ids(context, child_id, set(active)))
    return descendants


def expand_selected_docs_for_document_tree(context: ExportContext, selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_ids = {normalize_text(doc.get("doc_id")) for doc in selected}
    expanded_ids = set(selected_ids)
    for doc_id in selected_ids:
        expanded_ids.update(descendant_doc_ids(context, doc_id))
    return [
        doc
        for doc in context.docs
        if normalize_text(doc.get("doc_id")) in expanded_ids
    ]


def effective_missing_summary_only(config: dict[str, Any], override: bool | None) -> bool:
    selection = config.get("selection", {})
    if override is not None:
        if not selection.get("supports_missing_summary_only") and override:
            return False
        return override
    return bool(selection.get("default_missing_summary_only")) if selection.get("supports_missing_summary_only") else False


def skipped_reason_counts(skipped: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in skipped:
        reason = normalize_text(item.get("reason"))
        if reason:
            counts[reason] = counts.get(reason, 0) + 1
    return counts


def skipped_summary_warnings(skipped: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    for reason, count in sorted(skipped_reason_counts(skipped).items()):
        if reason == "unknown_doc_id":
            continue
        label = SKIPPED_REASON_LABELS.get(reason, reason.replace("_", " "))
        warnings.append(f"selection: {count} document(s) skipped because they {label}")
    return warnings
