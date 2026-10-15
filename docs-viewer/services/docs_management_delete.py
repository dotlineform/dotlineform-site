"""One confirmed exact-target Delete with retained effects and no restoration."""

from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_index_order import exclude_nodes, index_order_path, index_order_text, read_index_order, tree_parent_ids
from docs_management_context import log_event
from docs_management_document_target import normalize_managed_document_target, resolve_managed_document_collection
from docs_selected_documents import read_selected, selected_path, selected_text
from docs_source_model import write_text_atomic
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import complete_document_deletion


def delete_documents(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    collection = "collection" in body
    expected = {"collection", "doc_id", "confirm"} if collection else {"doc_ids", "confirm"}
    if set(body) != expected or body["confirm"] is not True:
        raise ValueError("Delete requires exact targets and confirm=true")
    if collection:
        target = normalize_managed_document_target({key: body[key] for key in ("collection", "doc_id")})
        requested_ids = [target["doc_id"]]
    else:
        if not isinstance(body["doc_ids"], list) or not body["doc_ids"]:
            raise ValueError("Delete requires a nonempty document ID array")
        requested_ids = [normalize_managed_document_target({"doc_id": value})["doc_id"] for value in body["doc_ids"]]
        target = {"doc_id": requested_ids[0]}
    owner = resolve_managed_document_collection(repo_root, collection=target.get("collection"))
    require_document_authoring(owner.parent_config)
    if owner.collection == "catalogue":
        raise ValueError("Catalogue documents are deleted through Regenerate")
    payload = {
        "ok": True, "target": target, "requested_doc_ids": requested_ids,
        "deleted_doc_ids": [], "source_deleted": False, "generation_complete": False,
        "index_updated": False, "selected_updated": False, "phase": "inputs", "dry_run": dry_run,
    }
    try:
        tree = None
        parents = None
        delete_ids = requested_ids
        if not collection:
            order_path = index_order_path(owner.parent_config)
            tree = read_index_order(order_path)
            parents = tree_parent_ids(tree)
            for doc_id in requested_ids:
                if doc_id not in parents:
                    raise FileNotFoundError(f"Document is not in Index: {doc_id}")
            requested = set(requested_ids)
            delete_ids = []

            def collect(nodes: list[dict[str, Any]], included: bool = False) -> None:
                for node in nodes:
                    selected = included or node["doc_id"] in requested
                    if selected:
                        delete_ids.append(node["doc_id"])
                    collect(node.get("children", []), selected)

            collect(tree)
        selected = read_selected(owner.parent_config)
        removed = set(delete_ids)
        rows = [row for row in selected["docs"] if not (row.get("collection", "") == owner.collection and row["doc_id"] in removed)]
        updated_selected = {**selected, "docs": rows}
        if dry_run:
            return {**payload, "delete_doc_ids": delete_ids}
        for doc_id in delete_ids:
            payload.update(phase="source", failing_target={**owner.request_target(), "doc_id": doc_id})
            path = owner.source_root / f"{doc_id}.md"
            if not is_document_id(doc_id, collection=owner.collection) or path.is_symlink() or path.resolve().parent != owner.source_root:
                raise ValueError("Delete source must be an exact confined document path")
            path.unlink()
            payload["deleted_doc_ids"].append(doc_id)
        payload["source_deleted"] = True
        payload.pop("failing_target", None)
        if tree is not None:
            payload["phase"] = "index"
            write_text_atomic(order_path, index_order_text(exclude_nodes(tree, removed)))
            parents = {doc_id: parent for doc_id, parent in parents.items() if doc_id not in removed}
            payload["index_updated"] = True
        payload["phase"] = "selected"
        if rows != selected["docs"]:
            write_text_atomic(selected_path(owner.parent_config), selected_text(updated_selected))
        payload["selected_updated"] = True
        payload["phase"] = "generation"
        payload["rebuild"] = complete_document_deletion(repo_root, owner, delete_ids, updated_selected, parent_ids=parents)
        payload.update(generation_complete=True, phase="complete", delete_count=len(delete_ids))
        payload.pop("failing_target", None)
        log_event(repo_root, "docs-delete", {"collection": owner.collection, "deleted_doc_ids": delete_ids})
    except Exception as error:
        payload.update(ok=False, delete_count=len(payload["deleted_doc_ids"]), error=f"Delete {owner.collection or 'ordinary documents'} {requested_ids} failed during {payload['phase']}: {error}")
    return payload
