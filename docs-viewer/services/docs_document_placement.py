"""Read the ordinary parent or named collection host for document metadata."""

from pathlib import Path

from docs_document_location import collection_report_placement
from docs_management_document_target import ManagedDocumentTarget


def document_location_parent_id(repo_root: Path, source: ManagedDocumentTarget) -> str:
    """Return the exact selected location for the existing metadata picker."""
    if not source.collection:
        return source.document.parent_id
    return collection_report_placement(
        repo_root, source.collection, stage=source.stage,
    )[2]
