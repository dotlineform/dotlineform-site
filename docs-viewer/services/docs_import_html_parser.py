#!/usr/bin/env python3
"""HTML and SVG parsing/rendering for Docs staged source imports."""

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
    slugify,
)

BLOCK_TAGS = {
    "body",
    "section",
    "article",
    "div",
    "p",
    "ul",
    "ol",
    "li",
    "blockquote",
    "pre",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "details",
    "summary",
    "footer",
}
DROP_TAGS = {"head", "script", "meta", "title"}
PROMPT_META_CLASS_TOKENS = {"prompt", "meta", "shade"}
SEMANTIC_CALLOUT_CLASS_TOKENS = {"key"}
LIST_WRAPPER_CLASS_TOKENS = {"legend"}
ROWSPAN_COLSPAN_ATTRS = {"rowspan", "colspan"}
PROMPT_META_TEXT_PREFIXES = ("[prompt]", "original prompt", "follow-up")

SVG_EVENT_ATTR_PATTERN = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
SVG_EXTERNAL_REF_ATTRS = {"href", "xlink:href", "src"}


ROWSPAN_COLSPAN_ATTRS = {"rowspan", "colspan"}

def text_node_has_ancestor(node: Any, tags: set[str]) -> bool:
    current = node.parent
    while current:
        if current.tag in tags:
            return True
        current = current.parent
    return False

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


def parse_with_bs4(source_html: str) -> ParsedDocument:
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


def render_prompt_meta_block(text: str) -> str:
    content = escape_markdown_pipes(normalize_space(text))
    if not content:
        return ""
    return f"> {content}"


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


def svg_safety_warnings(source_svg: str, svg: Optional[ElementNode]) -> list[str]:
    warnings: list[str] = []
    if re.search(r"<\s*script\b", source_svg or "", flags=re.IGNORECASE):
        warnings.append("SVG contained script content; unsafe script blocks were stripped.")
    if SVG_EVENT_ATTR_PATTERN.search(source_svg or ""):
        warnings.append("SVG contained event-handler attributes; unsafe on* attributes were stripped.")
    external_refs: list[str] = []
    if svg:
        for node in walk(svg):
            if not isinstance(node, ElementNode):
                continue
            for attr_name in SVG_EXTERNAL_REF_ATTRS:
                value = node.attr(attr_name)
                if value.startswith(("http://", "https://", "//")):
                    external_refs.append(value)
    if external_refs:
        warnings.append(f"SVG contains {len(external_refs)} external reference(s); review the rendered output.")
    return warnings


def sanitize_svg_source(source_svg: str) -> tuple[str, str, list[str], int]:
    parsed = parse_with_bs4(source_svg)
    svg = find_first(parsed.root, "svg")
    if svg is None:
        return "", "", ["No <svg> root was found in the staged SVG file."], 0
    title_node = find_first(svg, "title")
    title = normalize_space(title_node.text_content()) if title_node else ""
    warnings = svg_safety_warnings(source_svg, svg)
    return serialize_node(svg), title, warnings, sum(1 for node in walk(svg) if isinstance(node, ElementNode) and node.tag == "svg")


def extract_title(root: ElementNode) -> str:
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
        return serialize_node(node)
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
                cells.append(normalize_space("".join(render_inline(grand) for grand in child.children)))
        if cells:
            rows.append(cells)
    return rows


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
        return serialize_node(node)
    if tag == "img":
        return render_inline(node)
    return "\n\n".join(part for part in (render_block(child, warnings, include_prompt_meta) for child in node.children) if part)


def build_summary(
    root: ElementNode,
    *,
    source_html: str,
    source_filename_stem: str,
    title: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    warnings: list[str] = []
    body = find_first(root, "body") or root
    markdown = render_block(body, warnings, include_prompt_meta=include_prompt_meta).strip()
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
        "markdown_preview": markdown,
    }
