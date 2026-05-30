"""Tag assignment save and import planners."""

from __future__ import annotations

import copy
from typing import Any, Dict

from tag_services import tag_source_model as tag_source


def ensure_assignment_series_row(payload: Dict[str, Any], series_id: str) -> Dict[str, Any]:
    if not isinstance(payload.get("series"), dict):
        payload["series"] = {}
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = "tag_assignments_v1"

    series_obj = payload["series"]
    row = series_obj.get(series_id)
    if not isinstance(row, dict):
        row = {}
        series_obj[series_id] = row
    return row


def apply_assignment_update(payload: Dict[str, Any], series_id: str, tags: list[Dict[str, Any]], now_utc: str) -> Dict[str, Any]:
    row = ensure_assignment_series_row(payload, series_id)

    row["tags"] = list(tags)
    row["updated_at_utc"] = now_utc
    payload["updated_at_utc"] = now_utc
    return payload


def apply_work_assignment_update(
    payload: Dict[str, Any],
    series_id: str,
    work_id: str,
    tags: list[Dict[str, Any]],
    keep_work: bool,
    now_utc: str,
) -> tuple[Dict[str, Any], bool]:
    row = ensure_assignment_series_row(payload, series_id)
    series_tags = tag_source.sanitize_assignment_tags(row.get("tags", []), f"series[{series_id}].tags", strict=False)
    series_tag_ids = {item["tag_id"] for item in series_tags}
    sanitized_tags = [item for item in tags if item["tag_id"] not in series_tag_ids]

    works_obj = row.get("works")
    if not isinstance(works_obj, dict):
        works_obj = {}
        row["works"] = works_obj

    deleted = False
    if keep_work or sanitized_tags:
        works_obj[work_id] = {
            "tags": list(sanitized_tags),
            "updated_at_utc": now_utc,
        }
    else:
        if work_id in works_obj:
            deleted = True
            del works_obj[work_id]
        if not works_obj:
            row.pop("works", None)

    row["updated_at_utc"] = now_utc
    payload["updated_at_utc"] = now_utc
    return payload, deleted


