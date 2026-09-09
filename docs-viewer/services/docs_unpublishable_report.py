"""Read explicitly excluded documents across every Analysis Working collection."""

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
    collections = [("", "Scope documents", config)] + [
        (child.sub_scope, child.title, child) for child in config.sub_scopes
    ]
    rows: list[dict[str, Any]] = []
    for sub_scope, title, collection in collections:
        documents = [
            document
            for document in load_document_collection_docs_for_config(repo_root, config, collection)
            if document.front_matter.get("publishable") is False
        ]
        if not documents:
            continue
        collection_url = management_collection_viewer_url(repo_root, scope, sub_scope, stage=stage)
        for document in documents:
            rows.append({
                "target": {"scope": scope, "stage": stage, "sub_scope": sub_scope, "doc_id": document.doc_id},
                "title": document.title,
                "collection_title": title,
                "href": management_document_viewer_url(collection_url, document.doc_id, sub_scope=bool(sub_scope)),
            })
    rows.sort(key=lambda row: (row["title"].casefold(), row["target"]["sub_scope"], row["target"]["doc_id"]))
    return {"ok": True, "schema_version": "docs_unpublishable_report_v1", "scope": scope, "stage": stage, "rows": rows}
