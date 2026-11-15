"""Project the ready reading order and render a Book's ordinary host body."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any
from urllib.parse import urlencode

from docs_json_files import load_json_object
from docs_publication_paths import confined
from docs_publication_preparation import write_json
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, generated_documents_path


@dataclass(frozen=True)
class Chapter:
    doc_id: str
    title: str


@dataclass(frozen=True)
class Heading:
    title: str
    entries: tuple[Chapter | Heading, ...]


BookContents = tuple[Chapter | Heading, ...]


def book_contents(manifest: dict[str, Any]) -> BookContents:
    """Use completed placement and titles, omitting drafts and empty headings."""
    order = manifest["book_order"]
    ready = {row["doc_id"]: row["title"] for row in manifest["docs"] if not row["draft"]}

    def chapters(doc_ids: list[str]) -> list[Chapter]:
        return [Chapter(doc_id, ready[doc_id]) for doc_id in doc_ids if doc_id in ready]

    def headings(nodes: list[dict[str, Any]]) -> list[Heading]:
        result = []
        for node in nodes:
            entries = [*chapters(node["doc_ids"]), *headings(node.get("sections", []))]
            if entries:
                result.append(Heading(node["title"], tuple(entries)))
        return result

    return (*chapters(order["root"]), *headings(order["tree"]))


def changed_book_contents(
    previous: dict[str, Any], current: dict[str, Any], *, selected: set[str] | None = None,
) -> BookContents | None:
    """Skip TOC work on saves that carry the same placement and ready titles."""
    if previous["book_order"] == current["book_order"]:
        def ready_titles(manifest: dict[str, Any]) -> dict[str, str]:
            return {row["doc_id"]: row["title"] for row in manifest["docs"]
                    if not row["draft"] and (selected is None or row["doc_id"] in selected)}

        if ready_titles(previous) == ready_titles(current):
            return None
    completed = book_contents(current)
    return completed if completed != book_contents(previous) else None


def render_book_contents(title: str, collection: str, contents: BookContents) -> str:
    def render_list(entries: BookContents) -> str:
        if not entries:
            return ""
        rows = []
        for entry in entries:
            if isinstance(entry, Chapter):
                query = urlencode({"doc": entry.doc_id, "collection": collection})
                body = f'<a href="?{escape(query)}">{escape(entry.title)}</a>'
            else:
                body = f"{escape(entry.title)}{render_list(entry.entries)}"
            rows.append(f"<li>{body}</li>")
        return f"<ol>{''.join(rows)}</ol>"

    return (f'<h1>{escape(title)}</h1>\n'
            f'<nav data-docs-book-toc aria-label="Table of contents">{render_list(contents)}</nav>\n')


def refresh_book_contents(
    config: DocsStageConfig, book: DocsCollectionConfig, contents: BookContents,
) -> dict[str, Any] | None:
    """Replace the exact saved host body and return its completed payload."""
    host_id = book.report_host_doc_id
    path = confined(generated_documents_path(config), f"by-id/{host_id}.json")
    payload = load_json_object(path, f"Book host {host_id}")
    content = render_book_contents(payload["title"], book.collection, contents)
    if payload["content_html"] == content:
        return None
    payload["content_html"] = content
    write_json(path, payload)
    return payload
