"""Plan exact Catalogue deletions from current canonical data without media cleanup."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from catalogue.catalogue_galleries import (
    MEMBERSHIPS_FILE, gallery_memberships_payload, read_gallery_memberships,
)
from catalogue.catalogue_series_galleries import (
    SERIES_GALLERIES_FILE, read_series_galleries, without_series,
)
from catalogue.catalogue_source import (
    CatalogueSourceRecords, SOURCE_FILES, payload_for_map, read_source_map,
)
from catalogue.catalogue_shared_changes import (
    empty_shared_changes, work_shared_changes, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST,
)
from catalogue.catalogue_report_inputs import SERIES_PATH


@dataclass(frozen=True)
class DeleteApplyPlan:
    """Carry exact removals and their resulting records through one combined write."""

    payloads: dict[Path, dict[str, Any]]
    affected: dict[str, list[str]]
    previous: CatalogueSourceRecords
    current: CatalogueSourceRecords
    shared: dict[str, list[str]]


def build_delete_apply_plan(
    source_dir: Path, kind: str, record_ids: list[str],
) -> DeleteApplyPlan:
    """Read canonical inputs once and remove exact identities and their owned references.

    Record revisions do not qualify deletion intent. Unknown identities fail
    before writes; the UI owns the empty-Series rule. Unrelated records and
    references remain untouched; complete canonical audits have explicit owners.
    Work deletion reads only Works and memberships and writes memberships only
    when a selected entry is removed; definition stores are not required.
    Series deletion reads only definitions and relevance pairs, preserving
    Works without another membership scan.
    """
    payloads: dict[Path, dict[str, Any]] = {}
    if kind == "works":
        source = CatalogueSourceRecords(works=read_source_map(source_dir, "works"), series={})
        works = dict(source.works)
        series_ids: set[str] = set()
        for work_id in record_ids:
            original = works.pop(work_id, None)
            if original is None:
                raise ValueError(f"Work not found: {work_id}")
            if original.get("series_id"):
                series_ids.add(original["series_id"])
        memberships = read_gallery_memberships(source_dir)
        deleted_work_ids = set(record_ids)
        membership_changed = bool(deleted_work_ids & memberships.keys())
        remaining_memberships = (
            {wid: ids for wid, ids in memberships.items() if wid not in deleted_work_ids}
            if membership_changed else memberships
        )
        current = replace(source, works=works)
        payloads[(source_dir / SOURCE_FILES["works"]).resolve()] = payload_for_map("works", works)
        if membership_changed:
            payloads[(source_dir / MEMBERSHIPS_FILE).resolve()] = gallery_memberships_payload(remaining_memberships)
        affected = {"works": record_ids, "series": sorted(series_ids)}
        shared = work_shared_changes(source.works, works, memberships, remaining_memberships, record_ids)
    elif kind == "series" and len(record_ids) == 1:
        source = CatalogueSourceRecords(works={}, series=read_source_map(source_dir, "series"))
        series_id = record_ids[0]
        series = dict(source.series)
        if series.pop(series_id, None) is None:
            raise ValueError(f"Series not found: {series_id}")
        pairs = read_series_galleries(source_dir)
        current = replace(source, series=series)
        remaining_pairs = without_series(pairs, series_id)
        payloads[(source_dir / SOURCE_FILES["series"]).resolve()] = payload_for_map("series", series)
        if series_id in pairs.pairs_by_series:
            payloads[(source_dir / SERIES_GALLERIES_FILE).resolve()] = remaining_pairs.payload()
        affected = {"works": [], "series": record_ids}
        shared = {**empty_shared_changes(), "deleted_series": record_ids,
                  "current_galleries": list(pairs.pairs_by_series.get(series_id, ())),
                  "shared_outputs": sorted([RELATIONSHIP_INDEX, RELATIONSHIP_REPORT, WORK_DOCUMENT_COVERAGE_MANIFEST, SERIES_PATH])}
    else:
        raise ValueError("delete kind must be works or one series")
    return DeleteApplyPlan(payloads, affected, source, current, shared)
