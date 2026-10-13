"""Merge selected document metadata into the current collection manifest."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CollectionDocumentSummary:
    """Saved document identity and title needed by collection rendering."""

    doc_id: str
    title: str


def read_collection_manifest(path: Path) -> dict[str, Any]:
    """Parse saved metadata; never audit rows or recover by scanning sources."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Targeted collection build requires readable {path.name}; run a complete Build first") from exc


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
        "docs": sorted(rows, key=lambda row: (row["title"].lower(), row["doc_id"])),
    }
