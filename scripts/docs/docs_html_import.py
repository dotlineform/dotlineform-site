#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import binascii
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from docs_scope_config import IMPORT_MEDIA_CONFIGS, MEDIA_PATH_PREFIXES, SCOPE_ROOTS


STAGING_REL_DIR = Path("var/docs/import-staging")
HTML_STAGED_SUFFIXES = {".html", ".htm"}
MARKDOWN_STAGED_SUFFIXES = {".md", ".markdown"}
TEXT_STAGED_SUFFIXES = {".txt"}
SVG_STAGED_SUFFIXES = {".svg"}
RASTER_IMAGE_STAGED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
FILE_MEDIA_STAGED_SUFFIXES = {".pdf", ".zip", ".csv", ".tsv", ".json", ".jsonl", ".docx", ".xlsx", ".pptx"}
SUPPORTED_STAGED_SUFFIXES = (
    HTML_STAGED_SUFFIXES
    | MARKDOWN_STAGED_SUFFIXES
    | TEXT_STAGED_SUFFIXES
    | SVG_STAGED_SUFFIXES
    | RASTER_IMAGE_STAGED_SUFFIXES
    | FILE_MEDIA_STAGED_SUFFIXES
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
PLAIN_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")
PLAIN_URL_TRAILING_PUNCTUATION = ".,;:!?)]}'"
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s*#\s+(.+?)\s*#*\s*$", re.MULTILINE)
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MARKDOWN_IMAGE_REWRITE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)\s]+)(?P<title>\s+\"[^\"]*\")?\)"
)
MARKDOWN_LINK_REWRITE_PATTERN = re.compile(
    r"(?<!!)\[(?P<label>[^\]]+)\]\((?P<target>[^)\s]+)(?P<title>\s+\"[^\"]*\")?\)"
)
MARKDOWN_INLINE_RASTER_IMAGE_PATTERN = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<url>data:image/(?P<subtype>png|jpe?g|webp|gif);base64,(?P<data>[A-Za-z0-9+/=]+))\)",
    re.IGNORECASE,
)
APPLE_NOTES_CAPTION_SPAN_PATTERN = re.compile(
    r"<span\b(?P<attrs>[^>]*)style=\"(?P<style>[^\"]*font-size:\s*11\.285714[^;\"]*;?[^\"]*)\"(?P<tail>[^>]*)>"
    r"(?P<body>.*?)</span>",
    re.IGNORECASE | re.DOTALL,
)
SVG_EVENT_ATTR_PATTERN = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
SVG_EXTERNAL_REF_ATTRS = {"href", "xlink:href", "src"}
INLINE_RASTER_EXTENSIONS = {
    "gif": "gif",
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "webp": "webp",
}
DOCS_IMPORT_ROLE_META_NAME = "dlf:docs-import-role"
INTERACTIVE_HTML_ROLE = "interactive-html"


@dataclass(frozen=True)
class SourceImporter:
    source_format: str
    suffixes: set[str]
    include_prompt_meta: bool = False
    creates_remote_media_plan: bool = False


SOURCE_IMPORTERS = [
    SourceImporter("html", HTML_STAGED_SUFFIXES, include_prompt_meta=True),
    SourceImporter("markdown", MARKDOWN_STAGED_SUFFIXES),
    SourceImporter("text", TEXT_STAGED_SUFFIXES),
    SourceImporter("svg", SVG_STAGED_SUFFIXES),
    SourceImporter("image", RASTER_IMAGE_STAGED_SUFFIXES, creates_remote_media_plan=True),
    SourceImporter("file", FILE_MEDIA_STAGED_SUFFIXES, creates_remote_media_plan=True),
]
SOURCE_IMPORTER_BY_SUFFIX = {
    suffix: importer
    for importer in SOURCE_IMPORTERS
    for suffix in importer.suffixes
}


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def escape_markdown_pipes(text: str) -> str:
    return (text or "").replace("|", r"\|")


def text_node_has_ancestor(node: Any, tags: set[str]) -> bool:
    current = node.parent
    while current:
        if current.tag in tags:
            return True
        current = current.parent
    return False


def autolink_plain_urls(text: str) -> str:
    parts: list[str] = []
    last_index = 0
    for match in PLAIN_URL_PATTERN.finditer(text or ""):
        raw_url = match.group(0)
        url = raw_url.rstrip(PLAIN_URL_TRAILING_PUNCTUATION)
        trailing = raw_url[len(url):]
        if not url:
            continue
        parts.append(escape_markdown_pipes(text[last_index:match.start()]))
        parts.append(f"<{escape_markdown_pipes(url)}>")
        parts.append(escape_markdown_pipes(trailing))
        last_index = match.end()
    parts.append(escape_markdown_pipes(text[last_index:]))
    return "".join(parts)


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return text or "imported-doc"


def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", value.strip()) if part)


def fence_code(text: str) -> str:
    content = text.rstrip("\n")
    return f"```\n{content}\n```"


def relative_path(base: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except Exception:
        return str(path)


def normalize_scope(scope: str) -> str:
    value = str(scope or "").strip().lower()
    if value not in SCOPE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SCOPE_ROOTS.keys()))}")
    return value


def detect_bundle_bin() -> Optional[str]:
    rbenv_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    if rbenv_bundle.exists() and os.access(rbenv_bundle, os.X_OK):
        return str(rbenv_bundle)
    return shutil.which("bundle")


def source_format_for_path(path: Path) -> str:
    if path.is_dir():
        return "markdown_package"
    importer = SOURCE_IMPORTER_BY_SUFFIX.get(path.suffix.lower())
    if importer:
        return importer.source_format
    raise ValueError(
        "staged file must use one of these extensions: "
        f"{', '.join(sorted(SUPPORTED_STAGED_SUFFIXES))}"
    )


def html_import_role_for_path(path: Path) -> str:
    if path.suffix.lower() not in HTML_STAGED_SUFFIXES:
        return ""
    source_html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(source_html, "lxml")
    role_meta = soup.find(
        "meta",
        attrs={
            "name": lambda value: str(value or "").strip().lower() == DOCS_IMPORT_ROLE_META_NAME,
        },
    )
    if not role_meta:
        return ""
    return str(role_meta.get("content") or "").strip().lower()


