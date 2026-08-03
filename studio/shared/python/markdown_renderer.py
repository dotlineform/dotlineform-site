#!/usr/bin/env python3
"""Shared Markdown rendering helpers for Python app builders."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import re
from typing import Any, Dict, List

from markdown_it import MarkdownIt


@dataclass(frozen=True)
class MarkdownRenderOptions:
    """Renderer options that define the current Docs Viewer v2 contract."""

    enable_tables: bool = True
    allow_raw_html: bool = True


DEFAULT_MARKDOWN_RENDER_OPTIONS = MarkdownRenderOptions()

FENCED_CODE_OPEN_PATTERN = re.compile(r"^(?P<indent> {0,3})(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
PRE_OPEN_PATTERN = re.compile(r"<pre(?:\s[^>]*)?>", re.IGNORECASE)
PRE_CLOSE_PATTERN = re.compile(r"</pre\s*>", re.IGNORECASE)
MARKDOWN_LINE_ENDING_PATTERN = re.compile(r"(\r\n|\r|\n|\u2028|\u2029)")


def normalize_plain_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_markdown_unicode_separators(markdown: str | None) -> str:
    """Convert Unicode line separators to explicit Markdown line boundaries."""

    return _normalize_markdown_line_boundaries(markdown, normalize_unicode_blank_lines=False)


def normalize_markdown_blank_lines(markdown: str | None) -> str:
    """Normalize Unicode Markdown line boundaries outside literal blocks."""

    return _normalize_markdown_line_boundaries(markdown, normalize_unicode_blank_lines=True)


def _normalize_markdown_line_boundaries(
    markdown: str | None,
    *,
    normalize_unicode_blank_lines: bool,
) -> str:

    source = markdown or ""
    parts = MARKDOWN_LINE_ENDING_PATTERN.split(source)
    normalized: List[str] = []
    fence_character = ""
    fence_length = 0
    pre_depth = 0

    for index in range(0, len(parts), 2):
        line = parts[index]
        line_ending = parts[index + 1] if index + 1 < len(parts) else ""
        literal_line_ending = "\n" if line_ending in {"\u2028", "\u2029"} else line_ending

        if fence_character:
            normalized.extend((line, literal_line_ending))
            if re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                line,
            ):
                fence_character = ""
                fence_length = 0
            continue

        if pre_depth:
            normalized.extend((line, literal_line_ending))
            pre_depth += len(PRE_OPEN_PATTERN.findall(line))
            pre_depth = max(0, pre_depth - len(PRE_CLOSE_PATTERN.findall(line)))
            continue

        fence_match = FENCED_CODE_OPEN_PATTERN.match(line)
        if fence_match:
            fence = fence_match.group("fence")
            info = fence_match.group("info")
            if fence[0] != "`" or "`" not in info:
                fence_character = fence[0]
                fence_length = len(fence)
                normalized.extend((line, literal_line_ending))
                continue

        pre_depth = max(
            0,
            len(PRE_OPEN_PATTERN.findall(line)) - len(PRE_CLOSE_PATTERN.findall(line)),
        )
        if pre_depth:
            normalized.extend((line, literal_line_ending))
            continue

        is_unicode_space_only = (
            normalize_unicode_blank_lines
            and bool(line)
            and line.isspace()
            and any(character not in " \t" for character in line)
        )
        normalized_line = "" if is_unicode_space_only else line
        if line_ending == "\u2028":
            if normalized_line and not normalized_line.endswith(("  ", "\\")):
                normalized_line += " " if normalized_line.endswith(" ") else "  "
            line_ending = "\n"
        elif line_ending == "\u2029":
            line_ending = "\n\n"
        normalized.extend((normalized_line, line_ending))

    return "".join(normalized)


class PlainTextRenderer(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "div",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "main",
        "p",
        "pre",
        "section",
        "table",
        "tr",
    }

    def __init__(self, *, title: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.title = normalize_plain_text(title)
        self.lines: List[str] = []
        self.current_line = ""
        self.skip_depth = 0
        self.list_stack: List[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag_name in self.BLOCK_TAGS:
            self.block_break()
        elif tag_name == "br":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            self.block_break()
            self.list_stack.append({"tag": tag_name, "counter": 0})
        elif tag_name == "li":
            self.flush_line()
            marker = "- "
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["counter"] += 1
                marker = f"{self.list_stack[-1]['counter']}. "
            self.current_line += marker
        elif tag_name == "img":
            attrs_by_name = {key.lower(): str(value or "") for key, value in attrs}
            alt = normalize_plain_text(attrs_by_name.get("alt", ""))
            self.flush_line()
            self.lines.append(f"[image: {alt}]" if alt else "[image]")
            self.block_break()

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if self.skip_depth:
            if tag_name in {"script", "style"}:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag_name in self.BLOCK_TAGS:
            self.block_break()
        elif tag_name == "li":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.block_break()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = normalize_plain_text(data)
        if not text:
            return
        if self.current_line and not self.current_line.endswith(" ") and text[0] not in ".,;:!?)]}":
            self.current_line += " "
        self.current_line += text

    def flush_line(self) -> None:
        line = normalize_plain_text(self.current_line)
        if line:
            self.lines.append(line)
        self.current_line = ""

    def block_break(self) -> None:
        self.flush_line()
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def text(self) -> str:
        self.flush_line()
        lines = trim_blank_lines(self.lines)
        if lines and self.title and lines[0] == self.title:
            lines = trim_blank_lines(lines[1:])
        return "\n".join(collapse_blank_lines(lines)).strip()


@dataclass(frozen=True)
class MarkdownRenderResult:
    html: str
    plain_text: str


def trim_blank_lines(lines: List[str]) -> List[str]:
    result = list(lines)
    while result and result[0] == "":
        result.pop(0)
    while result and result[-1] == "":
        result.pop()
    return result


def collapse_blank_lines(lines: List[str]) -> List[str]:
    result: List[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        result.append(line)
        previous_blank = is_blank
    return result


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
    return build_markdown_renderer(options).render(normalize_markdown_blank_lines(markdown))


def plain_text_from_html(content_html: str | None, *, title: str = "") -> str:
    parser = PlainTextRenderer(title=title)
    parser.feed(content_html or "")
    parser.close()
    return parser.text()


def render_markdown_document(
    markdown: str | None,
    *,
    title: str = "",
    options: MarkdownRenderOptions | None = None,
) -> MarkdownRenderResult:
    html = render_markdown_to_html(markdown, options)
    return MarkdownRenderResult(html=html, plain_text=plain_text_from_html(html, title=title))


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
