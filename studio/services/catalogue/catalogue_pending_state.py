"""Strict private Catalogue queues under the configured Working owner."""

from __future__ import annotations

import json
import datetime as dt
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from studio.services.catalogue.catalogue_output_paths import catalogue_workspace_config
from studio.services.catalogue.catalogue_work_attachments import safe_download_filename
from studio.services.catalogue.catalogue_shared_changes import SHARED_FIELDS, REFRESH_FIELDS, shared_changes, validate_shared_changes


WORK_ID = re.compile(r"[0-9]{5}\Z")


def pending_path(repo_root: Path, filename: str) -> Path:
    """Resolve existing Working storage; queue creation belongs only to cutover."""
    workspace = catalogue_workspace_config(repo_root)
    root = workspace.workspace_root.path / "working"
    if root.is_symlink() or not root.is_dir():
        raise FileNotFoundError("Working Catalogue queue directory is unavailable")
    path = root / filename
    if path.is_symlink():
        raise ValueError("Catalogue queue must not be a symlink")
    return path


def validate_pending_state(repo_root: Path, value: Any, *, schema: str, progress: str) -> dict[str, Any]:
    """Validate headers, exact Work records and shared family/output selections."""
    publishing = progress == "preview_done"
    selection_fields = SHARED_FIELDS if publishing else REFRESH_FIELDS
    if not isinstance(value, dict) or set(value) != {"header", "current_works", "deleted_works", *selection_fields}:
        raise ValueError(f"Catalogue queue requires {schema}")
    header = value["header"]
    timestamp_field = "last_refreshed_at_utc" if progress == "refreshed" else "last_published_at_utc"
    header_fields = {"schema", timestamp_field}
    if not isinstance(header, dict) or set(header) != header_fields or header["schema"] != schema:
        raise ValueError(f"Catalogue queue header requires {schema}")
    timestamp = header[timestamp_field]
    if timestamp is not None:
        if not isinstance(timestamp, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", timestamp):
            raise ValueError(f"Catalogue {timestamp_field} must be null or a UTC timestamp")
        dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    for family in ("current_works", "deleted_works"):
        entries = value[family]
        if not isinstance(entries, dict):
            raise ValueError(f"Catalogue queue {family} must be an object")
        fields = {"image", "file_names", progress} | ({"metadata"} if family == "current_works" else set())
        for work_id, entry in entries.items():
            if not isinstance(work_id, str) or not WORK_ID.fullmatch(work_id):
                raise ValueError("Catalogue queue requires exact five-digit Work IDs")
            if not isinstance(entry, dict) or set(entry) != fields:
                raise ValueError(f"Work {work_id}: invalid Catalogue queue fields")
            if any(type(entry[field]) is not bool for field in fields - {"file_names"}):
                raise ValueError(f"Work {work_id}: Catalogue queue flags must be booleans")
            names = entry["file_names"]
            if not isinstance(names, list):
                raise ValueError(f"Work {work_id}: file_names must be an array")
            for name in names:
                safe_download_filename(name)
            if names != sorted(set(names)):
                raise ValueError(f"Work {work_id}: file_names must be sorted and distinct")
    if value["current_works"].keys() & value["deleted_works"].keys():
        raise ValueError("A queued Work cannot be both current and deleted")
    validate_shared_changes(repo_root, shared_changes(value, publishing=publishing), publishing=publishing)
    if not publishing and set(value["gallery_member_works"]) - (value["current_works"].keys() | value["deleted_works"].keys()):
        raise ValueError("Gallery member candidates require a retained queued Work")
    return value


def read_pending_state(repo_root: Path, filename: str, *, schema: str, progress: str) -> dict[str, Any]:
    """Missing or malformed queues stop the caller; never manufacture empty state."""
    path = pending_path(repo_root, filename)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Catalogue queue {filename} is unavailable: {error}") from error
    return validate_pending_state(repo_root, value, schema=schema, progress=progress)


def write_pending_state(repo_root: Path, filename: str, value: dict[str, Any], *, schema: str, progress: str) -> None:
    """Replace one validated queue after the caller's required work completes."""
    validate_pending_state(repo_root, value, schema=schema, progress=progress)
    path = pending_path(repo_root, filename)
    header_keys = ("schema", "last_refreshed_at_utc") if progress == "refreshed" else ("schema", "last_published_at_utc")
    value = {
        "header": {key: value["header"][key] for key in header_keys},
        **{family: {wid: value[family][wid] for wid in sorted(value[family])}
           for family in ("current_works", "deleted_works")},
        **shared_changes(value, publishing=progress == "preview_done"),
    }
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    fd, name = tempfile.mkstemp(prefix="catalogue-pending-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def pending_counts(value: dict[str, Any]) -> dict[str, int]:
    return {"current": len(value["current_works"]), "deleted": len(value["deleted_works"]),
            **{field: len(value[field]) for field in REFRESH_FIELDS}}
