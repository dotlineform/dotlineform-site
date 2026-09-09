"""Read explicitly excluded documents in the ordinary Analysis Working collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_document_location import management_collection_viewer_url, management_document_viewer_url
from docs_scope_config import load_docs_scope_stage
from docs_source_model import load_document_collection_docs_for_config


def build_unpublishable_report(repo_root: Path, *, scope: str, stage: str) -> dict[str, Any]:
    """Read current source flags without inherited exclusions or generated-data filters."""
    if scope != "analysis" or stage != "working":
        raise ValueError("Unpublishable is available only in Analysis Working")
    config = load_docs_scope_stage(repo_root, scope, stage)
    collection_url = management_collection_viewer_url(repo_root, scope, "", stage=stage)
    rows: list[dict[str, Any]] = []
    for document in load_document_collection_docs_for_config(repo_root, config, config):
        if document.front_matter.get("publishable") is not False:
            continue
        rows.append({
            "target": {"scope": scope, "stage": stage, "sub_scope": "", "doc_id": document.doc_id},
            "title": document.title,
            "collection_title": "Scope documents",
            "href": management_document_viewer_url(collection_url, document.doc_id, sub_scope=False),
        })
    rows.sort(key=lambda row: (row["title"].casefold(), row["target"]["sub_scope"], row["target"]["doc_id"]))
    return {"ok": True, "schema_version": "docs_unpublishable_report_v1", "scope": scope, "stage": stage, "rows": rows}
