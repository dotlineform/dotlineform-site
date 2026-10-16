"""Selected document media references and owned-file differences for generation."""

from __future__ import annotations

from typing import Any

from docs_document_images import document_thumbnail_filename
from docs_media_inventory import parsed_source_media_references


def document_media_references(owner: Any, document: Any) -> dict[str, list[str]]:
    """Use the supplied source/fields, independently of public presentation."""
    if owner.media is None:
        return {}
    from docs_builder.semantic_tokens import parse_semantic_tokens

    references: dict[str, set[str]] = {}
    for reference in parsed_source_media_references(
        owner, document.body_markdown, metadata=document.front_matter,
        semantic_tokens=parse_semantic_tokens(document.body_markdown, registry=None),
        doc_id=document.doc_id,
    ):
        references.setdefault(reference.media_type, set()).add(reference.identity)
    return {kind: sorted(names) for kind, names in references.items()}


def owned_document_files(doc_id: str, collection: str, record: dict[str, Any]) -> dict[str, set[str]]:
    """Limit removals to this document's namespace and fixed thumbnail identity."""
    media: dict[str, set[str]] = {}
    for kind, identities in record.get("media", {}).items():
        owned = {identity for identity in identities
                 if (identity == document_thumbnail_filename(doc_id, collection=collection)
                     if kind == "thumbs" else identity.startswith(doc_id + "/"))}
        if owned:
            media[kind] = owned
    return media


def removed_files(previous: dict[str, set[str]], current: dict[str, set[str]]) -> dict[str, list[str]]:
    return {kind: sorted(removed) for kind, identities in previous.items()
            if (removed := identities - current.get(kind, set()))}
