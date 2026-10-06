"""Render extensionless icon tokens as self-contained inline SVG masks.

Artwork stays in the canonical icon folder. Each renderer caches requested SVGs
for one build and emits portable HTML without reader-time asset resolution.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
import re
from collections.abc import Callable
from typing import Any

from markdown_it.rules_inline import StateInline

from .common import render_markdown_to_html
from .related_links_directive import RELATED_LINKS_PREFIX, install_related_links_rule
from .summary_directive import SUMMARY_DIRECTIVE, install_summary_rule
from markdown_renderer import build_markdown_renderer, normalize_markdown_blank_lines
from docs_svg_sanitizer import sanitize_svg_bytes
from docs_icon_assets import icon_asset_path


ICON_TOKEN_PREFIX = "[[icon:"
LITERAL_HTML_TAG_PATTERN = re.compile(r"</?(?:code|pre|script|style|textarea)\b", re.IGNORECASE)
# Saved Affinity artwork declares an external DTD. Remove that declaration,
# without loading it; the existing sanitizer still rejects entities/internal DTDs.
EXTERNAL_SVG_DOCTYPE_PATTERN = re.compile(
    rb"<!DOCTYPE\s+svg\s+(?:PUBLIC\s+['\"][^'\"]*['\"]\s+['\"][^'\"]*['\"]|SYSTEM\s+['\"][^'\"]*['\"])\s*>",
    re.IGNORECASE,
)
ICON_STYLE = (
    "display:inline-block;width:1em;height:1em;vertical-align:-0.125em;"
    "background-color:currentColor;mask-position:center;mask-size:contain;mask-repeat:no-repeat;"
)
TEXT_STYLE = (
    "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;"
    "clip-path:inset(50%);white-space:nowrap;"
)


class InlineIconRenderer:
    """Own exact SVG lookup and shared markup for authored/generated icons."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self._mask_urls: dict[str, str] = {}

    def _mask_url(self, name: str) -> str:
        if name not in self._mask_urls:
            path = icon_asset_path(self.repo_root, name)
            try:
                source = EXTERNAL_SVG_DOCTYPE_PATTERN.sub(b"", path.read_bytes())
            except OSError as exc:
                raise ValueError(f"Icon SVG could not be read: {name}.svg") from exc
            try:
                sanitized = sanitize_svg_bytes(source)
            except ValueError as exc:
                raise ValueError(f"Icon SVG {name}.svg: {exc}") from exc
            if sanitized.warnings:
                reasons = "; ".join(sanitized.warnings)
                raise ValueError(f"Icon SVG requires sanitization fixes: {name}.svg ({reasons})")
            encoded = base64.b64encode(sanitized.bytes).decode("ascii")
            self._mask_urls[name] = f"data:image/svg+xml;base64,{encoded}"
        return self._mask_urls[name]

    def render(self, name: str, *, decorative: bool = False) -> str:
        """Render one exact icon; text exports retain its extensionless token.

        Generated lists may mark an icon decorative when their text supplies its
        meaning. Authored icons expose the filename stem as their accessible name.
        """
        mask_url = self._mask_url(name)
        semantics = 'aria-hidden="true"' if decorative else f'role="img" aria-label="{html.escape(name, quote=True)}"'
        style = html.escape(f"{ICON_STYLE}mask-image:url({mask_url});", quote=True)
        return (
            f'<span class="docsViewer__inlineIcon" data-docs-icon="{name}" {semantics} style="{style}">'
            f'<span aria-hidden="true" style="{TEXT_STYLE}">[[icon:{name}]]</span></span>'
        )

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

    def render_markdown(self, markdown: str, *, related_links: Callable[[str], str] | None = None, summary: str = "") -> str:
        """Expand inline icons and document blocks, preserving literal code.

        Normal Markdown parsing also protects fences, indented code, comments,
        escaped text and raw HTML attributes. Icon tokens create no relationships.
        """
        if ICON_TOKEN_PREFIX not in markdown and RELATED_LINKS_PREFIX not in markdown and SUMMARY_DIRECTIVE not in markdown:
            return render_markdown_to_html(markdown)
        renderer = build_markdown_renderer()
        if SUMMARY_DIRECTIVE in markdown:
            install_summary_rule(renderer, summary=summary)
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
