"""One confirmed exact-target Delete with retained effects and no restoration."""

import os
from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_document_images import document_thumbnail_filename
from docs_index_order import exclude_nodes, index_order_path, index_order_text, read_index_order, tree_parent_ids
from docs_management_context import log_event
from docs_management_document_target import ManagedDocumentCollection, normalize_managed_document_target, resolve_managed_document_collection
from docs_publication_paths import confined
from docs_publication_preparation import PublicationHandoffError, PublicationPreparation, load_preparation
from docs_selected_documents import read_selected, selected_path, selected_text
from docs_source_model import write_text_atomic
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import complete_document_deletion


def collect_deleted_media(owner: ManagedDocumentCollection, doc_ids: list[str], publication: PublicationPreparation) -> list[Path]:
    """Select files beneath only the deleted namespaces and their fixed thumbnails."""
    media = owner.document_config.media
    directories: list[Path] = []
    if media is None:
        return directories
    for doc_id in doc_ids:
        removals: dict[str, list[str]] = {}
        for kind, config in media.types.items():
            root = config.asset_location.path
            identities: list[str] = []

            def collect(directory: Path) -> None:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        identity = Path(entry.path).relative_to(root).as_posix()
                        path = confined(root, identity)
                        if entry.is_dir(follow_symlinks=False):
                            collect(path)
                        else:
                            identities.append(identity)
                            publication.working_removals[(owner.collection, kind, identity)] = path
                directories.append(directory)

            if kind == "thumbs":
                identity = document_thumbnail_filename(doc_id, collection=owner.collection)
                path = confined(root, identity)
                if path.exists():
                    identities.append(identity)
                    publication.working_removals[(owner.collection, kind, identity)] = path
            else:
                directory = confined(root, doc_id)
                if directory.exists():
                    collect(directory)
            if identities:
                removals[kind] = identities
        publication.media_removals[doc_id] = removals
    return directories


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
        "media_deleted": False, "media_removal_effects": [], "publication_handoff_complete": False,
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
        payload["phase"] = "media selection"
        publication = load_preparation(repo_root, owner.workspace)
        payload["media_removal_effects"] = publication.removal_effects
        media_directories = collect_deleted_media(owner, delete_ids, publication)
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
            publication.selected()
        payload["selected_updated"] = True
        payload["phase"] = "generation"
        payload["rebuild"] = complete_document_deletion(repo_root, owner, delete_ids, updated_selected, parent_ids=parents, publication=publication)
        payload.update(generation_complete=True, publication_handoff_complete=True, phase="Working media folder removal")
        for directory in media_directories:
            directory.rmdir()
        payload["media_deleted"] = True
        payload.update(phase="complete", delete_count=len(delete_ids))
        payload.pop("failing_target", None)
        log_event(repo_root, "docs-delete", {"collection": owner.collection, "deleted_doc_ids": delete_ids})
    except Exception as error:
        if isinstance(error, PublicationHandoffError):
            payload.update(phase=error.phase, generation_complete=True, media_removal_effects=error.removal_effects)
        payload.update(ok=False, delete_count=len(payload["deleted_doc_ids"]), error=f"Delete {owner.collection or 'ordinary documents'} {requested_ids} failed during {payload['phase']}: {error}")
    return payload