def is_interactive_html_import_asset(path: Path) -> bool:
    if not path.is_file():
        return False
    return html_import_role_for_path(path) == INTERACTIVE_HTML_ROLE


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


def next_inline_media_filename(staging_root: Path, doc_id: str, extension: str, used_filenames: set[str]) -> str:
    safe_doc_id = slugify(doc_id or "imported-doc")
    safe_extension = INLINE_RASTER_EXTENSIONS.get(extension.lower(), extension.lower()).lstrip(".")
    index = 1
    while True:
        filename = f"{safe_doc_id}-image-{index:02d}.{safe_extension}"
        if filename not in used_filenames and not (staging_root / filename).exists():
            used_filenames.add(filename)
            return filename
        index += 1


def inline_media_plan(scope: str, filename: str, title: str, *, mime_type: str, size_bytes: int) -> dict[str, Any]:
    source_path = Path(filename)
    plan = build_media_plan(scope, "img", source_path, title)
    plan.update(
        {
            "source": "inline_data_url",
            "staging_path": (STAGING_REL_DIR / filename).as_posix(),
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        }
    )
    return plan


def apply_inline_raster_media_plans(repo_root: Path, summary: dict[str, Any], scope: str) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    if "data:image/" not in markdown:
        return

    staging_root = repo_root / STAGING_REL_DIR
    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
    existing_plans = summary.get("media_plans")
    plans: list[dict[str, Any]] = list(existing_plans) if isinstance(existing_plans, list) else []
    used_filenames: set[str] = {
        str(plan.get("source_path") or "")
        for plan in plans
        if isinstance(plan, dict) and str(plan.get("source_path") or "")
    }
    inline_plans: list[dict[str, Any]] = []
    warnings = summary.setdefault("warnings", [])

    def replace(match: re.Match[str]) -> str:
        subtype = match.group("subtype").lower()
        extension = INLINE_RASTER_EXTENSIONS.get(subtype)
        alt = normalize_space(match.group("alt"))
        if not extension:
            warnings.append(f"Unsupported inline image media type image/{subtype}; left the data URL inline.")
            return match.group(0)
        try:
            decoded = base64.b64decode(match.group("data"), validate=True)
        except (binascii.Error, ValueError):
            warnings.append(f"Could not decode inline image data for {alt or 'an imported image'}; left the data URL inline.")
            return match.group(0)

        filename = next_inline_media_filename(staging_root, proposed_doc_id, extension, used_filenames)
        title = alt or f"Inline image {len(inline_plans) + 1:02d}"
        plan = inline_media_plan(
            scope,
            filename,
            title,
            mime_type=f"image/{'jpeg' if extension == 'jpg' else extension}",
            size_bytes=len(decoded),
        )
        plans.append(plan)
        inline_plans.append(plan)
        if plan["manual_copy_required"]:
            warnings.append(
                f"Copy {filename} to the media path {plan['media_path']} before the rendered doc can display it."
            )
        return f"![{match.group('alt')}]({plan['media_token']})"

    normalized = MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def retarget_inline_raster_media_plans(repo_root: Path, summary: dict[str, Any], scope: str) -> None:
    plans = summary.get("media_plans")
    if not isinstance(plans, list) or not plans:
        return

    staging_root = repo_root / STAGING_REL_DIR
    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
    used_filenames: set[str] = {
        str(plan.get("source_path") or "")
        for plan in plans
        if isinstance(plan, dict) and plan.get("source") != "inline_data_url" and str(plan.get("source_path") or "")
    }
    markdown = str(summary.get("markdown_preview") or "")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []

    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            continue
        if plan.get("source") != "inline_data_url":
            continue
        old_token = str(plan.get("media_token") or "")
        old_filename = str(plan.get("source_path") or "")
        extension = Path(old_filename).suffix.lstrip(".") or "png"
        new_filename = next_inline_media_filename(staging_root, proposed_doc_id, extension, used_filenames)
        new_plan = inline_media_plan(
            scope,
            new_filename,
            str(plan.get("title") or f"Inline image {index + 1:02d}"),
            mime_type=str(plan.get("mime_type") or f"image/{'jpeg' if extension == 'jpg' else extension}"),
            size_bytes=int(plan.get("size_bytes") or 0),
        )
        if old_token:
            markdown = markdown.replace(old_token, new_plan["media_token"], 1)
        if old_filename != new_filename:
            old_media_path = media_path_for(scope, "img", old_filename)
            for warning_index, warning in enumerate(warnings):
                if isinstance(warning, str) and old_filename in warning:
                    warnings[warning_index] = warning.replace(old_filename, new_filename).replace(
                        old_media_path,
                        new_plan["media_path"],
                    )
        plans[index] = new_plan
    summary["markdown_preview"] = markdown


def retarget_markdown_package_media_plans(repo_root: Path, summary: dict[str, Any], scope: str) -> None:
    plans = summary.get("media_plans")
    if not isinstance(plans, list) or not plans:
        return
    package_indices = [
        index
        for index, plan in enumerate(plans)
        if isinstance(plan, dict) and plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}
    ]
    if not package_indices:
        return

    package_root = (repo_root / str(summary.get("package_path") or "")).resolve()
    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
    used_filenames: set[str] = set()
    markdown = str(summary.get("markdown_preview") or "")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    image_index = 0

    for index in package_indices:
        plan = plans[index]
        assert isinstance(plan, dict)
        old_token = str(plan.get("media_token") or "")
        old_filename = str(plan.get("source_path") or "")
        old_title = str(plan.get("title") or "")
        kind = str(plan.get("kind") or "")
        source_original = str(plan.get("source_original_path") or "")
        source_path = (repo_root / source_original).resolve()
        media_class = "img" if kind == "image" else "files"
        suffix = "image" if kind == "image" else "attachment"
        extension = "webp" if kind == "image" else Path(old_filename).suffix.lstrip(".")
        if kind == "image":
            image_index += 1
            new_title = readable_package_image_title(proposed_doc_id, image_index)
        else:
            new_title = str(plan.get("title") or humanize(source_path.stem) or old_filename)
        new_filename = next_package_media_filename(
            repo_root,
            scope,
            proposed_doc_id,
            media_class,
            suffix,
            extension,
            used_filenames,
        )
        new_plan = build_package_media_plan(
            repo_root,
            scope,
            package_root=package_root,
            source_path=source_path,
            filename=new_filename,
            title=new_title,
            kind=kind,
        )
        if old_token:
            if kind == "image" and old_title:
                old_markdown = f'![{old_title}]({old_token} "{old_title}")'
                new_markdown = f'![{new_title}]({new_plan["media_token"]} "{new_title}")'
                if old_markdown in markdown:
                    markdown = markdown.replace(old_markdown, new_markdown, 1)
                else:
                    markdown = markdown.replace(old_token, new_plan["media_token"], 1)
            else:
                markdown = markdown.replace(old_token, new_plan["media_token"], 1)
        if old_filename != new_filename:
            for warning_index, warning in enumerate(warnings):
                if isinstance(warning, str) and old_filename in warning:
                    warnings[warning_index] = warning.replace(old_filename, new_filename).replace(
                        str(plan.get("media_path") or ""),
                        new_plan["media_path"],
                    )
        plans[index] = new_plan
    summary["markdown_preview"] = markdown


