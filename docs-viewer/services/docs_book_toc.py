"""Project and render the ready reading order for a Book."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
from typing import Any
from urllib.parse import urlencode

@dataclass(frozen=True)
class Chapter:
    doc_id: str
    title: str


@dataclass(frozen=True)
class Heading:
    title: str
    entries: tuple[Chapter | Heading, ...]


@dataclass(frozen=True)
class BookContents:
    before: tuple[Chapter, ...]
    entries: tuple[Chapter | Heading, ...]
    after: tuple[Chapter, ...]

    def reading_order(self, host: Chapter | None) -> tuple[Chapter, ...]:
        def flatten(entries: tuple[Chapter | Heading, ...]):
            for entry in entries:
                if isinstance(entry, Heading):
                    yield from flatten(entry.entries)
                else:
                    yield entry

        return (*self.before, *((host,) if host else ()), *flatten(self.entries), *self.after)


def edition_rows(manifest: dict[str, Any], edition: str) -> dict[str, dict[str, Any]]:
    """Select ready pages for an edition from completed Book metadata."""
    order = manifest["book_order"]
    matter = set(order["front"]) | set(order["back"])
    return {row["doc_id"]: row for row in manifest["docs"]
            if not row["draft"] and (row["doc_id"] not in matter or row.get("book_edition", "both") in ("both", edition))}


def book_contents(manifest: dict[str, Any], host_id: str, *, edition: str = "web") -> BookContents:
    """Project reading order and TOC entries from the same ready selection."""
    order = manifest["book_order"]
    ready = edition_rows(manifest, edition)

    def chapters(doc_ids: list[str]) -> list[Chapter]:
        return [Chapter(doc_id, ready[doc_id]["title"]) for doc_id in doc_ids if doc_id in ready]

    def headings(nodes: list[dict[str, Any]]) -> list[Heading]:
        result = []
        for node in nodes:
            entries = [*chapters(node["doc_ids"]), *headings(node.get("sections", []))]
            if entries:
                result.append(Heading(node["title"], tuple(entries)))
        return result

    front = order["front"]
    toc_position = front.index(host_id)
    return BookContents(
        tuple(chapters(front[:toc_position])),
        (*chapters(front[toc_position + 1:]), *chapters(order["root"]), *headings(order["tree"])),
        tuple(chapters(order["back"])),
    )


def changed_book_contents(
    previous: dict[str, Any], current: dict[str, Any], host_id: str, *, selected: set[str] | None = None,
) -> BookContents | None:
    """Refresh when either the TOC entries or reading order change."""
    if previous["book_order"] == current["book_order"]:
        def ready_titles(manifest: dict[str, Any]) -> dict[str, str]:
            return {doc_id: row["title"] for doc_id, row in edition_rows(manifest, "web").items()
                    if selected is None or doc_id in selected}

        if ready_titles(previous) == ready_titles(current):
            return None
    completed = book_contents(current, host_id)
    return completed if completed != book_contents(previous, host_id) else None


def render_book_contents(collection: str, host: Chapter, contents: BookContents) -> str:
    def render_list(entries: tuple[Chapter | Heading, ...]) -> str:
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

    reading_order = [[entry.doc_id, entry.title] for entry in contents.reading_order(host)]
    order = escape(json.dumps(reading_order, ensure_ascii=False))
    return (f'<nav data-docs-book-toc="{escape(collection)}" data-book-host="{escape(host.doc_id)}" '
            f'data-book-order="{order}" aria-label="Table of contents">{render_list(contents.entries)}</nav>\n')
