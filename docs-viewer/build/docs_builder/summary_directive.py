"""Standalone document Summary blocks and their Search-source omission."""

from __future__ import annotations

import html
import re
from typing import Any

from markdown_it.rules_block import StateBlock

from markdown_renderer import build_markdown_renderer, normalize_markdown_blank_lines


SUMMARY_DIRECTIVE = "[[summary]]"


def install_summary_rule(renderer: Any, *, summary: str) -> None:
    """Expand exact standalone blocks after parsing, preserving literal contexts.

    The caller supplies the document's normalized metadata text. Summary content
    is escaped directly into HTML and never parsed as Markdown or more tokens.
    """
    def parse(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:
        del end_line
        if state.is_code_block(start_line):
            return False
        start = state.bMarks[start_line] + state.tShift[start_line]
        if state.src[start:state.eMarks[start_line]].strip() != SUMMARY_DIRECTIVE:
            return False
        if not silent:
            token = state.push("docs_summary", "", 0)
            token.map = [start_line, start_line + 1]
            state.line = start_line + 1
        return True

    def render(tokens: Any, index: int, options: Any, env: Any) -> str:
        del tokens, index, options, env
        if not summary:
            return ""
        paragraphs = re.split(r"\n[ \t]*\n+", summary)
        content = "".join(
            "<p>" + "<br>\n".join(html.escape(line) for line in paragraph.split("\n")) + "</p>"
            for paragraph in paragraphs
        )
        return f'<div class="docsViewer__summary">{content}</div>\n'

    # Do not interrupt a paragraph: its inline code may span this entire line.
    renderer.block.ruler.before("paragraph", "docs_summary", parse, {"alt": ["reference", "blockquote", "list"]})
    renderer.renderer.rules["docs_summary"] = render


def omit_summary_directives(markdown: str) -> str:
    """Keep Summary indexed only as metadata; code examples remain searchable."""
    if SUMMARY_DIRECTIVE not in markdown:
        return markdown
    normalized = normalize_markdown_blank_lines(markdown)
    renderer = build_markdown_renderer()
    install_summary_rule(renderer, summary="")
    lines = normalized.splitlines(keepends=True)
    for token in renderer.parse(normalized):
        if token.type == "docs_summary":
            line = token.map[0]
            lines[line] = lines[line].replace(SUMMARY_DIRECTIVE, "", 1)
    return "".join(lines)
