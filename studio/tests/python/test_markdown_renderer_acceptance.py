#!/usr/bin/env python3
"""Docs Viewer v2 Markdown renderer acceptance fixtures."""

from __future__ import annotations

from html.parser import HTMLParser
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from markdown_renderer import render_markdown_document  # noqa: E402


class SemanticHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.start_tags: list[str] = []
        self.links: list[dict[str, str]] = []
        self.text_by_tag: dict[str, list[str]] = {}
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        self.start_tags.append(tag_name)
        self._tag_stack.append(tag_name)
        if tag_name == "a":
            attrs_by_name = {key.lower(): str(value or "") for key, value in attrs}
            self.links.append({"href": attrs_by_name.get("href", "")})

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index] == tag_name:
                del self._tag_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        for tag_name in self._tag_stack:
            self.text_by_tag.setdefault(tag_name, []).append(text)


def parse_html(html: str) -> SemanticHTMLParser:
    parser = SemanticHTMLParser()
    parser.feed(html)
    parser.close()
    return parser


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_in(member: Any, container: Any, label: str) -> None:
    if member not in container:
        raise AssertionError(f"{label}: expected {member!r} in {container!r}")


def assert_contains(haystack: str, needle: str, label: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"{label}: expected {needle!r} in {haystack!r}")


def test_acceptance_fixture_renders_expected_html_semantics() -> None:
    result = render_markdown_document(
        """# Fixture Title

Intro with [a reference](/docs/?scope=studio&doc=fixture) and `inline code`.

- First item
- Second item

```python
print("hello")
```

<details><summary>Raw summary</summary><p>Raw body</p></details>

| Name | Value |
| --- | --- |
| Alpha | 1 |
""",
        title="Fixture Title",
    )
    parsed = parse_html(result.html)

    for tag_name in ("h1", "p", "a", "code", "ul", "li", "pre", "details", "summary", "table", "th", "td"):
        assert_in(tag_name, parsed.start_tags, f"{tag_name} tag")
    assert_equal(parsed.links, [{"href": "/docs/?scope=studio&doc=fixture"}], "link target")
    assert_in("Fixture Title", parsed.text_by_tag["h1"], "heading text")
    assert_in("inline code", parsed.text_by_tag["code"], "inline code text")
    assert_in('print("hello")', parsed.text_by_tag["code"], "fenced code text")
    assert_in("Raw summary", parsed.text_by_tag["summary"], "raw summary text")
    assert_in("Alpha", parsed.text_by_tag["td"], "table body text")


def test_acceptance_fixture_generates_plain_text_from_rendered_html() -> None:
    result = render_markdown_document(
        """# Fixture Title

Intro with [a reference](/docs/?scope=studio&doc=fixture) and `inline code`.

- First item
- Second item

```python
print("hello")
```

<details><summary>Raw summary</summary><p>Raw body</p></details>

| Name | Value |
| --- | --- |
| Alpha | 1 |
""",
        title="Fixture Title",
    )

    assert_equal(
        result.plain_text,
        "\n".join(
            [
                "Intro with a reference and inline code.",
                "",
                "- First item",
                "- Second item",
                "",
                'print("hello")',
                "",
                "Raw summary",
                "",
                "Raw body",
                "",
                "Name Value",
                "",
                "Alpha 1",
            ]
        ),
        "plain text",
    )


def test_acceptance_fixture_preserves_raw_html_without_sanitizing() -> None:
    result = render_markdown_document('<div data-kind="fixture"><span>Trusted raw HTML</span></div>')

    assert_contains(result.html, '<div data-kind="fixture"><span>Trusted raw HTML</span></div>', "raw html")
    assert_equal(result.plain_text, "Trusted raw HTML", "raw html plain text")


def main() -> None:
    test_acceptance_fixture_renders_expected_html_semantics()
    test_acceptance_fixture_generates_plain_text_from_rendered_html()
    test_acceptance_fixture_preserves_raw_html_without_sanitizing()
    print("Markdown renderer acceptance tests OK")


if __name__ == "__main__":
    main()
