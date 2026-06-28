#!/usr/bin/env python3
"""Field extraction and transform helpers for Docs Viewer exports."""

from __future__ import annotations

import copy
from html.parser import HTMLParser
from typing import Any

from docs_data_sharing import rendered_content
from docs_export_common import collapse_blank_lines, normalize_text, trim_blank_lines
from docs_export_config import SUPPORTED_TRANSFORMS
from docs_export_selection import ExportContext


class PlainTextExtractor(HTMLParser):
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
        "section",
        "table",
    }

    def __init__(
        self,
        *,
        title: str,
        omit_code_blocks: bool,
        image_text_mode: str,
        empty_image_mode: str,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.title = normalize_text(title)
        self.omit_code_blocks = omit_code_blocks
        self.image_text_mode = image_text_mode
        self.empty_image_mode = empty_image_mode
        self.lines: list[str] = []
        self.current_line = ""
        self.list_stack: list[dict[str, Any]] = []
        self.skip_depth = 0
        self.svg_depth = 0
        self.svg_text_tag: str | None = None
        self.svg_parts: list[str] = []
        self.blockquote_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        attrs_by_name = {key.lower(): str(value or "") for key, value in attrs}

        if tag_name in {"script", "style"} or (self.omit_code_blocks and tag_name in {"pre", "code"}):
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        if self.svg_depth:
            self.svg_depth += 1
            if tag_name in {"title", "desc", "text"}:
                self.svg_text_tag = tag_name
            return

        if tag_name == "svg":
            self.flush_line()
            self.svg_depth = 1
            self.svg_parts = []
            self.svg_text_tag = None
            return
        if tag_name in self.BLOCK_TAGS:
            self.block_break()
            if tag_name == "blockquote":
                self.blockquote_depth += 1
        elif tag_name == "br":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            self.block_break()
            self.list_stack.append({"tag": tag_name, "counter": 0})
        elif tag_name == "li":
            self.flush_line()
            prefix = "- "
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["counter"] += 1
                prefix = f"{self.list_stack[-1]['counter']}. "
            self.add_raw(prefix)
        elif tag_name == "img":
            self.add_image_marker(attrs_by_name.get("alt", ""))

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if self.skip_depth:
            if tag_name in {"script", "style", "pre", "code"}:
                self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.svg_depth:
            if tag_name == self.svg_text_tag:
                self.svg_text_tag = None
            self.svg_depth -= 1
            if self.svg_depth == 0:
                self.add_image_marker("; ".join(self.svg_parts))
                self.svg_parts = []
                self.svg_text_tag = None
            return

        if tag_name in self.BLOCK_TAGS:
            self.block_break()
            if tag_name == "blockquote":
                self.blockquote_depth = max(0, self.blockquote_depth - 1)
        elif tag_name == "li":
            self.flush_line()
        elif tag_name in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.block_break()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.svg_depth:
            if self.svg_text_tag:
                text = normalize_text(data)
                if text:
                    self.svg_parts.append(text)
            return
        self.add_text(data)

    def add_raw(self, value: str) -> None:
        self.current_line += value

    def add_text(self, value: str) -> None:
        text = normalize_text(value)
        if not text:
            return
        if self.current_line and not self.current_line.endswith((" ", "\n")):
            self.current_line += " "
        self.current_line += text

    def add_image_marker(self, text: str) -> None:
        if self.image_text_mode == "omit":
            return
        image_text = normalize_text(text)
        if self.image_text_mode == "marker":
            marker = "[image]"
        elif self.image_text_mode == "extract_text" and image_text:
            marker = f"[image: {image_text}]"
        elif self.empty_image_mode == "marker":
            marker = "[image]"
        else:
            return
        self.flush_line()
        self.lines.append(marker)
        self.block_break()

    def flush_line(self) -> None:
        line = normalize_text(self.current_line)
        if line:
            if self.blockquote_depth and not line.startswith(">"):
                line = f"> {line}"
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


def normalize_plain_text(value: str) -> str:
    normalized_lines = [normalize_text(line) for line in str(value or "").splitlines()]
    return "\n".join(collapse_blank_lines(trim_blank_lines(normalized_lines))).strip()


def plain_text_from_rendered_html(
    content_html: str,
    *,
    title: str,
    omit_code_blocks: bool,
    options: dict[str, Any],
) -> str:
    image_text_mode = normalize_text(options.get("image_text_mode") or "extract_text")
    empty_image_mode = normalize_text(options.get("empty_image_mode") or "omit")
    if image_text_mode not in {"omit", "marker", "extract_text"}:
        image_text_mode = "extract_text"
    if empty_image_mode not in {"omit", "marker"}:
        empty_image_mode = "omit"
    parser = PlainTextExtractor(
        title=title,
        omit_code_blocks=omit_code_blocks,
        image_text_mode=image_text_mode,
        empty_image_mode=empty_image_mode,
    )
    parser.feed(content_html)
    parser.close()
    return parser.text()


def truncate_text(value: str, *, max_chars: int | None, marker: str, strategy: str) -> tuple[str, bool]:
    text = str(value or "")
    if not isinstance(max_chars, int) or max_chars < 1 or len(text) <= max_chars:
        return text, False
    marker_text = marker or "[truncated]"
    limit = max(0, max_chars - len(marker_text) - 1)
    truncated = text[:limit].rstrip()
    if strategy == "paragraph_boundary":
        boundary = truncated.rfind("\n\n")
        if boundary > 0:
            truncated = truncated[:boundary].rstrip()
    if truncated:
        return f"{truncated}\n{marker_text}", True
    return marker_text[:max_chars], True


def apply_transforms(
    value: Any,
    *,
    transforms: list[str],
    context: ExportContext,
    doc: dict[str, Any],
    mapping: dict[str, Any],
) -> tuple[Any, bool]:
    transformed = value
    truncated = False
    transform_set = set(transforms)
    for transform in transforms:
        if transform in {"identity", "headings_from_rendered_html", "omit_code_blocks"}:
            continue
        if transform == "plain_text_from_rendered_html":
            transformed = plain_text_from_rendered_html(
                str(transformed or ""),
                title=normalize_text(doc.get("title")),
                omit_code_blocks="omit_code_blocks" in transform_set,
                options=mapping.get("options") if isinstance(mapping.get("options"), dict) else {},
            )
        elif transform == "normalize_whitespace":
            transformed = normalize_plain_text(str(transformed or ""))
        elif transform == "truncate_chars":
            limit_key = normalize_text(mapping.get("limit_key"))
            limit_value = context.config.get("limits", {}).get(limit_key)
            truncate_config = context.config.get("limits", {}).get("truncate", {})
            transformed, was_truncated = truncate_text(
                str(transformed or ""),
                max_chars=limit_value if isinstance(limit_value, int) else None,
                marker=normalize_text(truncate_config.get("marker") or "[truncated]"),
                strategy=normalize_text(truncate_config.get("strategy") or "hard"),
            )
            truncated = truncated or was_truncated
        else:
            raise ValueError(f"Unsupported transform: {transform}")
    return transformed, truncated


def ancestor_chain(context: ExportContext, doc: dict[str, Any]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    parent_id = normalize_text(doc.get("parent_id"))
    while parent_id:
        if parent_id in seen:
            break
        seen.add(parent_id)
        parent = context.docs_by_id.get(parent_id)
        if parent is None:
            break
        chain.append(parent)
        parent_id = normalize_text(parent.get("parent_id"))
    chain.reverse()
    return chain


def source_value(context: ExportContext, doc: dict[str, Any], source: str) -> Any:
    doc_id = normalize_text(doc.get("doc_id"))
    if source in {"doc_id", "title", "parent_id", "summary", "last_updated", "viewable"}:
        return doc.get(source)
    if source == "current_summary":
        return doc.get("summary", "")
    if source == "parent_title":
        parent_id = normalize_text(doc.get("parent_id"))
        parent = context.docs_by_id.get(parent_id)
        return parent.get("title") if parent else ""
    if source == "ancestors":
        return related_document_refs(ancestor_chain(context, doc))
    if source == "children":
        return related_document_refs(context.children_by_parent.get(doc_id, []))
    if source == "headings":
        return rendered_content.doc_headings(context.source_context, doc_id)
    if source == "source_text":
        return rendered_content.render_doc_html(context.source_context, doc_id)
    raise ValueError(f"Unsupported field source: {source}")


def related_document_refs(docs: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in docs:
        ref_id = normalize_text(item.get("doc_id"))
        if not ref_id:
            continue
        refs.append(
            {
                "id": ref_id,
                "title": normalize_text(item.get("title")),
            }
        )
    return refs


def set_output_path(record: dict[str, Any], output_path: str, value: Any) -> None:
    parts = [part for part in output_path.split(".") if part]
    if not parts:
        raise ValueError("output_path cannot be blank")
    target = record
    for part in parts[:-1]:
        current = target.get(part)
        if not isinstance(current, dict):
            current = {}
            target[part] = current
        target = current
    target[parts[-1]] = value


def build_document_record(context: ExportContext, doc: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str], bool]:
    record: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    truncated = False
    doc_id = normalize_text(doc.get("doc_id"))
    for mapping in context.config.get("document_fields", []):
        if not isinstance(mapping, dict):
            errors.append(f"{doc_id}: invalid field mapping")
            continue
        source = normalize_text(mapping.get("source"))
        output_path = normalize_text(mapping.get("output_path"))
        transforms = [normalize_text(item) for item in mapping.get("transforms", [])]
        unsupported = [item for item in transforms if item and item not in SUPPORTED_TRANSFORMS]
        if unsupported:
            errors.append(f"{doc_id}: unsupported transform(s): {', '.join(unsupported)}")
            continue
        try:
            value = source_value(context, doc, source)
        except (FileNotFoundError, ValueError, NotImplementedError) as exc:
            errors.append(f"{doc_id}: {exc}")
            continue

        if value is None and "default" in mapping:
            value = copy.deepcopy(mapping.get("default"))
        if value is None:
            value = ""
        try:
            value, was_truncated = apply_transforms(
                value,
                transforms=transforms,
                context=context,
                doc=doc,
                mapping=mapping,
            )
            truncated = truncated or was_truncated
        except ValueError as exc:
            errors.append(f"{doc_id}: {exc}")
            continue
        if mapping.get("required") and value in ("", [], {}):
            errors.append(f"{doc_id}: required field {source} is empty")
            continue
        if not mapping.get("include_if_empty", True) and value in ("", [], {}):
            continue
        if not output_path:
            errors.append(f"{doc_id}: field {source} has blank output_path")
            continue
        set_output_path(record, output_path, value)
    return record, warnings, errors, truncated
