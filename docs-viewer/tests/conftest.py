"""Shared test import path setup for Docs Viewer-owned checks."""

from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
PROJECTS_BASE_ENV = "DOTLINEFORM_PROJECTS_BASE_DIR"


_ORIGINAL_PROJECTS_BASE = os.environ.get(PROJECTS_BASE_ENV)
_COLLECTION_PROJECTS_WORKSPACE = tempfile.TemporaryDirectory(
    prefix="docs-viewer-pytest-projects-"
)
_COLLECTION_PROJECTS_BASE = Path(_COLLECTION_PROJECTS_WORKSPACE.name)
(_COLLECTION_PROJECTS_BASE / "data-sharing").mkdir()
(_COLLECTION_PROJECTS_BASE / "docs-viewer").mkdir()
os.environ[PROJECTS_BASE_ENV] = str(_COLLECTION_PROJECTS_BASE)


for path in (FIXTURES_DIR, REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402


ensure_studio_python_paths(__file__)


def pytest_unconfigure() -> None:
    """Restore the invoking environment after collection-safe test isolation."""

    if _ORIGINAL_PROJECTS_BASE is None:
        os.environ.pop(PROJECTS_BASE_ENV, None)
    else:
        os.environ[PROJECTS_BASE_ENV] = _ORIGINAL_PROJECTS_BASE
    _COLLECTION_PROJECTS_WORKSPACE.cleanup()


@pytest.fixture(autouse=True)
def external_data_sharing_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    projects_base = tmp_path / "projects-base"
    workspace = projects_base / "data-sharing"
    workspace.mkdir(parents=True)
    (projects_base / "docs-viewer").mkdir()
    monkeypatch.setenv("DOTLINEFORM_PROJECTS_BASE_DIR", str(projects_base))
    from docs_scope_config import DOCS_SCOPE_CONFIGS, DOCUMENT_SOURCE_ROOTS

    original_configs = dict(DOCS_SCOPE_CONFIGS)
    original_roots = dict(DOCUMENT_SOURCE_ROOTS)
    try:
        yield workspace
    finally:
        DOCS_SCOPE_CONFIGS.clear()
        DOCS_SCOPE_CONFIGS.update(original_configs)
        DOCUMENT_SOURCE_ROOTS.clear()
        DOCUMENT_SOURCE_ROOTS.update(original_roots)
