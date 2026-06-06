#!/usr/bin/env python3
"""Helpers for the unified Admin activity feed."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


ACTIVITY_CONTRACT_REL_PATH = Path("studio/data/config/runtime/activity-contract.json")
JOURNAL_REL_PATH = Path("var/admin/activity/activity_log.jsonl")
FEED_REL_PATH = Path("var/admin/activity/activity_log.json")
JOURNAL_LIMIT = 1000
FEED_LIMIT = 100
FEED_SCHEMA = "admin_activity_log_v1"
ACTIVITY_ID_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9_.:-]+")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _coerce_json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, set):
        return [_coerce_json_value(item) for item in sorted(value)]
    if isinstance(value, dict):
        return {str(key): _coerce_json_value(item) for key, item in value.items()}
    return str(value)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def activity_context_value(value: Any) -> str:
    return str(value or "").strip()


def activity_id_component(value: Any) -> str:
    text = activity_context_value(value)
    safe_value = ACTIVITY_ID_SAFE_PATTERN.sub("-", text).strip("-")
    return safe_value or "activity"


def studio_activity_id(now_utc: str, correlation_id: str, script_purpose_id: str) -> str:
    return f"{now_utc}-{activity_id_component(correlation_id)}-{activity_id_component(script_purpose_id)}"


def activity_correlation_id(value: Any) -> str:
    requested = activity_context_value(value)
    if requested:
        return requested
    return f"activity:{utc_now()}:{os.getpid()}"


def _contract_action(contract: Mapping[str, Any], page_id: str, action_id: str) -> Mapping[str, Any]:
    pages = contract.get("pages") if isinstance(contract.get("pages"), Mapping) else {}
    page = pages.get(page_id) if isinstance(pages, Mapping) else None
    if not isinstance(page, Mapping):
        raise ValueError(f"activity_context.page_id is not covered by the activity contract: {page_id}")
    actions = page.get("actions") if isinstance(page.get("actions"), Mapping) else {}
    action = actions.get(action_id) if isinstance(actions, Mapping) else None
    if not isinstance(action, Mapping):
        raise ValueError(f"activity_context.action_id is not covered by the activity contract: {action_id}")
    return action


def normalize_activity_context_from_contract(
    repo_root: str | Path,
    raw_context: Any,
    *,
    endpoint: str = "",
    record_id: Any = None,
    record_id_field: str = "",
) -> Dict[str, str]:
    if raw_context is None or raw_context == "":
        return {}
    if not isinstance(raw_context, Mapping):
        raise ValueError("activity_context must be an object")

    resolved_repo_root = Path(repo_root).expanduser().resolve()
    contract = _read_json(resolved_repo_root / ACTIVITY_CONTRACT_REL_PATH)
    page_id = activity_context_value(raw_context.get("page_id"))
    action_id = activity_context_value(raw_context.get("action_id"))
    action = _contract_action(contract, page_id, action_id)

    expected_endpoint = activity_context_value(action.get("endpoint"))
    if endpoint and expected_endpoint and endpoint != expected_endpoint:
        raise ValueError(f"activity_context.action_id {action_id!r} is not valid for endpoint {endpoint}")

    expected_values = {
        "route": activity_context_value(action.get("route") or _contract_page_route(contract, page_id)),
        "control_id": activity_context_value(action.get("control_id")),
        "control_selector": activity_context_value(action.get("control_selector")),
    }
    for key, expected in expected_values.items():
        if not expected:
            continue
        value = activity_context_value(raw_context.get(key))
        if value != expected:
            raise ValueError(f"activity_context.{key} must be {expected!r}")

    resolved_record_id_field = record_id_field or activity_context_value(action.get("record_id_field"))
    resolved_record_id = activity_context_value(record_id)
    requested_record_id = activity_context_value(raw_context.get(resolved_record_id_field)) if resolved_record_id_field else ""
    if resolved_record_id and requested_record_id != resolved_record_id:
        raise ValueError(f"activity_context.{resolved_record_id_field} must match request {resolved_record_id_field}")

    context = {
        "correlation_id": activity_correlation_id(raw_context.get("correlation_id")),
        "page_id": page_id,
        "action_id": action_id,
        "route": expected_values["route"],
        "control_id": expected_values["control_id"],
    }
    if expected_values["control_selector"]:
        context["control_selector"] = expected_values["control_selector"]
    if resolved_record_id_field:
        context[resolved_record_id_field] = requested_record_id or resolved_record_id
    return context


def _contract_page_route(contract: Mapping[str, Any], page_id: str) -> str:
    pages = contract.get("pages") if isinstance(contract.get("pages"), Mapping) else {}
    page = pages.get(page_id) if isinstance(pages, Mapping) else None
    return activity_context_value(page.get("route")) if isinstance(page, Mapping) else ""


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _compact_ids(ids: Any, limit: int = 12) -> Dict[str, Any]:
    raw_ids = ids if isinstance(ids, list) else []
    ordered = [str(item).strip() for item in raw_ids if str(item).strip()]
    return {
        "count": len(ordered),
        "sample_ids": ordered[:limit],
        "truncated": max(0, len(ordered) - limit),
    }


def _compact_record_groups(groups: Any) -> Dict[str, Any]:
    raw_groups = groups if isinstance(groups, Mapping) else {}
    return {
        "works": _compact_ids(raw_groups.get("works")),
        "series": _compact_ids(raw_groups.get("series")),
        "work_details": _compact_ids(raw_groups.get("work_details")),
        "moments": _compact_ids(raw_groups.get("moments")),
        "docs": _compact_ids(raw_groups.get("docs")),
        "files": _compact_ids(raw_groups.get("files")),
        "tags": _compact_ids(raw_groups.get("tags")),
        "aliases": _compact_ids(raw_groups.get("aliases")),
        "search": _compact_ids(raw_groups.get("search")),
    }


def _contract_labels(contract: Mapping[str, Any], entry: Mapping[str, Any]) -> Dict[str, str]:
    page_id = str(entry.get("page_id") or "").strip()
    action_id = str(entry.get("user_action_id") or entry.get("action_id") or "").strip()
    purpose_id = str(entry.get("script_purpose_id") or "").strip()
    pages = contract.get("pages") if isinstance(contract.get("pages"), Mapping) else {}
    page = pages.get(page_id) if isinstance(pages, Mapping) else {}
    actions = page.get("actions") if isinstance(page, Mapping) and isinstance(page.get("actions"), Mapping) else {}
    action = actions.get(action_id) if isinstance(actions, Mapping) else {}
    purposes = contract.get("script_purposes") if isinstance(contract.get("script_purposes"), Mapping) else {}
    purpose = purposes.get(purpose_id) if isinstance(purposes, Mapping) else {}
    return {
        "page_label": str(page.get("label") or entry.get("page_label") or page_id).strip(),
        "user_action_label": str(action.get("label") or entry.get("user_action_label") or action_id).strip(),
        "script_purpose_label": str(purpose.get("label") or entry.get("script_purpose_label") or purpose_id).strip(),
    }


def _normalize_detail_items(items: Any) -> list[str]:
    raw_items = items if isinstance(items, list) else []
    return [str(item).strip() for item in raw_items if str(item).strip()]


def _normalize_source_refs(refs: Any) -> list[Dict[str, str]]:
    raw_refs = refs if isinstance(refs, list) else []
    normalized: list[Dict[str, str]] = []
    for ref in raw_refs:
        if not isinstance(ref, Mapping):
            continue
        kind = str(ref.get("kind") or "").strip()
        path = str(ref.get("path") or "").strip()
        if kind and path:
            normalized.append({"kind": kind, "path": path})
    return normalized


def studio_activity_entry(
    activity_context: Mapping[str, str],
    *,
    script_purpose_id: str,
    now_utc: str = "",
    status: str = "completed",
    record_groups: Mapping[str, Any] | None = None,
    detail_items: Iterable[Any] | None = None,
    source_refs: Iterable[Mapping[str, Any]] | None = None,
    activity_id_suffix: Any = "",
) -> Dict[str, Any]:
    resolved_now = activity_context_value(now_utc) or utc_now()
    correlation_id = activity_context_value(activity_context.get("correlation_id"))
    resolved_purpose = activity_context_value(script_purpose_id)
    row_id = studio_activity_id(resolved_now, correlation_id, resolved_purpose)
    suffix = activity_context_value(activity_id_suffix)
    if suffix:
        row_id = f"{row_id}-{activity_id_component(suffix)}"
    return {
        "id": row_id,
        "activity_id": row_id,
        "correlation_id": correlation_id,
        "timestamp": resolved_now,
        "time_utc": resolved_now,
        "status": activity_context_value(status) or "completed",
        "page_id": activity_context_value(activity_context.get("page_id")),
        "user_action_id": activity_context_value(activity_context.get("action_id")),
        "script_purpose_id": resolved_purpose,
        "record_groups": dict(record_groups or {}),
        "detail_items": [activity_context_value(item) for item in (detail_items or []) if activity_context_value(item)],
        "source_refs": [dict(ref) for ref in (source_refs or []) if isinstance(ref, Mapping)],
    }


def _normalize_entry(entry: Mapping[str, Any], contract: Mapping[str, Any]) -> Dict[str, Any]:
    coerced = _coerce_json_value(dict(entry))
    if not isinstance(coerced, dict):
        raise ValueError("Admin activity entry must normalize to an object")

    labels = _contract_labels(contract, coerced)
    action_id = str(coerced.get("user_action_id") or coerced.get("action_id") or "").strip()
    normalized: Dict[str, Any] = {
        "id": str(coerced.get("id") or coerced.get("activity_id") or "").strip(),
        "activity_id": str(coerced.get("activity_id") or coerced.get("id") or "").strip(),
        "correlation_id": str(coerced.get("correlation_id") or "").strip(),
        "timestamp": str(coerced.get("timestamp") or coerced.get("time_utc") or "").strip(),
        "time_utc": str(coerced.get("time_utc") or coerced.get("timestamp") or "").strip(),
        "status": str(coerced.get("status") or "completed").strip(),
        "page_id": str(coerced.get("page_id") or "").strip(),
        "page_label": labels["page_label"],
        "user_action_id": action_id,
        "user_action_label": labels["user_action_label"],
        "script_purpose_id": str(coerced.get("script_purpose_id") or "").strip(),
        "script_purpose_label": labels["script_purpose_label"],
        "record_groups": _compact_record_groups(coerced.get("record_groups")),
        "detail_items": _normalize_detail_items(coerced.get("detail_items")),
        "source_refs": _normalize_source_refs(coerced.get("source_refs")),
    }
    missing = [key for key in ("id", "correlation_id", "timestamp", "page_id", "user_action_id", "script_purpose_id") if not normalized.get(key)]
    if missing:
        raise ValueError(f"Admin activity entry missing required fields: {', '.join(missing)}")
    return normalized


def append_studio_activity(repo_root: str | Path, entries: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> tuple[Path, Path]:
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    journal_path = resolved_repo_root / JOURNAL_REL_PATH
    feed_path = resolved_repo_root / FEED_REL_PATH
    contract = _read_json(resolved_repo_root / ACTIVITY_CONTRACT_REL_PATH)

    raw_entries: Iterable[Mapping[str, Any]]
    if isinstance(entries, Mapping):
        raw_entries = [entries]
    else:
        raw_entries = entries
    normalized_entries = [_normalize_entry(entry, contract) for entry in raw_entries]
    if not normalized_entries:
        return journal_path, feed_path

    existing = _read_jsonl(journal_path)
    retained = [*existing, *normalized_entries][-JOURNAL_LIMIT:]
    journal_text = "".join(json.dumps(item, ensure_ascii=False, sort_keys=False) + "\n" for item in retained)
    _atomic_write_text(journal_path, journal_text)

    feed_entries = retained[-FEED_LIMIT:]
    feed_payload = {
        "header": {
            "schema": FEED_SCHEMA,
            "count": len(feed_entries),
        },
        "entries": list(reversed(feed_entries)),
    }
    _atomic_write_text(feed_path, json.dumps(feed_payload, ensure_ascii=False, indent=2) + "\n")
    return journal_path, feed_path
