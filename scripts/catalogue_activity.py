#!/usr/bin/env python3
"""Helpers for the Studio catalogue source activity feed."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List


JOURNAL_REL_PATH = Path("var/studio/catalogue/logs/catalogue_activity.jsonl")
FEED_REL_PATH = Path("assets/studio/data/catalogue_activity.json")
JOURNAL_LIMIT = 500
FEED_LIMIT = 50
FEED_SCHEMA = "catalogue_activity_v2"


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
    if isinstance(ids, dict):
        count = int(ids.get("count") or 0)
        sample_ids = ids.get("sample_ids") if isinstance(ids.get("sample_ids"), list) else []
        truncated = int(ids.get("truncated") or 0)
        ordered = [str(item).strip() for item in sample_ids if str(item).strip()]
        return {
            "count": count,
            "sample_ids": ordered[:limit],
            "truncated": max(0, truncated),
        }
    raw_ids = ids if isinstance(ids, list) else []
    ordered = [str(item).strip() for item in raw_ids if str(item).strip()]
    return {
        "count": len(ordered),
        "sample_ids": ordered[:limit],
        "truncated": max(0, len(ordered) - limit),
    }


def _first_sample(group: Any) -> str:
    compact = _compact_ids(group, limit=1)
    sample_ids = compact.get("sample_ids") if isinstance(compact.get("sample_ids"), list) else []
    return str(sample_ids[0]).strip() if sample_ids else ""


def _source_event_label(entry: Dict[str, Any]) -> str:
    operation = str(entry.get("operation") or "").strip()
    if operation.endswith(".create"):
        return "Created"
    if operation.endswith(".save") or operation.startswith("bulk-save"):
        return "Saved"
    if operation.endswith(".delete"):
        return "Deleted"
    if operation == "moment.import":
        return "Imported"
    if operation.startswith("catalogue/import-") or entry.get("kind") == "source_import":
        return "Imported"
    if entry.get("kind") == "validation":
        return "Validation failed"
    return "Updated"


def _attention_label(entry: Dict[str, Any]) -> str:
    kind = str(entry.get("kind") or "").strip()
    status = str(entry.get("status") or "").strip()
    operation = str(entry.get("operation") or "").strip()
    if status == "failed":
        return "fix and retry"
    if operation == "moment.import":
        return "published"
    if kind in {"source_save", "source_import"}:
        return "rebuild pending"
    return "review"


def _primary_scope(entry: Dict[str, Any], affected: Dict[str, Any]) -> Dict[str, str]:
    operation = str(entry.get("operation") or "").strip()
    scope_order = [
        ("work_details", "work_detail", "work detail"),
        ("work_files", "work_file", "work file"),
        ("work_links", "work_link", "work link"),
        ("works", "work", "work"),
        ("series", "series", "series"),
        ("moments", "moment", "moment"),
    ]
    if operation.startswith("bulk-save.") or operation.startswith("catalogue/import-"):
        if operation.endswith("work-details") or "work-detail" in operation:
            return {"kind": "bulk_work_details", "label": "bulk work detail selection", "id": ""}
        return {"kind": "bulk_works", "label": "bulk work selection", "id": ""}
    for group_key, scope_kind, label_prefix in scope_order:
        scope_id = _first_sample(affected.get(group_key))
        if not scope_id:
            continue
        compact = _compact_ids(affected.get(group_key))
        count = int(compact.get("count") or 0)
        if count > 1:
            return {"kind": scope_kind, "label": f"{count} {label_prefix} records", "id": scope_id}
        return {"kind": scope_kind, "label": f"{label_prefix} {scope_id}", "id": scope_id}
    return {"kind": "", "label": "general catalogue", "id": ""}


def _build_feed_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    affected = entry.get("affected") if isinstance(entry.get("affected"), dict) else {}
    compact_affected = {
        "works": _compact_ids(affected.get("works")),
        "series": _compact_ids(affected.get("series")),
        "work_details": _compact_ids(affected.get("work_details")),
        "work_files": _compact_ids(affected.get("work_files")),
        "work_links": _compact_ids(affected.get("work_links")),
        "moments": _compact_ids(affected.get("moments")),
    }
    primary_scope = _primary_scope(entry, affected)
    return {
        "id": entry.get("id"),
        "time_utc": entry.get("time_utc"),
        "kind": entry.get("kind"),
        "operation": entry.get("operation"),
        "status": entry.get("status"),
        "summary": entry.get("summary"),
        "event_label": _source_event_label(entry),
        "attention_label": _attention_label(entry),
        "needs_attention": _attention_label(entry) not in {"published"},
        "scope_kind": primary_scope["kind"],
        "scope_label": primary_scope["label"],
        "scope_id": primary_scope["id"],
        "affected": compact_affected,
        "log_ref": entry.get("log_ref"),
    }


def append_catalogue_activity(repo_root: str | Path, entry: Dict[str, Any]) -> tuple[Path, Path]:
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    journal_path = resolved_repo_root / JOURNAL_REL_PATH
    feed_path = resolved_repo_root / FEED_REL_PATH

    normalized_entry = _coerce_json_value(entry)
    if not isinstance(normalized_entry, dict):
        raise ValueError("catalogue activity entry must normalize to an object")

    existing = _read_jsonl(journal_path)
    existing.append(normalized_entry)
    retained = existing[-JOURNAL_LIMIT:]
    journal_text = "".join(json.dumps(item, ensure_ascii=False, sort_keys=False) + "\n" for item in retained)
    _atomic_write_text(journal_path, journal_text)

    feed_entries = [
        _build_feed_entry(item)
        for item in retained
        if str(item.get("kind") or "").strip() != "build"
    ][-FEED_LIMIT:]
    feed_payload = {
        "header": {
            "schema": FEED_SCHEMA,
            "count": len(feed_entries),
        },
        "entries": list(reversed(feed_entries)),
    }
    _atomic_write_text(feed_path, json.dumps(feed_payload, ensure_ascii=False, indent=2) + "\n")
    return journal_path, feed_path
