"""Pure index and member-row builders for generated Catalogue artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence

from catalogue.catalogue_generation_common import (
    coerce_int,
    coerce_string,
    compact_json_object,
    compute_payload_version,
    is_empty,
    slug_id,
)

from catalogue.series_ids import normalize_series_id


class CatalogueGenerationIndexError(ValueError):
    """Raised when source records cannot produce valid generated indexes."""


@dataclass(frozen=True)
class SeriesWorkIndexContext:
    series_title_by_id: Dict[str, str]
    series_project_folders_by_id: Dict[str, List[str]]
    work_meta_by_id: Dict[str, Dict[str, Any]]
    work_ids_by_series_all: Dict[str, List[str]]


def build_series_work_index_context(
    *,
    series_records: Mapping[str, Mapping[str, Any]],
    work_records: Mapping[str, Mapping[str, Any]],
) -> SeriesWorkIndexContext:
    series_title_by_id: Dict[str, str] = {}
    seen_series_ids: set[str] = set()
    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        if sid in seen_series_ids:
            raise CatalogueGenerationIndexError(f"Catalogue source has duplicate series_id: {sid}")
        seen_series_ids.add(sid)
        title = coerce_string(series_record.get("title"))
        if title is not None:
            series_title_by_id[sid] = title

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

    work_meta_by_id: Dict[str, Dict[str, Any]] = {}
    work_ids_by_series_all: Dict[str, List[str]] = {}
    for work_record in work_records.values():
        wid_raw = work_record.get("work_id")
        if is_empty(wid_raw):
            continue
        wid = slug_id(wid_raw)
        meta = dict(work_record)
        series_ids = [normalize_series_id(work_record["series_id"])] if work_record.get("series_id") else []
        sid = series_ids[0] if series_ids else ""
        meta["work_id"] = wid
        meta["series_id"] = sid
        meta["series_title"] = series_title_by_id.get(sid) if sid else None
        work_meta_by_id[wid] = meta
        for series_id in series_ids:
            work_ids_by_series_all.setdefault(series_id, []).append(wid)

    return SeriesWorkIndexContext(
        series_title_by_id=series_title_by_id,
        series_project_folders_by_id=series_project_folders_by_id,
        work_meta_by_id=work_meta_by_id,
        work_ids_by_series_all=work_ids_by_series_all,
    )


def ordered_work_ids_by_series(context: SeriesWorkIndexContext) -> Dict[str, List[str]]:
    return {sid: sorted(ids) for sid, ids in context.work_ids_by_series_all.items()}


def build_series_member_work_records(
    *,
    context: SeriesWorkIndexContext,
    series_id: str,
) -> List[Dict[str, Any]]:
    return build_member_work_records(context=context, work_ids=context.work_ids_by_series_all.get(series_id, []))


def build_member_work_records(
    *, context: SeriesWorkIndexContext, work_ids: Sequence[str],
) -> List[Dict[str, Any]]:
    """Share the compact, ascending Work-ID member projection across groupings."""
    member_works: List[Dict[str, Any]] = []
    for work_id in sorted(work_ids):
        work_meta = context.work_meta_by_id[work_id]
        year = coerce_int(work_meta.get("year"))
        year_display = coerce_string(work_meta.get("year_display"))
        if year_display is None:
            year_display = str(year) if year is not None else None
        member_works.append(compact_json_object({
            "work_id": work_id,
            "title": coerce_string(work_meta.get("title")) or work_id,
            "year": year,
            "year_display": year_display,
        }))
    return member_works


def build_series_index_records(
    *,
    series_records: Mapping[str, Mapping[str, Any]],
    context: SeriesWorkIndexContext,
) -> Dict[str, Dict[str, Any]]:
    member_ids_by_series = ordered_work_ids_by_series(context)
    series_payload_unsorted: Dict[str, Dict[str, Any]] = {}
    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        series_title = coerce_string(series_record.get("title")) or sid
        year = coerce_int(series_record.get("year"))
        year_display = coerce_string(series_record.get("year_display"))
        if year_display is None:
            year_display = str(year) if year is not None else None
        ordered_work_ids = member_ids_by_series.get(sid, [])
        series_payload_unsorted[sid] = compact_json_object({
            "series_id": sid,
            "title": series_title,
            "year": year,
            "year_display": year_display,
            "work_count": len(ordered_work_ids),
        })

    return {sid: series_payload_unsorted[sid] for sid in sorted(series_payload_unsorted.keys())}


def build_series_index_payload(
    *,
    series_records: Mapping[str, Mapping[str, Any]],
    context: SeriesWorkIndexContext,
    generated_at_utc: str,
) -> Dict[str, Any]:
    series_payload = build_series_index_records(series_records=series_records, context=context)
    version_payload = compact_json_object({
        "schema": "series_index_v3",
        "series": series_payload,
    })
    version = compute_payload_version(version_payload)
    return compact_json_object({
        "header": {
            "schema": "series_index_v3",
            "version": version,
            "generated_at_utc": generated_at_utc,
            "count": len(series_payload),
        },
        "series": series_payload,
    })
