#!/usr/bin/env python3
"""HTML import-preview summaries for Docs staged source imports."""

from __future__ import annotations

from typing import Any

from docs_html_markdown import (
    ElementNode,
    ParsedDocument,
    find_first,
    html_to_markdown,
    is_prompt_meta_node,
    is_semantic_callout_node,
    svg_safety_warnings,
    walk,
)
from docs_import_common import normalize_space, slugify


def build_summary(
    root: ElementNode,
    *,
    source_html: str,
    source_filename_stem: str,
    title: str,
    include_prompt_meta: bool,
    parsed: ParsedDocument | None = None,
) -> dict[str, Any]:
    conversion = html_to_markdown(source_html, include_prompt_meta=include_prompt_meta, parsed=parsed)
    warnings = list(conversion.warnings)
    links = []
    images = []
    svg_count = 0
    prompt_meta_blocks = 0
    semantic_callouts = 0
    details_count = 0
    for node in walk(root):
        if not isinstance(node, ElementNode):
            continue
        if node.tag == "a" and node.attr("href"):
            links.append(node.attr("href"))
        if node.tag == "img" and node.attr("src"):
            images.append(node.attr("src"))
        if node.tag == "svg":
            svg_count += 1
            warnings.extend(svg_safety_warnings(source_html, node))
        if node.tag == "details":
            details_count += 1
        if is_prompt_meta_node(node):
            prompt_meta_blocks += 1
        if is_semantic_callout_node(node):
            semantic_callouts += 1
    title_source = "title" if find_first(root, "title") and normalize_space(find_first(root, "title").text_content()) else ("h1" if find_first(root, "h1") else "fallback")
    return {
        "title": title or "Imported Doc",
        "title_source": title_source,
        "proposed_doc_id": slugify(source_filename_stem or title or "Imported Doc"),
        "proposed_doc_id_source": "filename" if source_filename_stem else "title",
        "source_stats": {
            "chars": len(source_html),
            "links": len(links),
            "images": len(images),
            "svg": svg_count,
            "details": details_count,
            "prompt_meta_blocks": prompt_meta_blocks,
            "semantic_callouts": semantic_callouts,
        },
        "image_summary": {
            "external": sum(1 for src in images if src.startswith("http://") or src.startswith("https://")),
            "data_urls": sum(1 for src in images if src.startswith("data:")),
            "repo_local_or_other": sum(1 for src in images if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:"))),
        },
        "warnings": warnings,
        "markdown_preview": conversion.markdown,
    }
