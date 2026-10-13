"""Place an ordinary subtree and project its saved navigation metadata."""

from pathlib import Path
from typing import Any

from docs_index_order import INDEX_ORDER_FILENAME, index_order_text, move_node, read_index_order, tree_parent_ids
from docs_management_document_target import normalize_managed_document_target, resolve_managed_document_collection
from docs_source_model import write_text_atomic
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import project_document_position


def position_document(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    if set(body) != {"doc_id", "target_doc_id", "placement"}:
        raise ValueError("Position requires doc_id, target_doc_id and placement")
    target = normalize_managed_document_target({"doc_id": body["doc_id"]})
    if not isinstance(body["target_doc_id"], str) or not isinstance(body["placement"], str):
        raise ValueError("Position destination and placement must be strings")
    if body["target_doc_id"]:
        normalize_managed_document_target({"doc_id": body["target_doc_id"]})
    owner = resolve_managed_document_collection(repo_root)
    require_document_authoring(owner.parent_config)
    payload = {"ok": True, "target": target, "position_saved": False, "generation_complete": False, "phase": "inputs", "dry_run": dry_run}
    try:
        tree = read_index_order(owner.source_root)
        move_node(tree, target["doc_id"], body["target_doc_id"], body["placement"])
        parents = tree_parent_ids(tree)
        if dry_run:
            return payload

        def write_position(committed: dict[str, Any]) -> None:
            payload["phase"] = "position"
            write_text_atomic(owner.source_root / INDEX_ORDER_FILENAME, index_order_text(tree))
            payload["position_saved"] = True
            payload["committed_document"] = committed
            payload["phase"] = "generation"

        payload["committed_document"] = project_document_position(repo_root, owner, target["doc_id"], parents, write_position)
        payload.update(generation_complete=True, phase="complete")
    except Exception as error:
        payload.update(ok=False, error=f"Position {target['doc_id']} failed during {payload['phase']}: {error}")
    return payload
