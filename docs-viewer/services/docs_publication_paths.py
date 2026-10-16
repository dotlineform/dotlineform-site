"""Configured completed publication inputs; no generation or policy reads."""

from pathlib import Path
from typing import Any

from docs_workspace_config import generated_documents_path, generated_search_path, safe_relative_path, select_workspace_stage, source_control_path


def confined(root: Path, relative: str | Path) -> Path:
    relative = safe_relative_path(str(relative), field="publication artifact")
    path = root / relative
    if path.resolve() != path or not path.is_relative_to(root):
        raise ValueError("Publication artifact must stay inside its configured owner")
    return path


def working_owner(workspace: Any, collection: str) -> Any:
    working = select_workspace_stage(workspace, "working")
    return next(owner for owner in working.collections if owner.collection == collection) if collection else working


def document_path(workspace: Any, collection: str, doc_id: str) -> Path:
    return confined(generated_documents_path(working_owner(workspace, collection)), Path("by-id") / f"{doc_id}.json")


def shared_path(workspace: Any, owner: str, output: str) -> Path:
    """Resolve one queued identity to its existing completed input."""
    working = select_workspace_stage(workspace, "working")
    if owner == "workspace":
        if output == "search":
            return generated_search_path(working)
        if output == "selected":
            return source_control_path(working, "selected.json")
        names = {"ordinary_index": "public-index-tree.json", "recent": "recent.json"}
        return confined(generated_documents_path(working), names[output])
    if output != "collection_manifest":
        raise ValueError(f"Unknown collection publication output: {output}")
    return confined(generated_documents_path(working_owner(workspace, owner)), "manifest.json")
