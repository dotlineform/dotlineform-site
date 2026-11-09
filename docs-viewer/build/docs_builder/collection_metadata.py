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
    """Replace selected rows in title order, carrying the new row objects forward."""
    selected = set(selected_doc_ids)
    rows = [dict(row) for row in previous["docs"] if row["doc_id"] not in selected]
    rows.extend(replacement["docs"])
    return {
        "docs": sorted(rows, key=lambda row: (row["title"].lower(), row["doc_id"])),
    }


def project_context_catalogue_targets(rows: list[dict[str, Any]], item_payloads: dict[str, dict[str, Any]]) -> None:
    """Attach completed Catalogue target IDs to the new Context rows in place."""
    for row in rows:
        references = item_payloads[row["doc_id"]].get("catalogue", {}).get("references", ())
        work_ids: set[str] = set()
        gallery_ids: set[str] = set()
        for reference in references:
            target = reference["target"]
            ids = gallery_ids if target["kind"] == "catalogue-gallery" else work_ids
            ids.add(target["id"])
        if work_ids or gallery_ids:
            row["catalogue_targets"] = {"work_ids": sorted(work_ids), "gallery_ids": sorted(gallery_ids)}
