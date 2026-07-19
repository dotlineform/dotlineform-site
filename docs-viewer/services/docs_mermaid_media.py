from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Protocol, Sequence

from lxml import etree

from docs_artifact_locations import ArtifactLocationAdapter, ArtifactStat, normalize_artifact_identity
from docs_svg_sanitizer import SanitizedSvg, sanitize_svg_bytes


MERMAID_TOOLCHAIN_ROOT = Path(__file__).resolve().parents[1] / "build" / "mermaid"
MERMAID_EXECUTABLE_RELATIVE_PATH = Path("node_modules/.bin/mmdc")
MERMAID_CONFIG_FILENAME = "mermaid-config.json"
MERMAID_BACKGROUND = "white"
MERMAID_VIEWPORT_WIDTH = 1200
MERMAID_VIEWPORT_HEIGHT = 800
ACC_TITLE_PATTERN = re.compile(r"^\s*accTitle\s*:\s*(\S.*)\s*$", re.MULTILINE)
ACC_DESCR_INLINE_PATTERN = re.compile(r"^\s*accDescr\s*:\s*(\S.*)\s*$", re.MULTILINE)
ACC_DESCR_BLOCK_PATTERN = re.compile(r"^\s*accDescr\s*\{\s*(.*?)\s*\}", re.MULTILINE | re.DOTALL)
VISIBLE_SVG_ELEMENTS = frozenset(
    {"circle", "ellipse", "image", "line", "path", "polygon", "polyline", "rect", "text", "use"}
)


class MermaidBuildContext(Protocol):
    source: ArtifactLocationAdapter
    published: ArtifactLocationAdapter
    write: bool


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class MermaidMediaPlan:
    source_identity: str
    published_identity: str


def plan_mermaid_media(source_inventory: Iterable[ArtifactStat]) -> tuple[MermaidMediaPlan, ...]:
    """Map canonical Mermaid sources to deterministic same-basename SVG identities."""

    plans = [
        MermaidMediaPlan(
            source_identity=normalize_artifact_identity(item.identity),
            published_identity=normalize_artifact_identity(Path(item.identity).with_suffix(".svg")),
        )
        for item in source_inventory
        if Path(item.identity).suffix == ".mmd"
    ]
    plans.sort(key=lambda item: item.source_identity)
    published_identities = [item.published_identity for item in plans]
    if len(set(published_identities)) != len(published_identities):
        raise ValueError("Mermaid sources resolve to duplicate published SVG identities")
    return tuple(plans)


def _local_name(value: str) -> str:
    return etree.QName(value).localname.lower()


def _require_accessible_source(identity: str, source: str) -> None:
    title = ACC_TITLE_PATTERN.search(source)
    description = ACC_DESCR_INLINE_PATTERN.search(source) or ACC_DESCR_BLOCK_PATTERN.search(source)
    if title is None or not title.group(1).strip():
        raise ValueError(f"Mermaid source {identity!r} requires a non-empty accTitle")
    if description is None or not description.group(1).strip():
        raise ValueError(f"Mermaid source {identity!r} requires a non-empty accDescr")


def _validate_sanitized_svg(identity: str, sanitized: SanitizedSvg) -> None:
    try:
        root = etree.fromstring(sanitized.bytes)
    except etree.XMLSyntaxError as exc:  # pragma: no cover - shared sanitizer already parses this
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} is not well-formed") from exc

    view_box = str(root.get("viewBox") or "").split()
    try:
        view_box_values = [float(value) for value in view_box]
    except ValueError as exc:
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} has an invalid viewBox") from exc
    if len(view_box_values) != 4 or view_box_values[2] <= 0 or view_box_values[3] <= 0:
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} requires a responsive viewBox")

    descriptions = [
        " ".join("".join(element.itertext()).split())
        for element in root.iter()
        if isinstance(element.tag, str) and _local_name(element.tag) == "desc"
    ]
    if not sanitized.title or not any(descriptions):
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} lost required accessibility metadata")
    if not any(
        isinstance(element.tag, str) and _local_name(element.tag) in VISIBLE_SVG_ELEMENTS
        for element in root.iter()
    ):
        raise RuntimeError(f"Sanitized Mermaid SVG for {identity!r} contains no visible diagram content")


