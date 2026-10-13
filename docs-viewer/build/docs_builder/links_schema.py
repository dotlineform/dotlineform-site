"""Version 4 Links records: unique flat document summaries in each direction."""

from dataclasses import asdict
from typing import Any

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


def read_relationship_payload(payload: Any) -> DocumentLinks:
    """Decode saved endpoint summaries without auditing generated relationships."""
    def summary(value: Any) -> DocumentSummary:
        identity = {name: value[name] for name in ("collection", "doc_id")}
        return DocumentSummary(DocumentTarget(**identity), value["title"])

    def entries(value: Any) -> dict[DocumentTarget, DocumentSummary]:
        result = {}
        for row in value:
            document = summary(row)
            result[document.target] = document
        return result

    return DocumentLinks(summary(payload["self"]), entries(payload["outgoing"]), entries(payload["incoming"]))
