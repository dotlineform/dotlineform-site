"""Canonical, write-free source grammar for Docs-owned semantic images."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import quote, unquote_to_bytes


FIGURE_PLACEMENT_CLASSES = {
    "full": "docsViewerFigure--full-column",
    "left": "docsViewerFigure--image-left",
    "right": "docsViewerFigure--image-right",
}
FIGURE_NATURAL_WIDTH_CLASS = "docsViewerFigure--natural-width"
IMAGE_FIELDS = frozenset({"alt", "caption", "summary", "placement", "fill_width"})
TEXT_SPACE = re.compile(r"[\t\n\v\f\r \x1c-\x1f\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+")
IMAGE_PATH = re.compile(r"docs/(?:collections/[a-z0-9][a-z0-9-]*/)?(?P<media_type>img|svg)/.+")


@dataclass(frozen=True)
class ImageToken:
    """Decoded authored fields; media_path is logical identity, never a URL."""

    media_path: str
    alt: str
    caption: str
    summary: str
    placement: str
    fill_width: bool

    @property
    def media_type(self) -> str:
        return IMAGE_PATH.fullmatch(self.media_path).group("media_type")


def image_text(value: str, *, multiline: bool = False) -> str:
    """Normalize literal text identically to the browser image serializer."""
    if multiline:
        lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        return "\n".join(TEXT_SPACE.sub(" ", line).strip(" ") for line in lines).strip(" \n")
    return TEXT_SPACE.sub(" ", value).strip(" ")


def encode_image_value(value: str) -> str:
    return quote(value, safe="-._~")


def encode_image_path(value: str) -> str:
    return quote(value, safe="/-._~")


def valid_image_path(value: str) -> bool:
    """Reject non-Docs roles, ambiguous separators and traversal before resolution."""
    return bool(
        IMAGE_PATH.fullmatch(value)
        and not re.search(r"[\\\x00-\x1f\x7f]", value)
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def decode_image_value(value: str, *, path: bool = False) -> str | None:
    """Decode only canonical UTF-8 escapes, using slash separators for identities."""
    try:
        decoded = unquote_to_bytes(value).decode("utf-8")
        encoded = encode_image_path(decoded) if path else encode_image_value(decoded)
    except (UnicodeError, ValueError):
        return None
    return decoded if encoded == value else None


def serialize_image_token(
    *, media_path: Any, alt: Any, caption: Any = "", summary: Any = "",
    placement: Any, fill_width: Any,
) -> str:
    """Return the one canonical source form, or empty text for invalid fields."""
    if (
        not isinstance(media_path, str) or not valid_image_path(media_path)
        or not all(isinstance(value, str) for value in (alt, caption, summary, placement))
        or type(fill_width) is not bool
    ):
        return ""
    alt_text = image_text(alt)
    caption_text = image_text(caption)
    summary_text = image_text(summary, multiline=True)
    placement_text = image_text(placement).lower()
    if not alt_text or placement_text not in FIGURE_PLACEMENT_CLASSES:
        return ""
    fields = [("alt", alt_text)]
    if caption_text:
        fields.append(("caption", caption_text))
    if summary_text:
        fields.append(("summary", summary_text))
    fields.extend((("placement", placement_text), ("fill_width", "true" if fill_width else "false")))
    try:
        query = "&".join(f"{key}={encode_image_value(value)}" for key, value in fields)
        return f"[[image:{encode_image_path(media_path)}|{query}]]"
    except UnicodeError:
        return ""


def parse_image_token(raw: str) -> ImageToken | None:
    """Accept only canonical fields/order/UTF-8 encoding; never supply defaults."""
    if not raw.startswith("[[image:") or not raw.endswith("]]") or "\n" in raw or "\r" in raw:
        return None
    identity, separator, query = raw[8:-2].partition("|")
    media_path = decode_image_value(identity, path=True)
    if not separator or media_path is None:
        return None
    fields: dict[str, str] = {}
    for pair in query.split("&"):
        key, separator, encoded = pair.partition("=")
        if not separator or key not in IMAGE_FIELDS or key in fields or not encoded:
            return None
        value = decode_image_value(encoded)
        if value is None:
            return None
        fields[key] = value
    if not {"alt", "placement", "fill_width"}.issubset(fields) or fields["fill_width"] not in {"true", "false"}:
        return None
    token = ImageToken(media_path, fields["alt"], fields.get("caption", ""), fields.get("summary", ""), fields["placement"], fields["fill_width"] == "true")
    canonical = serialize_image_token(
        media_path=token.media_path, alt=token.alt, caption=token.caption, summary=token.summary,
        placement=token.placement, fill_width=token.fill_width,
    )
    return token if canonical == raw else None
