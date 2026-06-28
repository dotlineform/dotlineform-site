#!/usr/bin/env python3
"""Rendered Docs content helpers for Data Sharing document workflows."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from markdown_renderer import plain_text_from_html  # noqa: E402


class HeadingCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self._current_tag = ""
        self._current_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        tag_name = tag.lower()
        if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_tag = tag_name
            self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        if not self._current_tag or tag.lower() != self._current_tag:
            return
        text = normalize_text("".join(self._current_parts))
        if text:
            self.headings.append(text)
        self._current_tag = ""
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_tag:
            self._current_parts.append(data)


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def source_doc_for_id(context: Any, doc_id: str) -> Any:
    normalized_doc_id = str(doc_id or "").strip()
    doc = context.source_docs_by_id.get(normalized_doc_id)
    if doc is None:
        raise ValueError(f"unknown doc_id for Data Sharing source context: {normalized_doc_id}")
    return doc


def render_doc_html(context: Any, doc_id: str) -> str:
    normalized_doc_id = str(doc_id or "").strip()
    if normalized_doc_id not in context.render_cache:
        doc = source_doc_for_id(context, normalized_doc_id)
        payload = context.builder.item_entry(doc, context.source_docs, {})
        context.render_cache[normalized_doc_id] = str(payload.get("content_html") or "")
    return context.render_cache[normalized_doc_id]


def doc_content_text(context: Any, doc_id: str) -> str:
    doc = source_doc_for_id(context, doc_id)
    return plain_text_from_html(render_doc_html(context, doc.doc_id), title=doc.title)


def doc_headings(context: Any, doc_id: str) -> list[str]:
    doc = source_doc_for_id(context, doc_id)
    parser = HeadingCollector()
    parser.feed(render_doc_html(context, doc.doc_id))
    parser.close()
    headings = list(parser.headings)
    if headings and normalize_text(headings[0]) == normalize_text(doc.title):
        headings.pop(0)
    return headings
