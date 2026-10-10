"""Rebuild one exact Working document without modifying its source."""

from pathlib import Path
from typing import Any

from docs_catalogue_media import read_catalogue_work
from docs_management_document_target import ManagedDocumentTarget, resolve_managed_document_target
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import rebuild_collection_outputs, rebuild_working_outputs
from studio.services.catalogue.catalogue_pending_publication import merge_completed_works


def rebuild_document(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Await document/Links rendering from current inputs; omit Search and media production."""
    resolved = resolve_managed_document_target(repo_root, body)
    return rebuild_resolved_document(repo_root, resolved)


def rebuild_resolved_document(repo_root: Path, resolved: ManagedDocumentTarget) -> dict[str, Any]:
    """Build the validated target and queue completed Catalogue document changes.

    Source Save uses this same owner. Document-only publication contributes no
    media changes and preserves existing media selections and Publish progress.
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
    if resolved.collection == "catalogue":
        try:
            work = read_catalogue_work(repo_root, resolved.doc_id)["work"]
            download_names = {item["filename"] for item in work.get("downloads", [])}
            merge_completed_works(repo_root, [(
                "current_works", resolved.doc_id,
                {"metadata": True, "image": False, "file_names": []}, download_names,
            )])
        except Exception as error:
            raise RuntimeError(
                f"Catalogue document {resolved.doc_id} rebuilt, but its publication queue update failed: {error}"
            ) from error
    return {
        "ok": True, "target": resolved.request_target(), "rebuild": rebuild,
        "summary_text": "Document rebuilt.",
    }
