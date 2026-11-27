"""Standalone document Summary blocks."""

from __future__ import annotations

from typing import Any

from .standalone_directive import install_standalone_directive


SUMMARY_DIRECTIVE = "[[summary]]"
SUMMARY_TOKEN = "docs_summary"


def install_summary_rule(renderer: Any, *, summary_html: str) -> None:
    """Expand exact standalone blocks after parsing, preserving literal contexts.

    The caller supplies completed restricted Summary markup. This rule wraps it
    without reparsing the authored text or interpreting more source tokens.
    """
    install_standalone_directive(
        renderer, SUMMARY_DIRECTIVE, SUMMARY_TOKEN,
        lambda: f'<div class="docsViewer__summary">{summary_html}</div>\n' if summary_html else "",
    )
