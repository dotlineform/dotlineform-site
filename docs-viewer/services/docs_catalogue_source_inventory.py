"""Read exact Working Catalogue document associations for reconciliation."""

from __future__ import annotations

from pathlib import Path
import re

from docs_document_identity import is_doc_timestamp, is_immutable_doc_id
from docs_management_document_target import confined_source_path, resolve_managed_document_collection, source_doc_from_path
import docs_source_model as source_model


WORK_ID = re.compile(r"[0-9]{5}\Z")


def catalogue_source_documents(repo_root: Path) -> dict[str, source_model.SourceDoc]:
    """Inventory configured sources once, rejecting missing or duplicate Work identities."""
    collection = resolve_managed_document_collection(repo_root, collection="catalogue")
    documents: dict[str, source_model.SourceDoc] = {}
    for path in source_model.document_markdown_paths(collection.source_root):
        document = source_doc_from_path(
            path=confined_source_path(collection.source_root, path),
            requested_doc_id=path.stem,
        )
        fields = document.front_matter
        work_id = fields.get("work_id")
        if not is_immutable_doc_id(document.doc_id) or fields.get("collection") != "catalogue":
            raise ValueError(f"Catalogue source {path.name} has invalid document or collection identity")
        if not isinstance(work_id, str) or not WORK_ID.fullmatch(work_id):
            raise ValueError(f"Catalogue document {document.doc_id} requires one exact five-digit work_id")
        if not isinstance(fields.get("title"), str) or not fields["title"].strip():
            raise ValueError(f"Catalogue document {document.doc_id} requires a title")
        if (not is_doc_timestamp(fields.get("added_date"))
                or not is_doc_timestamp(fields.get("last_updated"))
                or type(fields.get("draft")) is not bool):
            raise ValueError(f"Catalogue document {document.doc_id} has invalid timestamps or draft state")
        if work_id in documents:
            raise ValueError(f"Work {work_id} has multiple Catalogue documents")
        documents[work_id] = document
    return documents