def raw_markdown_for_inline_media(source_path: Path, *, include_prompt_meta: bool) -> str:
    source_format = source_format_for_path(source_path)
    if source_format == "html":
        source_html = source_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_with_bs4(source_html)
        title = extract_title(parsed.root)
        summary = build_summary(
            parsed.root,
            source_html=source_html,
            source_filename_stem=source_path.stem,
            title=title,
            include_prompt_meta=include_prompt_meta,
        )
        return str(summary.get("markdown_preview") or "")
    if source_format == "markdown":
        summary = build_markdown_summary(source_path.read_text(encoding="utf-8", errors="replace"), source_path.stem)
        return str(summary.get("markdown_preview") or "")
    if source_format == "markdown_package":
        markdown_path = find_package_markdown_file(source_path)
        return normalize_apple_notes_caption_spans(markdown_path.read_text(encoding="utf-8", errors="replace"))
    return ""


def package_media_target_path(repo_root: Path, plan: dict[str, Any], scope: str) -> Path:
    filename = str(plan.get("source_path") or "").strip()
    if not filename or Path(filename).name != filename:
        raise ValueError(f"Invalid package media filename: {filename!r}")
    if plan.get("storage_mode") == "repo_assets":
        target_rel = Path(str(plan.get("repo_asset_path") or ""))
        if not str(target_rel) or target_rel.name != filename:
            raise ValueError(f"Invalid package media repo asset path: {target_rel.as_posix()!r}")
        target_root = (repo_root / IMPORT_MEDIA_CONFIGS[scope].repo_assets_path_prefix).resolve()
        target_path = (repo_root / target_rel).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Package media target escapes repo assets root: {target_rel.as_posix()!r}")
        return target_path
    if plan.get("storage_mode") == "staging_manual":
        target_root = (repo_root / STAGING_REL_DIR).resolve()
        target_path = (target_root / filename).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Package media filename escapes staging root: {filename!r}")
        return target_path
    raise ValueError("Docs Import media storage mode is not available for package media writes.")


def package_media_source_path(repo_root: Path, package_root: Path, plan: dict[str, Any]) -> Path:
    source_rel = str(plan.get("source_original_path") or "").strip()
    if not source_rel:
        raise ValueError("Package media plan is missing source_original_path.")
    source_path = (repo_root / source_rel).resolve()
    if not source_path.is_relative_to(package_root.resolve()):
        raise ValueError(f"Package media source escapes package root: {source_rel}")
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Package media source does not exist: {source_rel}")
    return source_path


def convert_package_image_to_webp(source_path: Path, target_path: Path, *, max_width: int = 800) -> dict[str, Any]:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for Markdown package image conversion. "
            "Install requirements.txt before importing package images."
        ) from exc

    with Image.open(source_path) as image:
        if getattr(image, "is_animated", False):
            raise ValueError(f"Animated image conversion is not supported for Markdown package imports: {source_path.name}")
        image = ImageOps.exif_transpose(image)
        original_width, original_height = image.size
        output = image
        resized = False
        if original_width > max_width:
            ratio = max_width / float(original_width)
            output = image.resize((max_width, max(1, round(original_height * ratio))), Image.Resampling.LANCZOS)
            resized = True
        if output.mode in {"RGBA", "LA"} or (output.mode == "P" and "transparency" in output.info):
            output = output.convert("RGBA")
        else:
            output = output.convert("RGB")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        output.save(target_path, "WEBP", quality=85, method=6)
        output_width, output_height = output.size
    return {
        "original_width": original_width,
        "original_height": original_height,
        "output_width": output_width,
        "output_height": output_height,
        "resized": resized,
    }


def materialize_package_media_plans(repo_root: Path, package_root: Path, plans: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    package_plans = [
        plan
        for plan in plans
        if plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}
    ]
    if not package_plans:
        return []
    normalized_scope = normalize_scope(scope)
    written: list[dict[str, Any]] = []
    for plan in package_plans:
        source_path = package_media_source_path(repo_root, package_root, plan)
        target_path = package_media_target_path(repo_root, plan, normalized_scope)
        if target_path.exists():
            raise FileExistsError(f"Package media target already exists: {relative_path(repo_root, target_path)}")
        if plan.get("source") == "markdown_package_image":
            conversion_result = convert_package_image_to_webp(
                source_path,
                target_path,
                max_width=int((plan.get("conversion") or {}).get("max_width") or 800),
            )
            size_bytes = target_path.stat().st_size
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            conversion_result = {}
            size_bytes = target_path.stat().st_size
        written.append(
            {
                "source_path": plan.get("source_path", ""),
                "source_original_path": plan.get("source_original_path", ""),
                "staging_path": plan.get("staging_path", relative_path(repo_root, target_path)),
                "size_bytes": size_bytes,
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
                "kind": plan.get("kind", ""),
                "conversion": conversion_result,
            }
        )
    return written


