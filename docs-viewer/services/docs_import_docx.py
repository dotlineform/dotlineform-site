#!/usr/bin/env python3
"""Mammoth-owned DOCX-to-semantic-HTML adapter for Docs Import."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docs_html_markdown import ElementNode, parse_html_document, walk
from docs_import_common import normalize_space


DOCX_TITLE_CLASS = "dlf-docx-title"
DOCX_CLAMPED_HEADING_CLASS = "dlf-docx-heading-clamped"
DOCX_IMAGE_CONTENT_TYPES = {
    "image/gif": "image/gif",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
}

# Word's Title occupies the canonical document H1. Word Heading 1 therefore
# starts the document body at H2. Markdown has no H7, so Heading 6 is retained
# at H6 and reported as a lossy clamp.
DOCX_STYLE_MAP = """
p.Title => h1.dlf-docx-title:fresh
p[style-name='Title'] => h1.dlf-docx-title:fresh
p.Subtitle => p.dlf-docx-subtitle:fresh
p[style-name='Subtitle'] => p.dlf-docx-subtitle:fresh
p.Heading1 => h2:fresh
p[style-name='Heading 1'] => h2:fresh
p.Heading2 => h3:fresh
p[style-name='Heading 2'] => h3:fresh
p.Heading3 => h4:fresh
p[style-name='Heading 3'] => h4:fresh
p.Heading4 => h5:fresh
p[style-name='Heading 4'] => h5:fresh
p.Heading5 => h6:fresh
p[style-name='Heading 5'] => h6:fresh
p.Heading6 => h6.dlf-docx-heading-clamped:fresh
p[style-name='Heading 6'] => h6.dlf-docx-heading-clamped:fresh
""".strip()


@dataclass(frozen=True)
class DocxHtmlConversion:
    """Semantic HTML plus safe adapter metadata; the HTML is never rewritten."""

    html: str
    title: str
    warnings: tuple[str, ...]


def _message_text(message: Any) -> str:
    kind = normalize_space(str(getattr(message, "type", "") or "warning")).lower()
    text = normalize_space(str(getattr(message, "message", "") or message))
    if not text:
        return ""
    label = "Mammoth" if kind == "warning" else f"Mammoth {kind}"
    return f"{label}: {text}"


def _semantic_markers(source_html: str) -> tuple[str, bool]:
    parsed = parse_html_document(source_html)
    title = ""
    clamped_heading = False
    for node in walk(parsed.root):
        if not isinstance(node, ElementNode):
            continue
        classes = node.class_tokens()
        if not title and DOCX_TITLE_CLASS in classes:
            title = normalize_space(node.text_content())
        if DOCX_CLAMPED_HEADING_CLASS in classes:
            clamped_heading = True
    return title, clamped_heading


def _docx_image_converter(mammoth_module: Any, warnings: list[str]):
    image_index = 0

    def image_attributes(image: Any) -> dict[str, str]:
        nonlocal image_index
        image_index += 1
        label = normalize_space(str(getattr(image, "alt_text", "") or "")) or f"Word image {image_index:02d}"
        attributes = {"alt": label}
        content_type = normalize_space(str(getattr(image, "content_type", "") or "")).lower()
        normalized_content_type = DOCX_IMAGE_CONTENT_TYPES.get(content_type)
        if not normalized_content_type:
            warnings.append(
                f"Word image {label!r} uses unsupported media type {content_type or 'unknown'} and was omitted."
            )
            return attributes
        try:
            with image.open() as image_file:
                image_bytes = image_file.read()
        except Exception:
            warnings.append(f"Word image {label!r} could not be read and was omitted.")
            return attributes
        if not image_bytes:
            warnings.append(f"Word image {label!r} was empty and was omitted.")
            return attributes
        encoded = base64.b64encode(image_bytes).decode("ascii")
        attributes["src"] = f"data:{normalized_content_type};base64,{encoded}"
        return attributes

    return mammoth_module.images.img_element(image_attributes)


def convert_docx_to_html(source_path: Path) -> DocxHtmlConversion:
    """Convert one validated DOCX file without allowing document-owned policy."""

    try:
        import mammoth
    except ImportError as exc:
        raise RuntimeError(
            "Mammoth is required for Word document import. Install the pinned requirements.txt dependencies."
        ) from exc

    image_warnings: list[str] = []
    try:
        with source_path.open("rb") as source_file:
            result = mammoth.convert_to_html(
                source_file,
                style_map=DOCX_STYLE_MAP,
                include_default_style_map=True,
                include_embedded_style_map=False,
                external_file_access=False,
                convert_image=_docx_image_converter(mammoth, image_warnings),
            )
    except Exception as exc:
        raise ValueError(
            f"Could not convert staged Word document {source_path.name}: {type(exc).__name__}."
        ) from exc

    source_html = str(result.value or "")
    title, clamped_heading = _semantic_markers(source_html)
    warnings = [
        text
        for message in result.messages
        if (text := _message_text(message))
    ]
    warnings.extend(image_warnings)
    if clamped_heading:
        warnings.append(
            "Word Heading 6 was kept at Markdown heading level 6 because the document title occupies level 1."
        )
    return DocxHtmlConversion(
        html=source_html,
        title=title,
        warnings=tuple(warnings),
    )
