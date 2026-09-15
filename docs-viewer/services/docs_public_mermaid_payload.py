#!/usr/bin/env python3
"""Detect accepted document payloads that still require Mermaid projection."""

from __future__ import annotations

import html
import re
from typing import Any, Mapping


PUBLIC_MERMAID_HTML_FENCE_PATTERN = re.compile(
    r'<pre><code class="language-mermaid">(?P<source>.*?)</code></pre>',
    re.DOTALL,
)


def public_mermaid_payload_requires_projection(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    content_html = payload.get("content_html")
    return isinstance(content_html, str) and bool(
        PUBLIC_MERMAID_HTML_FENCE_PATTERN.search(content_html)
    )


def project_mermaid_payload(payload: Mapping[str, Any], diagrams: list[dict[str, Any]]) -> dict[str, Any]:
    """Replace exact generated fences with prepared images without retaining source.

    The caller supplies the source-derived plan for this document only. Matching
    fence text and ordinal prevents attaching another revision's SVG variants.
    """
    content = payload.get("content_html")
    if not isinstance(content, str):
        raise ValueError("Mermaid preparation requires generated document HTML")
    index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal index
        if index >= len(diagrams):
            raise ValueError("Generated Mermaid fences do not match the source plan")
        diagram = diagrams[index]
        index += 1
        source, projection = diagram["source"], diagram["projection"]
        if (source["doc_id"] != payload.get("doc_id") or source["fence_index"] != index
                or html.unescape(match.group("source")) != source["mermaid"]):
            raise ValueError("Generated Mermaid fence identity or source is stale")
        attrs = {
            "src": projection["variants"]["light"]["url"],
            "alt": projection["title"],
            "title": projection["description"],
            "data-docs-viewer-diagram-kind": "themed-mermaid",
            "data-docs-viewer-diagram-light-src": projection["variants"]["light"]["url"],
            "data-docs-viewer-diagram-dark-src": projection["variants"]["dark"]["url"],
        }
        return "<img " + " ".join(f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()) + ">"

    projected = PUBLIC_MERMAID_HTML_FENCE_PATTERN.sub(replace, content)
    if index != len(diagrams):
        raise ValueError("Generated Mermaid fences do not match the source plan")
    return {**payload, "content_html": projected}


__all__ = [
    "PUBLIC_MERMAID_HTML_FENCE_PATTERN",
    "project_mermaid_payload",
    "public_mermaid_payload_requires_projection",
]
