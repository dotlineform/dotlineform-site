"""Canonical Gallery identities and Work-owned membership references."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_revisions import CatalogueRevisionConflict


GALLERIES_FILE = "galleries.json"
MEMBERSHIPS_FILE = "galleries-by-work.json"
GALLERIES_SCHEMA = "catalogue_source_galleries_v1"
MEMBERSHIPS_SCHEMA = "catalogue_source_galleries_by_work_v1"


@dataclass(frozen=True)
class CatalogueGalleries:
    galleries: dict[str, dict[str, str]]
    works: dict[str, list[str]]

    def payloads(self) -> dict[str, dict[str, Any]]:
        return {
            GALLERIES_FILE: {
                "header": {"schema": GALLERIES_SCHEMA, "count": len(self.galleries)},
                "galleries": dict(sorted(self.galleries.items())),
            },
            MEMBERSHIPS_FILE: {
                "header": {"schema": MEMBERSHIPS_SCHEMA, "count": len(self.works)},
                "works": {wid: sorted(ids) for wid, ids in sorted(self.works.items())},
            },
        }


def validate_gallery_id(gallery_id: str) -> None:
    """Require the canonical exact ID without padding or other aliases."""
    if not isinstance(gallery_id, str) or not re.fullmatch(r"[0-9]{3,}", gallery_id) or f"{int(gallery_id):03d}" != gallery_id:
        raise ValueError(f"Invalid exact Gallery ID: {gallery_id!r}")


def validate_galleries(data: CatalogueGalleries, works: Mapping[str, Any]) -> None:
    """Reject ambiguous identities, copied metadata and dangling membership."""
    for gid, gallery in data.galleries.items():
        validate_gallery_id(gid)
        if not isinstance(gallery, dict) or set(gallery) != {"gallery_id", "title"}:
            raise ValueError(f"Gallery {gid} must contain only gallery_id and title")
        if gallery["gallery_id"] != gid:
            raise ValueError(f"Gallery {gid} has a different gallery_id")
        title = gallery["title"]
        if not isinstance(title, str) or not title.strip() or title != title.strip():
            raise ValueError(f"Gallery {gid} needs a non-empty trimmed title")
    for wid, ids in data.works.items():
        if not isinstance(wid, str) or not re.fullmatch(r"[0-9]{5}", wid) or wid not in works:
            raise ValueError(f"Gallery membership references unknown exact Work ID: {wid!r}")
        if not isinstance(ids, list) or any(not isinstance(gid, str) for gid in ids):
            raise ValueError(f"Gallery membership for {wid} must be an array of Gallery IDs")
        if len(ids) != len(set(ids)):
            raise ValueError(f"Gallery membership for {wid} contains duplicates")
        for gid in ids:
            if gid not in data.galleries:
                raise ValueError(f"Work {wid} references unknown Gallery {gid!r}")


def read_galleries(source_dir: Path, works: Mapping[str, Any]) -> CatalogueGalleries:
    """Read the two authorities; missing data is an error, never Series-derived."""
    maps = []
    for name, schema, key in (
        (GALLERIES_FILE, GALLERIES_SCHEMA, "galleries"),
        (MEMBERSHIPS_FILE, MEMBERSHIPS_SCHEMA, "works"),
    ):
        payload = json.loads((source_dir / name).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"header", key}:
            raise ValueError(f"Invalid canonical Gallery payload: {name}")
        header, records = payload["header"], payload[key]
        if not isinstance(records, dict) or not isinstance(header, dict):
            raise ValueError(f"Invalid canonical Gallery objects: {name}")
        if header.get("schema") != schema or header.get("count") != len(records):
            raise ValueError(f"Invalid canonical Gallery header: {name}")
        maps.append(records)
    data = CatalogueGalleries(galleries=maps[0], works=maps[1])
    validate_galleries(data, works)
    return data


def require_work_membership_revision(data: CatalogueGalleries, work_id: str, expected: Any) -> None:
    """Check the editor's exact membership set independently of Work metadata."""
    if not isinstance(expected, list) or any(not isinstance(gid, str) for gid in expected):
        raise ValueError("expected_gallery_ids must be an array of Gallery IDs")
    if sorted(expected) != sorted(data.works.get(work_id, [])):
        raise CatalogueRevisionConflict("Work Gallery membership changed; reload before saving.")


def with_work_memberships(
    data: CatalogueGalleries, works: Mapping[str, Any], replacements: Mapping[str, Any],
) -> CatalogueGalleries:
    """Validate all replacements together; empty selections remove their entries."""
    memberships = {**data.works, **replacements}
    updated = CatalogueGalleries(data.galleries, memberships)
    validate_galleries(updated, works)
    for work_id, gallery_ids in replacements.items():
        if gallery_ids:
            memberships[work_id] = sorted(gallery_ids)
        else:
            del memberships[work_id]
    return updated
