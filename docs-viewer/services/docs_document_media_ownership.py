"""Selected document media references and owned-file differences for generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from docs_document_images import document_thumbnail_filename
from docs_media_inventory import parsed_source_media_references


def document_media_references(owner: Any, *, doc_id: str, body: str, metadata: dict[str, Any]) -> dict[str, list[str]]:
    """Use the supplied source/fields, independently of public presentation."""
    if owner.media is None:
        return {}
    from docs_builder.semantic_tokens import parse_semantic_tokens

    references: dict[str, set[str]] = {}
    for reference in parsed_source_media_references(
        owner, body, metadata=metadata,
        semantic_tokens=parse_semantic_tokens(body, registry=None), doc_id=doc_id,
    ):
        references.setdefault(reference.media_type, set()).add(reference.identity)
    return {kind: sorted(names) for kind, names in references.items()}


def owned_document_files(doc_id: str, collection: str, references: dict[str, list[str]]) -> dict[str, set[str]]:
    """Limit removals to this document's namespace and fixed thumbnail identity."""
    media: dict[str, set[str]] = {}
    for kind, identities in references.items():
        owned = {identity for identity in identities
                 if (identity == document_thumbnail_filename(doc_id, collection=collection)
                     if kind == "thumbs" else identity.startswith(doc_id + "/"))}
        if owned:
            media[kind] = owned
    return media


def removed_files(previous: dict[str, set[str]], current: dict[str, set[str]]) -> dict[str, list[str]]:
    return {kind: sorted(removed) for kind, identities in previous.items()
            if (removed := identities - current.get(kind, set()))}


@dataclass(frozen=True)
class DocumentMediaChange:
    """One authoring operation's references and exact owned removals, in memory."""

    current: dict[str, list[str]]
    removed: dict[str, list[str]]
    added: dict[str, list[str]]
    ready: dict[str, list[str]] = field(default_factory=dict)


def compare_document_media(owner: Any, doc_id: str, *, previous_body: str, previous_metadata: dict[str, Any], body: str, metadata: dict[str, Any]) -> DocumentMediaChange:
    before = document_media_references(owner, doc_id=doc_id, body=previous_body, metadata=previous_metadata)
    current = document_media_references(owner, doc_id=doc_id, body=body, metadata=metadata)
    collection = getattr(owner, "collection", "")
    return DocumentMediaChange(current, removed_files(
        owned_document_files(doc_id, collection, before), owned_document_files(doc_id, collection, current),
    ), {kind: sorted(added) for kind, names in current.items() if (added := set(names) - set(before.get(kind, [])))})
