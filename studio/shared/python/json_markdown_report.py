"""Deterministic Markdown rendering and atomic writing for JSON-compatible reports."""

from __future__ import annotations

import math
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping


def _validate_json_value(value: Any, *, path: str = "payload") -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} mapping keys must be strings")
            _validate_json_value(item, path=f"{path}.{key}")
        return
    raise ValueError(f"{path} must contain only JSON-compatible values")


def _escape_inline(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    text = str(value)
    for character in ("\\", "`", "*", "_", "[", "]", "<", ">", "#", "|"):
        text = text.replace(character, f"\\{character}")
    return text.replace("\r", " ").replace("\n", "  \n")


def _label(value: str) -> str:
    return _escape_inline(value.replace("_", " ").strip())


def _ordered_items(
    payload: Mapping[str, Any],
    section_order: Iterable[str] | None,
) -> list[tuple[str, Any]]:
    if section_order is None:
        return list(payload.items())
    ordered_keys: list[str] = []
    seen: set[str] = set()
    for raw_key in section_order:
        key = str(raw_key)
        if key in payload and key not in seen:
            ordered_keys.append(key)
            seen.add(key)
    ordered_keys.extend(key for key in payload if key not in seen)
    return [(key, payload[key]) for key in ordered_keys]


def _render_list_item(value: Any, *, indent: int) -> list[str]:
    prefix = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for index, (key, item) in enumerate(value.items()):
            marker = "-" if index == 0 else " "
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{marker} **{_label(key)}:**")
                lines.extend(_render_nested(item, indent=indent + 1))
            else:
                lines.append(f"{prefix}{marker} **{_label(key)}:** {_escape_inline(item)}")
        return lines or [f"{prefix}- {{}}"]
    if isinstance(value, list):
        if not value:
            return [f"{prefix}- []"]
        lines = []
        for item in value:
            lines.extend(_render_list_item(item, indent=indent))
        return lines
    return [f"{prefix}- {_escape_inline(value)}"]


def _render_nested(value: Any, *, indent: int = 0) -> list[str]:
    if isinstance(value, list):
        if not value:
            return [f"{'  ' * indent}- []"]
        lines: list[str] = []
        for item in value:
            lines.extend(_render_list_item(item, indent=indent))
        return lines
    if isinstance(value, dict):
        if not value:
            return [f"{'  ' * indent}- {{}}"]
        return _render_list_item(value, indent=indent)
    return [_escape_inline(value)]


def render_json_markdown_report(
    payload: Any,
    *,
    title: str,
    section_order: Iterable[str] | None = None,
) -> str:
    """Render JSON-compatible data as deterministic escaped Markdown."""

    _validate_json_value(payload)
    clean_title = str(title or "").strip()
    if not clean_title:
        raise ValueError("title is required")
    lines = [f"# {_escape_inline(clean_title)}"]
    if isinstance(payload, dict):
        for key, value in _ordered_items(payload, section_order):
            lines.extend(["", f"## {_label(key)}", ""])
            lines.extend(_render_nested(value))
    else:
        lines.extend(["", *_render_nested(payload)])
    return "\n".join(lines).rstrip() + "\n"


def write_json_markdown_report(
    path: Path | str,
    payload: Any,
    *,
    title: str,
    section_order: Iterable[str] | None = None,
) -> Path:
    """Render and atomically replace one caller-selected Markdown report path."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_json_markdown_report(
        payload,
        title=title,
        section_order=section_order,
    )
    descriptor, temp_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(markdown)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return target


__all__ = ["render_json_markdown_report", "write_json_markdown_report"]
