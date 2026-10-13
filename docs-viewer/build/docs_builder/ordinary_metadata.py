"""Reuse saved navigation rows for unselected ordinary documents."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, TYPE_CHECKING

from .source import DocRecord

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
    rows, previous, previous_text = read_saved_navigation(builder)
    selected_by_id = {doc.doc_id: doc for doc in docs}
    documents: list[DocRecord | OrdinaryDocumentSummary] = []
    for doc_id, parent_id in parent_ids.items():
        if doc_id in selected_by_id:
            documents.append(selected_by_id[doc_id])
        else:
            row = rows[doc_id]
            documents.append(OrdinaryDocumentSummary(doc_id, row["title"], parent_id, row))
    return documents, previous, previous_text


def read_saved_navigation(
    builder: DocsDataBuilder,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], str]:
    """Read generated navigation once without auditing its completed handoff."""
    path = builder.output_dir / "index-tree.json"
    if builder.output_dir.is_symlink() or path.is_symlink() or path.resolve().parent != builder.output_dir.resolve():
        raise ValueError("Generated navigation must stay in its configured directory")
    previous_text = path.read_text(encoding="utf-8")
    previous = json.loads(previous_text)
    rows: dict[str, dict[str, Any]] = {}

    def visit(nodes: list[dict[str, Any]]) -> None:
        for node in nodes:
            rows[node["doc_id"]] = {key: value for key, value in node.items() if key != "children"}
            visit(node.get("children", []))

    visit(previous["docs"])
    return rows, previous, previous_text
