#!/usr/bin/env python3
"""Produce verified public Mermaid theme pairs into a prepared projection location."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping

from docs_artifact_locations import ArtifactLocationAdapter, normalize_artifact_identity
from docs_mermaid_renderer import (
    MERMAID_TOOLCHAIN_ROOT,
    CommandRunner,
    RenderedMermaidSvg,
    mermaid_toolchain_paths,
    render_mermaid_path,
)
from docs_public_mermaid_projection import (
    PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION,
    PUBLIC_MERMAID_PLAN_SCHEMA_VERSION,
    PUBLIC_MERMAID_THEMES,
    public_mermaid_projection_id,
    public_mermaid_variant_identity,
)


PUBLIC_MERMAID_BUILD_SCHEMA_VERSION = "docs_public_mermaid_projection_build_v1"
PUBLIC_MERMAID_MANIFEST_IDENTITY = "manifest.json"
DOCS_VIEWER_THEME_CSS_REL_PATH = Path("site/docs-viewer/static/css/docs-viewer-theme.css")
PUBLIC_MERMAID_FONT_FAMILY = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
)
THEME_BLOCK_PATTERN = re.compile(
    r"""html\[data-theme=["'](?P<theme>light|dark)["']\]\s*\{(?P<body>.*?)\}""",
    re.DOTALL,
)
THEME_VARIABLE_PATTERN = re.compile(
    r"--docs-viewer-theme-(?P<name>[a-z0-9-]+)\s*:\s*(?P<value>[^;]+);"
)
REQUIRED_THEME_ROLES = frozenset(
    {
        "canvas",
        "surface",
        "surface-subtle",
        "text",
        "text-muted",
        "border-strong",
        "selection-surface",
        "selection-text",
    }
)


def load_public_mermaid_theme_seeds(theme_css_path: Path) -> dict[str, dict[str, str]]:
    """Read the shared Docs Viewer palette owner into Mermaid semantic seeds."""

    css = theme_css_path.read_text(encoding="utf-8")
    roles_by_theme: dict[str, dict[str, str]] = {}
    for match in THEME_BLOCK_PATTERN.finditer(css):
        theme = match.group("theme")
        if theme in roles_by_theme:
            raise ValueError(f"Docs Viewer theme CSS defines {theme!r} more than once")
        roles = {
            variable.group("name"): variable.group("value").strip()
            for variable in THEME_VARIABLE_PATTERN.finditer(match.group("body"))
        }
        missing = sorted(REQUIRED_THEME_ROLES - set(roles))
        if missing:
            raise ValueError(
                f"Docs Viewer {theme} theme is missing Mermaid roles: {', '.join(missing)}"
            )
        roles_by_theme[theme] = roles
    missing_themes = sorted(set(PUBLIC_MERMAID_THEMES) - set(roles_by_theme))
    if missing_themes:
        raise ValueError(
            f"Docs Viewer theme CSS is missing public Mermaid themes: {', '.join(missing_themes)}"
        )
    return {theme: roles_by_theme[theme] for theme in PUBLIC_MERMAID_THEMES}


def public_mermaid_theme_variables(theme: str, roles: Mapping[str, str]) -> dict[str, Any]:
    """Mirror the managed inline Mermaid semantic mapping with one fixed font."""

    return {
        "background": roles["surface"],
        "primaryColor": roles["surface-subtle"],
        "mainBkg": roles["surface-subtle"],
        "primaryTextColor": roles["text"],
        "textColor": roles["text"],
        "nodeTextColor": roles["text"],
        "titleColor": roles["text"],
        "actorTextColor": roles["text"],
        "primaryBorderColor": roles["border-strong"],
        "nodeBorder": roles["border-strong"],
        "actorBorder": roles["border-strong"],
        "noteBorderColor": roles["border-strong"],
        "lineColor": roles["text-muted"],
        "arrowheadColor": roles["text-muted"],
        "secondaryColor": roles["selection-surface"],
        "activationBkgColor": roles["selection-surface"],
        "noteBkgColor": roles["selection-surface"],
        "secondaryTextColor": roles["selection-text"],
        "noteTextColor": roles["selection-text"],
        "tertiaryColor": roles["canvas"],
        "clusterBkg": roles["canvas"],
        "fontFamily": PUBLIC_MERMAID_FONT_FAMILY,
        "darkMode": theme == "dark",
    }


def public_mermaid_render_config(theme: str, roles: Mapping[str, str]) -> dict[str, Any]:
    return {
        "startOnLoad": False,
        "suppressErrorRendering": True,
        "theme": "base",
        "themeVariables": public_mermaid_theme_variables(theme, roles),
        "securityLevel": "strict",
        "htmlLabels": False,
        "flowchart": {
            "htmlLabels": False,
        },
    }


def _validate_matching_geometry(
    projection_id: str,
    rendered_by_theme: Mapping[str, RenderedMermaidSvg],
) -> None:
    light = rendered_by_theme["light"].view_box
    dark = rendered_by_theme["dark"].view_box
    light_ratio = light[2] / light[3]
    dark_ratio = dark[2] / dark[3]
    if not math.isclose(light_ratio, dark_ratio, rel_tol=1e-9, abs_tol=1e-9):
        raise RuntimeError(
            f"Public Mermaid variants for {projection_id!r} have incompatible responsive geometry"
        )


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _validate_plan_ownership(
    diagrams: list[Any],
    manifest_records: list[Any],
    removals: list[Any],
) -> None:
    manifest_by_id: dict[str, Mapping[str, Any]] = {}
    for raw_record in manifest_records:
        if not isinstance(raw_record, Mapping):
            raise ValueError("public Mermaid projection next manifest diagram must be an object")
        projection_id = str(raw_record.get("projection_id") or "")
        if not projection_id or projection_id in manifest_by_id:
            raise ValueError("public Mermaid projection next manifest has invalid or duplicate diagrams")
        manifest_by_id[projection_id] = raw_record

    diagram_ids: set[str] = set()
    for item in diagrams:
        if not isinstance(item, Mapping) or item.get("action") not in {
            "create",
            "replace",
            "unchanged",
        }:
            raise ValueError("public Mermaid projection plan diagram has an invalid action")
        projection = item.get("projection")
        if not isinstance(projection, Mapping):
            raise ValueError("public Mermaid projection plan diagram requires a projection record")
        doc_id = str(projection.get("doc_id") or "")
        fence_index = projection.get("fence_index")
        projection_id = str(projection.get("projection_id") or "")
        if projection_id != public_mermaid_projection_id(doc_id, fence_index):
            raise ValueError("public Mermaid projection plan diagram has an invalid projection identity")
        if projection_id in diagram_ids:
            raise ValueError("public Mermaid projection plan has duplicate diagram identities")
        diagram_ids.add(projection_id)
        variants = projection.get("variants")
        if not isinstance(variants, Mapping) or set(variants) != set(PUBLIC_MERMAID_THEMES):
            raise ValueError("public Mermaid projection plan requires explicit light and dark variants")
        for theme in PUBLIC_MERMAID_THEMES:
            variant = variants[theme]
            if not isinstance(variant, Mapping):
                raise ValueError("public Mermaid projection plan variant must be an object")
            if variant.get("artifact_identity") != public_mermaid_variant_identity(
                projection_id,
                theme,
            ):
                raise ValueError("public Mermaid projection plan variant is outside projection ownership")
        manifest_record = manifest_by_id.get(projection_id)
        if manifest_record is None or manifest_record.get("variants") != variants:
            raise ValueError("public Mermaid projection plan and next manifest variants disagree")

    if diagram_ids != set(manifest_by_id):
        raise ValueError("public Mermaid projection plan and next manifest diagrams disagree")

    for removal in removals:
        if not isinstance(removal, Mapping):
            raise ValueError("public Mermaid projection removal must be an object")
        projection_id = str(removal.get("projection_id") or "")
        doc_id = str(removal.get("doc_id") or "")
        fence_index = removal.get("fence_index")
        if projection_id != public_mermaid_projection_id(doc_id, fence_index):
            raise ValueError("public Mermaid projection removal has an invalid projection identity")
        expected = [
            public_mermaid_variant_identity(projection_id, theme)
            for theme in PUBLIC_MERMAID_THEMES
        ]
        if removal.get("variant_identities") != expected:
            raise ValueError("public Mermaid projection removal is outside manifest ownership")


def _snapshot(
    adapter: ArtifactLocationAdapter,
    identities: list[str],
) -> dict[str, bytes | None]:
    return {
        identity: adapter.read(identity) if adapter.stat(identity) is not None else None
        for identity in identities
    }


def _restore_snapshot(
    adapter: ArtifactLocationAdapter,
    snapshots: Mapping[str, bytes | None],
) -> None:
    failures: list[str] = []
    for identity, previous in reversed(list(snapshots.items())):
        try:
            current = adapter.stat(identity)
            if previous is None:
                if current is not None:
                    adapter.delete(identity)
                if adapter.stat(identity) is not None:
                    raise RuntimeError("artifact remained after rollback delete")
            else:
                adapter.replace(identity, previous)
                if not adapter.verify_bytes(identity, previous):
                    raise RuntimeError("artifact rollback byte verification failed")
        except Exception as exc:  # pragma: no cover - catastrophic provider failure
            failures.append(f"{identity}: {exc}")
    if failures:
        raise RuntimeError("public Mermaid projection rollback failed: " + "; ".join(failures))


def _apply_projection_transaction(
    prepared: ArtifactLocationAdapter,
    *,
    writes: list[tuple[str, bytes]],
    removals: list[str],
    manifest_bytes: bytes,
    manifest_owned_identities: set[str],
) -> None:
    write_identities = [normalize_artifact_identity(identity) for identity, _data in writes]
    removal_identities = [normalize_artifact_identity(identity) for identity in removals]
    if len(set(write_identities)) != len(write_identities):
        raise ValueError("public Mermaid projection transaction has duplicate writes")
    if set(write_identities) & set(removal_identities):
        raise ValueError("public Mermaid projection transaction cannot write and remove one identity")
    for identity in write_identities:
        if identity not in manifest_owned_identities and prepared.stat(identity) is not None:
            raise RuntimeError(
                f"public Mermaid projection refuses unowned existing artifact: {identity}"
            )

    affected = list(
        dict.fromkeys(
            [
                *write_identities,
                *removal_identities,
                PUBLIC_MERMAID_MANIFEST_IDENTITY,
            ]
        )
    )
    snapshots = _snapshot(prepared, affected)
    try:
        for identity, data in writes:
            if identity in manifest_owned_identities:
                prepared.replace(identity, data, content_type="image/svg+xml")
            else:
                prepared.write(identity, data, content_type="image/svg+xml")
            if not prepared.verify_bytes(identity, data):
                raise RuntimeError(
                    f"public Mermaid projection byte verification failed: {identity}"
                )
        for identity in removal_identities:
            if prepared.stat(identity) is not None:
                prepared.delete(identity)
            if prepared.stat(identity) is not None:
                raise RuntimeError(
                    f"public Mermaid projection removal verification failed: {identity}"
                )
        prepared.replace(
            PUBLIC_MERMAID_MANIFEST_IDENTITY,
            manifest_bytes,
            content_type="application/json",
        )
        if not prepared.verify_bytes(PUBLIC_MERMAID_MANIFEST_IDENTITY, manifest_bytes):
            raise RuntimeError("public Mermaid projection manifest byte verification failed")
    except Exception as exc:
        try:
            _restore_snapshot(prepared, snapshots)
        except Exception as rollback_exc:
            raise RuntimeError(
                f"public Mermaid projection transaction failed ({exc}); {rollback_exc}"
            ) from exc
        raise RuntimeError("public Mermaid projection transaction failed and was rolled back") from exc


def produce_public_mermaid_projection(
    plan: Mapping[str, Any],
    *,
    prepared: ArtifactLocationAdapter,
    write: bool,
    theme_css_path: Path,
    toolchain_root: Path = MERMAID_TOOLCHAIN_ROOT,
    run_command: CommandRunner = subprocess.run,
) -> dict[str, Any]:
    """Render complete theme pairs, then atomically replace prepared outputs and manifest."""

    if plan.get("schema_version") != PUBLIC_MERMAID_PLAN_SCHEMA_VERSION:
        raise ValueError(
            f"public Mermaid projection plan schema_version must be {PUBLIC_MERMAID_PLAN_SCHEMA_VERSION}"
        )
    scope = str(plan.get("scope") or "").strip()
    if not scope:
        raise ValueError("public Mermaid projection plan scope is required")
    if not write:
        return {
            "schema_version": PUBLIC_MERMAID_BUILD_SCHEMA_VERSION,
            "scope": scope,
            "write": False,
            "summary": {
                "planned_diagram_count": len(plan.get("diagrams") or []),
                "planned_variant_count": len(plan.get("diagrams") or []) * len(PUBLIC_MERMAID_THEMES),
                "failure_count": len(plan.get("failures") or []),
            },
            "failures": list(plan.get("failures") or []),
        }

    diagrams = plan.get("diagrams")
    manifest = plan.get("manifest")
    if not isinstance(diagrams, list) or not isinstance(manifest, Mapping):
        raise ValueError("public Mermaid projection plan requires diagrams and manifest")
    manifest_records = manifest.get("diagrams")
    if (
        manifest.get("schema_version") != PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION
        or manifest.get("scope") != scope
        or not isinstance(manifest_records, list)
    ):
        raise ValueError("public Mermaid projection plan carries an invalid next manifest")
    removals = plan.get("removals")
    if not isinstance(removals, list):
        raise ValueError("public Mermaid projection plan removals must be a list")
    _validate_plan_ownership(diagrams, manifest_records, removals)
    manifest_by_id = {
        str(record["projection_id"]): record
        for record in manifest_records
    }

    failures = [
        {**failure, "stage": "inventory"}
        for failure in plan.get("failures") or []
    ]
    successful_ids: set[str] = set()
    writes: list[tuple[str, bytes]] = []
    render_failed_owned_ids: list[str] = []
    manifest_owned_identities: set[str] = {
        identity
        for item in diagrams
        if item.get("action") in {"replace", "unchanged"}
        for identity in (
            item.get("projection", {}).get("variants", {}).get(theme, {}).get("artifact_identity", "")
            for theme in PUBLIC_MERMAID_THEMES
        )
        if identity
    }
    planned_removals = [
        identity
        for removal in removals
        for identity in removal.get("variant_identities") or []
    ]
    manifest_owned_identities.update(planned_removals)

    if diagrams:
        executable, _base_config = mermaid_toolchain_paths(toolchain_root)
        theme_seeds = load_public_mermaid_theme_seeds(theme_css_path)
        with tempfile.TemporaryDirectory(prefix="docs-public-mermaid-") as temporary_directory:
            temporary_root = Path(temporary_directory)
            config_paths: dict[str, Path] = {}
            for theme in PUBLIC_MERMAID_THEMES:
                config_path = temporary_root / f"{theme}-config.json"
                config_path.write_text(
                    json.dumps(
                        public_mermaid_render_config(theme, theme_seeds[theme]),
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                config_paths[theme] = config_path

            for diagram_index, item in enumerate(diagrams):
                projection = item.get("projection") or {}
                source = item.get("source") or {}
                projection_id = str(projection.get("projection_id") or "")
                diagram_root = temporary_root / f"{diagram_index:04d}"
                diagram_root.mkdir()
                source_path = diagram_root / f"{projection_id}.mmd"
                source_path.write_text(str(source.get("mermaid") or ""), encoding="utf-8")
                rendered_by_theme: dict[str, RenderedMermaidSvg] = {}
                try:
                    for theme in PUBLIC_MERMAID_THEMES:
                        roles = theme_seeds[theme]
                        rendered_by_theme[theme] = render_mermaid_path(
                            f"{projection_id}/{theme}",
                            source_path,
                            executable=executable,
                            config=config_paths[theme],
                            background=roles["surface"],
                            output_path=diagram_root / f"{theme}.svg",
                            run_command=run_command,
                            require_matching_accessibility=True,
                        )
                    _validate_matching_geometry(projection_id, rendered_by_theme)
                except Exception as exc:
                    failures.append(
                        {
                            "doc_id": projection.get("doc_id", ""),
                            "fence_index": projection.get("fence_index", 0),
                            "projection_id": projection_id,
                            "stage": "render",
                            "message": str(exc),
                        }
                    )
                    if item.get("action") in {"replace", "unchanged"}:
                        render_failed_owned_ids.extend(
                            projection.get("variants", {}).get(theme, {}).get("artifact_identity", "")
                            for theme in PUBLIC_MERMAID_THEMES
                        )
                    continue
                successful_ids.add(projection_id)
                for theme in PUBLIC_MERMAID_THEMES:
                    identity = projection["variants"][theme]["artifact_identity"]
                    writes.append((identity, rendered_by_theme[theme].bytes))

    successful_manifest_records = [
        dict(record)
        for projection_id, record in manifest_by_id.items()
        if projection_id in successful_ids
    ]
    successful_manifest_records.sort(key=lambda record: record["projection_id"])
    produced_manifest = {
        "schema_version": PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION,
        "scope": scope,
        "diagrams": successful_manifest_records,
    }
    removal_identities = list(
        dict.fromkeys(
            identity
            for identity in [*planned_removals, *render_failed_owned_ids]
            if identity
        )
    )
    _apply_projection_transaction(
        prepared,
        writes=writes,
        removals=removal_identities,
        manifest_bytes=_json_bytes(produced_manifest),
        manifest_owned_identities=manifest_owned_identities,
    )
    return {
        "schema_version": PUBLIC_MERMAID_BUILD_SCHEMA_VERSION,
        "scope": scope,
        "write": True,
        "summary": {
            "successful_diagram_count": len(successful_ids),
            "published_variant_count": len(writes),
            "failure_count": len(failures),
            "removed_variant_count": len(removal_identities),
        },
        "successful_projection_ids": sorted(successful_ids),
        "published_identities": [identity for identity, _data in writes],
        "removed_identities": removal_identities,
        "failures": failures,
        "manifest": produced_manifest,
    }


__all__ = [
    "DOCS_VIEWER_THEME_CSS_REL_PATH",
    "PUBLIC_MERMAID_BUILD_SCHEMA_VERSION",
    "PUBLIC_MERMAID_FONT_FAMILY",
    "PUBLIC_MERMAID_MANIFEST_IDENTITY",
    "load_public_mermaid_theme_seeds",
    "produce_public_mermaid_projection",
    "public_mermaid_render_config",
    "public_mermaid_theme_variables",
]
