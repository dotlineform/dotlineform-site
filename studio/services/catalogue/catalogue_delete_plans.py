"""Plan exact Catalogue deletions from current canonical data without media cleanup."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from catalogue.catalogue_galleries import (
    CatalogueGalleries, MEMBERSHIPS_FILE, read_galleries, validate_galleries,
)
from catalogue.catalogue_series_galleries import (
    SERIES_GALLERIES_FILE, read_series_galleries, without_series,
)
from catalogue.catalogue_source import (
    CatalogueSourceRecords, SOURCE_FILES, payload_for_map, records_from_json_source,
    validate_source_records,
)
from catalogue.catalogue_shared_changes import empty_shared_changes, work_shared_changes, RELATIONSHIP_INDEX, RELATIONSHIP_REPORT


@dataclass(frozen=True)
class DeleteApplyPlan:
    """Carry current inputs and validated resulting records through one combined write."""

    payloads: dict[Path, dict[str, Any]]
    affected: dict[str, list[str]]
    previous: CatalogueSourceRecords
    current: CatalogueSourceRecords
    shared: dict[str, list[str]]


def build_delete_apply_plan(
    source_dir: Path, kind: str, record_ids: list[str],
) -> DeleteApplyPlan:
    """Read canonical inputs once and remove exact identities and their owned references.

    Work metadata revisions do not qualify deletion intent. Unknown identities,
    invalid resulting data and a Series with member Works fail before writes.
    """
    source = records_from_json_source(source_dir)
    payloads: dict[Path, dict[str, Any]] = {}
    if kind == "works":
        works = dict(source.works)
        series_ids: set[str] = set()
        for work_id in record_ids:
            original = works.pop(work_id, None)
            if original is None:
                raise ValueError(f"Work not found: {work_id}")
            if original.get("series_id"):
                series_ids.add(original["series_id"])
        galleries = read_galleries(source_dir, source.works)
        remaining_memberships = CatalogueGalleries(
            galleries=galleries.galleries,
            works={wid: ids for wid, ids in galleries.works.items() if wid in works},
        )
        validate_galleries(remaining_memberships, works)
        current = replace(source, works=works)
        payloads[(source_dir / SOURCE_FILES["works"]).resolve()] = payload_for_map("works", works)
        payloads[(source_dir / MEMBERSHIPS_FILE).resolve()] = remaining_memberships.payloads()[MEMBERSHIPS_FILE]
        affected = {"works": record_ids, "series": sorted(series_ids)}
        shared = work_shared_changes(source.works, works, galleries.works, remaining_memberships.works, record_ids)
    elif kind == "series" and len(record_ids) == 1:
        series_id = record_ids[0]
        series = dict(source.series)
        if series.pop(series_id, None) is None:
            raise ValueError(f"Series not found: {series_id}")
        if any(work.get("series_id") == series_id for work in source.works.values()):
            raise ValueError("Only Series with no member Works can be deleted.")
        galleries = read_galleries(source_dir, source.works)
        pairs = read_series_galleries(source_dir, source.series, galleries.galleries)
        current = replace(source, series=series)
        payloads[(source_dir / SOURCE_FILES["series"]).resolve()] = payload_for_map("series", series)
        if series_id in pairs.pairs_by_series:
            payloads[(source_dir / SERIES_GALLERIES_FILE).resolve()] = without_series(pairs, series_id).payload()
        affected = {"works": [], "series": record_ids}
        shared = {**empty_shared_changes(), "deleted_series": record_ids,
                  "current_galleries": list(pairs.pairs_by_series.get(series_id, ())),
                  "shared_outputs": sorted([RELATIONSHIP_INDEX, RELATIONSHIP_REPORT])}
    else:
        raise ValueError("delete kind must be works or one series")
    errors = validate_source_records(current)
    if errors:
        raise ValueError("source validation failed: " + "; ".join(errors[:20]))
    return DeleteApplyPlan(payloads, affected, source, current, shared)
