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
    entries: tuple[Chapter, ...]
    linked: bool


@dataclass(frozen=True)
class BookContents:
    before: tuple[Chapter, ...]
    entries: tuple[Chapter | Heading, ...]
    after: tuple[Chapter, ...]

    def reading_order(self, host: Chapter | None) -> tuple[Chapter, ...]:
        chapters = tuple(chapter for entry in self.entries
                         for chapter in (entry.entries if isinstance(entry, Heading) else (entry,)))
        return (*self.before, *((host,) if host else ()), *chapters, *self.after)


def edition_rows(manifest: dict[str, Any], edition: str) -> dict[str, dict[str, Any]]:
    """Select ready pages for an edition from completed Book metadata."""
    order = manifest["book_order"]
    matter = set(order["front"]) | set(order["back"])
    chapters = set(order["root"])
    for part in order["tree"]:
        if "sections" in part:
            chapters.update(part["doc_ids"])
    ready = {}
    for row in manifest["docs"]:
        if row["draft"]:
            continue
        doc_id = row["doc_id"]
        if doc_id in chapters or (doc_id in matter and row.get("book_edition", "both") in ("both", edition)):
            ready[doc_id] = row
    return ready


def book_contents(manifest: dict[str, Any], host_id: str, *, edition: str = "web") -> BookContents:
    """Project reading order and TOC entries from the same ready selection."""
    return project_book_contents(manifest["book_order"], edition_rows(manifest, edition), host_id)


def project_book_contents(order: dict[str, Any], ready: dict[str, dict[str, Any]], host_id: str) -> BookContents:
    def chapters(doc_ids: list[str]) -> list[Chapter]:
        return [Chapter(doc_id, ready[doc_id]["title"]) for doc_id in doc_ids if doc_id in ready]

    linked = order.get("link_part_headings", False)
    parts = []
    for part in order["tree"]:
        if "sections" in part and (entries := chapters(part["doc_ids"])):
            parts.append(Heading(part["title"], tuple(entries), linked))
    front = order["front"]
    toc_position = front.index(host_id)
    return BookContents(
        tuple(chapters(front[:toc_position])),
        (*chapters(front[toc_position + 1:]), *chapters(order["root"]), *parts),
        tuple(chapters(order["back"])),
    )


def changed_book_contents(
    previous: dict[str, Any], current: dict[str, Any], host_id: str, *, selected: set[str] | None = None,
) -> BookContents | None:
    """Refresh when either the TOC entries or reading order change."""
    before = edition_rows(previous, "web")
    after = edition_rows(current, "web")
    if previous["book_order"] == current["book_order"]:
        def ready_titles(rows: dict[str, dict[str, Any]]) -> dict[str, str]:
            return {doc_id: row["title"] for doc_id, row in rows.items()
                    if selected is None or doc_id in selected}

        if ready_titles(before) == ready_titles(after):
            return None
    completed = project_book_contents(current["book_order"], after, host_id)
    return completed if completed != project_book_contents(previous["book_order"], before, host_id) else None


def render_book_contents(collection: str, host: Chapter, contents: BookContents) -> str:
    def link(doc_id: str, title: str) -> str:
        query = urlencode({"doc": doc_id, "collection": collection})
        return f'<a href="?{escape(query)}">{escape(title)}</a>'

    def render_list(entries: tuple[Chapter | Heading, ...]) -> str:
        if not entries:
            return ""
        rows = "".join(f"<li>{render_entry(entry)}</li>" for entry in entries)
        return f"<ol>{rows}</ol>"

    def render_entry(entry: Chapter | Heading) -> str:
        if isinstance(entry, Chapter):
            return link(entry.doc_id, entry.title)
        if entry.linked:
            return link(entry.entries[0].doc_id, entry.title) + render_list(entry.entries[1:])
        return escape(entry.title) + render_list(entry.entries)

    reading_order = [[entry.doc_id, entry.title] for entry in contents.reading_order(host)]
    order = escape(json.dumps(reading_order, ensure_ascii=False))
    return (f'<nav data-docs-book-toc="{escape(collection)}" data-book-host="{escape(host.doc_id)}" '
            f'data-book-order="{order}" aria-label="Table of contents">{render_list(contents.entries)}</nav>\n')