def plan_assignment_save(
    existing_payload: Dict[str, Any],
    series_id: Any,
    work_id: Any,
    keep_work: Any,
    tags: Any,
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    if not isinstance(series_id, str) or not series_id or not tag_source.SLUG_RE.fullmatch(series_id):
        raise ValueError("series_id must be a non-empty slug-safe string")

    sanitized_tags = tag_source.sanitize_assignment_tags(tags, "tags", strict=True)
    if work_id is None:
        updated_payload = apply_assignment_update(existing_payload, series_id, sanitized_tags, now_utc)
        deleted = False
        persisted_tags = sanitized_tags
    else:
        if not isinstance(work_id, str) or not tag_source.WORK_ID_RE.fullmatch(work_id):
            raise ValueError("work_id must be a 5-digit string")
        if keep_work is None:
            keep_work = False
        if not isinstance(keep_work, bool):
            raise ValueError("keep_work must be a boolean when work_id is provided")
        updated_payload, deleted = apply_work_assignment_update(existing_payload, series_id, work_id, sanitized_tags, keep_work, now_utc)
        persisted_tags = tag_source.sanitize_assignment_tags(
            updated_payload["series"][series_id].get("works", {}).get(work_id, {}).get("tags", []),
            "tags",
            strict=False,
        )

    response_payload: Dict[str, Any] = {
        "ok": True,
        "series_id": series_id,
        "work_id": work_id,
        "keep_work": keep_work,
        "updated_at_utc": now_utc,
        "tag_count": len(persisted_tags),
    }
    if work_id is not None:
        response_payload["deleted"] = deleted

    would_write = {
        "series_id": series_id,
        "work_id": work_id,
        "keep_work": keep_work,
        "tags": sanitized_tags,
        "updated_at_utc": now_utc,
        "deleted": deleted,
    }
    return updated_payload, response_payload, would_write


def preview_assignment_import(
    existing_payload: Dict[str, Any],
    import_session: Dict[str, Any],
    series_index_payload: Dict[str, Any],
) -> Dict[str, Any]:
    current_series = existing_payload.get("series") if isinstance(existing_payload.get("series"), dict) else {}
    valid_series = tag_source.build_series_work_membership(series_index_payload)
    preview_rows: list[Dict[str, Any]] = []
    applicable_count = 0
    conflict_count = 0
    invalid_count = 0
    missing_count = 0

    for series_id in sorted(import_session.get("series", {}).keys()):
        entry = import_session["series"][series_id]
        staged_row = tag_source.normalize_assignment_series_row_for_compare(entry.get("staged_row"))
        base_row = tag_source.normalize_assignment_series_row_for_compare(entry.get("base_row_snapshot"))
        current_row = tag_source.normalize_assignment_series_row_for_compare(current_series.get(series_id))

        row_preview: Dict[str, Any] = {
            "series_id": series_id,
            "base_series_updated_at_utc": str(entry.get("base_series_updated_at_utc") or ""),
            "current_series_updated_at_utc": str((current_series.get(series_id) or {}).get("updated_at_utc") or ""),
            "status": "apply",
            "resolution_required": False,
            "invalid_work_ids": [],
        }

        if series_id not in valid_series:
            row_preview["status"] = "missing"
            row_preview["resolution_required"] = False
            missing_count += 1
            preview_rows.append(row_preview)
            continue

        invalid_work_ids = sorted(
            work_id
            for work_id in (staged_row.get("works") or {}).keys()
            if work_id not in valid_series.get(series_id, set())
        )
        if invalid_work_ids:
            row_preview["status"] = "invalid"
            row_preview["invalid_work_ids"] = invalid_work_ids
            invalid_count += 1
            preview_rows.append(row_preview)
            continue

        if not tag_source.assignment_series_rows_equal(current_row, base_row):
            row_preview["status"] = "conflict"
            row_preview["resolution_required"] = True
            conflict_count += 1
        else:
            applicable_count += 1

        preview_rows.append(row_preview)

    return {
        "series": preview_rows,
        "applicable_count": applicable_count,
        "conflict_count": conflict_count,
        "invalid_count": invalid_count,
        "missing_count": missing_count,
        "staged_series_count": len(preview_rows),
    }


def build_assignment_import_preview_summary(preview_payload: Dict[str, Any]) -> str:
    return (
        f"assignment import preview; staged {preview_payload['staged_series_count']}; "
        f"apply {preview_payload['applicable_count']}; conflict {preview_payload['conflict_count']}; "
        f"invalid {preview_payload['invalid_count']}; missing {preview_payload['missing_count']}"
    )


def build_assignment_import_apply_summary(apply_stats: Dict[str, Any]) -> str:
    return (
        f"assignment import apply; staged {apply_stats['staged_series_count']}; "
        f"applied {apply_stats['applied_series']}; skipped {apply_stats['skipped_series']}; "
        f"overwritten {apply_stats['overwritten_series']}; conflicts {apply_stats['conflict_count']}; "
        f"invalid {apply_stats['invalid_count']}; missing {apply_stats['missing_count']}"
    )


def build_assignment_import_preview_response(
    preview_payload: Dict[str, Any],
    import_filename: str,
    now_utc: str,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": build_assignment_import_preview_summary(preview_payload),
        "import_filename": import_filename,
        **preview_payload,
    }


def apply_assignment_import(
    existing_payload: Dict[str, Any],
    import_session: Dict[str, Any],
    preview: Dict[str, Any],
    resolutions: Dict[str, str],
    now_utc: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    updated_payload = copy.deepcopy(existing_payload)
    if not isinstance(updated_payload.get("series"), dict):
        updated_payload["series"] = {}

    applied_series = 0
    skipped_series = 0
    overwritten_series = 0

    preview_by_series = {
        str(row.get("series_id") or ""): row
        for row in preview.get("series", [])
        if isinstance(row, dict)
    }

    for series_id in sorted(import_session.get("series", {}).keys()):
        row_preview = preview_by_series.get(series_id) or {}
        status = str(row_preview.get("status") or "")
        if status in {"invalid", "missing"}:
            skipped_series += 1
            continue

        resolution = str(resolutions.get(series_id) or "").strip().lower()
        if status == "conflict":
            if resolution == "skip":
                skipped_series += 1
                continue
            if resolution != "overwrite":
                raise ValueError(f"resolution required for conflicted series: {series_id}")
            overwritten_series += 1

        staged_row = tag_source.normalize_assignment_series_row_for_compare(import_session["series"][series_id].get("staged_row"))
        series_row = ensure_assignment_series_row(updated_payload, series_id)
        series_row["tags"] = staged_row.get("tags", [])
        works = staged_row.get("works") if isinstance(staged_row.get("works"), dict) else {}
        if works:
            works_out: Dict[str, Any] = {}
            for work_id, work_row in works.items():
                works_out[work_id] = {
                    "tags": list(work_row.get("tags", [])),
                    "updated_at_utc": now_utc,
                }
            series_row["works"] = works_out
        else:
            series_row.pop("works", None)
        series_row["updated_at_utc"] = now_utc
        applied_series += 1

    updated_payload["updated_at_utc"] = now_utc
    stats = {
        "applied_series": applied_series,
        "skipped_series": skipped_series,
        "overwritten_series": overwritten_series,
        "conflict_count": int(preview.get("conflict_count") or 0),
        "invalid_count": int(preview.get("invalid_count") or 0),
        "missing_count": int(preview.get("missing_count") or 0),
        "staged_series_count": int(preview.get("staged_series_count") or 0),
    }
    return updated_payload, stats


def build_assignment_import_apply_response(
    preview_response_payload: Dict[str, Any],
    apply_stats: Dict[str, Any],
) -> Dict[str, Any]:
    response_payload = dict(preview_response_payload)
    response_payload["summary_text"] = build_assignment_import_apply_summary(apply_stats)
    response_payload.update(apply_stats)
    return response_payload
