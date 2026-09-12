"""Version 1 Links records: validated prior state and deterministic projection."""

from dataclasses import asdict
from typing import Any

from docs_document_identity import is_immutable_doc_id
from .links_model import DocumentLinks, DocumentSummary, DocumentTarget, Occurrence, Relationship


def relationship_payload(record: DocumentLinks) -> dict[str, Any]:
    """Serialize one record with stable summaries, occurrence order and counts."""
    def entries(direction: dict[DocumentTarget, Relationship]) -> list[dict[str, Any]]:
        return [asdict(direction[key]) for key in sorted(
            direction, key=lambda key: (direction[key].document.title.casefold(), key),
        )]

    return {
        "schema_version": 1,
        "self": asdict(record.document),
        "outgoing": entries(record.outgoing),
        "incoming": entries(record.incoming),
        "counts": {
            "outgoing_documents": len(record.outgoing),
            "incoming_documents": len(record.incoming),
            "outgoing_occurrences": sum(len(entry.occurrences) for entry in record.outgoing.values()),
            "incoming_occurrences": sum(len(entry.occurrences) for entry in record.incoming.values()),
        },
    }


def read_relationship_payload(payload: Any, target: DocumentTarget) -> DocumentLinks:
    """Reject malformed or misowned prior state; never manufacture a replacement."""
    def summary(value: Any) -> DocumentSummary:
        if not isinstance(value, dict) or set(value) != {"target", "title", "href", "subject"}:
            raise ValueError("Links requires a complete document summary")
        identity = value["target"]
        if not isinstance(identity, dict) or set(identity) != {"scope", "sub_scope", "doc_id"}:
            raise ValueError("Links requires an exact document target")
        if (not all(isinstance(item, str) for item in identity.values())
                or identity["scope"] != target.scope or not is_immutable_doc_id(identity["doc_id"])):
            raise ValueError("Links document identity does not match its scope")
        if not isinstance(value["title"], str) or not isinstance(value["href"], str) or not isinstance(value["subject"], dict):
            raise ValueError("Links document summary is invalid")
        return DocumentSummary(DocumentTarget(**identity), value["title"], value["href"], value["subject"])

    def entries(value: Any) -> dict[DocumentTarget, Relationship]:
        if not isinstance(value, list):
            raise ValueError("Links requires incoming and outgoing lists")
        result = {}
        for row in value:
            if not isinstance(row, dict) or set(row) != {"document", "occurrences"}:
                raise ValueError("Links relationship is invalid")
            document = summary(row["document"])
            occurrences = row["occurrences"]
            if document.target in result or not isinstance(occurrences, list) or not occurrences:
                raise ValueError("Links requires unique relationships with occurrences")
            if any(not isinstance(item, dict) or set(item) != {"label", "href"}
                   or not all(isinstance(text, str) for text in item.values()) for item in occurrences):
                raise ValueError("Links occurrence is invalid")
            result[document.target] = Relationship(document, tuple(Occurrence(**item) for item in occurrences))
        return result

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Unsupported Links record schema")
    record = DocumentLinks(summary(payload.get("self")), entries(payload.get("outgoing")), entries(payload.get("incoming")))
    if record.document.target != target:
        raise ValueError("Links record identity does not match its exact document")
    if payload.get("counts") != relationship_payload(record)["counts"]:
        raise ValueError("Links counts do not match its relationships")
    return record