def materialize_inline_raster_media(
    repo_root: Path,
    *,
    source_path: Path,
    import_preview: dict[str, Any],
    include_prompt_meta: bool,
) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    raw_plans = import_preview.get("media_plans")
    if isinstance(raw_plans, list):
        plans.extend(plan for plan in raw_plans if isinstance(plan, dict))
    raw_plan = import_preview.get("media_plan")
    if isinstance(raw_plan, dict):
        plans.append(raw_plan)
    if not plans:
        return []

    inline_plans = [plan for plan in plans if plan.get("source") == "inline_data_url"]
    package_written = materialize_package_media_plans(repo_root, source_path, plans, normalize_scope(str(import_preview.get("scope")))) if source_path.is_dir() else []
    source_file_plans = [plan for plan in plans if plan.get("source") != "inline_data_url"]
    valid_inline_matches: list[tuple[re.Match[str], bytes]] = []
    if inline_plans:
        raw_markdown = raw_markdown_for_inline_media(source_path, include_prompt_meta=include_prompt_meta)
        for match in MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.finditer(raw_markdown):
            try:
                decoded = base64.b64decode(match.group("data"), validate=True)
            except (binascii.Error, ValueError):
                continue
            valid_inline_matches.append((match, decoded))

        if len(valid_inline_matches) < len(inline_plans):
            raise RuntimeError("Inline media extraction plan no longer matches the staged source.")

    written: list[dict[str, Any]] = list(package_written)
    for plan, (_, decoded) in zip(inline_plans, valid_inline_matches):
        filename = str(plan.get("source_path") or "").strip()
        if not filename or Path(filename).name != filename:
            raise ValueError(f"Invalid inline media filename: {filename!r}")
        if plan.get("storage_mode") == "repo_assets":
            target_rel = Path(str(plan.get("repo_asset_path") or ""))
            if not str(target_rel) or target_rel.name != filename:
                raise ValueError(f"Invalid inline media repo asset path: {target_rel.as_posix()!r}")
            scope = normalize_scope(str(import_preview.get("scope")))
            target_root = (repo_root / IMPORT_MEDIA_CONFIGS[scope].repo_assets_path_prefix).resolve()
            target_path = (repo_root / target_rel).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Inline media target escapes repo assets root: {target_rel.as_posix()!r}")
        elif plan.get("storage_mode") == "staging_manual":
            target_root = (repo_root / STAGING_REL_DIR).resolve()
            target_path = (target_root / filename).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Inline media filename escapes staging root: {filename!r}")
        else:
            raise ValueError("Docs Import media storage mode is not available for inline media writes.")
        if target_path.exists():
            relative_target = target_path.relative_to(repo_root.resolve()).as_posix()
            raise FileExistsError(f"Inline media target already exists: {relative_target}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(decoded)
        written.append(
            {
                "source_path": filename,
                "staging_path": plan.get("staging_path", ""),
                "size_bytes": len(decoded),
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
            }
        )
    for plan in source_file_plans:
        if plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}:
            continue
        if plan.get("storage_mode") != "repo_assets":
            continue
        filename = str(plan.get("source_path") or "").strip()
        if not filename or Path(filename).name != filename:
            raise ValueError(f"Invalid source media filename: {filename!r}")
        if filename != source_path.name:
            raise ValueError(f"Source media filename {filename!r} does not match staged source {source_path.name!r}")
        target_rel = Path(str(plan.get("repo_asset_path") or ""))
        if not str(target_rel) or target_rel.name != filename:
            raise ValueError(f"Invalid source media repo asset path: {target_rel.as_posix()!r}")
        scope = normalize_scope(str(import_preview.get("scope")))
        target_root = (repo_root / IMPORT_MEDIA_CONFIGS[scope].repo_assets_path_prefix).resolve()
        target_path = (repo_root / target_rel).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Source media target escapes repo assets root: {target_rel.as_posix()!r}")
        if target_path.exists():
            raise FileExistsError(f"Source media target already exists: {target_rel.as_posix()}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        written.append(
            {
                "source_path": filename,
                "staging_path": relative_path(repo_root, source_path),
                "size_bytes": target_path.stat().st_size,
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
            }
        )
    return written


