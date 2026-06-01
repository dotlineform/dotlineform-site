#!/usr/bin/env python3
"""Shared Markdown rendering helpers for Python app builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from markdown_it import MarkdownIt


@dataclass(frozen=True)
class MarkdownRenderOptions:
    """Renderer options that define the current Docs Viewer v2 contract."""

    enable_tables: bool = True
    allow_raw_html: bool = True


DEFAULT_MARKDOWN_RENDER_OPTIONS = MarkdownRenderOptions()


def build_markdown_renderer(options: MarkdownRenderOptions | None = None) -> MarkdownIt:
    render_options = options or DEFAULT_MARKDOWN_RENDER_OPTIONS
    renderer = MarkdownIt("commonmark")
    if render_options.enable_tables:
        renderer.enable("table")
    if not render_options.allow_raw_html:
        renderer.disable("html_block")
        renderer.disable("html_inline")
    return renderer


def render_markdown_to_html(markdown: str | None, options: MarkdownRenderOptions | None = None) -> str:
    return build_markdown_renderer(options).render(markdown or "")


def markdown_renderer_contract(options: MarkdownRenderOptions | None = None) -> Dict[str, Any]:
    render_options = options or DEFAULT_MARKDOWN_RENDER_OPTIONS
    enabled_rules: List[str] = []
    if render_options.enable_tables:
        enabled_rules.append("table")
    return {
        "library": "markdown-it-py",
        "preset": "commonmark",
        "enabled_rules": enabled_rules,
        "enabled_plugins": [],
        "allow_raw_html": render_options.allow_raw_html,
        "sanitizes_html": False,
    }
