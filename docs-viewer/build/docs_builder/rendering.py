from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .common import (
    HTML_ATTR_PATTERN_TEMPLATE,
    IMG_PATTERN,
    INTERACTIVE_HTML_FILENAME_PATTERN,
    INTERACTIVE_HTML_HEIGHT_PATTERN,
    INTERACTIVE_HTML_TOKEN_PATTERN,
    MEDIA_IMAGE_TOKEN_PATTERN,
    MEDIA_TOKEN_ALLOWED_ATTRS,
    MEDIA_TOKEN_DIMENSION_PATTERN,
    MEDIA_TOKEN_PATTERN,
    html_attr,
    load_docs_scope_configs,
    normalize_viewer_base_url,
)
from .source import DocRecord


def add_missing_image_titles(content_html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw_attrs = match.group(1) or ""
        alt = html_attr(raw_attrs, "alt").strip()
        title = html_attr(raw_attrs, "title").strip()
        if not alt or title:
            return match.group(0)
        attrs = re.sub(r"\s*/\s*\Z", "", raw_attrs)
        closing = " /" if re.search(r"\s*/\s*\Z", raw_attrs) else ""
        return f'<img{attrs} title="{html.escape(html.unescape(alt), quote=True)}"{closing}>'

    return IMG_PATTERN.sub(replace, content_html or "")


class ContentRenderingMixin:
    def rewrite_doc_links(self, content_html: str, *, current_doc: DocRecord, docs: list[DocRecord]) -> str:
        docs_by_id = {doc.doc_id: doc for doc in docs}

        def replace(match: re.Match[str]) -> str:
            quote_char = match.group(1)
            href = match.group(2)
            rewritten = self.rewrite_href(
                href,
                current_doc=current_doc,
                docs_by_id=docs_by_id,
            )
            return f"href={quote_char}{rewritten}{quote_char}"

        return re.sub(r"href=([\"'])(.*?)\1", replace, content_html)

    def rewrite_href(
        self,
        href: str,
        *,
        current_doc: DocRecord,
        docs_by_id: dict[str, DocRecord],
    ) -> str:
        if not href or href.startswith(("#", "mailto:")) or re.match(r"\A[a-z][a-z0-9+\-.]*:", href, re.IGNORECASE):
            return href
        parsed = urlparse(href)
        path_part = parsed.path or ""
        if not path_part:
            return href
        query_values = parse_qs(parsed.query)
        viewer_doc_id = (query_values.get("doc") or [""])[0]
        if viewer_doc_id and self.viewer_path_match(path_part, query_values):
            target = docs_by_id.get(viewer_doc_id)
            return self.viewer_url_for(target.doc_id, parsed.fragment) if target else href
        return href

    def viewer_path_match(self, path_part: str, query_values: dict[str, list[str]]) -> bool:
        explicit_scope = (query_values.get("scope") or [""])[0]
        if explicit_scope and explicit_scope != self.scope_id:
            return False
        if normalize_viewer_base_url(path_part) == self.viewer_base_url:
            return True
        return self.viewer_scope_for_path().get(normalize_viewer_base_url(path_part), "") == self.scope_id

    def viewer_scope_for_path(self) -> dict[str, str]:
        if self._viewer_scope_for_path is None:
            configs = load_docs_scope_configs(self.repo_root)
            self._viewer_scope_for_path = {
                normalize_viewer_base_url(config.viewer_base_url): scope_id for scope_id, config in configs.items()
            }
        return self._viewer_scope_for_path

    def resolve_content_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        resolved = self.resolve_interactive_html_tokens(self.resolve_media_tokens(markdown))
        return self.resolve_semantic_ref_tokens(resolved, doc=doc, references_by_doc=references_by_doc)

    def resolve_media_tokens(self, markdown: str) -> str:
        if "[[media:" not in markdown:
            return markdown
        rendered = MEDIA_IMAGE_TOKEN_PATTERN.sub(self.render_media_image_token, markdown)
        return MEDIA_TOKEN_PATTERN.sub(lambda match: self.resolve_media_url(self.parse_media_token(match.group(1))[0]), rendered)

    def render_media_image_token(self, match: re.Match[str]) -> str:
        media_path, media_attrs = self.parse_media_token(match.group("body"))
        attrs: dict[str, Any] = {
            "src": self.resolve_media_url(media_path),
            "alt": self.unescape_markdown_label(match.group("alt")),
        }
        attrs.update(media_attrs)
        return f"<img {self.html_attrs(attrs)}>"

    def parse_media_token(self, raw_body: str) -> tuple[str, dict[str, int]]:
        parts = raw_body.strip().split()
        media_path = parts.pop(0) if parts else ""
        attrs: dict[str, int] = {}
        for part in parts:
            key, sep, value = part.partition("=")
            if key not in MEDIA_TOKEN_ALLOWED_ATTRS or not sep or not MEDIA_TOKEN_DIMENSION_PATTERN.fullmatch(value):
                supported = ", ".join(sorted(MEDIA_TOKEN_ALLOWED_ATTRS))
                raise RuntimeError(f"Invalid media token attribute {part!r}; supported attributes: {supported}")
            attrs[key] = int(value)
        return media_path, attrs

    def unescape_markdown_label(self, value: str) -> str:
        return re.sub(r"\\([\\`*{}\[\]()#+\-.!_>])", r"\1", value or "")

    def resolve_media_url(self, raw_path: str) -> str:
        relative_path = raw_path.strip()
        if not relative_path:
            return ""
        if re.match(r"\A[a-z][a-z0-9+\-.]*://", relative_path, re.IGNORECASE):
            return relative_path
        clean_path = relative_path.lstrip("/")
        media = self.site_config.get("media")
        media_base = str(media.get("base") if isinstance(media, dict) else "").strip()
        return f"/{clean_path}" if not media_base else f"{media_base.rstrip('/')}/{clean_path}"

    def resolve_interactive_html_tokens(self, markdown: str) -> str:
        if "[[interactive-html:" not in markdown:
            return markdown
        return INTERACTIVE_HTML_TOKEN_PATTERN.sub(lambda match: self.interactive_html_iframe(match.group(1)), markdown)

    def interactive_html_iframe(self, raw_body: str) -> str:
        token = self.parse_interactive_html_token(raw_body)
        filename = token["filename"]
        asset_path = self.repo_root / self.interactive_html_asset_relative_path(filename)
        if not asset_path.exists():
            raise RuntimeError(
                f"Interactive HTML asset not found for scope {self.scope_id}: "
                f"{self.interactive_html_asset_relative_path(filename)}"
            )
        public_path = f"/assets/docs/interactive/{self.scope_id}/{filename}"
        title = f"Interactive HTML: {filename}"
        style_attr = f' style="--docs-viewer-interactive-height: {token["height"]}px"' if token.get("height") else ""
        return (
            f'<iframe class="docsViewer__interactiveFrame" src="{html.escape(public_path, quote=True)}" '
            f'sandbox="allow-scripts" loading="lazy" title="{html.escape(title, quote=True)}"{style_attr}></iframe>'
        )

    def parse_interactive_html_token(self, raw_body: str) -> dict[str, Any]:
        parts = raw_body.strip().split()
        filename = parts.pop(0) if parts else ""
        if not INTERACTIVE_HTML_FILENAME_PATTERN.fullmatch(filename):
            raise RuntimeError(f"Invalid interactive HTML token {filename!r}; use a same-scope .html filename only")
        token: dict[str, Any] = {"filename": filename}
        for part in parts:
            key, _, value = part.partition("=")
            if key != "height":
                raise RuntimeError(f"Invalid interactive HTML token attribute {part!r}; supported attributes: height")
            if not INTERACTIVE_HTML_HEIGHT_PATTERN.fullmatch(value):
                raise RuntimeError(f"Invalid interactive HTML token height in {raw_body!r}; use height=<positive pixel integer>")
            token["height"] = int(value)
        return token

    def interactive_html_asset_relative_path(self, filename: str) -> Path:
        return Path("site/assets/docs/interactive") / self.scope_id / filename

    def html_attrs(self, attrs: dict[str, Any]) -> str:
        return " ".join(f'{key}="{html.escape(str(value), quote=True)}"' for key, value in attrs.items())
