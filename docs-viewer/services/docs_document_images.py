"""Fixed, independent thumbnails owned by authored collections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, is_curated_book, location_child


THUMBNAIL_COLLECTIONS = frozenset({"library", "works", "concepts", "moments", "texts"})


def supports_document_thumbnail(owner: DocsStageConfig | DocsCollectionConfig | None) -> bool:
    return (
        isinstance(owner, DocsCollectionConfig)
        and (owner.collection in THUMBNAIL_COLLECTIONS or is_curated_book(owner))
        and owner.media is not None and "thumbs" in owner.media.types
    )


def document_thumbnail_filename(doc_id: str) -> str:
    """Format the fixed filename for an already resolved document ID."""
    return f"{doc_id}-thumb.webp"


def document_thumbnail_path(owner: Any, doc_id: str) -> Path:
    """Confine an exact document thumbnail to its configured media owner."""
    filename = document_thumbnail_filename(doc_id)
    return location_child(owner.media.types["thumbs"].asset_location, Path(filename)).path


def has_document_thumbnail(owner: Any, doc_id: str) -> bool:
    """Read presence once at metadata discovery; readers consume has_thumbnail."""
    return supports_document_thumbnail(owner) and document_thumbnail_path(owner, doc_id).is_file()
