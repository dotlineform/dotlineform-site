"""Render selected public Mermaid theme pairs through the shared SVG boundary."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping

from docs_mermaid_renderer import RenderedMermaidSvg, render_mermaid_path
from docs_public_mermaid_projection import PUBLIC_MERMAID_THEMES

DOCS_VIEWER_THEME_CSS_REL_PATH = Path("docs-viewer/static/css/docs-viewer-theme.css")
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



def render_public_mermaid_variants(diagrams: list[dict[str, Any]], *, executable: Path, theme_seeds: Mapping[str, Mapping[str, str]]) -> dict[str, bytes]:
    """Produce complete selected pairs; stop on the first renderer/output error."""
    writes = {}
    with tempfile.TemporaryDirectory(prefix="docs-public-mermaid-") as temporary:
        root = Path(temporary)
        configs = {}
        for theme in PUBLIC_MERMAID_THEMES:
            path = root / f"{theme}-config.json"
            path.write_text(json.dumps(public_mermaid_render_config(theme, theme_seeds[theme])), encoding="utf-8")
            configs[theme] = path
        for index, diagram in enumerate(diagrams):
            projection = diagram["projection"]
            identity = projection["projection_id"]
            directory = root / str(index)
            directory.mkdir()
            source = directory / f"{identity}.mmd"
            source.write_text(diagram["source"]["mermaid"], encoding="utf-8")
            rendered = {
                theme: render_mermaid_path(
                    f"{identity}/{theme}", source, executable=executable, config=configs[theme],
                    background=theme_seeds[theme]["surface"], output_path=directory / f"{theme}.svg",
                    run_command=subprocess.run, require_matching_accessibility=True,
                ) for theme in PUBLIC_MERMAID_THEMES
            }
            _validate_matching_geometry(identity, rendered)
            for theme, svg in rendered.items():
                writes[projection["variants"][theme]["artifact_identity"]] = svg.bytes
    return writes
