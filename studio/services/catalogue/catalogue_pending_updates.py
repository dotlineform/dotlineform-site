"""Mutation-owned changes awaiting Refresh and Catalogue document generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from studio.services.catalogue.catalogue_pending_state import (
    pending_path, read_pending_state, validate_pending_state, write_pending_state,
)


SCHEMA = "catalogue_updates_pending_v3"
FILENAME = "catalogue-updates-pending.json"


def pending_updates_path(repo_root: Path) -> Path:
    return pending_path(repo_root, FILENAME)


def validate_pending_updates(value: Any) -> dict[str, Any]:
    return validate_pending_state(value, schema=SCHEMA, progress="refreshed")


def read_pending_updates(repo_root: Path) -> dict[str, Any]:
    return read_pending_state(repo_root, FILENAME, schema=SCHEMA, progress="refreshed")


def write_pending_updates(repo_root: Path, value: dict[str, Any]) -> None:
    write_pending_state(repo_root, FILENAME, value, schema=SCHEMA, progress="refreshed")


def initial_pending_updates() -> dict[str, Any]:
    """Cutover starts without a successful Refresh time and requires shared output."""
    return {"header": {"schema": SCHEMA, "last_refreshed_at_utc": None, "shared_refresh_pending": True},
            "current_works": {}, "deleted_works": {}}


def accumulate_work_changes(
    repo_root: Path, current: Mapping[str, Mapping[str, Any]], deleted: Mapping[str, Mapping[str, Any]],
    *, downloads_by_work: Mapping[str, set[str]],
    shared_refresh_pending: bool = False,
) -> dict[str, Any]:
    """Merge known mutation effects and reset only changed entries' readiness.

    Deletion replaces current selection; recreation replaces deletion selection.
    Removed references cancel their pending transfers without losing other media.
    """
    pending = read_pending_updates(repo_root)
    for work_id, changes in current.items():
        old = pending["current_works"].get(work_id, {})
        names = (set(old.get("file_names", [])) | set(changes["file_names"])) & downloads_by_work[work_id]
        pending["deleted_works"].pop(work_id, None)
        pending["current_works"][work_id] = {
            "metadata": old.get("metadata", False) or changes["metadata"],
            "image": old.get("image", False) or changes["image"],
            "file_names": sorted(names), "refreshed": False,
        }
    for work_id, selection in deleted.items():
        pending["current_works"].pop(work_id, None)
        pending["deleted_works"][work_id] = {**selection, "refreshed": False}
    if current or deleted or shared_refresh_pending:
        pending["header"]["shared_refresh_pending"] = True
        write_pending_updates(repo_root, pending)
    return pending


def remove_pending_update(repo_root: Path, pending: dict[str, Any], family: str, work_id: str) -> None:
    """Remove one entry only after document generation and publication merge."""
    del pending[family][work_id]
    write_pending_updates(repo_root, pending)
