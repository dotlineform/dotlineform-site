"""Inspect physical Work-source folders without directly registered Works."""

from __future__ import annotations

from collections import Counter
import os
from pathlib import Path
import stat
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from docs_local_links import encode_relative_target  # noqa: E402
from catalogue.catalogue_report_inputs import read_work_sources  # noqa: E402
from docs_work_source_inspection import SourceRoot, WorkSourceInspection, collect_work_sources  # noqa: E402
from pipeline_config import load_pipeline_config, work_media_source_config  # noqa: E402
from studio.shared.python.projects_directories import configured_projects_base  # noqa: E402

REPORT_SCHEMA = "docs_folders_without_works_report_v1"


def _registered_directories(
    works: Mapping[str, Mapping[str, Any]], source_config: Mapping[str, Any],
) -> Counter[tuple[str, str]]:
    """Group saved declarations once using the prepared source map, without I/O."""
    return Counter(
        (source.source_id, source.directory)
        for source in collect_work_sources(works, source_config)
    )


def _physical_membership(
    directories: Counter[tuple[str, str]], roots: Mapping[str, SourceRoot], inspection: WorkSourceInspection,
) -> Counter[tuple[str, int, int]]:
    """Reuse inspected parent/leaf metadata, ignoring missing/non-directory leaves.

    The leaf reader accepts any unfollowed type, so an existing regular file at
    the declared folder path still supplies no membership. Parent directories
    and declared symlinks retain the shared inspector's strict confinement.
    """
    membership: Counter[tuple[str, int, int]] = Counter()
    for (source_id, directory), count in directories.items():
        parent, _, name = directory.rpartition("/")
        root = roots[source_id]
        parent_directory = inspection.directory(root, parent) if parent else root.directory
        record = inspection.file(parent_directory, name)
        if record is not None and stat.S_ISDIR(record.st_mode):
            membership[source_id, record.st_dev, record.st_ino] += count
    return membership


def _folder_rows(
    source_id: str, source_root: SourceRoot, membership: Counter[tuple[str, int, int]], inspection: WorkSourceInspection,
) -> list[dict[str, Any]]:
    # Parents enter this mapping before descendants. Reverse traversal can then
    # sum complete branches once without reopening directories or Work files.
    direct: dict[str, int] = {}
    pending = [(source_root.directory, "")]
    while pending:
        directory, relative = pending.pop()
        try:
            with os.scandir(directory.path) as children:
                for child in children:
                    if not child.is_dir(follow_symlinks=False):
                        continue
                    child_relative = f"{relative}/{child.name}" if relative else child.name
                    record = inspection.entry(directory, child)
                    if record is None:
                        raise FileNotFoundError(child.path)
                    child_directory = inspection.directory(source_root, child_relative)
                    direct[child_relative] = membership[source_id, record.st_dev, record.st_ino]
                    pending.append((child_directory, child_relative))
        except (OSError, ValueError) as error:
            folder = f"{source_root.subdir}/{relative}" if relative else source_root.subdir
            raise ValueError(f"Work source folder could not be scanned: {folder}") from error

    totals = dict(direct)
    for relative in reversed(direct):
        parent = relative.rpartition("/")[0]
        if parent in totals:
            totals[parent] += totals[relative]
    rows = []
    for relative, count in direct.items():
        if count:
            continue
        folder = f"{source_root.subdir}/{relative}"
        rows.append({
            "folder": folder,
            "works_below": totals[relative],
            "local_target": encode_relative_target(folder),
        })
    return rows


def folders_without_works_report(repo_root: Path) -> dict[str, Any]:
    """Scan all configured roots afresh, returning zero-direct-membership folders.

    Physical folder identity handles filesystem case/Unicode equivalence.
    Membership counts refreshed primary-source declarations, including missing
    images in existing folders. Descendant counts cover scanned physical folders;
    root containers and symlinks are omitted, while hidden/empty folders remain.
    Any unreadable input fails the whole run. No file content or saved report is
    read or written; Finder receives only encoded paths relative to Projects.
    """
    source_config = work_media_source_config(load_pipeline_config(repo_root=repo_root))
    works = read_work_sources(repo_root)
    inspection = WorkSourceInspection(configured_projects_base())
    roots = inspection.source_roots(source_config["roots"], source_config["roots"])
    directories = _registered_directories(works, source_config)
    membership = _physical_membership(directories, roots, inspection)
    rows = [
        row for source_id, source_root in roots.items()
        for row in _folder_rows(source_id, source_root, membership, inspection)
    ]
    rows.sort(key=lambda row: (row["folder"].casefold(), row["folder"]))
    return {"ok": True, "report": {"schema_version": REPORT_SCHEMA, "rows": rows}}
