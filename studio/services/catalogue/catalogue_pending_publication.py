"""Completed Catalogue changes and Publish-owned per-Work progress."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from studio.services.catalogue.catalogue_pending_state import read_pending_state, write_pending_state
from studio.services.catalogue.catalogue_shared_changes import SHARED_FIELDS, merge_shared_changes, public_shared_outputs, validate_shared_changes


SCHEMA = "catalogue_publish_pending_v4"
FILENAME = "catalogue-publish-pending.json"


def read_pending_publication(repo_root: Path) -> dict[str, Any]:
    return read_pending_state(repo_root, FILENAME, schema=SCHEMA, progress="preview_done")


def write_pending_publication(repo_root: Path, value: dict[str, Any]) -> None:
    write_pending_state(repo_root, FILENAME, value, schema=SCHEMA, progress="preview_done")


def merge_completed_shared(repo_root: Path, completed: dict[str, list[str]]) -> None:
    """Forward completed shared output, excluding private reports and preserving Works."""
    validate_shared_changes(repo_root, completed, publishing=False)
    pending = read_pending_publication(repo_root)
    public = public_shared_outputs(repo_root)
    selection = {field: completed[field] for field in SHARED_FIELDS}
    selection["shared_outputs"] = [name for name in completed["shared_outputs"] if name in public]
    if not any(selection.values()):
        return
    merge_shared_changes(pending, selection, publishing=True)
    write_pending_publication(repo_root, pending)


def merge_completed_works(
    repo_root: Path, completed: Iterable[tuple[str, str, dict[str, Any], set[str]]],
) -> None:
    """Forward completed document work, preserving existing Publish progress.

    Regenerate never inspects an existing preview_done flag. Only a new record
    receives false; replace/merge selections leave the initialized flag untouched.
    """
    pending = read_pending_publication(repo_root)
    for family, work_id, selection, download_names in completed:
        other = "deleted_works" if family == "current_works" else "current_works"
        previous = pending[family].get(work_id)
        existing = previous if previous is not None else pending[other].get(work_id)
        record = {key: value for key, value in selection.items() if key != "refreshed"}
        if family == "current_works":
            prior = previous or {}
            record.update(
                metadata=record["metadata"] or prior.get("metadata", False),
                image=record["image"] or prior.get("image", False),
                file_names=sorted((set(record["file_names"]) | set(prior.get("file_names", []))) & download_names),
            )
        if existing is None:
            record["preview_done"] = False
        else:
            record = {**existing, **record}
            if family == "deleted_works":
                record.pop("metadata", None)
        pending[other].pop(work_id, None)
        pending[family][work_id] = record
    write_pending_publication(repo_root, pending)
