"""Read the exact configured Analysis Working publication ignore file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_management_document_target import confined_document_path
from docs_publication_ignore import publication_ignore_path, read_publication_ignore_ids
from docs_source_model import parse_source


def build_unpublishable_report(repo_root: Path, *, scope: str, stage: str) -> dict[str, Any]:
    """Read the explicit IDs and only their exact ordinary Working source titles."""
    if scope != "analysis" or stage != "working":
        raise ValueError("Unpublishable is available only in Analysis Working")
    doc_ids = sorted(read_publication_ignore_ids(repo_root))
    source_root = publication_ignore_path(repo_root).parent.resolve()
    documents = []
    for doc_id in doc_ids:
        try:
            source_path = confined_document_path(source_root, doc_id)
        except FileNotFoundError:
            title = None
        else:
            front_matter, _body = parse_source(source_path)
            if front_matter.get("doc_id") != doc_id:
                raise ValueError("Ignored document source identity does not match its ID")
            title = str(front_matter.get("title") or "").strip()
        documents.append({"doc_id": doc_id, "title": title})
    return {
        "ok": True, "schema_version": "docs_unpublishable_report_v3",
        "scope": scope, "stage": stage, "documents": documents,
    }
