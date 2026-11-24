"""Restricted formatting shared by document and image summaries."""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

from .math_rendering import install_docs_math

EMPHASIS_RULES = ["emphasis", "escape"]


def _summary_renderer(*, paragraph_breaks: bool = False, math: bool = False) -> MarkdownIt:
    renderer = MarkdownIt("zero", {"breaks": paragraph_breaks}).enable(EMPHASIS_RULES)
    if paragraph_breaks:
        renderer.enable("newline")
    if math:
        install_docs_math(renderer)
    return renderer


INLINE_RENDERER = _summary_renderer()
PARAGRAPH_RENDERER = _summary_renderer(paragraph_breaks=True)
MATH_INLINE_RENDERER = _summary_renderer(math=True)
MATH_PARAGRAPH_RENDERER = _summary_renderer(paragraph_breaks=True, math=True)


def render_summary_inline(summary: str, *, math: bool = False) -> str:
    """Render restricted inline image-summary markup with retained newlines."""
    renderer = MATH_INLINE_RENDERER if math else INLINE_RENDERER
    return renderer.renderInline(summary)


def render_summary_paragraphs(summary: str, *, math: bool = False) -> str:
    """Prepare summary paragraphs and explicit intra-paragraph breaks."""
    if not summary:
        return ""
    renderer = MATH_PARAGRAPH_RENDERER if math else PARAGRAPH_RENDERER
    return "".join(
        f"<p>{renderer.renderInline(paragraph)}</p>"
        for paragraph in re.split(r"\n[ \t]*\n+", summary)
    )
