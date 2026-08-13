"""Pure rendered-anchor collection and Docs Viewer target resolution."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import parse_qs, urljoin, urlparse


LOCAL_ORIGIN = "https://dotlineform.local"
WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    return WHITESPACE_PATTERN.sub(" ", str(value or "")).strip()


class AnchorCollector(HTMLParser):
    """Collect rendered anchors while excluding literal code regions."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._current_parts: list[str] = []
        self._code_depth = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"code", "pre"}:
            self._code_depth += 1
        if normalized_tag != "a" or self._code_depth > 0:
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href":
                href = str(value or "").strip()
                break
        self._current_href = href
        self._current_parts = []

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"code", "pre"}:
            self._code_depth = max(0, self._code_depth - 1)
        if normalized_tag != "a" or self._current_href is None:
            return
        self.anchors.append(
            {
                "href": self._current_href,
                "text": normalize_text("".join(self._current_parts)),
            }
        )
        self._current_href = None
        self._current_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_parts.append(data)


def collect_anchors(html_text: str) -> list[dict[str, str]]:
    parser = AnchorCollector()
    parser.feed(html_text)
    parser.close()
    return parser.anchors


def resolve_href(
    href: str,
    from_page_url: str,
    *,
    local_origin: str = LOCAL_ORIGIN,
) -> str:
    raw = normalize_text(href)
    if not raw:
        return ""
    absolute = urljoin(f"{local_origin}{from_page_url}", raw)
    parsed = urlparse(absolute)
    if parsed.netloc != urlparse(local_origin).netloc:
        return absolute
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    if parsed.fragment:
        path = f"{path}#{parsed.fragment}"
    return path


def parse_docs_target(
    resolved_href: str,
    *,
    viewer_routes: Iterable[tuple[str, str]],
    known_scopes: set[str] | None = None,
    local_origin: str = LOCAL_ORIGIN,
) -> dict[str, str] | None:
    """Resolve one rendered href using explicit viewer-route inputs.

    ``known_scopes`` retains Broken Links' existing invalid-scope fallback.
    Omitting it preserves any explicit scope so same-scope consumers can reject
    cross-scope and unknown-scope targets without configuration inference.
    """

    raw = normalize_text(resolved_href)
    if not raw or raw.startswith("#"):
        return None

    parsed = urlparse(raw)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if (
        parsed.scheme in {"http", "https"}
        and parsed.netloc != urlparse(local_origin).netloc
    ):
        return None

    path = parsed.path or ""
    query = parse_qs(parsed.query)
    trimmed_path = path.rstrip("/")
    fragment = normalize_text(parsed.fragment)

    for route_scope, viewer_base_url in viewer_routes:
        normalized_route_scope = normalize_text(route_scope).lower()
        viewer_path = normalize_text(viewer_base_url).rstrip("/")
        if trimmed_path != viewer_path:
            continue
        doc_id = normalize_text(query.get("doc", [""])[0])
        if not doc_id:
            return None
        explicit_scope = normalize_text(query.get("scope", [""])[0]).lower()
        if explicit_scope and (
            known_scopes is None or explicit_scope in known_scopes
        ):
            target_scope = explicit_scope
        else:
            target_scope = normalized_route_scope
        return {
            "kind": "viewer",
            "scope": target_scope,
            "doc_id": doc_id,
            "fragment": fragment,
        }

    if path.endswith(".md"):
        return {
            "kind": "source_markdown",
            "path": path,
            "fragment": fragment,
        }

    return None


def is_same_doc_fragment_link(
    *,
    current_scope: str,
    current_doc_id: str,
    target: dict[str, str],
) -> bool:
    if not normalize_text(target.get("fragment")):
        return False
    return (
        target.get("kind") == "viewer"
        and normalize_text(target.get("scope")).lower()
        == normalize_text(current_scope).lower()
        and normalize_text(target.get("doc_id"))
        == normalize_text(current_doc_id)
    )
