#!/usr/bin/env python3
"""Helpers for curated local build activity feeds."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List


JOURNAL_REL_PATH = Path("var/build_activity/build_catalogue.jsonl")
FEED_REL_PATH = Path("assets/studio/data/build_activity.json")
JOURNAL_LIMIT = 500
FEED_LIMIT = 50
FEED_SCHEMA = "studio_build_activity_v1"


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
        out: Dict[str, Any] = {}
        for key, item in value.items():
            out[str(key)] = _coerce_json_value(item)
        return out
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


def _compact_id_group(ids: List[str], limit: int = 12) -> Dict[str, Any]:
    ordered = [str(item).strip() for item in ids if str(item).strip()]
    return {
        "count": len(ordered),
        "sample_ids": ordered[:limit],
        "truncated": max(0, len(ordered) - limit),
    }


def _build_feed_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    changes = entry.get("changes", {}) if isinstance(entry.get("changes"), dict) else {}
    workbook = changes.get("workbook", {}) if isinstance(changes.get("workbook"), dict) else {}
    media = changes.get("media", {}) if isinstance(changes.get("media"), dict) else {}
    actions = entry.get("actions", {}) if isinstance(entry.get("actions"), dict) else {}
    return {
        "id": entry.get("id"),
        "time_utc": entry.get("time_utc"),
        "script": entry.get("script"),
        "status": entry.get("status"),
        "dry_run": bool(entry.get("dry_run")),
        "summary": entry.get("summary"),
        "planner_mode": entry.get("planner_mode"),
        "changes": {
            "workbook": {
                "works": _compact_id_group(list(workbook.get("works", []))),
                "series": _compact_id_group(list(workbook.get("series", []))),
                "work_details": _compact_id_group(list(workbook.get("work_details", []))),
                "moments": _compact_id_group(list(workbook.get("moments", []))),
            },
            "media": {
                "work": _compact_id_group(list(media.get("work", []))),
                "work_details": _compact_id_group(list(media.get("work_details", []))),
                "moment": _compact_id_group(list(media.get("moment", []))),
            },
        },
        "actions": _coerce_json_value(actions),
        "results": _coerce_json_value(entry.get("results", {})),
    }


def append_build_activity(repo_root: str | Path, entry: Dict[str, Any]) -> tuple[Path, Path]:
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    journal_path = resolved_repo_root / JOURNAL_REL_PATH
    feed_path = resolved_repo_root / FEED_REL_PATH

    normalized_entry = _coerce_json_value(entry)
    if not isinstance(normalized_entry, dict):
        raise ValueError("build activity entry must normalize to an object")

    existing = _read_jsonl(journal_path)
    existing.append(normalized_entry)
    retained = existing[-JOURNAL_LIMIT:]
    journal_text = "".join(json.dumps(item, ensure_ascii=False, sort_keys=False) + "\n" for item in retained)
    _atomic_write_text(journal_path, journal_text)

    feed_entries = [_build_feed_entry(item) for item in retained[-FEED_LIMIT:]]
    feed_payload = {
        "header": {
            "schema": FEED_SCHEMA,
            "count": len(feed_entries),
        },
        "entries": list(reversed(feed_entries)),
    }
    _atomic_write_text(feed_path, json.dumps(feed_payload, ensure_ascii=False, indent=2) + "\n")
    return journal_path, feed_path
