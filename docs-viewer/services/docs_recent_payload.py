"""Build and validate the shared, stage-independent Recents artifact."""

from typing import Any

from docs_document_identity import is_doc_date, is_document_id
from docs_workspace_config import COLLECTION_ID_PATTERN


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
    for row in candidates:
        if row.get("last_updated") != "" and not is_doc_date(row.get("last_updated")):
            raise ValueError("Recents requires date-only last_updated metadata")
    ordered = sorted(
        (row for row in candidates if row["last_updated"] and (row.get("collection", ""), row["doc_id"]) not in exclusions),
        key=lambda row: (row["title"].lower(), row["doc_id"], row.get("collection", "")),
    )
    ordered.sort(key=lambda row: row["last_updated"], reverse=True)
    fields = RECENT_FIELDS - {"timestamp"}
    payload = {
        "schema": DOCS_RECENT_SCHEMA_VERSION,
        "limit": limit,
        "generated_at": generated_at,
        "docs": [
            {**{key: row[key] for key in sorted(fields) if key in row}, "timestamp": row["last_updated"]}
            for row in ordered[:limit]
        ],
    }
    validate_recent_payload(payload)
    return payload


def validate_recent_payload(payload: dict[str, Any]) -> None:
    """Require exact targets and display metadata, never stored stage or URLs.

    Validation does not compare against current source or prepared membership:
    ordinary edits may leave this saved artifact stale until its owning build.
    """
    if set(payload) != {"schema", "limit", "generated_at", "docs"}:
        raise ValueError("Recents requires only schema, limit, generated_at and docs")
    if payload["schema"] != DOCS_RECENT_SCHEMA_VERSION:
        raise ValueError("Recents has an unsupported schema")
    if type(payload["limit"]) is not int or payload["limit"] < 1:
        raise ValueError("Recents limit must be a positive integer")
    if not isinstance(payload["generated_at"], str) or not payload["generated_at"].strip():
        raise ValueError("Recents requires generation time")
    rows = payload["docs"]
    if not isinstance(rows, list) or len(rows) > payload["limit"]:
        raise ValueError("Recents docs must be an array within its limit")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) - RECENT_FIELDS:
            raise ValueError("Recents rows must contain only identity and display metadata; rebuild Working Recents")
        for key in ("doc_id", "title", "timestamp"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Recents row requires {key}")
        for key in ("doc_id", "parent_id", "report_doc_id"):
            owner = row.get("collection", "") if key == "doc_id" else ""
            if key in row and (not isinstance(row[key], str) or not is_document_id(row[key], collection=owner)
                               or row[key] != row[key].strip()):
                raise ValueError(f"Recents {key} must use exact immutable document identity")
        if not is_doc_date(row["timestamp"]):
            raise ValueError("Recents requires date-only document updates")
        for key in ("parent_title", "collection_title"):
            if key in row and (not isinstance(row[key], str) or not row[key].strip()):
                raise ValueError(f"Recents {key} must be a non-empty string")
        collection = row.get("collection", "")
        if "collection" in row:
            if not isinstance(collection, str) or not COLLECTION_ID_PATTERN.fullmatch(collection):
                raise ValueError("Recents collection must use exact configured identity")
            if not row.get("report_doc_id") or not row.get("collection_title"):
                raise ValueError("Recents collection rows require report_doc_id and collection_title")
        elif "report_doc_id" in row or "collection_title" in row:
            raise ValueError("Recents host context requires collection identity")
        target = (collection, row["doc_id"])
        if target in seen:
            raise ValueError("Recents contains duplicate document targets")
        seen.add(target)
