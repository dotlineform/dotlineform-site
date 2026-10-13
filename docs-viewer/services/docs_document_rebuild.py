"""Rebuild one exact Working document without modifying its source."""

from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_work
from docs_management_document_target import ManagedDocumentCollection, ManagedDocumentTarget, resolve_managed_document_target
from docs_source_model import SourceDoc
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import rebuild_collection_outputs, rebuild_prepared_document_outputs, rebuild_working_outputs
from studio.services.catalogue.catalogue_pending_publication import merge_completed_works


def rebuild_document(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Await document/Links rendering from current inputs; omit Search and media production."""
    resolved = resolve_managed_document_target(repo_root, body)
    return rebuild_resolved_document(repo_root, resolved)


def rebuild_resolved_document(repo_root: Path, resolved: ManagedDocumentTarget) -> dict[str, Any]:
    """Build a validated authoring target and complete its generation handoff.

    Catalogue document builds contribute their document-only publication change
    regardless of which caller requested the build.
    """
    require_document_authoring(resolved.parent_config)
    if resolved.collection:
        rebuild = rebuild_collection_outputs(
            repo_root, resolved.collection, docs_doc_ids=[resolved.doc_id],
            links_doc_ids=[resolved.doc_id],
        )
    else:
        rebuild = rebuild_working_outputs(
            repo_root, docs_doc_ids=[resolved.doc_id], links_doc_ids=[resolved.doc_id],
            include_search=False, skip_media_builds=True,
        )
    queue_catalogue_document(repo_root, resolved.collection, resolved.doc_id)
    return {
        "ok": True, "target": resolved.request_target(), "rebuild": rebuild,
        "summary_text": "Document rebuilt.",
    }


def rebuild_prepared_document(
    repo_root: Path, owner: ManagedDocumentCollection | ManagedDocumentTarget, document: SourceDoc,
    *, parent_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate a completed Save/New handoff without reopening its source."""
    if parent_ids is None and isinstance(owner, ManagedDocumentTarget):
        parent_ids = owner.parent_ids
    rebuild = rebuild_prepared_document_outputs(repo_root, owner, document, parent_ids=parent_ids)
    queue_catalogue_document(repo_root, owner.collection, document.doc_id)
    target = {**owner.request_target(), "doc_id": document.doc_id}
    return {"ok": True, "target": target, "rebuild": rebuild, "summary_text": "Document rebuilt."}


def queue_catalogue_document(repo_root: Path, collection: str, doc_id: str) -> None:
    """Keep Catalogue document-only publication with every completed exact build."""
    if collection == "catalogue":
        try:
            work = read_catalogue_work(repo_root, doc_id)["work"]
            download_names = {item["filename"] for item in work.get("downloads", [])}
            merge_completed_works(repo_root, [(
                "current_works", doc_id,
                {"metadata": True, "image": False, "file_names": []}, download_names,
            )])
        except Exception as error:
            raise RuntimeError(
                f"Catalogue document {doc_id} rebuilt, but its publication queue update failed: {error}"
            ) from error
