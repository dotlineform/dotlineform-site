"""Render related sections from refreshed Working or captured relationship records."""

from __future__ import annotations

import html
import json
from typing import TYPE_CHECKING

from .links_model import DocumentLinks, DocumentTarget
from .links_schema import read_relationship_payload
from .related_links_directive import RELATED_LINKS_PREFIX
from .source import DocRecord
from docs_document_location import canonical_document_viewer_url

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


def prepare_related_links(
    builder: DocsDataBuilder, docs: list[DocRecord],
    current_records: dict[DocumentTarget, DocumentLinks | None],
) -> None:
    """Use this build's refreshed records or exact saved inputs for its sections.

    The existing Working Links updater owns relationship maintenance. Reuse its
    results for write and dry-run rendering, without a second refresh or read.
    Publish captures selected documents' records with their target rows intact.
    """
    builder.related_documents = {}
    root = builder.related_links_dir
    owners = {"", *(owner.collection for owner in builder.config.collections)}
    for doc in docs:
        if builder.only_doc_ids is not None and doc.doc_id not in builder.only_doc_ids:
            continue
        if RELATED_LINKS_PREFIX not in doc.body_markdown:
            continue
        target = DocumentTarget(getattr(builder, "collection_id", ""), doc.doc_id)
        if target in current_records:
            record = current_records[target]
        else:
            path = root / f"{doc.doc_id}.json"
            if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
                raise ValueError("Related-links JSON must stay inside its configured directory")
            if not path.is_file():
                continue
            record = read_relationship_payload(json.loads(path.read_text()), target)
        if record is None:
            continue
        if record.document.target != target:
            raise ValueError("Related-links record identity must match its exact document")
        if any(neighbour.collection not in owners for neighbour in record.incoming.keys() | record.outgoing.keys()):
            raise ValueError("Related links require exact configured collection owners")
        builder.related_documents[target] = record


def render_related_links(builder: DocsDataBuilder, doc: DocRecord, heading: str) -> str:
    """Emit a sorted list with portable targets, decorative icons and an optional heading."""
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
            href = "?" + canonical_document_viewer_url(destination.doc_id, collection=destination.collection).split("?", 1)[1]
        else:
            icon = "dlf-doc"
            href = (builder.rendered_viewer_target_for(destination.doc_id) if builder.config.stage == "review"
                    else "?" + canonical_document_viewer_url(destination.doc_id).split("?", 1)[1])
        rows.append(f'<li>{builder.inline_icons.render(icon, decorative=True)} <a data-docs-related-link="true" href="{html.escape(href, quote=True)}">{html.escape(summary.title)}</a></li>')
    level = 2 if target.collection == "catalogue" else 3
    title = f'<h{level}>{html.escape(heading)}</h{level}>\n' if heading else ""
    return f'<section data-docs-related-links="true">{title}<ul>\n' + "\n".join(rows) + "\n</ul></section>\n"
