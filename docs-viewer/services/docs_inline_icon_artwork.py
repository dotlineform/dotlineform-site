"""Canonical inline icon artwork and portable markup, independent of Markdown rendering."""

from __future__ import annotations

import base64
import html
from pathlib import Path
import re

from docs_svg_sanitizer import sanitize_svg_bytes
from docs_icon_assets import icon_asset_path


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


class InlineIconArtwork:
    """Read each requested canonical icon once per operation."""

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

