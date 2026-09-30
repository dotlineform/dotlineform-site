"""Version 4 Links records: unique flat document summaries in each direction."""

from dataclasses import asdict
from typing import Any

from docs_document_identity import is_document_id
from .links_model import DocumentLinks, DocumentSummary, DocumentTarget


def relationship_payload(record: DocumentLinks) -> dict[str, Any]:
    """Serialize unique endpoint summaries in deterministic title/identity order."""
    def summary(document: DocumentSummary) -> dict[str, str]:
        return {**asdict(document.target), "title": document.title}

    def entries(direction: dict[DocumentTarget, DocumentSummary]) -> list[dict[str, str]]:
        return [summary(direction[key]) for key in sorted(
            direction, key=lambda key: (direction[key].title.casefold(), key),
        )]

    return {
        "schema_version": 4,
        "self": summary(record.document),
        "outgoing": entries(record.outgoing),
        "incoming": entries(record.incoming),
    }


def read_relationship_payload(payload: Any, target: DocumentTarget) -> DocumentLinks:
    """Reject malformed or misowned prior state; never manufacture a replacement."""
    def summary(value: Any) -> DocumentSummary:
        if not isinstance(value, dict) or set(value) != {"collection", "doc_id", "title"}:
            raise ValueError("Links requires a complete document summary")
        identity = {name: value[name] for name in ("collection", "doc_id")}
        if (not all(isinstance(item, str) for item in identity.values())
                or not is_document_id(identity["doc_id"], collection=identity["collection"])):
            raise ValueError("Links document identity does not match Working")
        if not isinstance(value["title"], str) or not value["title"].strip():
            raise ValueError("Links document summary is invalid")
        return DocumentSummary(DocumentTarget(**identity), value["title"])

    def entries(value: Any) -> dict[DocumentTarget, DocumentSummary]:
        if not isinstance(value, list):
            raise ValueError("Links requires incoming and outgoing lists")
        result = {}
        for row in value:
            document = summary(row)
            if document.target in result:
                raise ValueError("Links requires unique document relationships")
            result[document.target] = document
        return result

    if (not isinstance(payload, dict) or payload.get("schema_version") != 4
            or set(payload) != {"schema_version", "self", "outgoing", "incoming"}):
        raise ValueError("Unsupported Links record schema")
    record = DocumentLinks(summary(payload.get("self")), entries(payload.get("outgoing")), entries(payload.get("incoming")))
    if record.document.target != target:
        raise ValueError("Links record identity does not match its exact document")
    return record
