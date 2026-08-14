"""Pure index builders for generated catalogue work and series artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

try:
    from catalogue import catalogue_generation_records as records
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        is_empty,
        normalize_status,
        normalize_text,
        numeric_aware_sort_key,
        slug_id,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue import catalogue_generation_records as records
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_numeric,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        is_empty,
        normalize_status,
        normalize_text,
        numeric_aware_sort_key,
        slug_id,
    )

try:
    from catalogue.series_ids import normalize_series_id
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.series_ids import normalize_series_id


class CatalogueGenerationIndexError(ValueError):
    """Raised when source records cannot produce valid generated indexes."""


@dataclass(frozen=True)
class SeriesWorkIndexContext:
    series_title_by_id: Dict[str, str]
    series_status_by_id: Dict[str, str]
    series_project_folders_by_id: Dict[str, List[str]]
    work_meta_by_id: Dict[str, Dict[str, Any]]
    work_status_by_id: Dict[str, str]
    work_ids_by_series_all: Dict[str, List[str]]
    series_sort_by_series_id: Dict[str, Dict[str, str]]
    series_sort_fields_by_series_id: Dict[str, List[str]]


def require_series_primary_work_id(
    sid: str,
    series_record: Mapping[str, Any],
    *,
    ordered_work_ids: Optional[List[str]] = None,
) -> str:
    """Return a required primary_work_id for a series and validate membership when provided."""
    raw = series_record.get("primary_work_id")
    if is_empty(raw):
        raise CatalogueGenerationIndexError(f"Series '{sid}' missing primary_work_id")
    wid = slug_id(raw)
    if ordered_work_ids and wid not in ordered_work_ids:
        raise CatalogueGenerationIndexError(f"Series '{sid}' primary_work_id '{wid}' is not in its works list")
    return wid


def build_series_work_index_context(
    *,
    series_records: Mapping[str, Mapping[str, Any]],
    work_records: Mapping[str, Mapping[str, Any]],
) -> SeriesWorkIndexContext:
    series_title_by_id: Dict[str, str] = {}
    series_status_by_id: Dict[str, str] = {}
    seen_series_ids: set[str] = set()
    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        if sid in seen_series_ids:
            raise CatalogueGenerationIndexError(f"Catalogue source has duplicate series_id: {sid}")
        seen_series_ids.add(sid)
        series_status_by_id[sid] = normalize_status(series_record.get("status"))
        title = coerce_string(series_record.get("title"))
        if title is not None:
            series_title_by_id[sid] = title

    series_project_folders_by_id: Dict[str, List[str]] = {}
    project_folder_sets_by_series: Dict[str, set[str]] = {}
    for work_record in work_records.values():
        folder = coerce_string(work_record.get("project_folder"))
        series_ids = records.parse_work_record_series_ids(work_record)
        if not series_ids or folder is None:
            continue
        for sid in series_ids:
            project_folder_sets_by_series.setdefault(sid, set()).add(folder)
    for sid, folder_set in project_folder_sets_by_series.items():
        series_project_folders_by_id[sid] = sorted(folder_set, key=lambda value: value.lower())

    works_sortable_fields = {fm_key for fm_key, _, _ in records.WORKS_SCHEMA}
    works_sortable_fields.update({"work_id", "series_title", "title_sort"})
    numeric_sort_fields = {"year", "height_cm", "width_cm", "depth_cm"}
    work_meta_by_id: Dict[str, Dict[str, Any]] = {}
    work_status_by_id: Dict[str, str] = {}
    work_ids_by_series_all: Dict[str, List[str]] = {}
    for work_record in work_records.values():
        wid_raw = work_record.get("work_id")
        if is_empty(wid_raw):
            continue
        wid = slug_id(wid_raw)
        meta = records.build_work_record_projection(work_record)
        work_status_by_id[wid] = normalize_status(work_record.get("status"))
        series_ids = records.parse_work_record_series_ids(work_record)
        sid = series_ids[0] if series_ids else ""
        meta["work_id"] = wid
        meta["series_ids"] = series_ids
        meta["series_id"] = sid
        meta["series_title"] = series_title_by_id.get(sid) if sid else None
        work_meta_by_id[wid] = meta
        for series_id in series_ids:
            work_ids_by_series_all.setdefault(series_id, []).append(wid)

    series_sort_by_series_id: Dict[str, Dict[str, str]] = {
        sid: {wid: wid for wid in work_ids}
        for sid, work_ids in work_ids_by_series_all.items()
    }
    series_sort_fields_by_series_id: Dict[str, List[str]] = {
        sid: ["work_id"] for sid in work_ids_by_series_all.keys()
    }

    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        sort_fields_raw = coerce_string(series_record.get("sort_fields")) or "work_id"

        parsed_fields: List[tuple[str, bool]] = []
        display_fields: List[str] = []
        for raw_token in sort_fields_raw.split(","):
            token = normalize_text(raw_token)
            if token == "":
                continue
            desc = token.startswith("-")
            field = normalize_text(token[1:] if desc else token).lower()
            display_field = field
            if field == "title":
                field = "title_sort"
                display_field = "title"
            elif field == "title_sort":
                display_field = "title"
            if field not in works_sortable_fields:
                raise CatalogueGenerationIndexError(
                    f"Series source has unknown sort field '{field}' for series_id '{sid}'"
                )
            if field == "work_id":
                continue
            parsed_fields.append((field, desc))
            display_fields.append(f"-{display_field}" if desc else display_field)

        parsed_fields.append(("work_id", False))
        display_fields.append("work_id")
        series_sort_fields_by_series_id[sid] = display_fields
        series_work_ids = list(work_ids_by_series_all.get(sid, []))
        if not series_work_ids:
            continue

        def sortable_value(wid: str, field: str) -> Any:
            if field == "title_sort":
                value = numeric_aware_sort_key(work_meta_by_id[wid].get("title"))
            else:
                value = work_meta_by_id[wid].get(field)
            if field in numeric_sort_fields:
                nv = coerce_numeric(value)
                return float("-inf") if nv is None else nv
            return normalize_text(value).lower()

        for field, desc in reversed(parsed_fields):
            series_work_ids.sort(
                key=lambda current_wid, current_field=field: sortable_value(current_wid, current_field),
                reverse=desc,
            )

        rank_width = max(3, len(str(len(series_work_ids))))
        for idx, wid in enumerate(series_work_ids, start=1):
            series_sort_by_series_id.setdefault(sid, {})[wid] = f"{idx:0{rank_width}d}-{wid}"

    return SeriesWorkIndexContext(
        series_title_by_id=series_title_by_id,
        series_status_by_id=series_status_by_id,
        series_project_folders_by_id=series_project_folders_by_id,
        work_meta_by_id=work_meta_by_id,
        work_status_by_id=work_status_by_id,
        work_ids_by_series_all=work_ids_by_series_all,
        series_sort_by_series_id=series_sort_by_series_id,
        series_sort_fields_by_series_id=series_sort_fields_by_series_id,
    )


def ordered_published_work_ids_by_series(context: SeriesWorkIndexContext) -> Dict[str, List[str]]:
    work_rows_by_series: Dict[str, List[tuple[str, str]]] = {}
    for sid, work_ids in context.work_ids_by_series_all.items():
        for wid in work_ids:
            if context.work_status_by_id.get(wid) != "published":
                continue
            series_sort = context.series_sort_by_series_id.get(sid, {}).get(wid, wid)
            work_rows_by_series.setdefault(sid, []).append((series_sort, wid))

    ordered: Dict[str, List[str]] = {}
    for sid, rows in work_rows_by_series.items():
        rows_sorted = sorted(rows, key=lambda item: (item[0], item[1]))
        ordered[sid] = [wid for _, wid in rows_sorted]
    return ordered


def build_series_member_work_records(
    *,
    context: SeriesWorkIndexContext,
    series_id: str,
) -> List[Dict[str, Any]]:
    ordered_work_ids = ordered_published_work_ids_by_series(context).get(series_id, [])
    member_works: List[Dict[str, Any]] = []
    for work_id in ordered_work_ids:
        work_meta = context.work_meta_by_id.get(work_id, {})
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
    ordered_work_ids_by_series = ordered_published_work_ids_by_series(context)
    series_payload_unsorted: Dict[str, Dict[str, Any]] = {}
    for series_record in series_records.values():
        sid_raw = series_record.get("series_id")
        if is_empty(sid_raw):
            continue
        sid = normalize_series_id(sid_raw)
        status = normalize_status(series_record.get("status"))
        if status != "published":
            continue

        series_title = coerce_string(series_record.get("title")) or sid
        year = coerce_int(series_record.get("year"))
        year_display = coerce_string(series_record.get("year_display"))
        if year_display is None:
            year_display = str(year) if year is not None else None
        ordered_work_ids = ordered_work_ids_by_series.get(sid, [])
        primary_work_id = require_series_primary_work_id(
            sid,
            series_record,
            ordered_work_ids=ordered_work_ids,
        )

        series_payload_unsorted[sid] = compact_json_object({
            "series_id": sid,
            "title": series_title,
            "year": year,
            "year_display": year_display,
            "primary_work_id": primary_work_id,
            "single_work_id": ordered_work_ids[0] if len(ordered_work_ids) == 1 else None,
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
