"""Render related sections from currently persisted relationship JSON."""

from __future__ import annotations

import html
import json
from typing import TYPE_CHECKING

from .links_model import DocumentTarget
from .links_schema import read_relationship_payload
from .related_links_directive import RELATED_LINKS_PREFIX
from .source import DocRecord
from docs_document_location import canonical_document_viewer_url

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


def prepare_related_links(builder: DocsDataBuilder, docs: list[DocRecord]) -> None:
    """Read exact saved records for rendered documents that request a section.

    Both full and targeted builds use persisted incoming/outgoing summaries. This
    performs no source discovery, relationship derivation or neighbour writes.
    Publish supplies captured records filtered to its eligible document set.
    """
    builder.related_documents = {}
    root = builder.related_links_dir
    owners = {"", *(owner.collection for owner in builder.config.collections)}
    for doc in docs:
        if builder.only_doc_ids is not None and doc.doc_id not in builder.only_doc_ids:
            continue
        if RELATED_LINKS_PREFIX not in doc.body_markdown:
            continue
        path = root / f"{doc.doc_id}.json"
        if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
            raise ValueError("Related-links JSON must stay inside its configured directory")
        if not path.is_file():
            continue
        target = DocumentTarget(getattr(builder, "collection_id", ""), doc.doc_id)
        record = read_relationship_payload(json.loads(path.read_text()), target)
        if any(neighbour.collection not in owners for neighbour in record.incoming.keys() | record.outgoing.keys()):
            raise ValueError("Related links require exact configured collection owners")
        builder.related_documents[target] = record


def render_related_links(builder: DocsDataBuilder, doc: DocRecord, heading: str) -> str:
    """Emit one title-sorted list with portable targets and shared decorative icons."""
    target = DocumentTarget(getattr(builder, "collection_id", ""), doc.doc_id)
    record = builder.related_documents.get(target)
    if record is None:
        return ""
    entries = {**record.incoming, **record.outgoing}
    entries.pop(target, None)
    if not entries:
        return ""
    owners = {owner.collection: owner for owner in builder.config.collections}
    rows = []
    for summary in sorted(entries.values(), key=lambda entry: (entry.title.casefold(), entry.target)):
        destination = summary.target
        if destination.collection:
            owner = owners[destination.collection]
            icon = owner.icon
            href = "?" + canonical_document_viewer_url(owner.report_host_doc_id, subdoc_id=destination.doc_id, subdoc_collection=destination.collection).split("?", 1)[1]
        else:
            icon = "dlf-doc"
            href = (builder.rendered_viewer_target_for(destination.doc_id) if builder.config.stage == "review"
                    else "?" + canonical_document_viewer_url(destination.doc_id).split("?", 1)[1])
        rows.append(f'<li>{builder.inline_icons.render(icon, decorative=True)} <a data-docs-related-link="true" href="{html.escape(href, quote=True)}">{html.escape(summary.title)}</a></li>')
    return f'<section data-docs-related-links="true"><h2>{html.escape(heading)}</h2>\n<ul>\n' + "\n".join(rows) + "\n</ul></section>\n"
