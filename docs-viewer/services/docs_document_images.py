"""Fixed, independent thumbnails owned by the four authored collections."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_document_identity import is_document_id
from docs_workspace_config import location_child


THUMBNAIL_COLLECTIONS = frozenset({"library", "works", "concepts", "moments"})


def document_thumbnail_filename(doc_id: str, *, collection: str) -> str:
    """Return the fixed identity; Catalogue and Index documents have other artwork."""
    if collection not in THUMBNAIL_COLLECTIONS or not is_document_id(doc_id, collection=collection):
        raise ValueError("thumbnail requires an exact authored collection document")
    return f"{doc_id}-thumb.webp"


def document_thumbnail_path(owner: Any, doc_id: str) -> Path:
    """Confine an exact document thumbnail to its configured media owner."""
    filename = document_thumbnail_filename(doc_id, collection=owner.collection)
    return location_child(owner.media.types["thumbs"].asset_location, Path(filename)).path


def has_document_thumbnail(owner: Any, doc_id: str) -> bool:
    """Read presence once at metadata discovery; readers consume has_thumbnail."""
    return (getattr(owner, "collection", "") in THUMBNAIL_COLLECTIONS
            and document_thumbnail_path(owner, doc_id).is_file())
