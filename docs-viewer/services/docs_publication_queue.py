"""Completed Docs publication selections, independent of generated artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_source_model import write_text_atomic
from docs_workspace_config import DocsStageConfig, DocsWorkspaceConfig


FILENAME = "docs-publish-pending.json"
FAMILIES = ("current_documents", "deleted_documents", "current_shared_outputs", "deleted_shared_outputs")


def queue_path(workspace: DocsWorkspaceConfig | DocsStageConfig) -> Path:
    path = workspace.workspace_root.path / "working" / FILENAME
    if path.resolve() != path:
        raise ValueError("Docs publication queue must stay in configured Working storage")
    return path


def empty_queue() -> dict[str, Any]:
    return {
        "header": {"schema": "docs_publish_pending_v1", "last_published_at_utc": None},
        **{family: {} for family in FAMILIES},
    }


def read_queue(workspace: DocsWorkspaceConfig | DocsStageConfig) -> dict[str, Any]:
    """Decode the application-produced handoff; missing state requires setup."""
    return json.loads(queue_path(workspace).read_bytes())


def save_queue(workspace: DocsWorkspaceConfig | DocsStageConfig, pending: dict[str, Any]) -> None:
    write_text_atomic(queue_path(workspace), json.dumps(pending, ensure_ascii=False, indent=2) + "\n")


def has_selections(pending: dict[str, Any]) -> bool:
    return any(pending[family] for family in FAMILIES)


def select_document(pending: dict[str, Any], doc_id: str, collection: str, *, media: dict[str, list[str]] | None = None, removed_media: dict[str, list[str]] | None = None, restored_media: dict[str, list[str]] | None = None, delete: bool = False) -> None:
    current, opposite = ("deleted_documents", "current_documents") if delete else ("current_documents", "deleted_documents")
    record: dict[str, Any] = {"collection": collection} if collection else {}
    if not delete and media:
        record["media"] = media
    removals: dict[str, set[str]] = {}
    for selection in (pending[current].get(doc_id, {}), pending[opposite].get(doc_id, {}), {"removed_media": removed_media or {}}):
        for kind, names in selection.get("removed_media", {}).items():
            removals.setdefault(kind, set()).update(names)
    remaining = {kind: sorted(names - set((restored_media or {}).get(kind, []))) for kind, names in removals.items()}
    remaining = {kind: names for kind, names in remaining.items() if names}
    if remaining:
        record["removed_media"] = remaining
    pending[opposite].pop(doc_id, None)
    pending[current][doc_id] = record


def select_shared(pending: dict[str, Any], owner: str, output: str, *, delete: bool = False) -> None:
    current, opposite = ("deleted_shared_outputs", "current_shared_outputs") if delete else ("current_shared_outputs", "deleted_shared_outputs")
    other = pending[opposite].get(owner)
    if other is not None:
        other.pop(output, None)
        if not other:
            del pending[opposite][owner]
    pending[current].setdefault(owner, {})[output] = {}
