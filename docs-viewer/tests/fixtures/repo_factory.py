"""Data-oriented fixtures for Docs Viewer tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_doc(
    root: Path,
    filename: str,
    front_matter: dict[str, object],
    *,
    body: str = "",
    scope: str = "studio",
    format_value: Callable[[object], str] = str,
) -> None:
    lines = ["---"]
    for key, value in front_matter.items():
        lines.append(f"{key}: {format_value(value)}")
    lines.extend(["---", "", body or f"# {front_matter['title']}", ""])
    path = root / "docs-viewer/source" / scope / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
