"""Catalogue lookup refresh execution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_lookup import (
    SERIES_MEMBER_WORK_FIELDS,
    SERIES_SEARCH_FIELDS,
    WORK_SEARCH_FIELDS,
    build_and_write_catalogue_lookup,
    build_series_lookup_payload,
    build_series_search_payload,
    build_work_search_payload,
    write_lookup_root_payload,
    write_series_lookup_payload,
)
from catalogue.catalogue_source import (
    normalize_series_ids_value,
    records_from_json_source,
)


LOOKUP_REFRESH_NONE = "none"
LOOKUP_REFRESH_SINGLE_RECORD = "single-record"
LOOKUP_REFRESH_TARGETED_MULTI_RECORD = "targeted-multi-record"
LOOKUP_REFRESH_FULL = "full"


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def _with_lookup_plan(result: dict[str, Any], lookup_plan: Mapping[str, Any]) -> dict[str, Any]:
    result["invalidation_class"] = lookup_plan["class"]
    result["unknown_fields"] = list(lookup_plan.get("unknown_fields") or [])
    return result


def _changed_field_set(changed_field_names: list[str]) -> set[str]:
    return {str(field).strip() for field in changed_field_names if str(field).strip()}


def _lookup_artifacts_for_fields(record_family: str, changed_fields: set[str]) -> set[str]:
    if record_family == "work":
        artifacts: set[str] = set()
        if changed_fields.intersection(WORK_SEARCH_FIELDS):
            artifacts.add("work_search")
        if changed_fields.intersection(SERIES_MEMBER_WORK_FIELDS):
            artifacts.add("related_series_records")
        return artifacts
    if record_family == "work_detail":
        return set()
    if record_family == "series":
        artifacts = {"series_record"}
        if changed_fields.intersection(SERIES_SEARCH_FIELDS):
            artifacts.add("series_search")
        return artifacts
    return set()


def derive_lookup_refresh_plan(
    *,
    record_family: str,
    changed_field_names: list[str],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    changed_fields = _changed_field_set(changed_field_names)
    registry_artifacts = {str(artifact) for artifact in build_plan.get("artifacts") or [] if str(artifact)}
    unknown_fields = list(build_plan.get("unknown_fields") or [])
    if not changed_fields or "studio-lookup" not in registry_artifacts:
        return {
            "class": LOOKUP_REFRESH_NONE,
            "mode": LOOKUP_REFRESH_NONE,
            "artifacts": [],
            "fields": sorted(changed_fields),
            "unknown_fields": unknown_fields,
        }
    if bool(build_plan.get("fallback")):
        return {
            "class": LOOKUP_REFRESH_FULL,
            "mode": LOOKUP_REFRESH_FULL,
            "artifacts": ["full_lookup_refresh"],
            "fields": sorted(changed_fields),
            "unknown_fields": unknown_fields,
        }

    artifacts = _lookup_artifacts_for_fields(record_family, changed_fields)
    if not artifacts:
        return {
            "class": LOOKUP_REFRESH_NONE,
            "mode": LOOKUP_REFRESH_NONE,
            "artifacts": [],
            "fields": sorted(changed_fields),
            "unknown_fields": unknown_fields,
        }

    mode = LOOKUP_REFRESH_SINGLE_RECORD if len(artifacts) == 1 else LOOKUP_REFRESH_TARGETED_MULTI_RECORD
    return {
        "class": mode,
        "mode": mode,
        "artifacts": sorted(artifacts),
        "fields": sorted(changed_fields),
        "unknown_fields": unknown_fields,
    }


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
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    lookup_plan: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = list(lookup_plan["artifacts"])
    if lookup_plan["class"] == LOOKUP_REFRESH_NONE:
        return {
            "mode": "none",
            "artifacts": [],
            "written_count": 0,
            "written_paths": [],
            "invalidation_class": lookup_plan["class"],
            "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
        }
    if lookup_plan["class"] == LOOKUP_REFRESH_SINGLE_RECORD:
        return _with_lookup_plan(
            work_lookup_record_refresh(source_dir, lookup_dir, repo_root, work_id),
            lookup_plan,
        )

    if lookup_plan["class"] != LOOKUP_REFRESH_TARGETED_MULTI_RECORD:
        return _with_lookup_plan(full_lookup_refresh(source_dir, lookup_dir, repo_root), lookup_plan)

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
        "invalidation_class": lookup_plan["class"],
        "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
    }


def detail_change_lookup_refresh(
    source_dir: Path,
    lookup_dir: Path,
    repo_root: Path,
    *,
    detail_uid: str,
    updated_record: Mapping[str, Any],
    lookup_plan: Mapping[str, Any],
) -> dict[str, Any]:
    if lookup_plan["class"] == LOOKUP_REFRESH_NONE:
        return {
            "mode": "none",
            "artifacts": [],
            "written_count": 0,
            "written_paths": [],
            "invalidation_class": lookup_plan["class"],
            "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
        }

    if lookup_plan["class"] != LOOKUP_REFRESH_TARGETED_MULTI_RECORD:
        return _with_lookup_plan(full_lookup_refresh(source_dir, lookup_dir, repo_root), lookup_plan)

    return {
        "mode": "none",
        "artifacts": [],
        "written_count": 0,
        "written_paths": [],
        "invalidation_class": lookup_plan["class"],
        "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
    }


def series_change_lookup_refresh(
    source_dir: Path,
    lookup_dir: Path,
    repo_root: Path,
    *,
    series_id: str,
    lookup_plan: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = list(lookup_plan["artifacts"])
    if lookup_plan["class"] == LOOKUP_REFRESH_NONE:
        return {
            "mode": "none",
            "artifacts": [],
            "written_count": 0,
            "written_paths": [],
            "invalidation_class": lookup_plan["class"],
            "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
        }
    if lookup_plan["class"] == LOOKUP_REFRESH_SINGLE_RECORD:
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
            "invalidation_class": lookup_plan["class"],
            "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
        }

    if lookup_plan["class"] != LOOKUP_REFRESH_TARGETED_MULTI_RECORD:
        return _with_lookup_plan(full_lookup_refresh(source_dir, lookup_dir, repo_root), lookup_plan)

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
        "invalidation_class": lookup_plan["class"],
        "unknown_fields": list(lookup_plan.get("unknown_fields") or []),
    }
