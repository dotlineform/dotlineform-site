"""Copy/remove independent document artwork and hand off exact metadata effects."""

from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_media_config
from docs_document_identity import is_document_id
from docs_document_images import THUMBNAIL_COLLECTIONS, document_thumbnail_path
from docs_json_files import load_json_object
from docs_management_document_target import committed_document_record, normalize_managed_document_target
from docs_publication_paths import confined, shared_path
from docs_publication_preparation import write_json
from docs_publication_queue import read_queue, save_queue, select_document, select_shared
from docs_selected_documents import read_selected, selected_path
from docs_workspace_config import load_docs_workspace_config, location_child, require_document_authoring, select_workspace_stage


def set_document_thumbnail(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Apply a selected Work's existing thumbnail, or delete with work_id=null.

    Source, dates, tokens and relationships are untouched. Saved generated
    metadata owns document/public membership; existing queued body-media writes
    survive this thumbnail-only operation. No source Work identity is persisted.
    """
    if set(body) != {"collection", "doc_id", "work_id"}:
        raise ValueError("Thumb requires collection, doc_id and work_id (null to delete)")
    target = normalize_managed_document_target({key: body[key] for key in ("collection", "doc_id")})
    collection, doc_id = target["collection"], target["doc_id"]
    if collection not in THUMBNAIL_COLLECTIONS:
        raise ValueError("Thumb is available only for Library, Context, Concepts and Moments")
    work_id = body["work_id"]
    if work_id is not None and (not isinstance(work_id, str) or not is_document_id(work_id, collection="catalogue")):
        raise ValueError("Choose an exact Catalogue Work")
    workspace = load_docs_workspace_config(repo_root)
    working = select_workspace_stage(workspace, "working")
    require_document_authoring(working)
    owner = next(item for item in working.collections if item.collection == collection)
    root = owner.generated.documents.location.path
    by_id_path = confined(root, Path("by-id") / f"{doc_id}.json")
    payload = load_json_object(by_id_path, "Document")
    manifest_path = confined(root, "manage-manifest.json")
    manifest = load_json_object(manifest_path, "Collection metadata")
    row = next(row for row in manifest["docs"] if row["doc_id"] == doc_id)
    public_path = shared_path(workspace, collection, "collection_manifest")
    public = load_json_object(public_path, "Public collection metadata")
    public_row = next((row for row in public["docs"] if row["doc_id"] == doc_id), None)
    selected = read_selected(working)
    pending = read_queue(workspace)
    thumbnail = document_thumbnail_path(owner, doc_id)
    present = work_id is not None
    phase = "thumbnail input"
    completed: list[str] = []
    try:
        if present:
            policy = read_catalogue_media_config(repo_root, workspace=workspace.catalogue.working)
            rendition = policy["thumbnails"]
            filename = f"{work_id}-{rendition['suffix']}-{rendition['sizes'][0]}.{policy['format']}"
            try:
                data = location_child(workspace.assets.work_thumbnails, Path(filename)).path.read_bytes()
            except FileNotFoundError as error:
                raise ValueError(f"Work {work_id} has no available thumbnail") from error
            phase = "thumbnail copy"
            thumbnail.parent.mkdir(parents=True, exist_ok=True)
            thumbnail.write_bytes(data)
            completed.append("thumbnail copied")

        def project(record: dict[str, Any]) -> None:
            if present:
                record["has_thumbnail"] = True
            else:
                record.pop("has_thumbnail", None)

        phase = "document metadata"
        project(payload)
        project(row)
        write_json(by_id_path, payload)
        write_json(manifest_path, manifest)
        completed.append("Working metadata updated")
        phase = "reader metadata"
        if public_row is not None:
            project(public_row)
            write_json(public_path, public)
            select_shared(pending, collection, "collection_manifest")
        for selected_row in selected["docs"]:
            if selected_row.get("collection") == collection and selected_row["doc_id"] == doc_id:
                project(selected_row)
                write_json(selected_path(working), selected)
                select_shared(pending, "workspace", "selected")
                break
        media = dict(pending["current_documents"].get(doc_id, {}).get("media", {}))
        media.pop("thumbs", None)
        artwork = {"thumbs": [thumbnail.name]}
        if present:
            media.update(artwork)
        if public_row is not None or not present or doc_id in pending["current_documents"] or doc_id in pending["deleted_documents"]:
            select_document(
                pending, doc_id, collection, media=artwork if present else {}, current_media=media,
                removed_media={} if present else artwork, restored_media=artwork if present else {},
                delete=public_row is None,
            )
        phase = "publication handoff"
        save_queue(workspace, pending)
        completed.append("publication queue saved")
        # Save exact publication removals before removing the Working copy.
        if not present:
            phase = "thumbnail removal"
            thumbnail.unlink(missing_ok=True)
    except (OSError, ValueError, RuntimeError) as error:
        effects = ", ".join(completed) or "none"
        raise RuntimeError(f"Thumb {collection}/{doc_id} failed during {phase}: {error}. Completed: {effects}.") from error
    return {"ok": True, "target": target, "record": committed_document_record(
        payload, doc_id, owner, collection=collection, thumbnail=present,
    )}
