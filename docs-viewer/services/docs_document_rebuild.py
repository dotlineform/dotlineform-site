"""Rebuild one exact Working document without modifying its source."""

from pathlib import Path
from typing import Any

from docs_management_document_target import resolve_managed_document_target
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import rebuild_collection_outputs, rebuild_working_outputs


def rebuild_document(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Await document/Links rendering from current inputs; omit Search and media production."""
    resolved = resolve_managed_document_target(repo_root, body)
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
    return {
        "ok": True, "target": resolved.request_target(), "rebuild": rebuild,
        "summary_text": "Document rebuilt.",
    }
