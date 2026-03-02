#!/usr/bin/env python3
"""Small JSONL logger for local scripts.

Log files are written to <repo-root>/logs/<script-name>.log.
Retention policy:
  - keep entries from the last 30 days
  - if none are within 30 days, keep the latest 1 day's worth (based on newest entry)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RETENTION_DAYS = 30
FALLBACK_KEEP_DAYS = 1


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_now_str() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> Optional[dt.datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _resolve_repo_root(script_path: Path, explicit_repo_root: Optional[Path]) -> Path:
    if explicit_repo_root is not None:
        repo_root = explicit_repo_root.expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise ValueError(f"repo root is missing _config.yml: {repo_root}")
        return repo_root

    script_dir = script_path.expanduser().resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("could not resolve repo root for logger")


def _coerce_detail_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_coerce_detail_value(item) for item in value]
    if isinstance(value, tuple):
        return [_coerce_detail_value(item) for item in value]
    if isinstance(value, set):
        return sorted(_coerce_detail_value(item) for item in value)
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            out[str(key)] = _coerce_detail_value(item)
        return out
    return str(value)


def _read_entries(log_path: Path) -> List[Tuple[Dict[str, Any], dt.datetime]]:
    if not log_path.exists():
        return []

    parsed: List[Tuple[Dict[str, Any], dt.datetime]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        entry_time = _parse_utc(obj.get("time_utc"))
        if entry_time is None:
            continue
        parsed.append((obj, entry_time))
    return parsed


def _apply_retention(
    entries: List[Tuple[Dict[str, Any], dt.datetime]],
    now_utc: dt.datetime,
) -> List[Dict[str, Any]]:
    if not entries:
        return []

    threshold_recent = now_utc - dt.timedelta(days=RETENTION_DAYS)
    recent = [(obj, ts) for obj, ts in entries if ts >= threshold_recent]
    if recent:
        return [obj for obj, _ in recent]

    latest_ts = max(ts for _, ts in entries)
    threshold_fallback = latest_ts - dt.timedelta(days=FALLBACK_KEEP_DAYS)
    fallback = [(obj, ts) for obj, ts in entries if ts >= threshold_fallback]
    return [obj for obj, _ in fallback]


def append_script_log(
    script_path: str | Path,
    event: str,
    details: Optional[Dict[str, Any]] = None,
    repo_root: Optional[str | Path] = None,
) -> Path:
    script = Path(script_path).expanduser().resolve()
    resolved_repo_root = _resolve_repo_root(script, Path(repo_root) if repo_root is not None else None)
    logs_dir = resolved_repo_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{script.stem}.log"

    now_utc = _utc_now()
    entry: Dict[str, Any] = {
        "time_utc": _utc_now_str(),
        "event": str(event).strip() or "event",
    }
    if details:
        entry["details"] = _coerce_detail_value(details)

    entries = _read_entries(log_path)
    entries.append((entry, now_utc))
    retained = _apply_retention(entries, now_utc)

    fd, temp_name = tempfile.mkstemp(prefix=f"{log_path.name}.", suffix=".tmp", dir=str(log_path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for item in retained:
                fh.write(json.dumps(item, ensure_ascii=False, sort_keys=False))
                fh.write("\n")
        os.replace(temp_path, log_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    return log_path
