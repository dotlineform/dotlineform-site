"""Recent-publications builders for generated catalogue artifacts."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

try:
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        normalize_text,
        parse_date,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from catalogue.catalogue_generation_common import (
        coerce_int,
        coerce_string,
        compact_json_object,
        compute_payload_version,
        normalize_text,
        parse_date,
    )


RECENT_INDEX_SCHEMA = "recent_index_v1"
RECENT_INDEX_LIMIT = 50


def normalize_recent_entry(entry: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(entry, Mapping):
        return None
    kind = normalize_text(entry.get("kind")).lower()
    if kind not in {"series", "work"}:
        return None
    target_id = normalize_text(entry.get("target_id"))
    title = coerce_string(entry.get("title"))
    caption = coerce_string(entry.get("caption"))
    published_date = parse_date(entry.get("published_date"))
    thumb_id = coerce_string(entry.get("thumb_id"))
    recorded_at_utc = coerce_string(entry.get("recorded_at_utc"))
    session_order = coerce_int(entry.get("session_order"))
    if not target_id or not title or not published_date:
        return None
    return compact_json_object({
        "id": f"{kind}:{target_id}",
        "kind": kind,
        "target_id": target_id,
        "title": title,
        "caption": caption,
        "published_date": published_date,
        "thumb_id": thumb_id,
        "recorded_at_utc": recorded_at_utc,
        "session_order": session_order,
    })


def sort_recent_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def key(entry: Dict[str, Any]) -> tuple[str, str, int, str, str]:
        return (
            str(entry.get("published_date") or ""),
            str(entry.get("recorded_at_utc") or ""),
            -(coerce_int(entry.get("session_order")) or 0),
            str(entry.get("title") or ""),
            str(entry.get("target_id") or ""),
        )

    return sorted(entries, key=key, reverse=True)


def format_series_work_count_caption(work_count: Any) -> str:
    count = int(work_count or 0)
    return f"{count} work{'s' if count != 1 else ''}"


def is_current_published_recent_target(
    entry: Mapping[str, Any],
    *,
    current_work_ids: set[str],
    current_series_ids: set[str],
    work_status_by_id: Mapping[str, str],
    series_status_by_id: Mapping[str, str],
) -> bool:
    kind = str(entry.get("kind") or "")
    target_id = str(entry.get("target_id") or "")
    if kind == "work":
        return target_id in current_work_ids and work_status_by_id.get(target_id) == "published"
    if kind == "series":
        return target_id in current_series_ids and series_status_by_id.get(target_id) == "published"
    return False


def primary_series_id_for_work(work_id: Any, *, work_meta_by_id: Mapping[str, Mapping[str, Any]]) -> str:
    work_meta = work_meta_by_id.get(str(work_id) or "", {})
    series_ids = work_meta.get("series_ids") if isinstance(work_meta, Mapping) else []
    if isinstance(series_ids, list) and series_ids:
        return str(series_ids[0] or "")
    return ""


def build_recent_publication_entries(
    *,
    existing_entries: List[Dict[str, Any]],
    series_publish_transitions: List[Dict[str, Any]],
    work_publish_transitions: List[Dict[str, Any]],
    series_payload: Mapping[str, Mapping[str, Any]],
    works_payload: Mapping[str, Mapping[str, Any]],
    work_meta_by_id: Mapping[str, Mapping[str, Any]],
    work_status_by_id: Mapping[str, str],
    series_status_by_id: Mapping[str, str],
    series_sort_by_series_id: Mapping[str, Mapping[str, str]],
    series_title_by_id: Mapping[str, str],
    recorded_at_utc: str,
) -> List[Dict[str, Any]]:
    current_work_ids = set(works_payload.keys())
    current_series_ids = set(series_payload.keys())
    retained_recent_entries = [
        entry
        for entry in existing_entries
        if is_current_published_recent_target(
            entry,
            current_work_ids=current_work_ids,
            current_series_ids=current_series_ids,
            work_status_by_id=work_status_by_id,
            series_status_by_id=series_status_by_id,
        )
    ]
    newly_published_series_ids = {
        str(entry.get("series_id") or "")
        for entry in series_publish_transitions
        if str(entry.get("series_id") or "")
    }

    existing_by_id = {
        str(entry.get("id") or f"{entry.get('kind')}:{entry.get('target_id')}"): entry
        for entry in retained_recent_entries
    }

    def refresh_series_recent_entry(
        series_id: str,
        published_date: Any,
        session_order_value: int,
        recorded_at_utc_value: Optional[str] = None,
    ) -> bool:
        if not series_id:
            return False
        series_entry = existing_by_id.get(f"series:{series_id}")
        series_record = series_payload.get(series_id, {})
        if not isinstance(series_record, Mapping) or not series_entry:
            return False
        refreshed = normalize_recent_entry({
            "kind": "series",
            "target_id": series_id,
            "title": coerce_string(series_record.get("title")) or series_id,
            "caption": format_series_work_count_caption(len(series_record.get("works") or [])),
            "published_date": published_date or series_entry.get("published_date"),
            "thumb_id": coerce_string(series_record.get("primary_work_id")) or coerce_string(series_entry.get("thumb_id")),
            "recorded_at_utc": recorded_at_utc_value or recorded_at_utc,
            "session_order": session_order_value,
        })
        if refreshed is None:
            return False
        existing_by_id[str(refreshed.get("id") or "")] = refreshed
        return True

    session_order = 0
    for entry in series_publish_transitions:
        series_id = str(entry.get("series_id") or "")
        if not series_id:
            continue
        session_order += 1
        normalized = normalize_recent_entry({
            "kind": "series",
            "target_id": series_id,
            "title": coerce_string(entry.get("title")) or series_id,
            "caption": format_series_work_count_caption(entry.get("work_count")),
            "published_date": entry.get("published_date"),
            "thumb_id": coerce_string(entry.get("primary_work_id")),
            "recorded_at_utc": recorded_at_utc,
            "session_order": session_order,
        })
        if normalized is not None:
            existing_by_id[str(normalized.get("id") or "")] = normalized

    def latest_series_recent_entry() -> Optional[Dict[str, Any]]:
        series_entries = [
            entry for entry in existing_by_id.values()
            if str(entry.get("kind") or "") == "series"
        ]
        if not series_entries:
            return None
        return sort_recent_entries(series_entries)[0]

    latest_series_entry = latest_series_recent_entry()
    latest_series_id = str(latest_series_entry.get("target_id") or "") if latest_series_entry else ""
    if latest_series_id:
        latest_series_work_entries = [
            entry for entry in existing_by_id.values()
            if (
                str(entry.get("kind") or "") == "work"
                and primary_series_id_for_work(entry.get("target_id"), work_meta_by_id=work_meta_by_id) == latest_series_id
            )
        ]
        if latest_series_work_entries:
            newest_absorbed_entry = sort_recent_entries(
                [existing_by_id.get(f"series:{latest_series_id}", latest_series_entry)] + latest_series_work_entries
            )[0]
            refresh_series_recent_entry(
                latest_series_id,
                newest_absorbed_entry.get("published_date"),
                coerce_int(newest_absorbed_entry.get("session_order")) or 1,
                coerce_string(newest_absorbed_entry.get("recorded_at_utc")),
            )
            for work_entry in latest_series_work_entries:
                existing_by_id.pop(str(work_entry.get("id") or ""), None)

    grouped_work_transitions: Dict[str, List[Dict[str, Any]]] = {}
    for entry in work_publish_transitions:
        primary_series_id = str(entry.get("primary_series_id") or "")
        if not primary_series_id or primary_series_id in newly_published_series_ids:
            continue
        grouped_work_transitions.setdefault(primary_series_id, []).append(entry)

    for series_id, entries in sorted(grouped_work_transitions.items()):
        entries_sorted = sorted(
            entries,
            key=lambda item: (
                str(series_sort_by_series_id.get(series_id, {}).get(str(item.get("work_id") or ""), str(item.get("work_id") or ""))),
                str(item.get("work_id") or ""),
            ),
        )
        first_entry = entries_sorted[0] if entries_sorted else {}
        if not first_entry:
            continue
        new_work_count = len(entries_sorted)
        series_title = coerce_string(first_entry.get("series_title")) or series_title_by_id.get(series_id) or series_id
        caption = series_title if new_work_count == 1 else f"{new_work_count} new works in {series_title}"
        if latest_series_id and series_id == latest_series_id:
            session_order += 1
            refresh_series_recent_entry(
                series_id,
                first_entry.get("published_date"),
                session_order,
            )
            for existing_id, existing_entry in list(existing_by_id.items()):
                if (
                    str(existing_entry.get("kind") or "") == "work"
                    and primary_series_id_for_work(existing_entry.get("target_id"), work_meta_by_id=work_meta_by_id) == series_id
                ):
                    existing_by_id.pop(existing_id, None)
            continue
        session_order += 1
        normalized = normalize_recent_entry({
            "kind": "work",
            "target_id": str(first_entry.get("work_id") or ""),
            "title": coerce_string(first_entry.get("title")) or str(first_entry.get("work_id") or ""),
            "caption": caption,
            "published_date": first_entry.get("published_date"),
            "thumb_id": str(first_entry.get("work_id") or ""),
            "recorded_at_utc": recorded_at_utc,
            "session_order": session_order,
        })
        if normalized is not None:
            existing_by_id[str(normalized.get("id") or "")] = normalized

    return [
        entry
        for entry in existing_by_id.values()
        if is_current_published_recent_target(
            entry,
            current_work_ids=current_work_ids,
            current_series_ids=current_series_ids,
            work_status_by_id=work_status_by_id,
            series_status_by_id=series_status_by_id,
        )
    ]


def build_recent_index_payload(
    *,
    entries: List[Dict[str, Any]],
    generated_at_utc: str,
    limit: int = RECENT_INDEX_LIMIT,
) -> Dict[str, Any]:
    sorted_entries = sort_recent_entries(entries)[:limit]
    version_payload = compact_json_object({
        "schema": RECENT_INDEX_SCHEMA,
        "entries": sorted_entries,
    })
    version = compute_payload_version(version_payload)
    return compact_json_object({
        "header": {
            "schema": RECENT_INDEX_SCHEMA,
            "version": version,
            "generated_at_utc": generated_at_utc,
            "count": len(sorted_entries),
        },
        "entries": sorted_entries,
    })
