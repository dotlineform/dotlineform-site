"""Shared fixtures for Docs Viewer service tests."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICE_DIR = REPO_ROOT / "docs-viewer" / "services"
for path in (DOCS_SERVICE_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import docs_viewer_service  # noqa: E402


STATIC_IMPORT_PATTERN = re.compile(
    r"(?:import|export)\s+(?:(?:[^'\"]+?)\s+from\s+)?[\"']([^\"']+)[\"']",
    re.DOTALL,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def static_module_imports(path: Path) -> list[str]:
    return [match.group(1) for match in STATIC_IMPORT_PATTERN.finditer(path.read_text(encoding="utf-8"))]


def public_entry_static_import_graph(repo_root: Path, entry: Path) -> set[Path]:
    visited: set[Path] = set()
    pending = [entry]
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for specifier in static_module_imports(current):
            if not specifier.startswith("."):
                continue
            target = (current.parent / specifier).resolve()
            if target.suffix:
                module_path = target
            else:
                module_path = target.with_suffix(".js")
            try:
                module_path.relative_to(repo_root)
            except ValueError:
                continue
            if module_path.exists() and module_path not in visited:
                pending.append(module_path)
    return visited
