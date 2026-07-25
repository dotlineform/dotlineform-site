#!/usr/bin/env python3
"""Shared Mermaid CLI, sanitization, and SVG validation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable

from lxml import etree

from docs_mermaid_accessibility import mermaid_accessibility_metadata
from docs_svg_sanitizer import sanitize_svg_bytes


MERMAID_TOOLCHAIN_ROOT = Path(__file__).resolve().parents[1] / "build" / "mermaid"
MERMAID_EXECUTABLE_RELATIVE_PATH = Path("node_modules/.bin/mmdc")
MERMAID_CONFIG_FILENAME = "mermaid-config.json"
MERMAID_VIEWPORT_WIDTH = 1200
MERMAID_VIEWPORT_HEIGHT = 800
VISIBLE_SVG_ELEMENTS = frozenset(
    {"circle", "ellipse", "image", "line", "path", "polygon", "polyline", "rect", "text", "use"}
)


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class RenderedMermaidSvg:
    bytes: bytes
    title: str
    description: str
    view_box: tuple[float, float, float, float]


def _local_name(value: str) -> str:
    return etree.QName(value).localname.lower()


def mermaid_toolchain_paths(toolchain_root: Path) -> tuple[Path, Path]:
    executable = toolchain_root / MERMAID_EXECUTABLE_RELATIVE_PATH
    config = toolchain_root / MERMAID_CONFIG_FILENAME
    if not executable.is_file():
        raise RuntimeError(
            "Mermaid CLI is not installed; run npm install in docs-viewer/build/mermaid"
        )
    if not config.is_file():
        raise RuntimeError(f"Mermaid render config is missing: {config}")
    return executable, config


def mermaid_render_command(
    executable: Path,
    config: Path,
    source: Path,
    output: Path,
    *,
    background: str,
) -> list[str]:
    return [
        str(executable),
        "--input",
        str(source),
        "--output",
        str(output),
        "--configFile",
        str(config),
        "--backgroundColor",
        background,
        "--width",
        str(MERMAID_VIEWPORT_WIDTH),
        "--height",
        str(MERMAID_VIEWPORT_HEIGHT),
    ]


def inspect_sanitized_mermaid_svg(identity: str, data: bytes) -> RenderedMermaidSvg:
    try:
        root = etree.fromstring(data)
    except etree.XMLSyntaxError as exc:  # pragma: no cover - the sanitizer parses first
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} is not well-formed") from exc

    raw_view_box = str(root.get("viewBox") or "").split()
    try:
        view_box = tuple(float(value) for value in raw_view_box)
    except ValueError as exc:
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} has an invalid viewBox") from exc
    if len(view_box) != 4 or view_box[2] <= 0 or view_box[3] <= 0:
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} requires a responsive viewBox")

    titles = [
        " ".join("".join(element.itertext()).split())
        for element in root.iter()
        if isinstance(element.tag, str) and _local_name(element.tag) == "title"
    ]
    descriptions = [
        " ".join("".join(element.itertext()).split())
        for element in root.iter()
        if isinstance(element.tag, str) and _local_name(element.tag) == "desc"
    ]
    title = next((value for value in titles if value), "")
    description = next((value for value in descriptions if value), "")
    if not title or not description:
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} lost required accessibility metadata")
    if not any(
        isinstance(element.tag, str) and _local_name(element.tag) in VISIBLE_SVG_ELEMENTS
        for element in root.iter()
    ):
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} contains no visible diagram content")
    return RenderedMermaidSvg(
        bytes=data,
        title=title,
        description=description,
        view_box=(view_box[0], view_box[1], view_box[2], view_box[3]),
    )


def render_mermaid_path(
    identity: str,
    source_path: Path,
    *,
    executable: Path,
    config: Path,
    background: str,
    output_path: Path,
    run_command: CommandRunner = subprocess.run,
    require_matching_accessibility: bool = False,
) -> RenderedMermaidSvg:
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Mermaid source {identity!r} must be UTF-8 text") from exc
    accessibility = mermaid_accessibility_metadata(identity, source_text)
    command = mermaid_render_command(
        executable,
        config,
        source_path,
        output_path,
        background=background,
    )
    try:
        completed = run_command(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"Mermaid renderer could not start for {identity!r}: {exc}") from exc
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout or "").split())
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"Mermaid renderer failed for {identity!r}{suffix}")
    if not output_path.is_file():
        raise RuntimeError(f"Mermaid renderer produced no SVG for {identity!r}")

    try:
        sanitized = sanitize_svg_bytes(output_path.read_bytes())
    except ValueError as exc:
        raise RuntimeError(f"Mermaid renderer produced invalid SVG for {identity!r}: {exc}") from exc
    rendered = inspect_sanitized_mermaid_svg(identity, sanitized.bytes)
    if require_matching_accessibility and (
        rendered.title != accessibility.title
        or rendered.description != accessibility.description
    ):
        raise RuntimeError(
            f"Sanitized Mermaid SVG for {identity!r} changed required accessibility metadata"
        )
    return rendered


__all__ = [
    "CommandRunner",
    "MERMAID_CONFIG_FILENAME",
    "MERMAID_EXECUTABLE_RELATIVE_PATH",
    "MERMAID_TOOLCHAIN_ROOT",
    "MERMAID_VIEWPORT_HEIGHT",
    "MERMAID_VIEWPORT_WIDTH",
    "RenderedMermaidSvg",
    "inspect_sanitized_mermaid_svg",
    "mermaid_render_command",
    "mermaid_toolchain_paths",
    "render_mermaid_path",
]
