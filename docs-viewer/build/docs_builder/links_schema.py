"""Provisional Links JSON projection; graph maintenance does not read this shape."""

from dataclasses import asdict
from typing import Any, Mapping

from .links_model import DocumentLinks, DocumentTarget, Reference, Relationships


def relationship_payload(
    view: Relationships,
    documents: Mapping[DocumentTarget, DocumentLinks],
) -> dict[str, Any]:
    """Serialize one complete links-by-id file with shallow counterpart summaries."""
    def summary(key: DocumentTarget) -> dict[str, Any]:
        document = documents[key]
        return {
            "target": asdict(key), "title": document.title,
            "href": document.href, "subject": document.subject,
        }

    def entries(direction: Mapping[DocumentTarget, tuple[Reference, ...]]) -> list[dict[str, Any]]:
        return [
            {"document": summary(key), "occurrences": [
                {"label": ref.label, "href": ref.href} for ref in direction[key]
            ]}
            for key in sorted(direction, key=lambda key: (documents[key].title.casefold(), key))
        ]

    return {
        "schema_version": 1,
        "self": summary(view.target),
        "outgoing": entries(view.outgoing),
        "incoming": entries(view.incoming),
        "counts": {
            "outgoing_documents": len(view.outgoing),
            "incoming_documents": len(view.incoming),
            "outgoing_occurrences": sum(map(len, view.outgoing.values())),
            "incoming_occurrences": sum(map(len, view.incoming.values())),
        },
    }
