"""Project one sibling order without document, rendering or eligibility work."""

import json
from pathlib import Path
from typing import Any, Callable

from docs_build_manifest import remove_build_manifest
from docs_index_order import tree_groups
from docs_json_files import render_json
from docs_management_context import utc_now
from docs_management_document_target import ManagedDocumentCollection
from docs_publication_paths import confined, shared_path
from docs_publication_queue import read_queue, save_queue, select_shared
from docs_source_model import write_text_atomic
from docs_workspace_config import generated_documents_path


def _reorder_navigation(payload: dict[str, Any], parent_id: str, child_doc_ids: list[str]) -> bool:
    """Reorder existing nodes, preserving the saved public membership/subtrees."""
    for siblings, current_parent in tree_groups(payload["docs"]):
        if current_parent != parent_id:
            continue
        by_id = {node["doc_id"]: node for node in siblings}
        ordered = [by_id[doc_id] for doc_id in child_doc_ids if doc_id in by_id]
        if ordered == siblings:
            return False
        siblings[:] = ordered
        payload["generated_at"] = utc_now()
        return True
    # An excluded parent has no group in the saved public navigation.
    return False


def project_navigation_order(
    repo_root: Path, owner: ManagedDocumentCollection, parent_id: str, child_doc_ids: list[str],
    write_position: Callable[[], None],
) -> None:
    """Save the supplied sibling order and only its changed navigation effects.

    Read each saved tree once. The caller owns canonical hierarchy persistence;
    public membership is already established, so no policy or document reads are
    needed. Queue only a changed public tree, preserving all pending selections.
    """
    management_path = confined(generated_documents_path(owner.parent_config), "index-tree.json")
    public_path = shared_path(owner.workspace, "workspace", "ordinary_index")
    management = json.loads(management_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    management_changed = _reorder_navigation(management, parent_id, child_doc_ids)
    public_changed = _reorder_navigation(public, parent_id, child_doc_ids)

    write_position()
    if management_changed:
        write_text_atomic(management_path, render_json(management))
        remove_build_manifest(repo_root, owner.parent_config)
    if public_changed:
        pending = read_queue(owner.workspace)
        write_text_atomic(public_path, render_json(public))
        select_shared(pending, "workspace", "ordinary_index")
        save_queue(owner.workspace, pending)
