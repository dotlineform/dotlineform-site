#!/usr/bin/env python3
"""Build validated source fragments for staged Docs media."""

from __future__ import annotations

from html import escape
from typing import Any


FIGURE_PLACEMENT_FULL = "full"
FIGURE_PLACEMENT_LEFT = "left"
FIGURE_PLACEMENT_RIGHT = "right"
FIGURE_PLACEMENT_CLASSES = {
    FIGURE_PLACEMENT_FULL: "docsViewerFigure--full-column",
    FIGURE_PLACEMENT_LEFT: "docsViewerFigure--image-left",
    FIGURE_PLACEMENT_RIGHT: "docsViewerFigure--image-right",
}
FIGURE_NATURAL_WIDTH_CLASS = "docsViewerFigure--natural-width"


def _plain_text(value: Any, *, field: str, required: bool) -> str:
    if value is None:
        text = ""
    elif not isinstance(value, str):
        raise ValueError(f"{field} must be plain text")
    else:
        text = " ".join(value.split())
    if required and not text:
        raise ValueError(f"{field} is required")
    return text


def _multiline_plain_text(value: Any, *, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be plain text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [" ".join(line.split()) for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def _boolean(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _markdown_label(value: Any, *, field: str) -> str:
    text = _plain_text(value, field=field, required=True)
    return text.replace("\\", r"\\").replace("[", r"\[").replace("]", r"\]")


def _media_token(value: Any) -> str:
    return _plain_text(value, field="media_token", required=True)


def validate_figure_presentation(
    caption: Any,
    summary: Any,
    placement: Any,
    fill_width: Any,
) -> tuple[str, str, str, bool]:
    caption_text = _plain_text(caption, field="caption", required=True)
    summary_text = _multiline_plain_text(summary, field="summary")
    placement_value = _plain_text(placement, field="placement", required=True).lower()
    if placement_value not in FIGURE_PLACEMENT_CLASSES:
        allowed = ", ".join(FIGURE_PLACEMENT_CLASSES)
        raise ValueError(f"placement must be one of: {allowed}")
    fill_width_value = _boolean(fill_width, field="fill_width")
    return caption_text, summary_text, placement_value, fill_width_value


def build_plain_image_fragment(alt_text: Any, media_token: Any) -> str:
    return f"![{_markdown_label(alt_text, field='alt_text')}]({_media_token(media_token)})"


def build_figure_image_fragment(
    alt_text: Any,
    media_token: Any,
    *,
    caption: Any,
    summary: Any = "",
    placement: Any,
    fill_width: Any,
) -> str:
    alt = _plain_text(alt_text, field="alt_text", required=True)
    token = _media_token(media_token)
    caption_text, summary_text, placement_value, fill_width_value = validate_figure_presentation(
        caption,
        summary,
        placement,
        fill_width,
    )
    modifiers = [FIGURE_PLACEMENT_CLASSES[placement_value]]
    if not fill_width_value:
        modifiers.append(FIGURE_NATURAL_WIDTH_CLASS)
    modifier_classes = " ".join(modifiers)
    summary_html = (
        f'\n    <span class="docsViewerFigure__summary">{escape(summary_text, quote=False)}</span>'
        if summary_text
        else ""
    )
    return (
        f'<figure class="docsViewerFigure {modifier_classes}">\n'
        f'  <img src="{escape(token, quote=True)}" alt="{escape(alt, quote=True)}">\n'
        "  <figcaption>\n"
        f'    <span class="docsViewerFigure__caption">{escape(caption_text, quote=False)}</span>'
        f"{summary_html}\n"
        "  </figcaption>\n"
        "</figure>"
    )


def build_file_link_fragment(label: Any, media_token: Any) -> str:
    return f"[{_markdown_label(label, field='label')}]({_media_token(media_token)})"


__all__ = [
    "FIGURE_PLACEMENT_FULL",
    "FIGURE_PLACEMENT_LEFT",
    "FIGURE_PLACEMENT_RIGHT",
    "FIGURE_NATURAL_WIDTH_CLASS",
    "build_figure_image_fragment",
    "build_file_link_fragment",
    "build_plain_image_fragment",
    "validate_figure_presentation",
]
