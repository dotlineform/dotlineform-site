from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .common import (
    HTML_ATTR_PATTERN_TEMPLATE,
    HTML_MEDIA_HEIGHT_PATTERN,
    HTML_MEDIA_TOKEN_PATTERN,
    IMG_PATTERN,
    MEDIA_IMAGE_TOKEN_PATTERN,
    MEDIA_TOKEN_ALLOWED_ATTRS,
    MEDIA_TOKEN_DIMENSION_PATTERN,
    MEDIA_TOKEN_PATTERN,
    html_attr,
    local_artifact_path,
    load_docs_scope_configs,
    normalize_viewer_base_url,
    normalize_artifact_identity,
    published_media_config,
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
        resolved = self.resolve_html_media_tokens(self.resolve_media_tokens(markdown))
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
        for media in self.config.published.media.values():
            reference_prefix = media.reference_prefix.as_posix().strip("/")
            if clean_path == reference_prefix:
                return media.served_path_prefix
            if clean_path.startswith(f"{reference_prefix}/"):
                identity = clean_path.removeprefix(f"{reference_prefix}/")
                return f"{media.served_path_prefix}/{identity}"
        if clean_path.startswith(f"docs/{self.scope_id}/"):
            raise RuntimeError(
                f"Docs media reference has no configured published role in scope {self.scope_id}: {clean_path}"
            )
        media = self.site_config.get("media")
        media_base = str(media.get("base") if isinstance(media, dict) else "").strip()
        return f"/{clean_path}" if not media_base else f"{media_base.rstrip('/')}/{clean_path}"

    def resolve_html_media_tokens(self, markdown: str) -> str:
        if "[[html-media:" not in markdown:
            return markdown
        return HTML_MEDIA_TOKEN_PATTERN.sub(lambda match: self.html_media_iframe(match.group(1)), markdown)

    def html_media_iframe(self, raw_body: str) -> str:
        token = self.parse_html_media_token(raw_body)
        media_path = token["media_path"]
        identity = token["identity"]
        media = published_media_config(self.config, "html")
        expected_prefix = media.reference_prefix.as_posix().strip("/")
        if media_path != expected_prefix and not media_path.startswith(f"{expected_prefix}/"):
            raise RuntimeError(
                f"HTML media token must use the configured same-scope prefix {expected_prefix}/"
            )
        asset_path = local_artifact_path(self.repo_root, media.location, identity)
        if asset_path is not None and not asset_path.is_file():
            raise RuntimeError(f"HTML media not found for scope {self.scope_id}: {media_path}")
        public_path = self.resolve_media_url(media_path)
        filename = Path(identity).name
        title = f"Interactive HTML: {filename}"
        style_attr = f' style="--docs-viewer-interactive-height: {token["height"]}px"' if token.get("height") else ""
        return (
            f'<iframe class="docsViewer__interactiveFrame" src="{html.escape(public_path, quote=True)}" '
            f'sandbox="allow-scripts" loading="lazy" title="{html.escape(title, quote=True)}"{style_attr}></iframe>'
        )

    def parse_html_media_token(self, raw_body: str) -> dict[str, Any]:
        parts = raw_body.strip().split()
        media_path = parts.pop(0).lstrip("/") if parts else ""
        try:
            normalized_path = normalize_artifact_identity(media_path)
        except ValueError as exc:
            raise RuntimeError(f"Invalid HTML media token path {media_path!r}") from exc
        path_parts = Path(normalized_path).parts
        if len(path_parts) < 4 or path_parts[0] != "docs" or path_parts[2] != "html":
            raise RuntimeError(
                f"Invalid HTML media token {media_path!r}; use docs/<scope>/html/<filename>.html"
            )
        identity = Path(*path_parts[3:]).as_posix()
        if Path(identity).suffix.lower() != ".html":
            raise RuntimeError(f"Invalid HTML media token {media_path!r}; published HTML media must end in .html")
        token: dict[str, Any] = {"media_path": normalized_path, "identity": identity}
        for part in parts:
            key, _, value = part.partition("=")
            if key != "height":
                raise RuntimeError(f"Invalid HTML media token attribute {part!r}; supported attributes: height")
            if not HTML_MEDIA_HEIGHT_PATTERN.fullmatch(value):
                raise RuntimeError(f"Invalid HTML media token height in {raw_body!r}; use height=<positive pixel integer>")
            token["height"] = int(value)
        return token

    def html_attrs(self, attrs: dict[str, Any]) -> str:
        return " ".join(f'{key}="{html.escape(str(value), quote=True)}"' for key, value in attrs.items())
