#!/usr/bin/env python3
"""Assignments family behavior for Analytics tags Data Sharing."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, Mapping

from data_sharing_adapters import AdapterResolution
from tag_services import tag_assignment_service, tag_source_model, tag_write_transactions

from ..context import (
    adapter_source_path,
    attach_apply_activity,
    issue,
    load_current_assignments,
    load_series_index,
    load_works_index,
    normalize_text,
    package_metadata,
    selected_record_indices,
    selection_required,
    source_files,
)
from ..returned import ReturnedPackage


def count_assignment_works(assignments_payload: Mapping[str, Any]) -> int:
    series_obj = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    count = 0
    for row in series_obj.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works") if isinstance(row.get("works"), dict) else {}
        count += len(works)
    return count


def series_ids_from_assignments(assignments_payload: Mapping[str, Any]) -> list[str]:
    series = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    return sorted(normalize_text(key) for key in series.keys() if normalize_text(key))


def work_ids_from_assignments(assignments_payload: Mapping[str, Any]) -> list[str]:
    series = assignments_payload.get("series") if isinstance(assignments_payload.get("series"), dict) else {}
    work_ids: set[str] = set()
    for row in series.values():
        if not isinstance(row, dict):
            continue
        works = row.get("works") if isinstance(row.get("works"), dict) else {}
        for work_id in works.keys():
            text = normalize_text(work_id)
            if text:
                work_ids.add(text)
    return sorted(work_ids)


def build_package(repo_root: Path, adapter: AdapterResolution, config_id: str, generated_at_utc: str) -> tuple[Dict[str, Any], Dict[str, int], Dict[str, list[str]]]:
    assignments = load_current_assignments(repo_root, adapter)
    series = assignments.get("series") if isinstance(assignments.get("series"), dict) else {}
    series_index = load_series_index(repo_root, adapter)
    works_index = load_works_index(repo_root, adapter)
    counts = {"series": len(series), "works": count_assignment_works(assignments)}
    payload = {
        "package_metadata": package_metadata(
            adapter=adapter,
            config_id=config_id,
            family="assignments",
            generated_at_utc=generated_at_utc,
            source_paths=source_files(repo_root, adapter, "assignments"),
            counts=counts,
        ),
        "series": copy.deepcopy(series),
        "catalogue_context": {
            "series_index_header": copy.deepcopy(series_index.get("header") if isinstance(series_index.get("header"), dict) else {}),
            "works_index_header": copy.deepcopy(works_index.get("header") if isinstance(works_index.get("header"), dict) else {}),
            "series_work_membership": {
                series_id: sorted(work_ids)
                for series_id, work_ids in sorted(tag_source_model.build_series_work_membership(series_index).items())
            },
        },
    }
    return payload, counts, {"series": series_ids_from_assignments(assignments), "works": work_ids_from_assignments(assignments)}


def normalize_import_payload(import_payload: Dict[str, Any], existing_payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_series = import_payload.get("series") if isinstance(import_payload.get("series"), dict) else {}
    current_series = existing_payload.get("series") if isinstance(existing_payload.get("series"), dict) else {}
    out_series: Dict[str, Dict[str, Any]] = {}
    for raw_series_id, raw_entry in raw_series.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not isinstance(raw_entry, dict):
            out_series[series_id] = raw_entry
            continue
        if "staged_row" in raw_entry:
            out_series[series_id] = raw_entry
            continue
        out_series[series_id] = {
            "base_series_updated_at_utc": str((current_series.get(series_id) or {}).get("updated_at_utc") or ""),
            "base_row_snapshot": copy.deepcopy(current_series.get(series_id) or {"tags": []}),
            "staged_row": raw_entry,
            "staged_at_utc": normalize_text(import_payload.get("updated_at_utc")),
        }
    return {
        "version": normalize_text(import_payload.get("version")),
        "updated_at_utc": normalize_text(import_payload.get("updated_at_utc")),
        "series": out_series,
    }


def record_groups(series_id: str, staged_row: Any) -> Dict[str, list[str]]:
    groups: Dict[str, list[str]] = {"series": [series_id] if series_id else []}
    tags: list[str] = []
    works: list[str] = []
    row = staged_row if isinstance(staged_row, dict) else {}
    for item in row.get("tags", []) if isinstance(row.get("tags"), list) else []:
        if isinstance(item, dict) and normalize_text(item.get("tag_id")):
            tags.append(normalize_text(item.get("tag_id")))
    works_obj = row.get("works") if isinstance(row.get("works"), dict) else {}
    for work_id, work_row in works_obj.items():
        work_id_text = normalize_text(work_id)
        if work_id_text:
            works.append(work_id_text)
        if isinstance(work_row, dict):
            for item in work_row.get("tags", []) if isinstance(work_row.get("tags"), list) else []:
                if isinstance(item, dict) and normalize_text(item.get("tag_id")):
                    tags.append(normalize_text(item.get("tag_id")))
    if works:
        groups["works"] = sorted(set(works))
    if tags:
        groups["tags"] = sorted(set(tags))
    return groups


def rows(
    existing_payload: Dict[str, Any],
    package: ReturnedPackage,
    series_index_payload: Dict[str, Any],
) -> tuple[list[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    import_payload = normalize_import_payload(package.import_payload, existing_payload)
    session = tag_source_model.sanitize_import_assignments_session(import_payload)
    preview = tag_assignment_service.preview_assignment_import(existing_payload, session, series_index_payload)
    review_rows: list[Dict[str, Any]] = []
    for index, row in enumerate(preview.get("series", [])):
        if not isinstance(row, dict):
            continue
        series_id = normalize_text(row.get("series_id"))
        status = normalize_text(row.get("status"))
        row_issues: list[Dict[str, Any]] = []
        if status == "conflict":
            row_issues.append(issue("warning", "conflict", "current tag assignments differ from the returned package base row", index))
        if status == "missing":
            row_issues.append(issue("error", "missing_series", "series is not present in the current catalogue index", index))
        invalid_work_ids = [str(item) for item in row.get("invalid_work_ids", []) if str(item)]
        if status == "invalid":
            row_issues.append(issue("error", "invalid_work_ids", f"invalid work ids: {', '.join(invalid_work_ids)}", index))
        staged = session.get("series", {}).get(series_id, {}).get("staged_row", {})
        groups = record_groups(series_id, staged)
        review_rows.append(
            {
                "id": f"assignment:{series_id}",
                "type": "tag_assignment",
                "title": series_id,
                "meta": status or "apply",
                "record_index": index,
                "selectable": status == "apply",
                "record_groups": groups,
                "issues": row_issues,
            }
        )
    return review_rows, session, preview


def selected_session(
    session: Dict[str, Any],
    preview: Dict[str, Any],
    selected: list[int],
) -> tuple[Dict[str, Any], list[Dict[str, Any]], list[Dict[str, Any]], list[Dict[str, Any]]]:
    preview_rows = [row for row in preview.get("series", []) if isinstance(row, dict)]
    by_index = {index: row for index, row in enumerate(preview_rows)}
    selected_series: Dict[str, Any] = {}
    selected_rows: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []
    errors: list[Dict[str, Any]] = []
    for index in selected:
        row = by_index.get(index)
        if row is None:
            skipped.append({"record_index": index, "reason": "missing_record", "message": "selected record is not present in staged file"})
            continue
        series_id = normalize_text(row.get("series_id"))
        status = normalize_text(row.get("status"))
        selected_rows.append({"record_index": index, "series_id": series_id})
        if status != "apply":
            errors.append({"record_index": index, "series_id": series_id, "reason": status or "not_applicable", "message": f"selected series is not directly applicable: {status}"})
            continue
        selected_series[series_id] = copy.deepcopy(session.get("series", {}).get(series_id))
    subset = {
        "version": normalize_text(session.get("version")),
        "updated_at_utc": normalize_text(session.get("updated_at_utc")),
        "series": selected_series,
    }
    return subset, skipped, errors, selected_rows


def selected_groups(review_rows: list[Dict[str, Any]], selected: list[int]) -> Dict[str, list[str]]:
    groups: Dict[str, set[str]] = {"series": set(), "works": set(), "tags": set()}
    selected_set = set(selected)
    for row in review_rows:
        if row.get("record_index") not in selected_set:
            continue
        row_groups = row.get("record_groups") if isinstance(row.get("record_groups"), dict) else {}
        for key in groups:
            for value in row_groups.get(key, []) if isinstance(row_groups.get(key), list) else []:
                text = normalize_text(value)
                if text:
                    groups[key].add(text)
    return {key: sorted(values) for key, values in groups.items() if values}


def apply(
    repo_root: Path,
    adapter: AdapterResolution,
    package: ReturnedPackage,
    body: Dict[str, Any],
    dry_run: bool,
    now_utc: str,
) -> Dict[str, Any]:
    selected = selected_record_indices(body.get("record_indices", []))
    selection_required(selected)
    confirmed = bool(body.get("confirm"))
    existing = load_current_assignments(repo_root, adapter)
    series_index = load_series_index(repo_root, adapter)
    review_rows, session, preview = rows(existing, package, series_index)
    subset, skipped, errors, selected_rows = selected_session(session, preview, selected)
    subset_preview = tag_assignment_service.preview_assignment_import(existing, subset, series_index)
    updated_payload, apply_stats = tag_assignment_service.apply_assignment_import(
        copy.deepcopy(existing),
        subset,
        subset_preview,
        {},
        now_utc,
    )
    changed = int(apply_stats.get("applied_series") or 0) > 0
    target_path = adapter_source_path(repo_root, adapter, "tag_assignments")
    ok = not errors
    if ok and confirmed and changed and not dry_run:
        tag_write_transactions.atomic_write_many({target_path: updated_payload})
    response_preview = tag_assignment_service.build_assignment_import_preview_response(subset_preview, package.filename, now_utc)
    response_payload = tag_assignment_service.build_assignment_import_apply_response(response_preview, apply_stats)
    groups = selected_groups(review_rows, selected)
    payload: Dict[str, Any] = {
        "ok": ok,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "staged_filename": package.filename,
        "operation": "assignments_apply",
        "tag_family": "assignments",
        "confirmed": confirmed,
        "dry_run": dry_run,
        "updated_at_utc": now_utc,
        "selected_records": selected_rows,
        "skipped": skipped,
        "errors": errors,
        "warnings": [],
        "counts": {
            "selected": len(selected),
            "changed": int(changed),
            "skipped": len(skipped) + int(apply_stats.get("skipped_series") or 0),
            "errors": len(errors),
            "warnings": 0,
            **apply_stats,
        },
        "written": bool(ok and confirmed and changed and not dry_run),
        "requires_confirmation": bool(ok and changed and not confirmed),
        "review_rows": review_rows,
        "summary_text": f"{'Updated' if ok and confirmed and not dry_run else 'Validated'} tag assignment changes: {response_payload.get('summary_text')}{' without writing' if not confirmed or dry_run else ''}.",
    }
    if payload["written"]:
        attach_apply_activity(
            repo_root,
            body,
            payload,
            record_groups={**groups, "files": [package.filename]},
            detail_items=[payload["summary_text"], f"Applied series: {apply_stats.get('applied_series')}; skipped: {apply_stats.get('skipped_series')}."],
            status="completed",
        )
    return payload
