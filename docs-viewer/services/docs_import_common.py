#!/usr/bin/env python3
"""Shared constants and helpers for Docs staged source imports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from docs_scope_config import DOCUMENT_SOURCE_ROOTS

HTML_STAGED_SUFFIXES = {".html", ".htm"}
MARKDOWN_STAGED_SUFFIXES = {".md", ".markdown"}
TEXT_STAGED_SUFFIXES = {".txt"}
SVG_STAGED_SUFFIXES = {".svg"}
RASTER_IMAGE_STAGED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
FILE_MEDIA_STAGED_SUFFIXES = {".pdf", ".zip", ".csv", ".tsv", ".json", ".jsonl", ".docx", ".xlsx", ".pptx"}
DOCUMENT_STAGED_SUFFIXES = HTML_STAGED_SUFFIXES | MARKDOWN_STAGED_SUFFIXES | TEXT_STAGED_SUFFIXES
TRUSTED_PACKAGE_CANDIDATE_SUFFIXES = {".json", ".jsonl"}
SUPPORTED_STAGED_SUFFIXES = DOCUMENT_STAGED_SUFFIXES | TRUSTED_PACKAGE_CANDIDATE_SUFFIXES

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

INLINE_RASTER_EXTENSIONS = {
    "gif": "gif",
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "webp": "webp",
}
DOCS_IMPORT_ROLE_META_NAME = "dlf:docs-import-role"
INTERACTIVE_HTML_ROLE = "interactive-html"
IMPORT_RESULTS_DIR_NAME = "results"


SOURCE_FORMAT_BY_SUFFIX = {
    **{suffix: "html" for suffix in HTML_STAGED_SUFFIXES},
    **{suffix: "markdown" for suffix in MARKDOWN_STAGED_SUFFIXES},
    **{suffix: "text" for suffix in TEXT_STAGED_SUFFIXES},
}

def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def escape_markdown_pipes(text: str) -> str:
    return (text or "").replace("|", r"\|")

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
    if value not in DOCUMENT_SOURCE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(DOCUMENT_SOURCE_ROOTS.keys()))}")
    return value


def source_format_for_path(path: Path) -> str:
    if path.is_dir():
        return "markdown_package"
    source_format = SOURCE_FORMAT_BY_SUFFIX.get(path.suffix.lower())
    if source_format:
        return source_format
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
