"""Pure delete preview planners for catalogue write paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import catalogue_cleanup
import catalogue_source_mutation as source_mutation
from catalogue_source import (
    CatalogueSourceRecords,
    normalize_status,
    normalize_series_ids_value,
    records_from_json_source,
    sort_record_map,
    validate_source_records,
)
from moment_sources import load_moment_metadata_records


def preview_work_delete(source_dir: Path, work_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    work_record = source_records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    dependent_detail_ids = sorted(
        detail_uid
        for detail_uid, detail_record in source_records.work_details.items()
        if str(detail_record.get("work_id") or "") == work_id
    )
    primary_series_ids = sorted(
        series_id
        for series_id, series_record in source_records.series.items()
        if str(series_record.get("primary_work_id") or "") == work_id
        and normalize_status(series_record.get("status")) == "published"
    )
    blockers: list[str] = []
    if primary_series_ids:
        blockers.append(
            "Work is primary_work_id for series: " + ", ".join(primary_series_ids) + ". Reassign those series before deleting the work."
        )
    affected = {
        "works": [work_id],
        "series": normalize_series_ids_value(work_record.get("series_ids")),
        "work_details": dependent_detail_ids,
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "work", work_id, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "work",
        "id": work_id,
        "record": work_record,
        "blockers": blockers,
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete work {work_id}, {len(dependent_detail_ids)} detail record(s), and remove {cleanup_count} generated/media file(s).",
    }


def series_records_with_draft_primary_cleared(
    series_records: Mapping[str, Dict[str, Any]],
    work_id: str,
) -> tuple[Dict[str, Dict[str, Any]], list[str]]:
    updated_series: Dict[str, Dict[str, Any]] = {}
    changed_series_ids: list[str] = []
    for series_id, series_record in series_records.items():
        next_record = dict(series_record)
        if (
            str(next_record.get("primary_work_id") or "") == work_id
            and normalize_status(next_record.get("status")) != "published"
        ):
            next_record["primary_work_id"] = None
            changed_series_ids.append(series_id)
        updated_series[series_id] = next_record
    return updated_series, sorted(changed_series_ids)


def preview_work_detail_delete(source_dir: Path, detail_uid: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    detail_record = source_records.work_details.get(detail_uid)
    if not isinstance(detail_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")
    work_id = str(detail_record.get("work_id") or "")
    affected = {
        "works": [work_id] if work_id else [],
        "series": [],
        "work_details": [detail_uid],
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "work_detail", detail_uid, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "work_detail",
        "id": detail_uid,
        "record": detail_record,
        "blockers": [],
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete work detail {detail_uid} and remove {cleanup_count} generated/media file(s).",
    }


def preview_series_delete(source_dir: Path, series_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    series_record = source_records.series.get(series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")
    member_work_ids = sorted(
        work_id
        for work_id, work_record in source_records.works.items()
        if series_id in normalize_series_ids_value(work_record.get("series_ids"))
    )
    affected = {
        "works": member_work_ids,
        "series": [series_id],
        "work_details": [],
    }
    cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, "series", series_id, affected) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "series",
        "id": series_id,
        "record": series_record,
        "blockers": [],
        "affected": affected,
        "cleanup": cleanup,
        "summary": f"Delete series {series_id}, remove it from {len(member_work_ids)} member work record(s), and remove {cleanup_count} generated/media file(s).",
    }


def preview_moment_delete(source_dir: Path, moment_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    moment_records = load_moment_metadata_records(source_dir)
    moment_record = moment_records.get(moment_id)
    if not isinstance(moment_record, dict):
        raise ValueError(f"moment_id not found: {moment_id}")
    cleanup = catalogue_cleanup.moment_delete_preview_cleanup(repo_root, moment_id) if repo_root is not None else {}
    cleanup_count = sum(
        int(cleanup.get(key, 0) or 0)
        for key in ("repo_artifacts", "repo_media", "staged_media")
    )
    return {
        "kind": "moment",
        "id": moment_id,
        "record": moment_record,
        "blockers": [],
        "affected": {
            "works": [],
            "series": [],
            "work_details": [],
            "moments": [moment_id],
        },
        "cleanup": cleanup,
        "summary": f"Delete moment {moment_id}, remove {cleanup_count} generated/media file(s), update the moments index, and rebuild catalogue search.",
    }


def validate_work_delete_records(source_dir: Path, work_id: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    updated_works = dict(source_records.works)
    updated_works.pop(work_id, None)
    updated_series, _changed_series_ids = series_records_with_draft_primary_cleared(source_records.series, work_id)
    updated_work_details = {
        detail_uid: detail_record
        for detail_uid, detail_record in source_records.work_details.items()
        if str(detail_record.get("work_id") or "") != work_id
    }
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(updated_works),
        work_details=sort_record_map(updated_work_details),
        series=sort_record_map(updated_series),
    )
    return validate_source_records(normalized_records)


def validate_work_detail_delete_records(source_dir: Path, detail_uid: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.work_details.pop(detail_uid, None)
    normalized_records = CatalogueSourceRecords(
        works=source_records.works,
        work_details=sort_record_map(source_records.work_details),
        series=source_records.series,
    )
    return validate_source_records(normalized_records)


def validate_series_delete_records(source_dir: Path, series_id: str) -> list[str]:
    source_records = records_from_json_source(source_dir)
    source_records.series.pop(series_id, None)
    updated_works: Dict[str, Dict[str, Any]] = {}
    for work_id, work_record in source_records.works.items():
        current_series_ids = normalize_series_ids_value(work_record.get("series_ids"))
        if series_id not in current_series_ids:
            continue
        updated_works[work_id] = source_mutation.normalize_work_update(
            work_id,
            work_record,
            {"series_ids": [value for value in current_series_ids if value != series_id]},
        )
    source_records.works.update(updated_works)
    normalized_records = CatalogueSourceRecords(
        works=sort_record_map(source_records.works),
        work_details=source_records.work_details,
        series=sort_record_map(source_records.series),
    )
    return validate_source_records(normalized_records)


def validate_moment_delete_records(source_dir: Path, moment_id: str) -> list[str]:
    moment_records = load_moment_metadata_records(source_dir)
    moment_records.pop(moment_id, None)
    errors: list[str] = []
    for remaining_moment_id, moment_record in sorted(moment_records.items()):
        errors.extend(
            f"{remaining_moment_id}: {error}"
            for error in source_mutation.validate_moment_record(remaining_moment_id, moment_record)
        )
    return errors


def build_delete_preview(source_dir: Path, kind: str, record_id: str, *, repo_root: Path | None = None) -> Dict[str, Any]:
    if kind == "work":
        preview = preview_work_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_work_delete_records(source_dir, record_id)
    elif kind == "work_detail":
        preview = preview_work_detail_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_work_detail_delete_records(source_dir, record_id)
    elif kind == "series":
        preview = preview_series_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_series_delete_records(source_dir, record_id)
    else:
        preview = preview_moment_delete(source_dir, record_id, repo_root=repo_root)
        preview["validation_errors"] = validate_moment_delete_records(source_dir, record_id)
    blockers = list(preview.get("blockers") or [])
    validation_errors = list(preview.get("validation_errors") or [])
    preview["blockers"] = blockers
    preview["blocked"] = bool(blockers or validation_errors)
    return preview
