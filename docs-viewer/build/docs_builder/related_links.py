"""Render related sections from refreshed Working or captured relationship records."""

from __future__ import annotations

import html
import json
from typing import Any, TYPE_CHECKING

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
) -> dict[DocumentTarget, DocumentLinks]:
    """Use this build's refreshed records or exact saved inputs for its sections.

    The existing Working Links updater owns relationship maintenance. Reuse its
    results for write and dry-run rendering, without a second refresh or read.
    Publish captures selected documents' records with their target rows intact.
    """
    related_documents = {}
    root = builder.related_links_dir
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
            record = read_relationship_payload(json.loads(path.read_text()))
            if record is not None and record.document.target != target:
                raise ValueError("Related-links record identity must match its exact document")
        if record is None:
            continue
        related_documents[target] = record
    return related_documents


def render_related_links(
    builder: DocsDataBuilder, doc: DocRecord, heading: str, catalogue_references: list[dict[str, Any]],
) -> str:
    """Render document relationships and exact authored Gallery targets together."""
    target = DocumentTarget(getattr(builder, "collection_id", ""), doc.doc_id)
    record = builder.related_documents.get(target)
    entries = {**record.incoming, **record.outgoing} if record is not None else {}
    entries.pop(target, None)
    owners = {owner.collection: owner for owner in builder.config.collections}
    catalogue = owners.get("catalogue")
    rows: dict[tuple[str, str, str, str], str] = {}
    for summary in entries.values():
        destination = summary.target
        if destination.collection:
            owner = owners[destination.collection]
            icon = owner.icon
            href = "?" + canonical_document_viewer_url(destination.doc_id, collection=destination.collection).split("?", 1)[1]
        else:
            icon = catalogue.icon if catalogue and destination.doc_id == catalogue.report_host_doc_id else "dlf-doc"
            href = (builder.rendered_viewer_target_for(destination.doc_id) if builder.config.stage == "review"
                    else "?" + canonical_document_viewer_url(destination.doc_id).split("?", 1)[1])
        key = (summary.title.casefold(), "document", destination.collection, destination.doc_id)
        rows[key] = (
            f'<li>{builder.inline_icons.render(icon, decorative=True)} '
            f'<a data-docs-related-link="true" href="{html.escape(href, quote=True)}">{html.escape(summary.title)}</a></li>'
        )
    galleries = {}
    for reference in catalogue_references:
        destination = reference["target"]
        if destination["kind"] == "catalogue-gallery":
            galleries.setdefault(destination["id"], reference["options"]["label"])
    if galleries:
        icon = builder.inline_icons.render("images", decorative=True)
        for gallery_id, label in galleries.items():
            key = (label.casefold(), "gallery", "catalogue", gallery_id)
            item = html.escape(label)
            if builder.config.stage != "review":
                item = (
                    '<span data-docs-content-detail="media" data-docs-media-kind="catalogue-gallery" '
                    f'data-docs-media-id="{html.escape(gallery_id, quote=True)}">'
                    '<button type="button" class="docsViewer__mediaTextLink" data-docs-media-open '
                    f'data-docs-related-link="true">{item}</button></span>'
                )
            rows[key] = f"<li>{icon} {item}</li>"
    if not rows:
        return ""
    level = 2 if target.collection == "catalogue" else 3
    title = f'<h{level}>{html.escape(heading)}</h{level}>\n' if heading else ""
    return f'<section data-docs-related-links="true">{title}<ul>\n' + "\n".join(rows[key] for key in sorted(rows)) + "\n</ul></section>\n"
