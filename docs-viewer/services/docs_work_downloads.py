"""Read refreshed Work download references and inventory their shared local files."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path  # noqa: E402
from docs_artifact_locations import ArtifactLocation  # noqa: E402
from docs_local_files import open_in_finder  # noqa: E402
from docs_workspace_config import safe_relative_path  # noqa: E402
from catalogue.catalogue_report_inputs import read_work_resources  # noqa: E402

STORAGE_PLACEHOLDERS = frozenset({".DS_Store", ".gitkeep"})


def _filename(value: Any) -> str:
    relative = safe_relative_path(value, field="Work download filename")
    if len(relative.parts) != 1 or value != relative.name or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise ValueError("Work download filename must be an exact direct filename")
    return value


def _saved_files(location: ArtifactLocation) -> list[str]:
    """Inspect direct entries in a configuration-confined directory once.

    Directory-entry metadata suffices: reject symlinks, keep exact regular-file
    basenames and never read file contents, sizes or nested directories.
    """
    filenames = []
    try:
        with os.scandir(location.path) as entries:
            for entry in entries:
                if entry.name in STORAGE_PLACEHOLDERS:
                    continue
                if entry.is_symlink():
                    raise ValueError("Work download storage must not contain symlinks")
                if entry.is_file(follow_symlinks=False):
                    filenames.append(_filename(entry.name))
    except (FileNotFoundError, NotADirectoryError) as error:
        raise RuntimeError("Work download storage is unavailable") from error
    except OSError as error:
        raise RuntimeError("Work download storage could not be read") from error
    return filenames


def work_downloads_report(repo_root: Path) -> dict[str, Any]:
    """Supply saved references and current filenames for browser-owned matching.

    Resolve configuration once, read one saved resource input and list the direct
    file family once. No paths, link facts or final report rows enter the handoff.
    """
    workspace = catalogue_workspace_config(repo_root)
    works = read_work_resources(workspace.catalogue.working)
    files = _saved_files(workspace.assets.work_files)
    return {"ok": True, "report": {
        "works": [
            {"work_id": work_id, "title": work["title"], "download_filenames": work["download_filenames"]}
            for work_id, work in works.items() if work["download_filenames"]
        ],
        "files": files,
    }}


def open_work_download(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Reveal an exact saved file, including an unassigned one, within its owner."""
    if set(body) != {"filename"}:
        raise ValueError("Work download opening requires only filename")
    filename = _filename(body["filename"])
    location = catalogue_workspace_config(repo_root).assets.work_files
    path = output_path(location, filename)
    try:
        present = path.is_file()
    except OSError as error:
        raise RuntimeError("Work download file could not be read") from error
    if not present:
        raise FileNotFoundError("Work download file is unavailable")
    try:
        open_in_finder(
            repo_root, path, reveal=True, dry_run=dry_run,
            failure_message="Work download could not be revealed in Finder",
        )
    except OSError as error:
        raise RuntimeError("Work download could not be revealed in Finder") from error
    return {"ok": True, "filename": filename, "dry_run": dry_run}
