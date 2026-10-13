"""Rebuild one exact Working document without modifying its source."""

from dataclasses import replace
from pathlib import Path
from typing import Any

from docs_management_document_target import ManagedDocumentCollection, ManagedDocumentTarget, committed_document_record, resolve_managed_document_target
from docs_source_model import SourceDoc, parse_collection_document_report, validate_document_status_front_matter
from docs_workspace_config import require_document_authoring
from docs_write_rebuild import rebuild_prepared_document_outputs
from studio.services.catalogue.catalogue_pending_publication import merge_completed_document


def rebuild_document(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Read one saved source and await its exact document/Links completion."""
    resolved = resolve_managed_document_target(repo_root, body)
    require_document_authoring(resolved.parent_config)
    document = resolved.document
    title = document.front_matter.get("title")
    if not isinstance(title, str):
        raise ValueError(f"Document {document.doc_id} title must be a string")
    validate_document_status_front_matter(
        document.front_matter, collection_config=resolved.document_config,
        source_name=document.path.name,
    )
    report = parse_collection_document_report(
        repo_root, resolved.parent_config, resolved.document_config, document.source_text,
        front_matter=document.front_matter, body=document.body, source_name=document.path.name,
    )
    prepared = replace(document, title=title, report=report)
    record = committed_document_record(
        document.front_matter, document.doc_id, resolved.document_config,
        collection=resolved.collection, parent_id=document.parent_id,
    )
    if not resolved.collection:
        record["report_id"] = report.id if report is not None else ""
    payload = rebuild_prepared_document(repo_root, resolved, prepared)
    payload["record"] = record
    return payload


def rebuild_prepared_document(
    repo_root: Path, owner: ManagedDocumentCollection | ManagedDocumentTarget, document: SourceDoc,
    *, parent_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate a prepared document and finish its Catalogue queue handoff."""
    if parent_ids is None and isinstance(owner, ManagedDocumentTarget):
        parent_ids = owner.parent_ids
    rebuild = rebuild_prepared_document_outputs(repo_root, owner, document, parent_ids=parent_ids)
    queue_catalogue_document(repo_root, owner, document.doc_id)
    target = {**owner.request_target(), "doc_id": document.doc_id}
    return {"ok": True, "target": target, "rebuild": rebuild, "summary_text": "Document rebuilt."}


def queue_catalogue_document(
    repo_root: Path, owner: ManagedDocumentCollection | ManagedDocumentTarget, doc_id: str,
) -> None:
    """Keep Catalogue document-only publication with every completed exact build."""
    if owner.collection == "catalogue":
        try:
            merge_completed_document(repo_root, doc_id, workspace=owner.workspace)
        except Exception as error:
            raise RuntimeError(
                f"Catalogue document {doc_id} rebuilt, but its publication queue update failed: {error}"
            ) from error
