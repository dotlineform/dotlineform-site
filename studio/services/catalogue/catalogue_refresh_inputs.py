"""Parse normal Refresh dependencies selected by the app-generated queue."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from catalogue.catalogue_galleries import CatalogueGalleries, GALLERIES_FILE, MEMBERSHIPS_FILE
from catalogue.catalogue_report_inputs import SERIES_PATH, WORK_RESOURCES_PATH, WORK_SOURCES_PATH
from catalogue.catalogue_series_galleries import CatalogueSeriesGalleries, SERIES_GALLERIES_FILE
from catalogue.catalogue_shared_changes import RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_INDEX
from catalogue.catalogue_source import CatalogueSourceRecords, SOURCE_FILES


def _read_map(source_dir: Path, filename: str, key: str) -> dict[str, Any]:
    return json.loads((source_dir / filename).read_text(encoding="utf-8"))[key]


def read_refresh_inputs(
    source_dir: Path, pending: dict[str, Any],
) -> tuple[CatalogueSourceRecords, CatalogueGalleries, CatalogueSeriesGalleries]:
    """Resolve dependencies from the supplied queue, never by scanning for changes.

    Queue producers own selections and completed Save owns authored data. Read
    only the maps used by selected projections, without validating file contents,
    identities or references. Deleted-only selections need no canonical map for
    agreement checks. Each required authority is parsed at most once per action.
    """
    outputs = set(pending["shared_outputs"])
    current_works = any(not entry["refreshed"] for entry in pending["current_works"].values())
    current_series, current_galleries = bool(pending["current_series"]), bool(pending["current_galleries"])
    relationships = bool(outputs & {RELATIONSHIP_INDEX, RELATIONSHIP_REPORT}) and (current_series or current_galleries)
    member_rows = bool(pending["created_galleries"] or (
        current_galleries and set(pending["gallery_member_works"]) & pending["current_works"].keys()
    ))
    metadata_rows = any(entry["metadata"] for entry in pending["current_works"].values())
    works_needed = current_works or member_rows or (metadata_rows and bool(outputs & {
        WORK_INDEX, WORK_SOURCES_PATH, WORK_RESOURCES_PATH,
    }))
    works = _read_map(source_dir, SOURCE_FILES["works"], "works") if works_needed else {}
    work_series = any("series_id" in works[wid] for wid, entry in pending["current_works"].items() if not entry["refreshed"])
    series_needed = work_series or (RELATIONSHIP_REPORT in outputs and (current_series or current_galleries)) or (current_series and bool(outputs & {
        SERIES_PATH,
    }))
    galleries_needed = current_works or relationships or current_galleries
    records = CatalogueSourceRecords(
        works=works,
        series=_read_map(source_dir, SOURCE_FILES["series"], "series") if series_needed else {},
    )
    galleries = CatalogueGalleries(
        galleries=_read_map(source_dir, GALLERIES_FILE, "galleries") if galleries_needed else {},
        works=_read_map(source_dir, MEMBERSHIPS_FILE, "works") if current_works or member_rows else {},
    )
    pairs = CatalogueSeriesGalleries({
        sid: tuple(ids) for sid, ids in _read_map(source_dir, SERIES_GALLERIES_FILE, "pairs_by_series").items()
    }) if relationships else CatalogueSeriesGalleries({})
    return records, galleries, pairs
