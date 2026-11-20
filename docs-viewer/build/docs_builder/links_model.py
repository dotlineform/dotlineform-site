"""One document's unique directed relationships and endpoint summaries."""

from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class DocumentTarget:
    collection: str
    doc_id: str


@dataclass(frozen=True)
class DocumentSummary:
    target: DocumentTarget
    title: str


@dataclass(frozen=True)
class OutgoingLink(DocumentSummary):
    explicit_doc_link: bool


@dataclass
class DocumentLinks:
    document: DocumentSummary
    outgoing: dict[DocumentTarget, OutgoingLink] = field(default_factory=dict)
    incoming: dict[DocumentTarget, DocumentSummary] = field(default_factory=dict)
