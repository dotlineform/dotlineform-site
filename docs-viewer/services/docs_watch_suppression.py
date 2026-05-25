#!/usr/bin/env python3
"""
Coordinate short-lived watcher suppressions for docs-management writes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


SUPPRESSIONS_REL_DIR = Path("var/docs/watch-suppressions")
SUPPRESSION_PENDING = "pending"
SUPPRESSION_COMPLETE = "complete"
DEFAULT_PENDING_TTL_SECONDS = 300
DEFAULT_COMPLETE_TTL_SECONDS = 30


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def isoformat_utc(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(value: str) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def suppressions_dir(repo_root: Path) -> Path:
    return repo_root / SUPPRESSIONS_REL_DIR


def suppression_path(repo_root: Path, scope: str, filename: str) -> Path:
    digest = hashlib.sha1(f"{scope}|{filename}".encode("utf-8")).hexdigest()
    return suppressions_dir(repo_root) / f"{scope}-{digest}.json"


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def set_watch_suppressions(
    repo_root: Path,
    scope: str,
    filenames: list[str],
    *,
    status: str,
    reason: str,
    ttl_seconds: int,
) -> None:
    now = utc_now()
    expires_at = now + dt.timedelta(seconds=max(1, int(ttl_seconds)))
    for filename in sorted({str(name or "").strip() for name in filenames if str(name or "").strip()}):
        payload = {
            "scope": scope,
            "filename": filename,
            "status": status,
            "reason": reason,
            "written_at": isoformat_utc(now),
            "expires_at": isoformat_utc(expires_at),
        }
        write_json_atomic(suppression_path(repo_root, scope, filename), payload)


def clear_watch_suppressions(repo_root: Path, scope: str, filenames: list[str]) -> None:
    for filename in sorted({str(name or "").strip() for name in filenames if str(name or "").strip()}):
        path = suppression_path(repo_root, scope, filename)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def load_active_watch_suppressions(repo_root: Path, scope: str) -> Dict[str, Dict[str, Any]]:
    root = suppressions_dir(repo_root)
    if not root.exists():
        return {}

    now = utc_now()
    active: Dict[str, Dict[str, Any]] = {}
    prefix = f"{scope}-"
    for path in sorted(root.glob(f"{prefix}*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(payload.get("scope") or "").strip() != scope:
            continue
        filename = str(payload.get("filename") or "").strip()
        expires_at = parse_utc(str(payload.get("expires_at") or ""))
        if not filename or expires_at is None or expires_at <= now:
            try:
                path.unlink()
            except OSError:
                pass
            continue
        payload["_path"] = str(path)
        active[filename] = payload
    return active
