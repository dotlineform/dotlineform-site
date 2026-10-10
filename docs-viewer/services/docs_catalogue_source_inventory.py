"""Read exact Working Catalogue document associations for reconciliation."""

from __future__ import annotations

from pathlib import Path
from docs_document_identity import is_doc_timestamp, is_document_id
from docs_management_document_target import confined_source_path, resolve_managed_document_collection, source_doc_from_path
import docs_source_model as source_model


def catalogue_source_documents(repo_root: Path, work_ids: list[str] | None = None) -> dict[str, source_model.SourceDoc]:
    """Read exact queued sources; only explicit design maintenance inventories all."""
    collection = resolve_managed_document_collection(repo_root, collection="catalogue")
    documents: dict[str, source_model.SourceDoc] = {}
    paths = (source_model.document_markdown_paths(collection.source_root) if work_ids is None else
             [collection.source_root / f"{work_id}.md" for work_id in work_ids])
    for path in paths:
        if work_ids is not None and not path.exists():
            continue
        document = source_doc_from_path(
            path=confined_source_path(collection.source_root, path),
            requested_doc_id=path.stem,
        )
        fields = document.front_matter
        if not is_document_id(document.doc_id, collection="catalogue") or fields.get("collection") != "catalogue":
            raise ValueError(f"Catalogue source {path.name} has invalid document or collection identity")
        if "work_id" in fields:
            raise ValueError(f"Catalogue document {document.doc_id} has redundant work_id")
        if not isinstance(fields.get("title"), str) or not fields["title"].strip():
            raise ValueError(f"Catalogue document {document.doc_id} requires a title")
        if (not is_doc_timestamp(fields.get("added_date"))
                or not is_doc_timestamp(fields.get("last_updated"))):
            raise ValueError(f"Catalogue document {document.doc_id} has invalid timestamps")
        if document.doc_id in documents:
            raise ValueError(f"Work {document.doc_id} has multiple Catalogue documents")
        documents[document.doc_id] = document
    return documents
