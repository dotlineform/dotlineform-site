"""Load normal Refresh dependencies once, without canonical corpus audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from catalogue.catalogue_galleries import CatalogueGalleries, read_gallery_definitions, read_gallery_memberships
from catalogue.catalogue_report_inputs import SERIES_PATH, WORK_RESOURCES_PATH, WORK_SOURCES_PATH
from catalogue.catalogue_series_galleries import CatalogueSeriesGalleries, read_series_galleries
from catalogue.catalogue_shared_changes import GALLERY_INDEX, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST, WORK_INDEX
from catalogue.catalogue_source import CatalogueSourceRecords, read_source_map


def read_refresh_inputs(
    source_dir: Path, pending: dict[str, Any],
) -> tuple[CatalogueSourceRecords, CatalogueGalleries, CatalogueSeriesGalleries]:
    """Resolve dependencies from the supplied queue, never by scanning for changes.

    Unloaded maps are unused by the selected projectors. Save owns canonical
    validity; readers check file envelopes and projections check consumed facts.
    Empty selection opens no canonical file. There is no process cache or audit
    bypass flag, and each required authority is parsed at most once per action.
    """
    outputs = set(pending["shared_outputs"])
    current_works = any(not entry["refreshed"] for entry in pending["current_works"].values())
    deleted_works = any(not entry["refreshed"] for entry in pending["deleted_works"].values())
    relationships = bool(outputs & {RELATIONSHIP_INDEX, RELATIONSHIP_REPORT})
    member_rows = bool(pending["created_galleries"] or (pending["current_galleries"] and pending["gallery_member_works"]))
    works_needed = current_works or deleted_works or member_rows or bool(outputs & {
        WORK_INDEX, WORK_DOCUMENT_COVERAGE_MANIFEST, WORK_SOURCES_PATH, WORK_RESOURCES_PATH,
    })
    series_needed = current_works or relationships or bool(pending["current_series"] or pending["deleted_series"]) or bool(outputs & {
        WORK_DOCUMENT_COVERAGE_MANIFEST, SERIES_PATH,
    })
    galleries_needed = current_works or relationships or GALLERY_INDEX in outputs or bool(
        pending["current_galleries"] or pending["deleted_galleries"],
    )
    records = CatalogueSourceRecords(
        works=read_source_map(source_dir, "works") if works_needed else {},
        series=read_source_map(source_dir, "series") if series_needed else {},
        work_detail_sections={}, work_details={},
    )
    galleries = CatalogueGalleries(
        galleries=read_gallery_definitions(source_dir) if galleries_needed else {},
        works=read_gallery_memberships(source_dir) if current_works or member_rows else {},
    )
    pairs = read_series_galleries(source_dir) if relationships else CatalogueSeriesGalleries({})
    return records, galleries, pairs
