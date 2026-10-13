"""Read exact Working Catalogue document associations for reconciliation."""

from __future__ import annotations

from pathlib import Path
from docs_management_document_target import ManagedDocumentCollection, confined_source_path, resolve_managed_document_collection, source_doc_from_path
import docs_source_model as source_model


def catalogue_source_documents(
    repo_root: Path, work_ids: list[str] | None = None, *, collection: ManagedDocumentCollection | None = None,
) -> dict[str, source_model.SourceDoc]:
    """Read exact queued sources; only explicit design maintenance inventories all."""
    collection = resolve_managed_document_collection(repo_root, collection="catalogue") if collection is None else collection
    documents: dict[str, source_model.SourceDoc] = {}
    paths = (source_model.document_markdown_paths(collection.source_root) if work_ids is None else
             [collection.source_root / f"{work_id}.md" for work_id in work_ids])
    for path in paths:
        if path.is_symlink():
            raise ValueError("Catalogue document source must not be a symlink")
        if work_ids is not None and not path.exists():
            continue
        document = source_doc_from_path(
            path=confined_source_path(collection.source_root, path),
            requested_doc_id=path.stem,
        )
        documents[document.doc_id] = document
    return documents
