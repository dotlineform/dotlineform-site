"""Reuse saved navigation rows for unselected ordinary documents."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, TYPE_CHECKING

from .common import DOCS_INDEX_TREE_SCHEMA_VERSION
from .source import DocRecord, InvalidDocIdError
from docs_document_identity import is_immutable_doc_id

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


@dataclass(frozen=True)
class OrdinaryDocumentSummary:
    doc_id: str
    title: str
    parent_id: str
    navigation_entry: dict[str, Any]


def targeted_document_metadata(
    builder: DocsDataBuilder,
    docs: list[DocRecord],
    parent_ids: dict[str, str],
) -> tuple[list[DocRecord | OrdinaryDocumentSummary], dict[str, Any], str]:
    """Merge required source records in canonical order; never recover by scanning."""
    if not builder.only_doc_ids:
        raise ValueError("Targeted docs build requires at least one document ID")
    selected_ids = set(builder.only_doc_ids) | set(builder.links_doc_ids or [])
    for doc_id in selected_ids:
        if not is_immutable_doc_id(doc_id):
            raise InvalidDocIdError(f"Invalid selected document ID: {doc_id}")
    path = builder.output_dir / "index-tree.json"
    try:
        previous_text = path.read_text(encoding="utf-8")
        previous = json.loads(previous_text)
    except (OSError, ValueError) as exc:
        raise RuntimeError("Targeted docs build requires a readable index tree; run a full Build first") from exc
    if not isinstance(previous, dict) or previous.get("schema") != DOCS_INDEX_TREE_SCHEMA_VERSION:
        raise RuntimeError("Targeted docs build requires a current index tree; run a full Build first")
    rows: dict[str, dict[str, Any]] = {}

    def visit(nodes: Any) -> None:
        if not isinstance(nodes, list):
            raise RuntimeError("Targeted docs build requires an index tree with document arrays; run a full Build first")
        for node in nodes:
            if not isinstance(node, dict):
                raise RuntimeError("Targeted docs build requires index tree records; run a full Build first")
            doc_id = node.get("doc_id")
            if not isinstance(doc_id, str) or not is_immutable_doc_id(doc_id) or doc_id in rows:
                raise RuntimeError("Targeted docs build requires unique index tree identities; run a full Build first")
            rows[doc_id] = {key: value for key, value in node.items() if key != "children"}
            visit(node.get("children", []))

    visit(previous.get("docs"))
    selected_by_id = {doc.doc_id: doc for doc in docs}
    documents: list[DocRecord | OrdinaryDocumentSummary] = []
    render_ids = set(builder.only_doc_ids)
    for doc_id, parent_id in parent_ids.items():
        if doc_id not in render_ids and not (builder.items_dir / f"{doc_id}.json").is_file():
            raise RuntimeError(f"Targeted docs build requires an existing payload for {doc_id}; run a full Build first")
        if doc_id in selected_by_id:
            documents.append(selected_by_id[doc_id])
            continue
        row = rows.get(doc_id)
        if (
            row is None
            or not isinstance(row.get("title"), str)
            or not row["title"].strip()
            or row.get("content_url") != builder.content_url_for(doc_id)
            or (builder.config.stage == "working" and not isinstance(row.get("draft"), bool))
            or (builder.config.stage != "working" and "draft" in row)
            or bool(set(row) - {"doc_id", "title", "content_url", "draft", "ui_status", "report_id"})
            or any(field in row and not isinstance(row[field], str) for field in ("ui_status", "report_id"))
        ):
            raise RuntimeError(f"Targeted docs build requires saved navigation metadata for {doc_id}; run a full Build first")
        documents.append(OrdinaryDocumentSummary(doc_id, row["title"], parent_id, row))
    return documents, previous, previous_text
