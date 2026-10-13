"""Build the shared, stage-independent Recents artifact from completed metadata."""

from typing import Any

DOCS_RECENT_SCHEMA_VERSION = "docs_recent_v2"
RECENT_FIELDS = frozenset({
    "doc_id", "title", "timestamp", "parent_id", "parent_title",
    "collection", "report_doc_id", "collection_title",
})


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
