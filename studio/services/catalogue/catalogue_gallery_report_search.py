"""Project the Catalogue report's compact Gallery definitions and direct memberships."""

import json
from pathlib import Path
from typing import Any, Iterable

from catalogue.catalogue_galleries import CatalogueGalleries


SCHEMA = "catalogue_gallery_report_search_v1"


def gallery_report_search_payload(galleries: CatalogueGalleries, *, timestamp: str) -> dict[str, Any]:
    return {
        "header": {"schema": SCHEMA, "generated_at_utc": timestamp},
        "galleries": {gid: record["title"] for gid, record in sorted(galleries.galleries.items())},
        "gallery_ids_by_work": {wid: ids for wid, ids in sorted(galleries.works.items()) if ids},
    }


def merge_gallery_report_search(
    path: Path, galleries: CatalogueGalleries, *,
    current_gallery_ids: Iterable[str], deleted_gallery_ids: Iterable[str], work_ids: Iterable[str], timestamp: str,
) -> dict[str, Any] | None:
    """Replace only supplied definitions and membership rows in the saved projection."""
    payload = json.loads(path.read_bytes())
    titles, memberships = payload["galleries"], payload["gallery_ids_by_work"]
    changed = False
    for gid in deleted_gallery_ids:
        if titles.pop(gid, None) is not None:
            changed = True
    for gid in current_gallery_ids:
        title = galleries.galleries[gid]["title"]
        if titles.get(gid) != title:
            titles[gid] = title
            changed = True
    for wid in work_ids:
        ids = galleries.works.get(wid)
        if ids:
            if memberships.get(wid) != ids:
                memberships[wid] = ids
                changed = True
        elif memberships.pop(wid, None) is not None:
            changed = True
    if not changed:
        return None
    payload["header"]["generated_at_utc"] = timestamp
    return payload
