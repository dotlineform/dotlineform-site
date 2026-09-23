"""Select exact output records, including both sides of Gallery membership edits."""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from external_workspace_paths import ExternalWorkspaceRoot

from catalogue.catalogue_galleries import CatalogueGalleries, validate_gallery_id
from catalogue.catalogue_output_paths import output_path
from catalogue.catalogue_source import CatalogueSourceRecords, slug_id
from catalogue.series_ids import normalize_series_id


def _previous_payload(workspace: ExternalWorkspaceRoot, family: str, identity: str) -> dict[str, Any] | None:
    directory = {"work": "works", "gallery": "galleries"}[family]
    path = output_path(workspace, f"{directory}/index/{identity}.json")
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    key = f"{family}_id"
    if not isinstance(payload, dict) or not isinstance(payload.get("header"), dict) or not isinstance(payload.get(family), dict):
        raise ValueError(f"Invalid generated {family} payload: {path}")
    if payload["header"].get(key) != identity or payload[family].get(key) != identity:
        raise ValueError(f"Generated {family} identity does not match {path}")
    return payload


def selected_output_paths(
    workspace: ExternalWorkspaceRoot, records: CatalogueSourceRecords, galleries: CatalogueGalleries,
    *, work_ids: Sequence[str] | None, series_ids: Sequence[str], gallery_ids: Sequence[str],
) -> set[str]:
    """Previous generated membership invalidates outputs; canonical data owns content."""
    if work_ids is None:
        selected = set()
        for family, ids in (("works", records.works), ("series", records.series), ("galleries", galleries.galleries)):
            selected.update(f"{family}/index/{identity}.json" for identity in ids)
            selected.update(path.relative_to(workspace.root).as_posix() for path in output_path(workspace, f"{family}/index").glob("*.json"))
        return selected

    selected_works = {slug_id(wid) for wid in work_ids}
    selected_series = {normalize_series_id(sid) for sid in series_ids}
    for gid in gallery_ids:
        validate_gallery_id(gid)
    selected_galleries = set(gallery_ids)
    for wid in selected_works:
        previous = _previous_payload(workspace, "work", wid)
        if previous is not None:
            previous_series = previous["work"].get("series_id")
            if previous_series:
                selected_series.add(normalize_series_id(previous_series))
            previous_galleries = previous["work"].get("galleries")
            if not isinstance(previous_galleries, list):
                raise ValueError(f"Generated Work {wid} galleries must be an array; regenerate complete Catalogue JSON")
            for gallery in previous_galleries:
                gid = gallery.get("gallery_id") if isinstance(gallery, dict) else None
                validate_gallery_id(gid)
                selected_galleries.add(gid)
        selected_galleries.update(galleries.works.get(wid, []))
        current_series = records.works.get(wid, {}).get("series_id")
        if current_series:
            selected_series.add(current_series)

    for gid in selected_galleries:
        previous = _previous_payload(workspace, "gallery", gid)
        if previous is not None:
            members = previous.get("member_works")
            if not isinstance(members, list):
                raise ValueError(f"Generated Gallery {gid} member_works must be an array")
            for member in members:
                wid = member.get("work_id") if isinstance(member, dict) else None
                if not isinstance(wid, str) or not re.fullmatch(r"[0-9]{5}", wid):
                    raise ValueError(f"Generated Gallery {gid} has an invalid member Work ID: {wid!r}")
                selected_works.add(wid)
    selected_works.update(wid for wid, ids in galleries.works.items() if selected_galleries.intersection(ids))
    return (
        {f"works/index/{wid}.json" for wid in selected_works}
        | {f"series/index/{sid}.json" for sid in selected_series}
        | {f"galleries/index/{gid}.json" for gid in selected_galleries}
    )
