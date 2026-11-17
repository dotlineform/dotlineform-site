"""Build the portfolio Recent artifact from completed collection and Gallery metadata."""

from typing import Any

from docs_workspace_config import DocsCollectionConfig

DOCS_RECENT_SCHEMA_VERSION = "docs_recent_v3"
RECENT_COLLECTIONS = frozenset({"works", "concepts", "moments"})


def build_recent_payload(
    collections: list[tuple[DocsCollectionConfig, dict[str, dict[str, Any]]]],
    galleries: dict[str, Any] | None, *, limit: int, generated_at: str,
    exclusions: frozenset[tuple[str, str]],
) -> dict[str, Any]:
    """Filter eligible dated additions before sorting and limiting the feed."""
    entries = []
    for owner, selected in collections:
        if owner.collection not in RECENT_COLLECTIONS:
            continue
        entries.extend({
            "doc_id": doc_id, "title": row["title"], "timestamp": row["added_date"],
            "collection": owner.collection, "report_doc_id": owner.report_host_doc_id, "collection_title": owner.title,
        } for doc_id, row in selected.items() if row["added_date"] and (owner.collection, doc_id) not in exclusions)
    if galleries is not None:
        entries.extend({
            "kind": "catalogue-gallery", "id": gallery_id,
            "title": galleries["galleries"][gallery_id], "timestamp": added_date,
        } for gallery_id, added_date in galleries.get("added_dates_by_gallery", {}).items())

    entries.sort(key=lambda row: (row["title"].lower(), row.get("doc_id") or row["id"], row.get("collection", "")))
    entries.sort(key=lambda row: row["timestamp"], reverse=True)
    return {"schema": DOCS_RECENT_SCHEMA_VERSION, "limit": limit, "generated_at": generated_at, "docs": entries[:limit]}
