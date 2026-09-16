"""Merge selected document metadata into a collection's saved manifests."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from docs_document_identity import is_immutable_doc_id


@dataclass(frozen=True)
class CollectionDocumentSummary:
    """Saved identity and location needed by rendering and subject projection."""

    doc_id: str
    title: str
    viewer_url: str


def read_collection_manifest(path: Path) -> dict[str, Any]:
    """Require saved metadata; never recover it by scanning source documents."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Targeted collection build requires readable {path.name}; run a complete Build first") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
        raise ValueError(f"Invalid collection manifest: {path.name}")
    seen: set[str] = set()
    for row in payload["docs"]:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("doc_id"), str)
            or not is_immutable_doc_id(row["doc_id"])
            or not isinstance(row.get("title"), str)
            or row["doc_id"] in seen
        ):
            raise ValueError(f"Invalid or duplicate document in {path.name}")
        seen.add(row["doc_id"])
    return payload


def merge_collection_manifest(
    previous: dict[str, Any],
    replacement: dict[str, Any],
    selected_doc_ids: list[str],
) -> dict[str, Any]:
    """Replace selected rows, including deletions, and restore title ordering."""
    selected = set(selected_doc_ids)
    rows = [dict(row) for row in previous["docs"] if row["doc_id"] not in selected]
    rows.extend(replacement["docs"])
    return {
        **previous,
        **replacement,
        "docs": sorted(rows, key=lambda row: (row["title"].lower(), row["doc_id"])),
    }
