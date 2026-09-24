"""Validate the saved, stage-independent Recents artifact before copying it."""

from typing import Any

from docs_document_identity import is_doc_timestamp, is_immutable_doc_id
from docs_workspace_config import COLLECTION_ID_PATTERN


DOCS_RECENT_SCHEMA_VERSION = "docs_recent_v1"
RECENT_FIELDS = frozenset({
    "doc_id", "title", "timestamp", "parent_id", "parent_title",
    "collection", "report_doc_id", "collection_title",
})


def validate_recent_payload(payload: dict[str, Any]) -> None:
    """Require exact targets and display metadata, never stored stage or URLs.

    Validation does not compare against current source or prepared membership:
    ordinary edits may leave this saved artifact stale until its owning build.
    """
    if set(payload) != {"schema", "basis", "limit", "generated_at", "docs"}:
        raise ValueError("Recents requires only schema, basis, limit, generated_at and docs")
    if (
        payload["schema"] != DOCS_RECENT_SCHEMA_VERSION
        or not isinstance(payload["basis"], str)
        or payload["basis"] not in {"added", "edited"}
    ):
        raise ValueError("Recents has an unsupported schema or date basis")
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
            if key in row and (not isinstance(row[key], str) or not is_immutable_doc_id(row[key]) or row[key] != row[key].strip()):
                raise ValueError(f"Recents {key} must use exact immutable document identity")
        if payload["basis"] == "edited" and not is_doc_timestamp(row["timestamp"]):
            raise ValueError("Edited Recents requires complete document timestamps")
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
