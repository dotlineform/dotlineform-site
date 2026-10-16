"""Apply only queued document, media and shared-output units."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_deploy_repo import utc_now
from docs_publication_preparation import confined, public_document_path, public_shared_path
from docs_publication_queue import FAMILIES, has_selections, save_queue
from docs_publication_transfer import SelectedTransfers, completed_effect, delete_path, read_bytes, write_bytes
from docs_workspace_config import generated_search_path, preview_documents_path, preview_search_path, public_documents_path, public_search_path, select_workspace_stage


def publish_selected_documents(repo_root: Path, workspace: Any, pending: dict[str, Any], transfers: SelectedTransfers, result: dict[str, Any]) -> None:
    if not has_selections(pending):
        return
    working = select_workspace_stage(workspace, "working")
    preview = select_workspace_stage(workspace, "preview")
    owners = {"": (working, preview), **{left.collection: (left, right) for left, right in zip(working.collections, preview.collections, strict=True)}}

    def complete() -> None:
        if not has_selections(pending):
            pending["header"]["last_published_at_utc"] = utc_now()
        save_queue(workspace, pending)

    for family in FAMILIES[:2]:
        deleting = family == "deleted_documents"
        for doc_id, selection in tuple(pending[family].items()):
            collection = selection.get("collection", "")
            result.update(phase="document Preview", target=f"{collection or 'documents'}/{doc_id}")
            source_owner, preview_owner = owners[collection]
            identity = Path("by-id") / f"{doc_id}.json"
            target = confined(preview_documents_path(preview_owner), identity)
            media_inputs = []
            if deleting:
                delete_path(target)
            else:
                for kind, names in selection.get("media", {}).items():
                    source = source_owner.media.types[kind].asset_location.path
                    destination = preview_owner.media.types[kind].asset_location.path
                    for name in names:
                        result["target"] = f"{collection or 'documents'}/{kind}/{name}"
                        media_target = confined(destination, name)
                        write_bytes(media_target, read_bytes(confined(source, name)))
                        completed_effect(result, "Preview files applied", media_target)
                        # Retain paths rather than all attachments' bytes so
                        # distribution holds only one selected media file.
                        media_inputs.append((kind, name, media_target))
                result["target"] = f"{collection or 'documents'}/{doc_id}"
                document_bytes = write_bytes(target, read_bytes(public_document_path(workspace, collection, doc_id)))
            completed_effect(result, "Preview files removed" if deleting else "Preview files applied", target)
            result.update(phase="document distribution")
            for kind, name, path in media_inputs:
                result["target"] = f"{collection or 'documents'}/{kind}/{name}"
                public = preview_owner.public_projection.media[kind]
                transfers.transfer(public.location, name, data=read_bytes(path))
                completed_effect(result, "media files distributed", name)
            result["target"] = f"{collection or 'documents'}/{doc_id}"
            deployed = confined(repo_root / public_documents_path(preview_owner), identity)
            if deleting:
                delete_path(deployed)
            else:
                write_bytes(deployed, document_bytes)
            completed_effect(result, "destination files removed" if deleting else "destination files applied", deployed)
            del pending[family][doc_id]
            complete()
            result["completed"].append({"family": family, "doc_id": doc_id})

    for family in FAMILIES[2:]:
        deleting = family == "deleted_shared_outputs"
        for owner, outputs in tuple(pending[family].items()):
            for output in tuple(outputs):
                result.update(phase="shared Preview", target=f"{owner}/{output}")
                if output == "search" and owner == "workspace":
                    source = generated_search_path(working)
                    target = preview_search_path(preview)
                    destination = repo_root / public_search_path(preview)
                else:
                    _source_owner, preview_owner = owners["" if owner == "workspace" else owner]
                    filename = {"ordinary_index": "index-tree.json", "recent": "recent.json", "selected": "selected.json", "collection_manifest": "manifest.json"}[output]
                    source = public_shared_path(workspace, owner, output)
                    target = confined(preview_documents_path(preview_owner), filename)
                    destination = confined(repo_root / public_documents_path(preview_owner), filename)
                if deleting:
                    delete_path(target)
                else:
                    data = write_bytes(target, read_bytes(source))
                completed_effect(result, "Preview files removed" if deleting else "Preview files applied", target)
                result["phase"] = "shared distribution"
                if deleting:
                    delete_path(destination)
                else:
                    write_bytes(destination, data)
                completed_effect(result, "destination files removed" if deleting else "destination files applied", destination)
                del outputs[output]
                if not outputs:
                    del pending[family][owner]
                complete()
                result["completed"].append({"family": family, "owner": owner, "output": output})
