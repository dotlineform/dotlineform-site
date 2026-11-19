"""Standalone document Summary blocks and their Search-source omission."""

from __future__ import annotations

from typing import Any

from markdown_renderer import build_markdown_renderer, normalize_markdown_blank_lines

from .standalone_directive import install_standalone_directive


SUMMARY_DIRECTIVE = "[[summary]]"


def install_summary_rule(renderer: Any, *, summary_html: str) -> None:
    """Expand exact standalone blocks after parsing, preserving literal contexts.

    The caller supplies completed restricted Summary markup. This rule wraps it
    without reparsing the authored text or interpreting more source tokens.
    """
    install_standalone_directive(
        renderer, SUMMARY_DIRECTIVE, "docs_summary",
        lambda: f'<div class="docsViewer__summary">{summary_html}</div>\n' if summary_html else "",
    )


def omit_summary_directives(markdown: str) -> str:
    """Keep Summary indexed only as metadata; code examples remain searchable."""
    if SUMMARY_DIRECTIVE not in markdown:
        return markdown
    normalized = normalize_markdown_blank_lines(markdown)
    renderer = build_markdown_renderer()
    install_summary_rule(renderer, summary_html="")
    lines = normalized.splitlines(keepends=True)
    for token in renderer.parse(normalized):
        if token.type == "docs_summary":
            line = token.map[0]
            lines[line] = lines[line].replace(SUMMARY_DIRECTIVE, "", 1)
    return "".join(lines)
