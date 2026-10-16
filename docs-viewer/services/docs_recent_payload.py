"""Build the shared, stage-independent Recents artifact from completed metadata."""

from typing import Any, Mapping

from docs_discovery_selection import DiscoverySelection
from docs_document_identity import doc_updated_date

DOCS_RECENT_SCHEMA_VERSION = "docs_recent_v2"
RECENT_FIELDS = frozenset({
    "doc_id", "title", "timestamp", "parent_id", "parent_title",
    "collection", "report_doc_id", "collection_title",
})


def recent_candidates(discovery: DiscoverySelection, ordinary_updated: Mapping[str, str]) -> list[dict[str, Any]]:
    """Project completed discovery metadata without reading document bodies."""
    rows = []
    for doc_id, row in discovery.ordinary.items():
        entry = {"doc_id": doc_id, "title": row["title"], "last_updated": doc_updated_date(ordinary_updated[doc_id])}
        parent_id = row["parent_id"]
        if parent_id:
            entry.update(parent_id=parent_id, parent_title=discovery.ordinary[parent_id]["title"])
        rows.append(entry)
    for owner, selected in discovery.collections:
        rows.extend({
            "doc_id": doc_id, "title": row["title"], "last_updated": row["last_updated"],
            "collection": owner.collection, "report_doc_id": owner.report_host_doc_id, "collection_title": owner.title,
        } for doc_id, row in selected.items())
    return rows


def build_recent_payload(
    candidates: list[dict[str, Any]], *, limit: int, generated_at: str,
    exclusions: frozenset[tuple[str, str]],
) -> dict[str, Any]:
    """Exclude exact targets, then sort the complete dated set before limiting."""
    ordered = sorted(
        (row for row in candidates if row["last_updated"] and (row.get("collection", ""), row["doc_id"]) not in exclusions),
        key=lambda row: (row["title"].lower(), row["doc_id"], row.get("collection", "")),
    )
    ordered.sort(key=lambda row: row["last_updated"], reverse=True)
    fields = RECENT_FIELDS - {"timestamp"}
    return {
        "schema": DOCS_RECENT_SCHEMA_VERSION,
        "limit": limit,
        "generated_at": generated_at,
        "docs": [
            {**{key: row[key] for key in sorted(fields) if key in row}, "timestamp": row["last_updated"]}
            for row in ordered[:limit]
        ],
    }
