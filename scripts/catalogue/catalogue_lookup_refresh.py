"""Catalogue lookup refresh execution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_lookup import (
    build_and_write_catalogue_lookup,
    build_series_lookup_payload,
    build_series_search_payload,
    build_work_detail_lookup_payload,
    build_work_detail_search_payload,
    build_work_lookup_payload,
    build_work_search_payload,
    write_detail_lookup_payload,
    write_lookup_root_payload,
    write_series_lookup_payload,
    write_work_lookup_payload,
)
from catalogue.catalogue_source import (
    normalize_series_ids_value,
    normalize_text,
    records_from_json_source,
    slug_id,
)
from catalogue import catalogue_invalidation as invalidation


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def _with_invalidation(result: dict[str, Any], invalidation_result: Mapping[str, Any]) -> dict[str, Any]:
    result["invalidation_class"] = invalidation_result["class"]
    result["unknown_fields"] = list(invalidation_result.get("unknown_fields") or [])
    return result


def full_lookup_refresh(source_dir: Path, lookup_dir: Path, repo_root: Path) -> dict[str, Any]:
    written = build_and_write_catalogue_lookup(source_dir, lookup_dir)
    return {
        "mode": "full",
        "artifacts": ["full_lookup_refresh"],
        "written_count": len(written),
        "written_paths": [rel_path(repo_root, path) for path in written],
    }


def work_lookup_record_refresh(source_dir: Path, lookup_dir: Path, repo_root: Path, work_id: str) -> dict[str, Any]:
    source_records = records_from_json_source(source_dir)
    written_path = write_work_lookup_payload(
        lookup_dir,
        work_id,
        build_work_lookup_payload(source_records, work_id),
    )
    return {
        "mode": "single-record",
        "artifacts": ["work_record"],
        "written_count": 1,
        "written_paths": [rel_path(repo_root, written_path)],
    }


def work_change_lookup_refresh(
    source_dir: Path,
    lookup_dir: Path,
    repo_root: Path,
    *,
    work_id: str,
    fields_changed: list[str],
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    invalidation_result: Mapping[str, Any],
    locked_single_record_fields: set[str],
) -> dict[str, Any]:
    artifacts = list(invalidation_result["artifacts"])
    use_single_record_lookup_refresh = (
        invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD
        and set(fields_changed).issubset(locked_single_record_fields)
    )
    if use_single_record_lookup_refresh:
        return _with_invalidation(
            work_lookup_record_refresh(source_dir, lookup_dir, repo_root, work_id),
            invalidation_result,
        )

    if invalidation_result["class"] != invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
        return _with_invalidation(full_lookup_refresh(source_dir, lookup_dir, repo_root), invalidation_result)

    source_records = records_from_json_source(source_dir)
    written_paths: list[str] = []

    if "work_record" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_work_lookup_payload(
                    lookup_dir,
                    work_id,
                    build_work_lookup_payload(source_records, work_id),
                ),
            )
        )

    if "work_search" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_lookup_root_payload(
                    lookup_dir,
                    "work_search.json",
                    build_work_search_payload(source_records),
                ),
            )
        )

    if "related_series_records" in artifacts:
        related_series_ids = set(normalize_series_ids_value(current_record.get("series_ids")))
        related_series_ids.update(normalize_series_ids_value(updated_record.get("series_ids")))
        for series_id in sorted(related_series_ids):
            written_paths.append(
                rel_path(
                    repo_root,
                    write_series_lookup_payload(
                        lookup_dir,
                        series_id,
                        build_series_lookup_payload(source_records, series_id),
                    ),
                )
            )

    if "related_work_detail_records" in artifacts:
        for detail_uid, detail_record in source_records.work_details.items():
            if normalize_text(detail_record.get("work_id")) != work_id:
                continue
            written_paths.append(
                rel_path(
                    repo_root,
                    write_detail_lookup_payload(
                        lookup_dir,
                        detail_uid,
                        build_work_detail_lookup_payload(source_records, detail_uid),
                    ),
                )
            )

    return {
        "mode": "targeted-multi-record",
        "artifacts": sorted(artifacts),
        "written_count": len(written_paths),
        "written_paths": written_paths,
        "invalidation_class": invalidation_result["class"],
        "unknown_fields": list(invalidation_result.get("unknown_fields") or []),
    }


def detail_change_lookup_refresh(
    source_dir: Path,
    lookup_dir: Path,
    repo_root: Path,
    *,
    detail_uid: str,
    updated_record: Mapping[str, Any],
    invalidation_result: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = list(invalidation_result["artifacts"])
    if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD:
        source_records = records_from_json_source(source_dir)
        written_path = write_detail_lookup_payload(
            lookup_dir,
            detail_uid,
            build_work_detail_lookup_payload(source_records, detail_uid),
        )
        return {
            "mode": "single-record",
            "artifacts": ["work_detail_record"],
            "written_count": 1,
            "written_paths": [rel_path(repo_root, written_path)],
            "invalidation_class": invalidation_result["class"],
            "unknown_fields": list(invalidation_result.get("unknown_fields") or []),
        }

    if invalidation_result["class"] != invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
        return _with_invalidation(full_lookup_refresh(source_dir, lookup_dir, repo_root), invalidation_result)

    source_records = records_from_json_source(source_dir)
    written_paths: list[str] = []
    if "work_detail_record" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_detail_lookup_payload(
                    lookup_dir,
                    detail_uid,
                    build_work_detail_lookup_payload(source_records, detail_uid),
                ),
            )
        )
    if "work_detail_search" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_lookup_root_payload(
                    lookup_dir,
                    "work_detail_search.json",
                    build_work_detail_search_payload(source_records),
                ),
            )
        )
    if "related_work_records" in artifacts:
        work_id = slug_id(updated_record.get("work_id"))
        written_paths.append(
            rel_path(
                repo_root,
                write_work_lookup_payload(
                    lookup_dir,
                    work_id,
                    build_work_lookup_payload(source_records, work_id),
                ),
            )
        )
    return {
        "mode": "targeted-multi-record",
        "artifacts": sorted(artifacts),
        "written_count": len(written_paths),
        "written_paths": written_paths,
        "invalidation_class": invalidation_result["class"],
        "unknown_fields": list(invalidation_result.get("unknown_fields") or []),
    }


def series_change_lookup_refresh(
    source_dir: Path,
    lookup_dir: Path,
    repo_root: Path,
    *,
    series_id: str,
    invalidation_result: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = list(invalidation_result["artifacts"])
    if invalidation_result["class"] == invalidation.LOOKUP_INVALIDATION_SINGLE_RECORD:
        source_records = records_from_json_source(source_dir)
        written_path = write_series_lookup_payload(
            lookup_dir,
            series_id,
            build_series_lookup_payload(source_records, series_id),
        )
        return {
            "mode": "single-record",
            "artifacts": ["series_record"],
            "written_count": 1,
            "written_paths": [rel_path(repo_root, written_path)],
            "invalidation_class": invalidation_result["class"],
            "unknown_fields": list(invalidation_result.get("unknown_fields") or []),
        }

    if invalidation_result["class"] != invalidation.LOOKUP_INVALIDATION_TARGETED_MULTI_RECORD:
        return _with_invalidation(full_lookup_refresh(source_dir, lookup_dir, repo_root), invalidation_result)

    source_records = records_from_json_source(source_dir)
    written_paths: list[str] = []
    if "series_record" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_series_lookup_payload(
                    lookup_dir,
                    series_id,
                    build_series_lookup_payload(source_records, series_id),
                ),
            )
        )
    if "series_search" in artifacts:
        written_paths.append(
            rel_path(
                repo_root,
                write_lookup_root_payload(
                    lookup_dir,
                    "series_search.json",
                    build_series_search_payload(source_records),
                ),
            )
        )
    if "related_work_records" in artifacts:
        for work_id, work_record in source_records.works.items():
            series_ids = normalize_series_ids_value(work_record.get("series_ids"))
            if series_id not in series_ids:
                continue
            written_paths.append(
                rel_path(
                    repo_root,
                    write_work_lookup_payload(
                        lookup_dir,
                        work_id,
                        build_work_lookup_payload(source_records, work_id),
                    ),
                )
            )
    return {
        "mode": "targeted-multi-record",
        "artifacts": sorted(artifacts),
        "written_count": len(written_paths),
        "written_paths": written_paths,
        "invalidation_class": invalidation_result["class"],
        "unknown_fields": list(invalidation_result.get("unknown_fields") or []),
    }
