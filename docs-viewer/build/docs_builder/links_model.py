"""One document's prepared relationships and contributor replacement operations."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, order=True)
class DocumentTarget:
    scope: str
    sub_scope: str
    doc_id: str


@dataclass(frozen=True)
class DocumentSummary:
    target: DocumentTarget
    title: str
    href: str
    subject: dict[str, Any]


@dataclass(frozen=True)
class Occurrence:
    label: str
    href: str


@dataclass(frozen=True)
class Relationship:
    document: DocumentSummary
    occurrences: tuple[Occurrence, ...]


@dataclass
class DocumentLinks:
    document: DocumentSummary
    outgoing: dict[DocumentTarget, Relationship] = field(default_factory=dict)
    incoming: dict[DocumentTarget, Relationship] = field(default_factory=dict)


def replace_contribution(
    entries: dict[DocumentTarget, Relationship],
    document: DocumentSummary,
    occurrences: tuple[Occurrence, ...],
) -> None:
    """Replace/remove one contributor while preserving every other contributor."""
    if occurrences:
        entries[document.target] = Relationship(document, occurrences)
    else:
        entries.pop(document.target, None)


def reference_counts(entries: dict[DocumentTarget, Relationship]) -> Counter:
    """Count authored occurrences, including repeats, for refresh diagnostics."""
    return Counter((target, occurrence) for target, entry in entries.items() for occurrence in entry.occurrences)
