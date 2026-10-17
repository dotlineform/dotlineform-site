"""Place an ordinary subtree and project its saved navigation metadata."""

from pathlib import Path
from typing import Any

from docs_index_order import index_order_path, index_order_text, insert_node, node_location, read_index_order, tree_parent_ids
from docs_management_document_target import normalize_managed_document_target, resolve_managed_document_collection
from docs_navigation_order import project_navigation_order
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
    owner = resolve_managed_document_collection(repo_root, require_existing_source_root=False)
    require_document_authoring(owner.parent_config)
    payload = {"ok": True, "target": target, "position_saved": False, "generation_complete": False, "phase": "inputs", "dry_run": dry_run}
    try:
        order_path = index_order_path(owner.parent_config)
        tree = read_index_order(order_path)
        siblings, index, previous_parent = node_location(tree, target["doc_id"])
        previous_order = [node["doc_id"] for node in siblings]
        parent_id = insert_node(tree, siblings.pop(index), body["target_doc_id"], body["placement"])
        payload["parent_changed"] = parent_id != previous_parent
        if dry_run:
            return payload

        def write_position(committed: dict[str, Any] | None = None) -> None:
            payload["phase"] = "position"
            if payload["parent_changed"] or previous_order != [node["doc_id"] for node in siblings]:
                write_text_atomic(order_path, index_order_text(tree))
            payload["position_saved"] = True
            if committed is not None:
                payload["committed_document"] = committed
            payload["phase"] = "generation" if payload["parent_changed"] else "navigation"

        if payload["parent_changed"]:
            payload["committed_document"] = project_document_position(repo_root, owner, target["doc_id"], tree_parent_ids(tree), write_position)
        else:
            project_navigation_order(repo_root, owner, parent_id, [node["doc_id"] for node in siblings], write_position)
        payload.update(generation_complete=True, phase="complete")
    except Exception as error:
        payload.update(ok=False, error=f"Position {target['doc_id']} failed during {payload['phase']}: {error}")
    return payload


def order_document_children(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Persist the browser's completed child order without a membership audit."""
    if set(body) != {"parent_doc_id", "child_doc_ids"}:
        raise ValueError("Order children requires parent_doc_id and child_doc_ids")
    target = normalize_managed_document_target({"doc_id": body["parent_doc_id"]})
    child_doc_ids = body["child_doc_ids"]
    if not isinstance(child_doc_ids, list) or any(not isinstance(doc_id, str) for doc_id in child_doc_ids):
        raise ValueError("child_doc_ids must be an array of strings")
    owner = resolve_managed_document_collection(repo_root, require_existing_source_root=False)
    require_document_authoring(owner.parent_config)
    payload = {"ok": True, "target": target, "position_saved": False, "generation_complete": False, "phase": "inputs", "dry_run": dry_run}
    try:
        order_path = index_order_path(owner.parent_config)
        tree = read_index_order(order_path)
        siblings, index, _ = node_location(tree, target["doc_id"])
        parent = siblings[index]
        children = parent.get("children", [])
        by_id = {node["doc_id"]: node for node in children}
        ordered = [by_id[doc_id] for doc_id in child_doc_ids]
        changed = ordered != children
        if changed:
            parent["children"] = ordered
        if dry_run:
            return payload

        def write_position() -> None:
            payload["phase"] = "position"
            if changed:
                write_text_atomic(order_path, index_order_text(tree))
            payload["position_saved"] = True
            payload["phase"] = "navigation"

        project_navigation_order(repo_root, owner, target["doc_id"], child_doc_ids, write_position)
        payload.update(generation_complete=True, phase="complete")
    except Exception as error:
        payload.update(ok=False, error=f"Order children of {target['doc_id']} failed during {payload['phase']}: {error}")
    return payload
