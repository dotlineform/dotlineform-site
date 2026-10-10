"""Canonical Gallery identities and Work-owned membership references."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

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
    """Require distinct identities/titles, exact metadata and valid membership."""
    title_ids: dict[str, str] = {}
    for gid, gallery in data.galleries.items():
        validate_gallery_id(gid)
        if not isinstance(gallery, dict) or set(gallery) != {"gallery_id", "title"}:
            raise ValueError(f"Gallery {gid} must contain only gallery_id and title")
        if gallery["gallery_id"] != gid:
            raise ValueError(f"Gallery {gid} has a different gallery_id")
        title = gallery["title"]
        if not isinstance(title, str) or not title.strip() or title != title.strip():
            raise ValueError(f"Gallery {gid} needs a non-empty trimmed title")
        title_key = " ".join(title.split()).casefold()
        other_id = title_ids.get(title_key)
        if other_id is not None:
            raise ValueError(
                f'Gallery titles must be unique: “{data.galleries[other_id]["title"]}” ({other_id}) '
                f'matches “{title}” ({gid}). Choose a different title.'
            )
        title_ids[title_key] = gid
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


def _read_map(source_dir: Path, name: str, schema: str, key: str) -> dict[str, Any]:
    payload = json.loads((source_dir / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"header", key}:
        raise ValueError(f"Invalid canonical Gallery payload: {name}")
    header, records = payload["header"], payload[key]
    if not isinstance(records, dict) or not isinstance(header, dict):
        raise ValueError(f"Invalid canonical Gallery objects: {name}")
    if header.get("schema") != schema or header.get("count") != len(records):
        raise ValueError(f"Invalid canonical Gallery header: {name}")
    return records


def read_gallery_definitions(source_dir: Path) -> dict[str, dict[str, str]]:
    """Read definitions without membership reads or a title-uniqueness audit."""
    return _read_map(source_dir, GALLERIES_FILE, GALLERIES_SCHEMA, "galleries")


def read_gallery_memberships(source_dir: Path) -> dict[str, list[str]]:
    """Read Work-owned memberships without joining the complete Work corpus."""
    return _read_map(source_dir, MEMBERSHIPS_FILE, MEMBERSHIPS_SCHEMA, "works")


def read_galleries(source_dir: Path) -> CatalogueGalleries:
    """Load both authorities; Save/maintenance explicitly validate their result."""
    return CatalogueGalleries(read_gallery_definitions(source_dir), read_gallery_memberships(source_dir))


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


def newly_empty_gallery_ids(
    before: CatalogueGalleries, after: CatalogueGalleries, work_ids: Iterable[str],
) -> list[str]:
    """Find Galleries emptied by the selected Works' accepted membership removals."""
    removed: set[str] = set()
    for work_id in work_ids:
        removed.update(set(before.works.get(work_id, [])) - set(after.works.get(work_id, [])))
    if not removed:
        return []
    for gallery_ids in after.works.values():
        removed.difference_update(gallery_ids)
        if not removed:
            break
    return sorted(removed)
