"""Tag assignment save planners."""

from __future__ import annotations

from typing import Any, Dict

from tags import tag_source_model as tag_source


def ensure_assignment_series_row(payload: Dict[str, Any], series_id: str) -> Dict[str, Any]:
    if not isinstance(payload.get("series"), dict):
        payload["series"] = {}
    if "tag_assignments_version" not in payload:
        payload["tag_assignments_version"] = tag_source.TAG_ASSIGNMENTS_VERSION

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
