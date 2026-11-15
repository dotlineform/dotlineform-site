"""Parse a document directive occupying its own Markdown block."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from markdown_it.rules_block import StateBlock


def install_standalone_directive(
    renderer: Any, directive: str, token_name: str, render_html: Callable[[], str],
) -> None:
    def parse(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:
        del end_line
        if state.is_code_block(start_line):
            return False
        start = state.bMarks[start_line] + state.tShift[start_line]
        if state.src[start:state.eMarks[start_line]].strip() != directive:
            return False
        if not silent:
            token = state.push(token_name, "", 0)
            token.map = [start_line, start_line + 1]
            state.line = start_line + 1
        return True

    # A paragraph can contain an inline code span across the directive's line.
    renderer.block.ruler.before("paragraph", token_name, parse, {"alt": ["reference", "blockquote", "list"]})
    renderer.renderer.rules[token_name] = lambda *_: render_html()
