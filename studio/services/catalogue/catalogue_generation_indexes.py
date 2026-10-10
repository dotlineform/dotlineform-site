"""Pure index and member-row builders for generated Catalogue artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence

from catalogue.catalogue_generation_common import (
    coerce_string,
    is_empty,
    slug_id,
)

from catalogue.series_ids import normalize_series_id


class CatalogueGenerationIndexError(ValueError):
    """Raised when source records cannot produce valid generated indexes."""


def build_work_index_row(*, work_id: str, work_record: Mapping[str, Any]) -> Dict[str, Any]:
    """Project only the identity and title consumed by Work target lookup."""
    title = coerce_string(work_record.get("title"))
    if title is None:
        raise CatalogueGenerationIndexError(f"Catalogue Work {work_id} has no index title")
    return {"work_id": work_id, "title": title}


@dataclass(frozen=True)
class SeriesWorkIndexContext:
    series_project_folders_by_id: Dict[str, List[str]]
    work_ids_by_series_all: Dict[str, List[str]]


def build_series_work_index_context(
    *,
    series_records: Mapping[str, Mapping[str, Any]],
    work_records: Mapping[str, Mapping[str, Any]],
) -> SeriesWorkIndexContext:
    seen_series_ids: set[str] = set()
    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        if sid in seen_series_ids:
            raise CatalogueGenerationIndexError(f"Catalogue source has duplicate series_id: {sid}")
        seen_series_ids.add(sid)

    series_project_folders_by_id: Dict[str, List[str]] = {}
    project_folder_sets_by_series: Dict[str, set[str]] = {}
    for work_record in work_records.values():
        folder = coerce_string(work_record.get("project_folder"))
        series_ids = [normalize_series_id(work_record["series_id"])] if work_record.get("series_id") else []
        if not series_ids or folder is None:
            continue
        for sid in series_ids:
            project_folder_sets_by_series.setdefault(sid, set()).add(folder)
    for sid, folder_set in project_folder_sets_by_series.items():
        series_project_folders_by_id[sid] = sorted(folder_set, key=lambda value: value.lower())

    work_ids_by_series_all: Dict[str, List[str]] = {}
    for work_record in work_records.values():
        wid_raw = work_record.get("work_id")
        if is_empty(wid_raw):
            continue
        wid = slug_id(wid_raw)
        series_ids = [normalize_series_id(work_record["series_id"])] if work_record.get("series_id") else []
        for series_id in series_ids:
            work_ids_by_series_all.setdefault(series_id, []).append(wid)

    return SeriesWorkIndexContext(
        series_project_folders_by_id=series_project_folders_by_id,
        work_ids_by_series_all=work_ids_by_series_all,
    )


def ordered_work_ids_by_series(context: SeriesWorkIndexContext) -> Dict[str, List[str]]:
    return {sid: sorted(ids) for sid, ids in context.work_ids_by_series_all.items()}


def build_member_work_records(
    *, work_records: Mapping[str, Mapping[str, Any]], work_ids: Sequence[str],
) -> List[Dict[str, Any]]:
    """Project Gallery member identities/titles directly in ascending Work-ID order."""
    return [
        {
            "work_id": work_id,
            "title": coerce_string(work_records[work_id].get("title")) or work_id,
        }
        for work_id in sorted(work_ids)
    ]
