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
    normalize_markdown_blank_lines,
    normalize_markdown_unicode_separators,
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


def test_projects_exact_table_detail_directive_onto_next_table() -> None:
    html = render_markdown_to_html(
        "<!-- dotlineform:table-detail -->\n\n"
        "| A | B |\n"
        "| - | - |\n"
        "| 1 | 2 |\n"
    )

    assert_contains(html, "<!-- dotlineform:table-detail -->", "directive preserved")
    assert_contains(html, '<table data-docs-content-detail="table">', "table detail marker")

    adjacent_html = render_markdown_to_html(
        "<!-- dotlineform:table-detail -->\n"
        "| A |\n"
        "| - |\n"
        "| 1 |\n"
    )
    assert_contains(adjacent_html, '<table data-docs-content-detail="table">', "adjacent table marker")


def test_table_detail_directive_ignores_lookalikes_and_intervening_blocks() -> None:
    cases = (
        "<!-- dotlineform:table-detail extra -->\n\n",
        " <!-- dotlineform:table-detail -->\n\n",
        "<!-- dotlineform:table-detail -->\n\nIntervening prose.\n\n",
        "<!-- dotlineform:table-detail -->\n\n<!-- ordinary comment -->\n\n",
        "<!-- dotlineform:table-detail -->\n\n[reference]: https://example.com\n\n",
    )
    table = "| A |\n| - |\n| 1 |\n"

    for source_prefix in cases:
        html = render_markdown_to_html(source_prefix + table)
        if 'data-docs-content-detail="table"' in html:
            raise AssertionError(f"unsupported table-detail association projected a marker: {source_prefix!r}")


def test_table_detail_directive_marks_only_its_associated_table() -> None:
    html = render_markdown_to_html(
        "| Ordinary |\n| - |\n| one |\n\n"
        "<!-- dotlineform:table-detail -->\n\n"
        "| Detailed |\n| - |\n| two |\n\n"
        "| Ordinary again |\n| - |\n| three |\n"
    )

    assert_equal(html.count('data-docs-content-detail="table"'), 1, "one associated table")
    assert_contains(html, '<table>\n<thead>\n<tr>\n<th>Ordinary</th>', "ordinary table fallback")
    assert_contains(
        html,
        '<table data-docs-content-detail="table">\n<thead>\n<tr>\n<th>Detailed</th>',
        "associated table",
    )


def test_content_detail_default_projects_the_same_marker_only_for_one_table() -> None:
    one_table = render_markdown_to_html(
        "| A |\n| - |\n| 1 |\n",
        MarkdownRenderOptions(content_detail_default_table=True),
    )
    two_tables = render_markdown_to_html(
        "| A |\n| - |\n| 1 |\n\n| B |\n| - |\n| 2 |\n",
        MarkdownRenderOptions(content_detail_default_table=True),
    )

    assert_contains(one_table, 'data-docs-content-detail="table"', "single default table")
    assert_equal(two_tables.count('data-docs-content-detail="table"'), 0, "ambiguous default tables")


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
    assert_equal(contract["content_detail_default_table"], False, "table default opt-in")
    assert_equal(contract["table_detail_directive"], "<!-- dotlineform:table-detail -->", "table directive")


def test_normalizes_unicode_space_only_lines_outside_literal_blocks() -> None:
    source = (
        "Text with a hard break  \n"
        "\u00a0\n"
        "Inline\u00a0space\n"
        "```text\n"
        "\u00a0\n"
        "```\n"
        "<pre>\n"
        "\u00a0\n"
        "</pre>\n"
    )

    normalized = normalize_markdown_blank_lines(source)

    assert_equal(
        normalized,
        (
            "Text with a hard break  \n"
            "\n"
            "Inline\u00a0space\n"
            "```text\n"
            "\u00a0\n"
            "```\n"
            "<pre>\n"
            "\u00a0\n"
            "</pre>\n"
        ),
        "Unicode-only blank lines",
    )


def test_unicode_space_only_line_ends_raw_html_block() -> None:
    html = render_markdown_to_html(
        "<figure>\n"
        "<img src=\"example.png\" alt=\"Example\">\n"
        "</figure>\n"
        "\u00a0\n"
        "## 3 symbols\n\n"
        "**birth**\n"
    )

    assert_contains(html, "<h2>3 symbols</h2>", "heading after raw HTML")
    assert_contains(html, "<strong>birth</strong>", "bold text after raw HTML")


def test_normalizes_unicode_line_and_paragraph_separators() -> None:
    source = (
        "First line\u2028Second line\u2029Second paragraph\n"
        "Already hard  \u2028Still hard\n"
        "Backslash hard\\\u2028Still hard\n"
        "One trailing space \u2028Still hard\n"
    )

    normalized = normalize_markdown_blank_lines(source)

    assert_equal(
        normalized,
        (
            "First line  \nSecond line\n\nSecond paragraph\n"
            "Already hard  \nStill hard\n"
            "Backslash hard\\\nStill hard\n"
            "One trailing space  \nStill hard\n"
        ),
        "Unicode line and paragraph separators",
    )
    html = render_markdown_to_html("First line\u2028Second line\u2029Second paragraph")
    assert_contains(html, "First line<br />\nSecond line", "Unicode line separator hard break")
    assert_contains(html, "</p>\n<p>Second paragraph</p>", "Unicode paragraph separator")


def test_separator_only_normalizer_preserves_unicode_blank_lines() -> None:
    normalized = normalize_markdown_unicode_separators("Before\n\u00a0\nAfter\u2028Next")

    assert_equal(normalized, "Before\n\u00a0\nAfter  \nNext", "separator-only normalization")


def test_normalizes_unicode_separators_without_markdown_spaces_in_literal_blocks() -> None:
    source = (
        "```text\u2028first\u2029second\u2028```\n"
        "<pre>\u2028first\u2029second\u2028</pre>\n"
    )

    normalized = normalize_markdown_blank_lines(source)

    assert_equal(
        normalized,
        "```text\nfirst\nsecond\n```\n<pre>\nfirst\nsecond\n</pre>\n",
        "Unicode separators in literal blocks",
    )


def main() -> None:
    test_renders_commonmark_blocks_and_inline_code()
    test_enables_table_rule_by_default()
    test_projects_exact_table_detail_directive_onto_next_table()
    test_table_detail_directive_ignores_lookalikes_and_intervening_blocks()
    test_table_detail_directive_marks_only_its_associated_table()
    test_content_detail_default_projects_the_same_marker_only_for_one_table()
    test_preserves_mermaid_fence_for_browser_adapter()
    test_raw_html_is_explicit_and_unsanitized_by_default()
    test_raw_html_can_be_escaped_for_untrusted_input()
    test_contract_records_no_external_plugins()
    test_normalizes_unicode_space_only_lines_outside_literal_blocks()
    test_unicode_space_only_line_ends_raw_html_block()
    test_normalizes_unicode_line_and_paragraph_separators()
    test_separator_only_normalizer_preserves_unicode_blank_lines()
    test_normalizes_unicode_separators_without_markdown_spaces_in_literal_blocks()
    print("Markdown renderer tests OK")


if __name__ == "__main__":
    main()
