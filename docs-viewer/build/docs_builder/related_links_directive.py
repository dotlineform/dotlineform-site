"""Standalone plain-heading related-links Markdown block syntax."""

from collections.abc import Callable
from typing import Any

from markdown_it.rules_block import StateBlock
from markdown_renderer import build_markdown_renderer, normalize_markdown_blank_lines


RELATED_LINKS_PREFIX = "[[links|"


def install_related_links_rule(renderer: Any, render_section: Callable[[str], str]) -> None:
    """Preserve fenced/indented code and raw HTML; reject empty plain headings."""
    def parse(state: StateBlock, start_line: int, end_line: int, silent: bool) -> bool:
        del end_line
        if state.is_code_block(start_line):
            return False
        start = state.bMarks[start_line] + state.tShift[start_line]
        line = state.src[start:state.eMarks[start_line]].strip()
        if not line.startswith(RELATED_LINKS_PREFIX) or not line.endswith("]]"):
            return False
        heading = line[len(RELATED_LINKS_PREFIX):-2].strip()
        if "]]" in heading:
            return False
        if not silent:
            if not heading:
                raise ValueError("Related-links directive requires a nonempty heading")
            token = state.push("docs_related_links", "", 0)
            token.content = heading
            token.map = [start_line, start_line + 1]
            state.line = start_line + 1
        return True

    def render(tokens: Any, index: int, options: Any, env: Any) -> str:
        del options, env
        return render_section(tokens[index].content)

    renderer.block.ruler.before("paragraph", "docs_related_links", parse, {"alt": ["paragraph", "reference", "blockquote", "list"]})
    renderer.renderer.rules["docs_related_links"] = render


def render_without_related_links(markdown: str) -> str:
    """Collect authored anchors without interpreting a directive's heading text."""
    renderer = build_markdown_renderer()
    install_related_links_rule(renderer, lambda heading: "")
    return renderer.render(normalize_markdown_blank_lines(markdown))
