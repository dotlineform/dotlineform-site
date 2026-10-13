"""Canonical Gallery identities and Work-owned membership references."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

GALLERIES_FILE = "galleries.json"
MEMBERSHIPS_FILE = "galleries-by-work.json"
GALLERIES_SCHEMA = "catalogue_source_galleries_v1"
MEMBERSHIPS_SCHEMA = "catalogue_source_galleries_by_work_v1"


@dataclass(frozen=True)
class CatalogueGalleries:
    galleries: dict[str, dict[str, str]]
    works: dict[str, list[str]]

    def definitions_payload(self) -> dict[str, Any]:
        return {
            "header": {"schema": GALLERIES_SCHEMA},
            "galleries": dict(sorted(self.galleries.items())),
        }

    def memberships_payload(self) -> dict[str, Any]:
        return {
            "header": {"schema": MEMBERSHIPS_SCHEMA},
            "works": {wid: sorted(ids) for wid, ids in sorted(self.works.items())},
        }

    def payloads(self) -> dict[str, dict[str, Any]]:
        return {
            GALLERIES_FILE: self.definitions_payload(),
            MEMBERSHIPS_FILE: self.memberships_payload(),
        }


def validate_gallery_id(gallery_id: str) -> None:
    """Require the canonical exact ID without padding or other aliases."""
    if not isinstance(gallery_id, str) or not re.fullmatch(r"[0-9]{3,}", gallery_id) or f"{int(gallery_id):03d}" != gallery_id:
        raise ValueError(f"Invalid exact Gallery ID: {gallery_id!r}")


def validate_galleries(data: CatalogueGalleries, works: Mapping[str, Any]) -> None:
    """Require exact identities/metadata and valid membership; titles may repeat."""
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


def _read_map(source_dir: Path, name: str, schema: str, key: str) -> dict[str, Any]:
    payload = json.loads((source_dir / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"header", key}:
        raise ValueError(f"Invalid canonical Gallery payload: {name}")
    header, records = payload["header"], payload[key]
    if not isinstance(records, dict) or not isinstance(header, dict):
        raise ValueError(f"Invalid canonical Gallery objects: {name}")
    if header != {"schema": schema}:
        raise ValueError(f"Invalid canonical Gallery header: {name}")
    return records


def read_gallery_definitions(source_dir: Path) -> dict[str, dict[str, str]]:
    """Read the saved definition map with header/envelope validation."""
    return _read_map(source_dir, GALLERIES_FILE, GALLERIES_SCHEMA, "galleries")


def read_gallery_memberships(source_dir: Path) -> dict[str, list[str]]:
    """Read memberships with a schema-only header and no Work-count requirement."""
    return _read_map(source_dir, MEMBERSHIPS_FILE, MEMBERSHIPS_SCHEMA, "works")


def read_galleries(source_dir: Path) -> CatalogueGalleries:
    """Load both envelopes; explicit validation and maintenance own corpus audits."""
    return CatalogueGalleries(read_gallery_definitions(source_dir), read_gallery_memberships(source_dir))


def with_work_memberships(
    data: CatalogueGalleries, replacements: Mapping[str, list[str]],
) -> CatalogueGalleries:
    """Persist Gallery sets whose representation and membership the UI validates.

    The UI supplies lists of distinct existing Gallery ID strings. Empty lists
    remove Work membership entries; explicit audits own canonical validation.
    """
    memberships = dict(data.works)
    for work_id, gallery_ids in replacements.items():
        if gallery_ids:
            memberships[work_id] = sorted(gallery_ids)
        else:
            memberships.pop(work_id, None)
    return CatalogueGalleries(data.galleries, memberships)
