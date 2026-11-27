"""Authored reading-page boundaries in supported Markdown collections."""

from typing import Any

from .standalone_directive import install_standalone_directive


PAGE_BREAK_COLLECTIONS = frozenset({"texts", "works", "concepts", "moments", "library"})
PAGE_BREAK_DIRECTIVE = "[[pagebreak]]"
PAGE_BREAK_TOKEN = "docs_page_break"


def install_page_break_rule(renderer: Any) -> None:
    """Emit an invisible boundary for each standalone top-level break."""
    install_standalone_directive(
        renderer, PAGE_BREAK_DIRECTIVE, PAGE_BREAK_TOKEN,
        lambda: '<div data-docs-page-break hidden></div>\n', top_level=True,
    )
