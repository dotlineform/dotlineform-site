#!/usr/bin/env python3
"""Helpers for the unified Studio activity feed."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


ACTIVITY_CONTRACT_REL_PATH = Path("assets/studio/data/activity_contract.json")
JOURNAL_REL_PATH = Path("var/studio/activity/activity_log.jsonl")
FEED_REL_PATH = Path("assets/studio/data/activity_log.json")
JOURNAL_LIMIT = 1000
FEED_LIMIT = 100
FEED_SCHEMA = "studio_activity_log_v1"


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


def _normalize_entry(entry: Mapping[str, Any], contract: Mapping[str, Any]) -> Dict[str, Any]:
    coerced = _coerce_json_value(dict(entry))
    if not isinstance(coerced, dict):
        raise ValueError("Studio activity entry must normalize to an object")

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
        raise ValueError(f"Studio activity entry missing required fields: {', '.join(missing)}")
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
