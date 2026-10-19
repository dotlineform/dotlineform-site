"""Render extensionless icon tokens as self-contained inline SVG masks.

Artwork stays in the canonical icon folder. Each renderer caches requested SVGs
for one build and emits portable HTML without reader-time asset resolution.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from markdown_it.rules_inline import StateInline

from .common import render_markdown_to_html
from .related_links_directive import RELATED_LINKS_PREFIX, install_related_links_rule
from .summary_directive import SUMMARY_DIRECTIVE, install_summary_rule
from markdown_renderer import build_markdown_renderer, normalize_markdown_blank_lines
from docs_inline_icon_artwork import InlineIconArtwork


ICON_TOKEN_PREFIX = "[[icon:"
LITERAL_HTML_TAG_PATTERN = re.compile(r"</?(?:code|pre|script|style|textarea)\b", re.IGNORECASE)


class InlineIconRenderer(InlineIconArtwork):
    """Own exact SVG lookup and shared markup for authored/generated icons."""

    def _parse_icon(self, state: StateInline, silent: bool) -> bool:
        if not state.src.startswith(ICON_TOKEN_PREFIX, state.pos):
            return False
        literal_depth = 0
        for previous in state.tokens:
            if previous.type == "html_inline" and LITERAL_HTML_TAG_PATTERN.match(previous.content):
                literal_depth = max(0, literal_depth - 1) if previous.content.startswith("</") else literal_depth + 1
        if literal_depth:
            return False
        closing = state.src.find("]]", state.pos + len(ICON_TOKEN_PREFIX), state.posMax)
        if closing < 0:
            return False
        name = state.src[state.pos + len(ICON_TOKEN_PREFIX):closing]
        if not silent:
            token = state.push("docs_inline_icon", "", 0)
            token.meta = {"name": name}
        state.pos = closing + 2
        return True

    def render_markdown(self, markdown: str, *, related_links: Callable[[str], str] | None = None, summary_html: str = "") -> str:
        """Expand inline icons and document blocks, preserving literal code.

        Normal Markdown parsing also protects fences, indented code, comments,
        escaped text and raw HTML attributes. Icon tokens create no relationships.
        """
        if ICON_TOKEN_PREFIX not in markdown and RELATED_LINKS_PREFIX not in markdown and SUMMARY_DIRECTIVE not in markdown:
            return render_markdown_to_html(markdown)
        renderer = build_markdown_renderer()
        if SUMMARY_DIRECTIVE in markdown:
            install_summary_rule(renderer, summary_html=summary_html)
        if RELATED_LINKS_PREFIX in markdown:
            if related_links is None:
                raise ValueError("Related links require a prepared document relationship context")
            install_related_links_rule(renderer, related_links)
        renderer.inline.ruler.before("link", "docs_inline_icon", self._parse_icon)
        render_image = renderer.renderer.rules["image"]

        def render_icon(tokens: Any, index: int, options: Any, env: Any) -> str:
            del options, env
            return self.render(tokens[index].meta["name"])

        def preserve_alt_tokens(tokens: Any) -> None:
            for token in tokens or []:
                if token.type == "docs_inline_icon":
                    token.type = "text"
                    token.content = f"[[icon:{token.meta['name']}]]"
                preserve_alt_tokens(token.children)

        def render_image_with_literal_icons(tokens: Any, index: int, options: Any, env: Any) -> str:
            preserve_alt_tokens(tokens[index].children)
            return render_image(tokens, index, options, env)

        renderer.renderer.rules["docs_inline_icon"] = render_icon
        renderer.renderer.rules["image"] = render_image_with_literal_icons
        return renderer.render(normalize_markdown_blank_lines(markdown))
