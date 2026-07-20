#!/usr/bin/env python3
"""Verify the shared Python Markdown renderer contract."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from markdown_renderer import (  # noqa: E402
    MarkdownRenderOptions,
    markdown_renderer_contract,
    render_markdown_to_html,
)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_contains(haystack: str, needle: str, label: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"{label}: expected {needle!r} in {haystack!r}")


def test_renders_commonmark_blocks_and_inline_code() -> None:
    html = render_markdown_to_html("# Heading\n\n- `one`\n- [two](https://example.com)\n")

    assert_contains(html, "<h1>Heading</h1>", "heading")
    assert_contains(html, "<li><code>one</code></li>", "inline code")
    assert_contains(html, '<a href="https://example.com">two</a>', "link")


def test_enables_table_rule_by_default() -> None:
    html = render_markdown_to_html("| A | B |\n| - | - |\n| 1 | 2 |\n")

    assert_contains(html, "<table>", "table enabled")
    assert_contains(html, "<th>A</th>", "table header")
    assert_contains(html, "<td>2</td>", "table cell")


def test_preserves_mermaid_fence_for_browser_adapter() -> None:
    html = render_markdown_to_html("```mermaid\nflowchart LR\n    A --> B\n```\n")

    assert_contains(html, '<pre><code class="language-mermaid">', "Mermaid code class")
    assert_contains(html, "flowchart LR", "Mermaid source")


def test_raw_html_is_explicit_and_unsanitized_by_default() -> None:
    html = render_markdown_to_html("<section><span>Raw</span></section>\n")

    assert_contains(html, "<section><span>Raw</span></section>", "raw html passthrough")
    assert_equal(markdown_renderer_contract()["sanitizes_html"], False, "sanitization boundary")


def test_raw_html_can_be_escaped_for_untrusted_input() -> None:
    html = render_markdown_to_html("<span>Raw</span>", MarkdownRenderOptions(allow_raw_html=False))

    assert_contains(html, "&lt;span&gt;Raw&lt;/span&gt;", "raw html escaped")


def test_contract_records_no_external_plugins() -> None:
    contract = markdown_renderer_contract()

    assert_equal(contract["library"], "markdown-it-py", "library")
    assert_equal(contract["preset"], "commonmark", "preset")
    assert_equal(contract["enabled_rules"], ["table"], "enabled rules")
    assert_equal(contract["enabled_plugins"], [], "enabled plugins")
    assert_equal(contract["allow_raw_html"], True, "raw html")


def main() -> None:
    test_renders_commonmark_blocks_and_inline_code()
    test_enables_table_rule_by_default()
    test_preserves_mermaid_fence_for_browser_adapter()
    test_raw_html_is_explicit_and_unsanitized_by_default()
    test_raw_html_can_be_escaped_for_untrusted_input()
    test_contract_records_no_external_plugins()
    print("Markdown renderer tests OK")


if __name__ == "__main__":
    main()