def _toolchain_paths(toolchain_root: Path) -> tuple[Path, Path]:
    executable = toolchain_root / MERMAID_EXECUTABLE_RELATIVE_PATH
    config = toolchain_root / MERMAID_CONFIG_FILENAME
    if not executable.is_file():
        raise RuntimeError(
            "Mermaid CLI is not installed; run npm install in docs-viewer/build/mermaid"
        )
    if not config.is_file():
        raise RuntimeError(f"Mermaid render config is missing: {config}")
    return executable, config


def _render_command(executable: Path, config: Path, source: Path, output: Path) -> list[str]:
    return [
        str(executable),
        "--input",
        str(source),
        "--output",
        str(output),
        "--configFile",
        str(config),
        "--backgroundColor",
        MERMAID_BACKGROUND,
        "--width",
        str(MERMAID_VIEWPORT_WIDTH),
        "--height",
        str(MERMAID_VIEWPORT_HEIGHT),
    ]


def _render_one(
    plan: MermaidMediaPlan,
    *,
    source: ArtifactLocationAdapter,
    executable: Path,
    config: Path,
    output_path: Path,
    run_command: CommandRunner,
) -> bytes:
    with source.stage_local(plan.source_identity) as source_path:
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Mermaid source {plan.source_identity!r} must be UTF-8 text") from exc
        _require_accessible_source(plan.source_identity, source_text)
        try:
            completed = run_command(
                _render_command(executable, config, source_path, output_path),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise RuntimeError(
                f"Mermaid renderer could not start for {plan.source_identity!r}: {exc}"
            ) from exc
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout or "").split())
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"Mermaid renderer failed for {plan.source_identity!r}{suffix}")
    if not output_path.is_file():
        raise RuntimeError(f"Mermaid renderer produced no SVG for {plan.source_identity!r}")

    try:
        sanitized = sanitize_svg_bytes(output_path.read_bytes())
    except ValueError as exc:
        raise RuntimeError(f"Mermaid renderer produced invalid SVG for {plan.source_identity!r}: {exc}") from exc
    _validate_sanitized_svg(plan.source_identity, sanitized)
    return sanitized.bytes


def _publish_outputs(
    rendered: Sequence[tuple[MermaidMediaPlan, bytes]],
    *,
    published: ArtifactLocationAdapter,
) -> None:
    for plan, data in rendered:
        try:
            published.replace(plan.published_identity, data, content_type="image/svg+xml")
            verified = published.verify_bytes(plan.published_identity, data)
        except Exception as exc:
            raise RuntimeError(
                f"Mermaid SVG publication failed for {plan.published_identity!r}"
            ) from exc
        if not verified:
            raise RuntimeError(
                f"Mermaid SVG publication verification failed for {plan.published_identity!r}"
            )


def produce_mermaid_svg(
    context: MermaidBuildContext,
    *,
    toolchain_root: Path = MERMAID_TOOLCHAIN_ROOT,
    run_command: CommandRunner = subprocess.run,
) -> tuple[str, ...]:
    """Render, sanitize, publish, and verify configured Mermaid source media."""

    plans = plan_mermaid_media(context.source.list())
    output_identities = tuple(plan.published_identity for plan in plans)
    if not context.write or not plans:
        return output_identities

    executable, config = _toolchain_paths(toolchain_root)
    with tempfile.TemporaryDirectory(prefix="docs-mermaid-render-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        rendered = [
            (
                plan,
                _render_one(
                    plan,
                    source=context.source,
                    executable=executable,
                    config=config,
                    output_path=temporary_root / f"{index:04d}.svg",
                    run_command=run_command,
                ),
            )
            for index, plan in enumerate(plans)
        ]
        _publish_outputs(rendered, published=context.published)
    return output_identities


__all__ = [
    "MERMAID_BACKGROUND",
    "MERMAID_CONFIG_FILENAME",
    "MERMAID_EXECUTABLE_RELATIVE_PATH",
    "MERMAID_TOOLCHAIN_ROOT",
    "MERMAID_VIEWPORT_HEIGHT",
    "MERMAID_VIEWPORT_WIDTH",
    "MermaidMediaPlan",
    "plan_mermaid_media",
    "produce_mermaid_svg",
]
