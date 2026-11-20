"""Version 5 Links records distinguish explicit links on each outgoing edge."""

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .links_model import DocumentLinks, DocumentSummary, DocumentTarget, OutgoingLink


def relationship_payload(record: DocumentLinks) -> dict[str, Any]:
    """Serialize unique endpoint summaries in deterministic title/identity order."""
    def summary(document: DocumentSummary) -> dict[str, Any]:
        row = {**asdict(document.target), "title": document.title}
        if isinstance(document, OutgoingLink):
            row["explicit_doc_link"] = document.explicit_doc_link
        return row

    def entries(direction: Mapping[DocumentTarget, DocumentSummary]) -> list[dict[str, Any]]:
        return [summary(direction[key]) for key in sorted(
            direction, key=lambda key: (direction[key].title.casefold(), key),
        )]

    return {
        "schema_version": 5,
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

    outgoing = {}
    for row in payload["outgoing"]:
        endpoint = summary(row)
        outgoing[endpoint.target] = OutgoingLink(endpoint.target, endpoint.title, row["explicit_doc_link"])
    return DocumentLinks(summary(payload["self"]), outgoing, entries(payload["incoming"]))
