from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from docs_artifact_locations import ArtifactLocationAdapter, ArtifactStat, normalize_artifact_identity
from docs_mermaid_renderer import (
    MERMAID_CONFIG_FILENAME,
    MERMAID_EXECUTABLE_RELATIVE_PATH,
    MERMAID_TOOLCHAIN_ROOT,
    MERMAID_VIEWPORT_HEIGHT,
    MERMAID_VIEWPORT_WIDTH,
    CommandRunner,
    mermaid_toolchain_paths,
    render_mermaid_path,
)


MERMAID_BACKGROUND = "white"


class MermaidBuildContext(Protocol):
    source: ArtifactLocationAdapter
    published: ArtifactLocationAdapter
    write: bool
    requested_published_identities: tuple[str, ...] | None
    replace_existing: bool


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
        return render_mermaid_path(
            plan.source_identity,
            source_path,
            executable=executable,
            config=config,
            background=MERMAID_BACKGROUND,
            output_path=output_path,
            run_command=run_command,
        ).bytes


def _publish_outputs(
    rendered: Sequence[tuple[MermaidMediaPlan, bytes]],
    *,
    published: ArtifactLocationAdapter,
    replace_existing: bool,
) -> None:
    for plan, data in rendered:
        try:
            if replace_existing:
                published.replace(
                    plan.published_identity,
                    data,
                    content_type="image/svg+xml",
                )
            else:
                published.write(
                    plan.published_identity,
                    data,
                    content_type="image/svg+xml",
                )
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
    if context.requested_published_identities is not None:
        requested = {
            normalize_artifact_identity(identity)
            for identity in context.requested_published_identities
        }
        plans = tuple(plan for plan in plans if plan.published_identity in requested)
    output_identities = tuple(plan.published_identity for plan in plans)
    if not context.write or not plans:
        return output_identities

    executable, config = mermaid_toolchain_paths(toolchain_root)
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
        _publish_outputs(
            rendered,
            published=context.published,
            replace_existing=getattr(context, "replace_existing", True),
        )
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
