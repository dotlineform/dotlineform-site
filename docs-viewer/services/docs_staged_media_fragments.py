"""Build source links for staged files; image source is owned by docs_image_tokens."""

from __future__ import annotations

from typing import Any


def build_file_link_fragment(label: Any, media_token: Any) -> str:
    """Return an escaped Markdown label around the managed file reference."""
    if not isinstance(label, str) or not label.strip():
        raise ValueError("label is required")
    if not isinstance(media_token, str) or not media_token.strip():
        raise ValueError("media_token is required")
    text = " ".join(label.split())
    escaped = text.replace("\\", r"\\").replace("[", r"\[").replace("]", r"\]")
    return f"[{escaped}]({media_token.strip()})"