def validate_markdown_with_jekyll(repo_root: Path, markdown: str) -> dict[str, Any]:
    renderer_script = repo_root / "scripts" / "render_markdown_with_jekyll.rb"
    if not renderer_script.exists():
        raise RuntimeError(f"Markdown renderer helper not found: {relative_path(repo_root, renderer_script)}")

    bundle_bin = detect_bundle_bin()
    if not bundle_bin:
        raise RuntimeError("Bundler not found; ensure the local Jekyll toolchain is available before validating imported Markdown.")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(markdown)
        handle.write("\n")
        temp_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [bundle_bin, "exec", "ruby", str(renderer_script), str(temp_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"Jekyll Markdown validation failed: {detail}")

    return {
        "ok": True,
        "html_chars": len(completed.stdout),
        "renderer": "scripts/render_markdown_with_jekyll.rb",
    }


def resolve_staged_html(repo_root: Path, staged_filename: str) -> Path:
    return resolve_staged_import_source(repo_root, staged_filename, allowed_suffixes=HTML_STAGED_SUFFIXES)


def resolve_staged_import_source(
    repo_root: Path,
    staged_filename: str,
    *,
    allowed_suffixes: set[str] | None = None,
) -> Path:
    filename = str(staged_filename or "").strip()
    if not filename:
        raise ValueError("staged_filename is required")
    path = (repo_root / STAGING_REL_DIR / filename).resolve()
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if staging_root not in [path, *path.parents]:
        raise ValueError(f"staged file must resolve inside {STAGING_REL_DIR.as_posix()}")
    if not path.exists():
        raise FileNotFoundError(f"staged import source does not exist: {filename}")
    if path.is_dir():
        if allowed_suffixes is not None:
            raise ValueError("staged file must use one of these extensions: " + ", ".join(sorted(allowed_suffixes)))
        if path.parent != staging_root:
            raise ValueError(f"staged Markdown packages must be direct child directories of {STAGING_REL_DIR.as_posix()}")
        return path
    suffixes = allowed_suffixes or SUPPORTED_STAGED_SUFFIXES
    if path.suffix.lower() not in suffixes:
        raise ValueError("staged file must use one of these extensions: " + ", ".join(sorted(suffixes)))
    return path


def list_staged_html_files(repo_root: Path) -> list[dict[str, Any]]:
    return [
        file
        for file in list_staged_import_source_files(repo_root)
        if file.get("source_format") == "html"
    ]


def list_staged_import_source_files(repo_root: Path) -> list[dict[str, Any]]:
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if not staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    candidates = [
        path
        for path in staging_root.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_STAGED_SUFFIXES
    ]
    package_candidates = [
        path
        for path in staging_root.iterdir()
        if path.is_dir() and not path.is_symlink()
    ]
    for path in sorted(candidates, key=lambda candidate: candidate.name.lower()):
        if is_interactive_html_import_asset(path):
            continue
        stat = path.stat()
        files.append(
            {
                "filename": path.name,
                "path": relative_path(repo_root, path),
                "source_format": source_format_for_path(path),
                "size_bytes": stat.st_size,
                "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    for path in sorted(package_candidates, key=lambda candidate: candidate.name.lower()):
        markdown_files = [
            file
            for file in path.rglob("*")
            if file.is_file() and file.suffix.lower() in MARKDOWN_STAGED_SUFFIXES
        ]
        if not markdown_files:
            continue
        package_files = [file for file in path.rglob("*") if file.is_file()]
        modified = max((file.stat().st_mtime for file in package_files), default=path.stat().st_mtime)
        files.append(
            {
                "filename": path.name,
                "path": relative_path(repo_root, path),
                "source_format": "markdown_package",
                "size_bytes": sum(file.stat().st_size for file in package_files),
                "modified_utc": dt.datetime.fromtimestamp(modified, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "package_file_count": len(package_files),
                "package_markdown_count": len(markdown_files),
            }
        )
    return files


def generate_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    source_format = source_format_for_path(source_path)
    if source_format == "markdown_package":
        return generate_markdown_package_import_preview(
            repo_root,
            package_path=source_path,
            scope=scope,
        )
    if source_format == "markdown":
        return generate_markdown_import_preview(
            repo_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "text":
        return generate_text_import_preview(
            repo_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "svg":
        return generate_svg_import_preview(
            repo_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "image":
        return generate_image_import_preview(
            repo_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "file":
        return generate_file_media_import_preview(
            repo_root,
            source_path=source_path,
            scope=scope,
        )
    return generate_html_import_preview(
        repo_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
    )


def generate_html_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_html = source_path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_with_bs4(source_html)
    title = extract_title(parsed.root)
    summary = build_summary(
        parsed.root,
        source_html=source_html,
        source_filename_stem=source_path.stem,
        title=title,
        include_prompt_meta=include_prompt_meta,
    )
    summary["scope"] = normalized_scope
    summary["source_format"] = "html"
    summary["source_path"] = relative_path(repo_root, source_path)
    summary["source_html"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = dict(parsed.tag_counts.most_common())
    summary["comment_count"] = parsed.comment_count
    apply_inline_raster_media_plans(repo_root, summary, normalized_scope)
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def extract_markdown_title(markdown: str, fallback: str) -> tuple[str, str]:
    match = MARKDOWN_HEADING_PATTERN.search(markdown or "")
    if match:
        title = normalize_space(re.sub(r"\s+#*$", "", match.group(1)))
        if title:
            return title, "h1"
    return humanize(fallback) or "Imported Doc", "filename"


def build_markdown_summary(source_markdown: str, source_filename_stem: str) -> dict[str, Any]:
    markdown = (source_markdown or "").lstrip("\ufeff").strip()
    title, title_source = extract_markdown_title(markdown, source_filename_stem)
    warnings: list[str] = []
    if not markdown:
        markdown = f"# {title}"
        warnings.append("Staged Markdown was blank; generated a title-only body.")
    link_matches = MARKDOWN_LINK_PATTERN.findall(markdown)
    image_matches = MARKDOWN_IMAGE_PATTERN.findall(markdown)
    plain_url_text = MARKDOWN_IMAGE_PATTERN.sub("", MARKDOWN_LINK_PATTERN.sub("", markdown))
    return {
        "title": title,
        "title_source": title_source,
        "proposed_doc_id": slugify(source_filename_stem or title or "Imported Doc"),
        "proposed_doc_id_source": "filename" if source_filename_stem else "title",
        "source_stats": {
            "chars": len(source_markdown or ""),
            "links": len(link_matches) + len(PLAIN_URL_PATTERN.findall(plain_url_text)),
            "images": len(image_matches),
            "svg": markdown.lower().count("<svg"),
            "details": markdown.lower().count("<details"),
        },
        "image_summary": {
            "external": sum(1 for src in image_matches if src.startswith("http://") or src.startswith("https://")),
            "data_urls": sum(1 for src in image_matches if src.startswith("data:")),
            "repo_local_or_other": sum(1 for src in image_matches if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:"))),
        },
        "warnings": warnings,
        "markdown_preview": markdown,
    }


def normalize_apple_notes_caption_spans(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attrs = f"{match.group('attrs') or ''}{match.group('tail') or ''}"
        attrs = re.sub(r'\sstyle="[^"]*"', "", attrs, flags=re.IGNORECASE)
        style = str(match.group("style") or "")
        style_parts = [
            part.strip()
            for part in style.split(";")
            if part.strip() and not part.strip().lower().startswith("font-size:")
        ]
        style_parts.insert(0, "font-size: var(--font-caption)")
        body = str(match.group("body") or "").strip()
        normalized_attrs = normalize_space(attrs)
        attr_text = f" {normalized_attrs}" if normalized_attrs else ""
        return f'<span{attr_text} style="{"; ".join(style_parts)};">{body}</span>'

    return APPLE_NOTES_CAPTION_SPAN_PATTERN.sub(replace, markdown or "")


def build_text_summary(source_text: str, source_filename_stem: str) -> dict[str, Any]:
    text = (source_text or "").lstrip("\ufeff")
    first_line = next((normalize_space(line) for line in text.splitlines() if normalize_space(line)), "")
    title = first_line if 0 < len(first_line) <= 90 else humanize(source_filename_stem)
    title = title or "Imported Text"
    body = autolink_plain_urls(text.strip())
    warnings: list[str] = []
    if not body:
        body = f"# {title}"
        warnings.append("Staged text was blank; generated a title-only body.")
    return {
        "title": title,
        "title_source": "first_line" if first_line and title == first_line else "filename",
        "proposed_doc_id": slugify(source_filename_stem or title or "Imported Text"),
        "proposed_doc_id_source": "filename" if source_filename_stem else "title",
        "source_stats": {
            "chars": len(source_text or ""),
            "links": len(PLAIN_URL_PATTERN.findall(source_text or "")),
            "images": 0,
            "svg": 0,
            "details": 0,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": body,
    }


def media_token(scope: str, media_class: str, filename: str) -> str:
    media_path = media_path_for(scope, media_class, filename)
    return f"[[media:{media_path}]]"


def media_path_prefix_for(scope: str) -> str:
    normalized_scope = normalize_scope(scope)
    return MEDIA_PATH_PREFIXES[normalized_scope].as_posix().strip("/")


def media_path_for(scope: str, media_class: str, filename: str) -> str:
    return f"{media_path_prefix_for(scope)}/{media_class}/{filename}"


def repo_asset_rel_path_for(scope: str, media_class: str, filename: str) -> str:
    normalized_scope = normalize_scope(scope)
    config = IMPORT_MEDIA_CONFIGS[normalized_scope]
    return (config.repo_assets_path_prefix / media_class / filename).as_posix()


def repo_asset_public_path_for(scope: str, media_class: str, filename: str) -> str:
    normalized_scope = normalize_scope(scope)
    config = IMPORT_MEDIA_CONFIGS[normalized_scope]
    return f"{config.repo_assets_public_path_prefix}/{media_class}/{filename}"


def media_link_for(scope: str, media_class: str, filename: str) -> str:
    normalized_scope = normalize_scope(scope)
    config = IMPORT_MEDIA_CONFIGS[normalized_scope]
    if config.storage_mode == "repo_assets":
        return repo_asset_public_path_for(normalized_scope, media_class, filename)
    if config.storage_mode == "staging_manual":
        return media_token(normalized_scope, media_class, filename)
    raise ValueError(
        f"Docs Import media storage mode {config.storage_mode!r} is reserved for a future backend "
        "and is not available yet."
    )


def build_media_plan(scope: str, media_class: str, source_path: Path, title: str) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    config = IMPORT_MEDIA_CONFIGS[normalized_scope]
    link = media_link_for(normalized_scope, media_class, source_path.name)
    if config.storage_mode == "repo_assets":
        media_path = repo_asset_rel_path_for(normalized_scope, media_class, source_path.name)
    else:
        media_path = media_path_for(normalized_scope, media_class, source_path.name)
    return {
        "storage_mode": config.storage_mode,
        "manual_copy_required": config.storage_mode != "repo_assets",
        "source_path": source_path.name,
        "media_path": media_path,
        "media_token": link,
        "media_link": link,
        "title": title,
        "repo_asset_path": (
            repo_asset_rel_path_for(normalized_scope, media_class, source_path.name)
            if config.storage_mode == "repo_assets"
            else ""
        ),
        "public_path": (
            repo_asset_public_path_for(normalized_scope, media_class, source_path.name)
            if config.storage_mode == "repo_assets"
            else ""
        ),
    }


def is_external_or_special_markdown_target(target: str) -> bool:
    value = str(target or "").strip()
    if not value:
        return True
    if value.startswith("#"):
        return True
    parsed = urlsplit(value)
    return bool(parsed.scheme or parsed.netloc)


def resolve_package_link_target(package_root: Path, markdown_path: Path, target: str) -> Path | None:
    if is_external_or_special_markdown_target(target):
        return None
    parsed = urlsplit(str(target or ""))
    if parsed.query or parsed.fragment:
        return None
    raw_path = unquote(parsed.path or "")
    if not raw_path or raw_path.startswith("/"):
        return None
    resolved = (markdown_path.parent / raw_path).resolve()
    package_resolved = package_root.resolve()
    if not resolved.is_relative_to(package_resolved):
        return None
    return resolved


def package_source_original_path(repo_root: Path, source_path: Path) -> str:
    return relative_path(repo_root, source_path)


def next_package_media_filename(
    repo_root: Path,
    scope: str,
    doc_id: str,
    media_class: str,
    suffix: str,
    extension: str,
    used_filenames: set[str],
) -> str:
    normalized_scope = normalize_scope(scope)
    safe_doc_id = slugify(doc_id or "imported-doc")
    safe_extension = extension.lower().lstrip(".")
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    repo_asset_root = (repo_root / IMPORT_MEDIA_CONFIGS[normalized_scope].repo_assets_path_prefix / media_class).resolve()
    index = 1
    while True:
        filename = f"{safe_doc_id}-{suffix}-{index:02d}.{safe_extension}"
        repo_asset_path = (repo_asset_root / filename).resolve()
        if (
            filename not in used_filenames
            and not (staging_root / filename).exists()
            and not repo_asset_path.exists()
        ):
            used_filenames.add(filename)
            return filename
        index += 1


def build_package_media_plan(
    repo_root: Path,
    scope: str,
    *,
    package_root: Path,
    source_path: Path,
    filename: str,
    title: str,
    kind: str,
) -> dict[str, Any]:
    media_class = "img" if kind == "image" else "files"
    plan = build_media_plan(scope, media_class, Path(filename), title)
    source_rel = package_source_original_path(repo_root, source_path)
    plan.update(
        {
            "source": f"markdown_package_{kind}",
            "kind": kind,
            "source_original_path": source_rel,
            "package_relative_source_path": source_path.resolve().relative_to(package_root.resolve()).as_posix(),
        }
    )
    if kind == "image":
        plan["conversion"] = {
            "format": "webp",
            "max_width": 800,
            "resize_only_if_wider": True,
        }
    if plan["manual_copy_required"]:
        plan["staging_path"] = (STAGING_REL_DIR / filename).as_posix()
    return plan


def package_media_warning(plan: dict[str, Any]) -> str:
    if plan.get("kind") == "attachment":
        return (
            f"Copy {plan.get('source_path')} to the media path {plan.get('media_path')} "
            "before the rendered download link will work."
        )
    return (
        f"Copy {plan.get('source_path')} to the media path {plan.get('media_path')} "
        "before the rendered doc can display it."
    )


def readable_package_image_title(doc_id: str, image_index: int) -> str:
    base = slugify(doc_id or "imported-doc").replace("-", " ") or "imported doc"
    return f"{base} image {image_index:02d}"


def find_package_markdown_file(package_root: Path) -> Path:
    markdown_files = sorted(
        [
            path
            for path in package_root.rglob("*")
            if path.is_file() and path.suffix.lower() in MARKDOWN_STAGED_SUFFIXES
        ],
        key=lambda path: path.relative_to(package_root).as_posix().lower(),
    )
    if not markdown_files:
        raise ValueError(f"Markdown package {package_root.name!r} does not contain a Markdown file.")
    if len(markdown_files) > 1:
        names = ", ".join(path.relative_to(package_root).as_posix() for path in markdown_files[:5])
        if len(markdown_files) > 5:
            names += ", ..."
        raise ValueError(f"Markdown package {package_root.name!r} contains multiple Markdown files: {names}")
    return markdown_files[0]


def rewrite_markdown_package_media_links(
    repo_root: Path,
    *,
    package_root: Path,
    markdown_path: Path,
    summary: dict[str, Any],
    scope: str,
) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    doc_id = str(summary.get("proposed_doc_id") or package_root.name or "imported-doc")
    plans: list[dict[str, Any]] = []
    warnings = summary.setdefault("warnings", [])
    used_filenames: set[str] = set()
    plans_by_target: dict[str, dict[str, Any]] = {}
    unresolved_count = 0
    unsupported_count = 0

    def plan_for_image(target: str, alt: str) -> dict[str, Any] | None:
        nonlocal unresolved_count, unsupported_count
        source = resolve_package_link_target(package_root, markdown_path, target)
        if source is None:
            return None
        key = source.as_posix()
        if key in plans_by_target:
            return plans_by_target[key]
        if not source.exists() or not source.is_file():
            unresolved_count += 1
            warnings.append(f"Package image target was not found: {target}")
            return None
        suffix = source.suffix.lower()
        if suffix not in RASTER_IMAGE_STAGED_SUFFIXES:
            unsupported_count += 1
            warnings.append(f"Unsupported package image type {suffix or '(none)'} for {target}; left the link unchanged.")
            return None
        image_index = len([plan for plan in plans if plan.get("kind") == "image"]) + 1
        filename = next_package_media_filename(repo_root, scope, doc_id, "img", "image", "webp", used_filenames)
        title = readable_package_image_title(doc_id, image_index)
        plan = build_package_media_plan(
            repo_root,
            scope,
            package_root=package_root,
            source_path=source,
            filename=filename,
            title=title,
            kind="image",
        )
        plans.append(plan)
        plans_by_target[key] = plan
        if plan["manual_copy_required"]:
            warnings.append(package_media_warning(plan))
        return plan

    def plan_for_attachment(target: str, label: str) -> dict[str, Any] | None:
        nonlocal unresolved_count, unsupported_count
        source = resolve_package_link_target(package_root, markdown_path, target)
        if source is None:
            return None
        key = source.as_posix()
        if key in plans_by_target:
            return plans_by_target[key]
        if not source.exists() or not source.is_file():
            unresolved_count += 1
            warnings.append(f"Package attachment target was not found: {target}")
            return None
        suffix = source.suffix.lower()
        if suffix in RASTER_IMAGE_STAGED_SUFFIXES:
            return None
        if suffix not in FILE_MEDIA_STAGED_SUFFIXES:
            unsupported_count += 1
            warnings.append(f"Unsupported package attachment type {suffix or '(none)'} for {target}; left the link unchanged.")
            return None
        filename = next_package_media_filename(repo_root, scope, doc_id, "files", "attachment", suffix, used_filenames)
        title = normalize_space(label) or humanize(source.stem) or f"Attachment {len([plan for plan in plans if plan.get('kind') == 'attachment']) + 1:02d}"
        plan = build_package_media_plan(
            repo_root,
            scope,
            package_root=package_root,
            source_path=source,
            filename=filename,
            title=title,
            kind="attachment",
        )
        plans.append(plan)
        plans_by_target[key] = plan
        if plan["manual_copy_required"]:
            warnings.append(package_media_warning(plan))
        return plan

    def replace_image(match: re.Match[str]) -> str:
        target = match.group("target")
        if str(target or "").startswith("data:image/"):
            return match.group(0)
        plan = plan_for_image(target, match.group("alt"))
        if not plan:
            return match.group(0)
        title = str(plan.get("title") or "").replace('"', r"\"")
        return f"![{plan['title']}]({plan['media_token']} \"{title}\")"

    def replace_link(match: re.Match[str]) -> str:
        plan = plan_for_attachment(match.group("target"), match.group("label"))
        if not plan:
            return match.group(0)
        return f"[{match.group('label')}]({plan['media_token']}{match.group('title') or ''})"

    markdown = MARKDOWN_IMAGE_REWRITE_PATTERN.sub(replace_image, markdown)
    markdown = MARKDOWN_LINK_REWRITE_PATTERN.sub(replace_link, markdown)
    summary["markdown_preview"] = markdown
    if plans:
        summary["media_plans"] = plans
    summary["source_stats"]["images"] = int(summary["source_stats"].get("images") or 0)
    summary["source_stats"]["attachments"] = len([plan for plan in plans if plan.get("kind") == "attachment"])
    summary["package_media_summary"] = {
        "planned": len(plans),
        "images": len([plan for plan in plans if plan.get("kind") == "image"]),
        "attachments": len([plan for plan in plans if plan.get("kind") == "attachment"]),
        "unresolved": unresolved_count,
        "unsupported": unsupported_count,
    }


def build_image_summary(source_path: Path, scope: str) -> dict[str, Any]:
    title = humanize(source_path.stem) or "Imported Image"
    plan = build_media_plan(scope, "img", source_path, title)
    markdown = f"# {title}\n\n![{title}]({plan['media_token']})"
    warnings = []
    if plan["manual_copy_required"]:
        warnings.append(
            f"Copy {source_path.name} to the media path {plan['media_path']} before the rendered doc can display it."
        )
    return {
        "title": title,
        "title_source": "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": 0,
            "links": 0,
            "images": 1,
            "svg": 0,
            "details": 0,
            "size_bytes": source_path.stat().st_size,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 1,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "media_plan": plan,
    }


def build_file_media_summary(source_path: Path, scope: str) -> dict[str, Any]:
    title = humanize(source_path.stem) or "Imported File"
    plan = build_media_plan(scope, "files", source_path, title)
    markdown = f"# {title}\n\n[Download {title}]({plan['media_token']})"
    warnings = []
    if plan["manual_copy_required"]:
        warnings.append(
            f"Copy {source_path.name} to the media path {plan['media_path']} before the rendered download link will work."
        )
    return {
        "title": title,
        "title_source": "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": 0,
            "links": 1,
            "images": 0,
            "svg": 0,
            "details": 0,
            "size_bytes": source_path.stat().st_size,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "media_plan": plan,
    }


def generate_markdown_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_markdown = source_path.read_text(encoding="utf-8", errors="replace")
    summary = build_markdown_summary(source_markdown, source_path.stem)
    summary["scope"] = normalized_scope
    summary["source_format"] = "markdown"
    summary["source_path"] = relative_path(repo_root, source_path)
    summary["source_markdown"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    apply_inline_raster_media_plans(repo_root, summary, normalized_scope)
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def generate_markdown_package_import_preview(
    repo_root: Path,
    *,
    package_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    package_root = package_path.resolve()
    markdown_path = find_package_markdown_file(package_root)
    source_markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
    package_markdown = normalize_apple_notes_caption_spans(source_markdown)
    summary = build_markdown_summary(package_markdown, package_path.name)
    summary["scope"] = normalized_scope
    summary["source_format"] = "markdown_package"
    summary["source_path"] = relative_path(repo_root, package_root)
    summary["source_markdown"] = relative_path(repo_root, markdown_path)
    summary["package_path"] = relative_path(repo_root, package_root)
    summary["package_markdown_path"] = markdown_path.relative_to(package_root).as_posix()
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    rewrite_markdown_package_media_links(
        repo_root,
        package_root=package_root,
        markdown_path=markdown_path,
        summary=summary,
        scope=normalized_scope,
    )
    apply_inline_raster_media_plans(repo_root, summary, normalized_scope)
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def generate_text_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_text = source_path.read_text(encoding="utf-8", errors="replace")
    summary = build_text_summary(source_text, source_path.stem)
    summary["scope"] = normalized_scope
    summary["source_format"] = "text"
    summary["source_path"] = relative_path(repo_root, source_path)
    summary["source_text"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def generate_svg_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_svg = source_path.read_text(encoding="utf-8", errors="replace")
    sanitized_svg, svg_title, warnings, svg_count = sanitize_svg_source(source_svg)
    title = svg_title or humanize(source_path.stem) or "Imported Diagram"
    markdown = f"# {title}\n\n{sanitized_svg}".strip()
    summary = {
        "title": title,
        "title_source": "svg_title" if svg_title else "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": len(source_svg),
            "links": len(PLAIN_URL_PATTERN.findall(source_svg)),
            "images": source_svg.lower().count("<image"),
            "svg": svg_count,
            "details": 0,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "scope": normalized_scope,
        "source_format": "svg",
        "source_path": relative_path(repo_root, source_path),
        "source_svg": relative_path(repo_root, source_path),
        "staging_root": STAGING_REL_DIR.as_posix(),
        "tag_counts": {"svg": svg_count} if svg_count else {},
        "comment_count": 0,
    }
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def generate_image_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_image_summary(source_path, normalized_scope)
    summary["scope"] = normalized_scope
    summary["source_format"] = "image"
    summary["source_path"] = relative_path(repo_root, source_path)
    summary["source_media"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def generate_file_media_import_preview(
    repo_root: Path,
    *,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_file_media_summary(source_path, normalized_scope)
    summary["scope"] = normalized_scope
    summary["source_format"] = "file"
    summary["source_path"] = relative_path(repo_root, source_path)
    summary["source_media"] = relative_path(repo_root, source_path)
    summary["staging_root"] = STAGING_REL_DIR.as_posix()
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["jekyll_validation"] = validate_markdown_with_jekyll(repo_root, summary["markdown_preview"])
    return summary


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not (root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {root}")
        return root
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        current = candidate.resolve()
        for parent in [current, *current.parents]:
            if (parent / "_config.yml").exists():
                return parent
    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def resolve_import_source(repo_root: Path, args: argparse.Namespace) -> Path:
    if args.source_html:
        path = Path(args.source_html).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Source HTML does not exist: {path}")
        return path
    if args.staged_filename:
        try:
            return resolve_staged_import_source(repo_root, args.staged_filename)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
    raise SystemExit("Pass either --source-html or --staged-filename.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run source import conversion for Docs Viewer source docs.")
    parser.add_argument("--repo-root", default="", help="Override repo root auto-detection.")
    parser.add_argument("--source-html", default="", help="Import directly from an HTML file path.")
    parser.add_argument("--staged-filename", default="", help="Import from var/docs/import-staging/<filename>.")
    parser.add_argument("--scope", default="studio", choices=sorted(SCOPE_ROOTS.keys()), help="Target docs scope.")
    parser.add_argument("--include-prompt-meta", action="store_true", help="Include clearly identifiable prompt/meta blocks.")
    parser.add_argument("--markdown-preview-out", default="", help="Optional path to write the Markdown preview.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = detect_repo_root(args.repo_root)
    source_path = resolve_import_source(repo_root, args)
    summary = generate_import_preview(
        repo_root,
        source_path=source_path,
        scope=args.scope,
        include_prompt_meta=bool(args.include_prompt_meta),
    )

    if args.markdown_preview_out:
        output_path = Path(args.markdown_preview_out).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary["markdown_preview"] + "\n", encoding="utf-8")
        summary["markdown_preview_out"] = str(output_path)

    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
