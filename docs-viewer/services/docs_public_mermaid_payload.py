#!/usr/bin/env python3
"""Detect accepted document payloads that still require Mermaid projection."""

from __future__ import annotations

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


__all__ = [
    "PUBLIC_MERMAID_HTML_FENCE_PATTERN",
    "public_mermaid_payload_requires_projection",
]
