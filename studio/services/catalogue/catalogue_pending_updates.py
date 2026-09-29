"""Private Working coordination list for changed Catalogue Work documents."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from docs_workspace_config import select_workspace_stage, source_container_path
from studio.services.catalogue.catalogue_output_paths import catalogue_workspace_config


SCHEMA = "catalogue_updates_pending_v1"
FILENAME = "updates-pending.json"
WORK_ID = re.compile(r"[0-9]{5}\Z")
WORK_RECORD = re.compile(r"works/index/([0-9]{5})\.json\Z")


def pending_updates_path(repo_root: Path) -> Path:
    """Resolve the configured private Catalogue source owner without creating it."""
    workspace = catalogue_workspace_config(repo_root)
    working = select_workspace_stage(workspace, "working")
    matching = [child for child in working.collections if child.collection == "catalogue"]
    if len(matching) != 1:
        raise ValueError("Working Catalogue collection must be configured exactly once")
    source_root = source_container_path(matching[0])
    if source_root.is_symlink() or not source_root.is_dir() or not source_root.resolve().is_relative_to(workspace.workspace_root.path):
        raise FileNotFoundError("Working Catalogue source directory is unavailable")
    path = source_root / FILENAME
    if path.is_symlink():
        raise ValueError("Catalogue pending updates file must not be a symlink")
    return path


def _work_ids(value: Any, label: str) -> list[str]:
    if (not isinstance(value, list) or any(not isinstance(item, str) or not WORK_ID.fullmatch(item) for item in value)
            or value != sorted(set(value))):
        raise ValueError(f"Catalogue pending {label} must be sorted distinct five-digit Work IDs")
    return value


def validate_pending_updates(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"schema", "current_work_ids", "deleted_work_ids"} or value.get("schema") != SCHEMA:
        raise ValueError("Catalogue pending updates schema is invalid")
    current = _work_ids(value["current_work_ids"], "current_work_ids")
    deleted = _work_ids(value["deleted_work_ids"], "deleted_work_ids")
    if set(current) & set(deleted):
        raise ValueError("Catalogue pending Work IDs cannot be both current and deleted")
    return value


def read_pending_updates(repo_root: Path) -> dict[str, Any]:
    """Require the existing list; missing or malformed state stops the caller."""
    path = pending_updates_path(repo_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError("Catalogue pending updates list is missing") from error
    except (OSError, ValueError) as error:
        raise ValueError(f"Catalogue pending updates list is unreadable: {error}") from error
    return validate_pending_updates(payload)


def _text(payload: dict[str, Any]) -> str:
    validate_pending_updates(payload)
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _replace_pending_updates(repo_root: Path, payload: dict[str, Any]) -> None:
    path = pending_updates_path(repo_root)
    data = _text(payload)
    fd, temporary_name = tempfile.mkstemp(prefix="updates-pending-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def accumulate_generated_work_changes(
    repo_root: Path, pending: dict[str, Any], result: dict[str, Any],
) -> dict[str, Any]:
    """Move exact Work IDs according to the latest completed generator result."""
    validate_pending_updates(pending)
    current = set(pending["current_work_ids"])
    deleted = set(pending["deleted_work_ids"])
    changes: dict[str, set[str]] = {}
    for key in ("written", "deleted"):
        paths = result.get(key)
        if not isinstance(paths, list):
            raise ValueError(f"Catalogue generator {key} result is invalid")
        ids: set[str] = set()
        for relative in paths:
            if not isinstance(relative, str):
                raise ValueError(f"Catalogue generator {key} path is invalid")
            match = WORK_RECORD.fullmatch(relative)
            if match:
                ids.add(match[1])
            elif relative.startswith("works/index/"):
                raise ValueError(f"Catalogue generator {key} Work path is invalid: {relative}")
        changes[key] = ids
    if changes["written"] & changes["deleted"]:
        raise ValueError("Catalogue generator reported a Work as both written and deleted")
    current.difference_update(changes["deleted"])
    current.update(changes["written"])
    deleted.difference_update(changes["written"])
    deleted.update(changes["deleted"])
    updated = {"schema": SCHEMA, "current_work_ids": sorted(current), "deleted_work_ids": sorted(deleted)}
    if updated != pending:
        _replace_pending_updates(repo_root, updated)
    return {"current": len(updated["current_work_ids"]), "deleted": len(updated["deleted_work_ids"]),
            "queued_current": len(changes["written"]), "queued_deleted": len(changes["deleted"])}


def clear_pending_updates(
    repo_root: Path, pending: dict[str, Any], *, current: set[str], deleted: set[str],
) -> dict[str, int]:
    """Remove only entries whose required source and Build operation completed."""
    validate_pending_updates(pending)
    remaining_current = set(pending["current_work_ids"]) - current
    remaining_deleted = set(pending["deleted_work_ids"]) - deleted
    updated = {"schema": SCHEMA, "current_work_ids": sorted(remaining_current),
               "deleted_work_ids": sorted(remaining_deleted)}
    if updated != pending:
        _replace_pending_updates(repo_root, updated)
    return {"current": len(remaining_current), "deleted": len(remaining_deleted)}
