"""Inspect canonical Work download references and their shared local files."""

from __future__ import annotations

from pathlib import Path
import stat
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
from docs_work_resources import canonical_works  # noqa: E402

REPORT_SCHEMA = "docs_work_downloads_report_v1"
STORAGE_PLACEHOLDERS = frozenset({".DS_Store", ".gitkeep"})


def _filename(value: Any) -> str:
    relative = safe_relative_path(value, field="Work download filename")
    if len(relative.parts) != 1 or value != relative.name or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise ValueError("Work download filename must be an exact direct filename")
    return value


def _saved_files(location: ArtifactLocation) -> set[str]:
    filenames = set()
    try:
        if not location.path.is_dir():
            raise RuntimeError("Work download storage is unavailable")
        for entry in location.path.iterdir():
            if entry.name in STORAGE_PLACEHOLDERS:
                continue
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError("Work download storage must not contain symlinks")
            if stat.S_ISREG(mode):
                filename = _filename(entry.name)
                output_path(location, filename)
                filenames.add(filename)
    except OSError as error:
        raise RuntimeError("Work download storage could not be read") from error
    return filenames


def work_downloads_report(repo_root: Path) -> dict[str, Any]:
    """Scan exact canonical references and direct files once without writing.

    Each reference retains its Work; files shared by Works appear on each row.
    Unassigned files have no Work and absent referenced files have no File.
    Presentation and sorting belong to the browser; no paths enter the payload.
    """
    works = canonical_works(repo_root)
    files = _saved_files(catalogue_workspace_config(repo_root).assets.work_files)
    referenced = set()
    rows = []
    for work_id, work in works.items():
        downloads = work.get("downloads")
        if downloads is None:
            continue
        if not isinstance(downloads, list):
            raise ValueError(f"Work {work_id} downloads must be an array")
        title = work.get("title")
        if downloads and (not isinstance(title, str) or not title.strip()):
            raise ValueError(f"Work {work_id} has no title")
        for download in downloads:
            if not isinstance(download, dict):
                raise ValueError(f"Work {work_id} download is invalid")
            filename = _filename(download.get("filename"))
            referenced.add(filename)
            rows.append({
                "work": {"work_id": work_id, "title": title, "filename": filename},
                "file": filename if filename in files else None,
            })
    rows.extend({"work": None, "file": filename} for filename in sorted(files - referenced))
    return {"ok": True, "report": {"schema_version": REPORT_SCHEMA, "rows": rows}}


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
