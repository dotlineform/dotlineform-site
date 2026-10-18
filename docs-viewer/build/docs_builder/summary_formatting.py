"""Restricted Markdown emphasis shared by document and image summaries."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt


EMPHASIS_RULES = ["emphasis", "escape"]
INLINE_RENDERER = MarkdownIt("zero").enable(EMPHASIS_RULES)
PARAGRAPH_RENDERER = MarkdownIt("zero", {"breaks": True}).enable([*EMPHASIS_RULES, "newline"])


def render_summary_inline(summary: str) -> str:
    """Render image-summary emphasis with literal HTML and retained newlines."""
    return INLINE_RENDERER.renderInline(summary)


def render_summary_paragraphs(summary: str) -> str:
    """Prepare document-summary paragraphs and explicit intra-paragraph breaks."""
    if not summary:
        return ""
    return "".join(
        f"<p>{PARAGRAPH_RENDERER.renderInline(paragraph)}</p>"
        for paragraph in re.split(r"\n[ \t]*\n+", summary)
    )
