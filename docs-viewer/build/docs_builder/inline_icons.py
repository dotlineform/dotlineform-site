"""Render extensionless icon tokens as self-contained inline SVG masks.

Artwork stays in the canonical icon folder. Each renderer caches requested SVGs
for one build and emits portable HTML without reader-time asset resolution.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from markdown_it.rules_inline import StateInline

from .math_rendering import build_docs_markdown_renderer
from .related_links_directive import RELATED_LINKS_PREFIX, install_related_links_rule
from .standalone_directive import install_standalone_directive
from .summary_directive import SUMMARY_DIRECTIVE, install_summary_rule
from markdown_renderer import normalize_markdown_blank_lines
from docs_inline_icon_artwork import InlineIconArtwork


ICON_TOKEN_PREFIX = "[[icon:"
DATE_TOKEN = "[[date]]"
TOC_DIRECTIVE = "[[toc]]"
LITERAL_HTML_TAG_PATTERN = re.compile(r"</?(?:code|pre|script|style|textarea)\b", re.IGNORECASE)


def inside_literal_html(state: StateInline) -> bool:
    depth = 0
    for token in state.tokens:
        if token.type == "html_inline" and LITERAL_HTML_TAG_PATTERN.match(token.content):
            depth = max(0, depth - 1) if token.content.startswith("</") else depth + 1
    return depth > 0


def install_date_rule(renderer: Any, date_text: str) -> None:
    def parse(state: StateInline, silent: bool) -> bool:
        if not state.src.startswith(DATE_TOKEN, state.pos, state.posMax) or inside_literal_html(state):
            return False
        if not silent:
            token = state.push("text" if date_text else "docs_empty_date", "", 0)
            token.content = date_text
        state.pos += len(DATE_TOKEN)
        return True

    renderer.inline.ruler.before("link", "docs_date", parse)
    if not date_text:
        renderer.renderer.rules["docs_empty_date"] = lambda *_: ""

        def suppress_empty_date_paragraph(state: Any) -> None:
            for index, token in enumerate(state.tokens[1:-1], 1):
                if token.type == "inline" and token.content.strip() == DATE_TOKEN and state.tokens[index - 1].type == "paragraph_open":
                    state.tokens[index - 1].hidden = True
                    state.tokens[index + 1].hidden = True

        renderer.core.ruler.after("inline", "docs_empty_date_paragraph", suppress_empty_date_paragraph)


class InlineIconRenderer(InlineIconArtwork):
    """Own exact SVG lookup and shared markup for authored/generated icons."""

    def _parse_icon(self, state: StateInline, silent: bool) -> bool:
        if not state.src.startswith(ICON_TOKEN_PREFIX, state.pos) or inside_literal_html(state):
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

    def render_markdown(
        self, markdown: str, *, related_links: Callable[[str], str] | None = None,
        summary_html: str = "", date_text: str = "", toc_html: Callable[[], str] | None = None,
    ) -> str:
        """Render Docs Markdown with math, inline icons and document fields.

        Normal Markdown parsing also protects fences, indented code, comments,
        escaped text and raw HTML attributes. Icon tokens create no relationships.
        """
        has_date = DATE_TOKEN in markdown
        has_toc = toc_html is not None and TOC_DIRECTIVE in markdown
        renderer = build_docs_markdown_renderer()
        if not has_date and not has_toc and all(
            marker not in markdown for marker in (ICON_TOKEN_PREFIX, RELATED_LINKS_PREFIX, SUMMARY_DIRECTIVE)
        ):
            return renderer.render(normalize_markdown_blank_lines(markdown))
        if has_date:
            install_date_rule(renderer, date_text)
        if SUMMARY_DIRECTIVE in markdown:
            install_summary_rule(renderer, summary_html=summary_html)
        if has_toc:
            install_standalone_directive(renderer, TOC_DIRECTIVE, "docs_toc", toc_html)
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
