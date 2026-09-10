"""Schema-independent document references, differences and relationship views."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, order=True)
class DocumentTarget:
    scope: str
    sub_scope: str
    doc_id: str


@dataclass(frozen=True)
class Reference:
    target: DocumentTarget
    label: str
    href: str


@dataclass(frozen=True)
class DocumentLinks:
    target: DocumentTarget
    title: str
    href: str
    subject: dict[str, Any]
    eligible: bool
    exists: bool
    references: tuple[Reference, ...]


@dataclass(frozen=True)
class LinkChanges:
    added: tuple[Reference, ...]
    deleted: tuple[Reference, ...]
    metadata_changed: bool


@dataclass(frozen=True)
class Relationships:
    target: DocumentTarget
    outgoing: Mapping[DocumentTarget, tuple[Reference, ...]]
    incoming: Mapping[DocumentTarget, tuple[Reference, ...]]


def compare_links(
    before: Mapping[DocumentTarget, DocumentLinks],
    after: Mapping[DocumentTarget, DocumentLinks],
) -> dict[DocumentTarget, LinkChanges]:
    """Compare unfiltered references, retaining repeated occurrences and deletions.

    Readiness is absent from this model: changing draft alone has no effect.
    Metadata/existence changes count even when no authored link changes.
    """
    changes = {}
    def metadata(doc):
        return (doc.title, doc.href, doc.subject, doc.eligible, doc.exists) if doc else None

    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key), after.get(key)
        if old == new:
            continue
        old_refs = Counter(old.references if old else ())
        new_refs = Counter(new.references if new else ())
        changes[key] = LinkChanges(
            added=tuple((new_refs - old_refs).elements()),
            deleted=tuple((old_refs - new_refs).elements()),
            metadata_changed=metadata(old) != metadata(new),
        )
    return changes


def relationship_views(
    documents: Mapping[DocumentTarget, DocumentLinks],
) -> dict[DocumentTarget, Relationships]:
    """Prepare shallow views from authoritative references, independently of JSON.

    Incoming entries are the reverse of authored outgoing references. Excluded
    and missing endpoints remain in the input baseline but never in the views.
    Recomputing the admitted graph supports initialisation and ordinary recovery;
    the writer compares records and changes only affected files.
    """
    admitted = {key for key, doc in documents.items() if doc.eligible and doc.exists}
    outgoing = {key: defaultdict(list) for key in admitted}
    incoming = {key: defaultdict(list) for key in admitted}
    for source in sorted(admitted):
        for reference in documents[source].references:
            if reference.target in admitted:
                outgoing[source][reference.target].append(reference)
                incoming[reference.target][source].append(reference)
    return {
        key: Relationships(
            key,
            {target: tuple(refs) for target, refs in outgoing[key].items()},
            {target: tuple(refs) for target, refs in incoming[key].items()},
        )
        for key in sorted(admitted)
    }
