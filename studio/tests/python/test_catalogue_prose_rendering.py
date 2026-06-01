#!/usr/bin/env python3
"""Verify catalogue prose rendering uses the shared Python Markdown renderer."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
if str(STUDIO_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SERVICES_DIR))

from catalogue.generate_work_pages import render_catalogue_prose_markdown  # noqa: E402


def assert_contains(haystack: str, needle: str, label: str) -> None:
    if needle not in haystack:
        raise AssertionError(f"{label}: expected {needle!r} in {haystack!r}")


def assert_not_contains(haystack: str, needle: str, label: str) -> None:
    if needle in haystack:
        raise AssertionError(f"{label}: did not expect {needle!r} in {haystack!r}")


def render_fixture(tmp_path: Path, name: str, markdown: str) -> str:
    path = tmp_path / f"{name}.md"
    path.write_text(markdown, encoding="utf-8")
    return render_catalogue_prose_markdown(path)


def assert_shared_renderer_html(html: str) -> None:
    for fragment in ("highlighter-rouge", "language-plaintext", '<div class="highlight">', '<span class="'):
        assert_not_contains(html, fragment, "Jekyll/Kramdown fragment")


def test_work_prose_renders_commonmark_links_emphasis_and_code(tmp_path: Path) -> None:
    html = render_fixture(
        tmp_path,
        "work",
        "# 3 symbols\n\nWork prose with **emphasis**, [series link](/series/026/), and `inline code`.",
    )

    assert_contains(html, "<h1>3 symbols</h1>", "work heading")
    assert_contains(html, "<strong>emphasis</strong>", "work emphasis")
    assert_contains(html, '<a href="/series/026/">series link</a>', "work link")
    assert_contains(html, "<code>inline code</code>", "work inline code")
    assert_shared_renderer_html(html)


def test_series_prose_renders_lists_without_jekyll_classes(tmp_path: Path) -> None:
    html = render_fixture(
        tmp_path,
        "series",
        "Series prose\n\n- item one\n- item two",
    )

    assert_contains(html, "<p>Series prose</p>", "series paragraph")
    assert_contains(html, "<ul>", "series list")
    assert_contains(html, "<li>item one</li>", "series list item")
    assert_shared_renderer_html(html)


def test_moment_prose_preserves_trusted_raw_html_and_tables(tmp_path: Path) -> None:
    html = render_fixture(
        tmp_path,
        "moment",
        '<aside data-kind="note">Moment note</aside>\n\n| Name | Value |\n| --- | --- |\n| Alpha | 1 |',
    )

    assert_contains(html, '<aside data-kind="note">Moment note</aside>', "moment raw html")
    assert_contains(html, "<table>", "moment table")
    assert_contains(html, "<th>Name</th>", "moment table heading")
    assert_contains(html, "<td>Alpha</td>", "moment table cell")
    assert_shared_renderer_html(html)


def main() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_work_prose_renders_commonmark_links_emphasis_and_code(tmp_path)
        test_series_prose_renders_lists_without_jekyll_classes(tmp_path)
        test_moment_prose_preserves_trusted_raw_html_and_tables(tmp_path)
    print("Catalogue prose rendering tests OK")


if __name__ == "__main__":
    main()
