#!/usr/bin/env python3
"""HTML parsing and HTML-to-Markdown conversion helpers."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from html import escape
from typing import Any, Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from docs_import_common import (
    autolink_plain_urls,
    escape_markdown_pipes,
    fence_code,
    normalize_space,
)

DROP_TAGS = {"head", "script", "meta", "title"}
PROMPT_META_CLASS_TOKENS = {"prompt", "meta", "shade"}
SEMANTIC_CALLOUT_CLASS_TOKENS = {"key"}
LIST_WRAPPER_CLASS_TOKENS = {"legend"}
PROMPT_META_TEXT_PREFIXES = ("[prompt]", "original prompt", "follow-up")
ROWSPAN_COLSPAN_ATTRS = {"rowspan", "colspan"}
SVG_MARKDOWN_BLANK_LINES_PATTERN = re.compile(r"\n(?:[ \t]*\n)+")


@dataclass
class TextNode:
    text: str
    parent: Optional["ElementNode"] = None

    def text_content(self) -> str:
        return self.text


@dataclass
class ElementNode:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)
    parent: Optional["ElementNode"] = None

    def add_child(self, child: Any) -> None:
        child.parent = self
        self.children.append(child)

    def attr(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)

    def class_tokens(self) -> set[str]:
        raw = self.attr("class")
        return {token.strip().lower() for token in raw.split() if token.strip()}

    def text_content(self) -> str:
        return "".join(child.text_content() for child in self.children)

    def inner_html(self) -> str:
        return "".join(serialize_node(child) for child in self.children)


@dataclass
class ParsedDocument:
    root: ElementNode
    tag_counts: Counter[str]
    comment_count: int


@dataclass(frozen=True)
class HtmlMarkdownResult:
    markdown: str
    warnings: list[str]
    title: str
    tag_counts: dict[str, int]
    comment_count: int


def parse_html_document(source_html: str) -> ParsedDocument:
    soup = BeautifulSoup(source_html, "lxml")
    root = ElementNode(tag="#document")
    tag_counts: Counter[str] = Counter()
    comment_count = 0

    def convert(node: Any) -> Optional[Any]:
        nonlocal comment_count
        if isinstance(node, Comment):
            comment_count += 1
            return None
        if isinstance(node, NavigableString):
            text = str(node)
            if not text:
                return None
            return TextNode(text=text)
        if isinstance(node, Tag):
            tag = node.name.lower()
            attrs: dict[str, str] = {}
            for key, value in node.attrs.items():
                if isinstance(value, list):
                    attrs[key.lower()] = " ".join(str(item) for item in value)
                else:
                    attrs[key.lower()] = str(value)
            element = ElementNode(tag=tag, attrs=attrs)
            tag_counts[tag] += 1
            for child in node.children:
                converted = convert(child)
                if converted is not None:
                    element.add_child(converted)
            return element
        return None

    for child in soup.contents:
        converted = convert(child)
        if converted is not None:
            root.add_child(converted)
    return ParsedDocument(root=root, tag_counts=tag_counts, comment_count=comment_count)


def serialize_attrs(attrs: dict[str, str], *, for_svg: bool) -> str:
    kept: list[str] = []
    for key, value in attrs.items():
        if not value and key not in {"viewbox", "xmlns", "role"}:
            continue
        if key.startswith("on"):
            continue
        if key == "style" and not for_svg:
            continue
        if key in {"target", "rel", "class", "id"} and not for_svg:
            continue
        kept.append(f' {key}="{escape(value, quote=True)}"')
    return "".join(kept)


def serialize_node(node: Any, *, in_svg: bool = False) -> str:
    if isinstance(node, TextNode):
        return escape(node.text, quote=False)
    tag = node.tag
    if tag == "script":
        return ""
    if tag in DROP_TAGS and not (in_svg and tag in {"title", "desc"}):
        return ""
    current_in_svg = in_svg or tag == "svg"
    attrs = serialize_attrs(node.attrs, for_svg=current_in_svg)
    if tag == "img":
        return f"<img{attrs}>"
    inner = "".join(serialize_node(child, in_svg=current_in_svg) for child in node.children)
    return f"<{tag}{attrs}>{inner}</{tag}>"


def serialize_svg_node(node: Any) -> str:
    """Keep inline SVG contiguous so Markdown renderers do not paragraphize its children."""

    return SVG_MARKDOWN_BLANK_LINES_PATTERN.sub("\n", serialize_node(node)).strip()


def walk(node: Any):
    yield node
    if isinstance(node, ElementNode):
        for child in node.children:
            yield from walk(child)


def find_first(node: ElementNode, tag: str) -> Optional[ElementNode]:
    for candidate in walk(node):
        if isinstance(candidate, ElementNode) and candidate.tag == tag:
            return candidate
    return None


def collect_all(node: ElementNode, tag: str) -> list[ElementNode]:
    matches: list[ElementNode] = []
    for candidate in walk(node):
        if isinstance(candidate, ElementNode) and candidate.tag == tag:
            matches.append(candidate)
    return matches


def extract_html_title(root: ElementNode) -> str:
    title_node = find_first(root, "title")
    if title_node:
        title_text = normalize_space(title_node.text_content())
        if title_text:
            return title_text
    h1_node = find_first(root, "h1")
    if h1_node:
        h1_text = normalize_space(h1_node.text_content())
        if h1_text:
            return h1_text
    return ""


def text_node_has_ancestor(node: Any, tags: set[str]) -> bool:
    current = node.parent
    while current:
        if current.tag in tags:
            return True
        current = current.parent
    return False


def render_prompt_meta_block(text: str) -> str:
    content = escape_markdown_pipes(normalize_space(text))
    if not content:
        return ""
    return f"> {content}"


def is_prompt_meta_node(node: ElementNode) -> bool:
    classes = node.class_tokens()
    if classes & PROMPT_META_CLASS_TOKENS:
        return True
    if any("prompt" in token or token == "meta" or token.startswith("meta-") or token.endswith("-meta") for token in classes):
        return True
    text = normalize_space(node.text_content()).lower()
    if node.tag in {"code", "pre", "div", "p", "blockquote"} and any(text.startswith(prefix) for prefix in PROMPT_META_TEXT_PREFIXES):
        return True
    return False


def is_semantic_callout_node(node: ElementNode) -> bool:
    classes = node.class_tokens()
    return bool(classes & SEMANTIC_CALLOUT_CLASS_TOKENS)


def render_inline(node: Any) -> str:
    if isinstance(node, TextNode):
        if text_node_has_ancestor(node, {"a", "code", "pre"}):
            return escape_markdown_pipes(node.text)
        return autolink_plain_urls(node.text)
    tag = node.tag
    if tag in {"strong", "b"}:
        return f"**{''.join(render_inline(child) for child in node.children).strip()}**"
    if tag in {"em", "i"}:
        return f"*{''.join(render_inline(child) for child in node.children).strip()}*"
    if tag == "code":
        return f"`{normalize_space(node.text_content())}`"
    if tag in {"sub", "sup"}:
        return serialize_node(node)
    if tag == "a":
        text = normalize_space("".join(render_inline(child) for child in node.children)) or escape_markdown_pipes(node.attr("href"))
        href = node.attr("href")
        if href:
            return f"[{text}]({href})"
        return text
    if tag == "br":
        return "\n"
    if tag == "img":
        src = node.attr("src")
        alt = normalize_space(node.attr("alt"))
        if src.startswith("http://") or src.startswith("https://"):
            return f"![{alt}]({src})" if alt else src
        if src.startswith("data:"):
            return f"![{alt}]({src})" if alt else src
        return src or alt
    if tag == "svg":
        return serialize_svg_node(node)
    return "".join(render_inline(child) for child in node.children)


def has_rowspan_or_colspan(table: ElementNode) -> bool:
    for candidate in walk(table):
        if isinstance(candidate, ElementNode):
            if any(attr in ROWSPAN_COLSPAN_ATTRS for attr in candidate.attrs):
                return True
    return False


def extract_table_rows(table: ElementNode) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in collect_all(table, "tr"):
        cells: list[str] = []
        for child in tr.children:
            if isinstance(child, ElementNode) and child.tag in {"th", "td"}:
                cells.append(render_table_cell(child))
        if cells:
            rows.append(cells)
    return rows


def render_table_cell(cell: ElementNode) -> str:
    parts: list[str] = []
    for child in cell.children:
        if isinstance(child, ElementNode) and child.tag in {"ul", "ol"}:
            items: list[str] = []
            for item in child.children:
                if not isinstance(item, ElementNode) or item.tag != "li":
                    continue
                text = normalize_space("".join(render_inline(grand) for grand in item.children))
                if text:
                    items.append(text)
            if items:
                parts.append("; ".join(items))
            continue
        text = normalize_space(render_inline(child))
        if text:
            parts.append(text)
    return "<br>".join(parts)


def render_table(table: ElementNode, warnings: list[str]) -> str:
    if has_rowspan_or_colspan(table):
        warnings.append("Complex table kept as plain text because rowspan/colspan is unsupported in v1.")
        return escape_markdown_pipes(normalize_space(table.text_content()))
    rows = extract_table_rows(table)
    if not rows:
        return ""
    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
    header = normalized_rows[0]
    body = normalized_rows[1:] if len(normalized_rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_list(node: ElementNode, warnings: list[str], indent: int = 0, ordered: bool = False) -> list[str]:
    lines: list[str] = []
    index = 1
    for child in node.children:
        if not isinstance(child, ElementNode) or child.tag != "li":
            continue
        prefix = f"{index}." if ordered else "-"
        segments: list[str] = []
        nested_blocks: list[str] = []
        for grand in child.children:
            if isinstance(grand, ElementNode) and grand.tag in {"ul", "ol"}:
                nested_blocks.append(
                    "\n".join(
                        render_list(
                            grand,
                            warnings,
                            indent=indent + 2,
                            ordered=(grand.tag == "ol"),
                        )
                    )
                )
            else:
                segments.append(render_inline(grand))
        line = (" " * indent) + f"{prefix} {normalize_space(''.join(segments))}".rstrip()
        lines.append(line)
        if nested_blocks:
            lines.extend(block for block in nested_blocks if block)
        index += 1
    return [line for line in lines if line.strip()]


def render_block(node: Any, warnings: list[str], include_prompt_meta: bool) -> str:
    if isinstance(node, TextNode):
        return escape_markdown_pipes(normalize_space(node.text))
    tag = node.tag
    if tag in DROP_TAGS:
        return ""
    if tag == "style" and node.parent and node.parent.tag != "svg":
        return ""
    if is_prompt_meta_node(node):
        if not include_prompt_meta:
            return ""
        return render_prompt_meta_block(node.text_content())
    if tag in {"body", "section", "article"}:
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag == "div":
        if is_semantic_callout_node(node):
            content = normalize_space("".join(render_inline(child) for child in node.children))
            return f"> {content}" if content else ""
        if node.class_tokens() & LIST_WRAPPER_CLASS_TOKENS:
            items = [normalize_space("".join(render_inline(child) for child in node.children))]
            text = ", ".join(item for item in items if item)
            return text
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag == "footer":
        return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        text = normalize_space("".join(render_inline(child) for child in node.children))
        return f"{'#' * level} {text}" if text else ""
    if tag == "p":
        return normalize_space("".join(render_inline(child) for child in node.children))
    if tag == "blockquote":
        inner = normalize_space("".join(render_inline(child) for child in node.children))
        return "\n".join(f"> {line}".rstrip() for line in inner.splitlines() if line.strip())
    if tag == "pre":
        return fence_code(node.text_content())
    if tag == "ul":
        return "\n".join(render_list(node, warnings, ordered=False))
    if tag == "ol":
        return "\n".join(render_list(node, warnings, ordered=True))
    if tag == "details":
        summary = next((child for child in node.children if isinstance(child, ElementNode) and child.tag == "summary"), None)
        parts: list[str] = []
        if summary:
            summary_text = normalize_space("".join(render_inline(child) for child in summary.children))
            if summary_text:
                parts.append(f"### {summary_text}")
        for child in node.children:
            if child is summary:
                continue
            rendered = render_block(child, warnings, include_prompt_meta)
            if rendered:
                parts.append(rendered)
        return "\n\n".join(parts)
    if tag == "summary":
        return ""
    if tag == "table":
        return render_table(node, warnings)
    if tag == "svg":
        return serialize_svg_node(node)
    if tag == "img":
        return render_inline(node)
    return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)


def html_to_markdown(
    source_html: str,
    *,
    include_prompt_meta: bool = False,
    parsed: ParsedDocument | None = None,
) -> HtmlMarkdownResult:
    parsed_document = parsed or parse_html_document(source_html)
    warnings: list[str] = []
    body = find_first(parsed_document.root, "body") or parsed_document.root
    markdown = render_block(body, warnings, include_prompt_meta=include_prompt_meta).strip()
    return HtmlMarkdownResult(
        markdown=markdown,
        warnings=warnings,
        title=extract_html_title(parsed_document.root),
        tag_counts=dict(parsed_document.tag_counts.most_common()),
        comment_count=parsed_document.comment_count,
    )
