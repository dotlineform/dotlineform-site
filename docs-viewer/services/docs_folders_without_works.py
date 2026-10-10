"""Inspect physical Work-source folders without directly registered Works."""

from __future__ import annotations

from collections import Counter
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_source import normalize_text  # noqa: E402
from catalogue_work_media_sources import (  # noqa: E402
    WorkMediaSourceRoot,
    resolve_work_media_path,
    resolve_work_media_source_id,
    resolve_work_media_source_root,
)
from docs_local_links import encode_relative_target  # noqa: E402
from catalogue.catalogue_report_inputs import read_work_sources  # noqa: E402
from pipeline_config import load_pipeline_config, work_media_source_ids  # noqa: E402

REPORT_SCHEMA = "docs_folders_without_works_report_v1"


def _relative_parts(value: str, label: str, *, single: bool = False) -> tuple[str, ...]:
    encode_relative_target(value)
    parts = tuple(value.split("/"))
    if single and len(parts) != 1:
        raise ValueError(f"{label} must identify one direct name")
    return parts


def _registered_directories(
    works: Mapping[str, Mapping[str, Any]], config: Mapping[str, Any],
) -> Counter[tuple[str, str]]:
    directories: Counter[tuple[str, str]] = Counter()
    for work_id, work in works.items():
        folder = normalize_text(work.get("project_folder"))
        filename = normalize_text(work.get("project_filename"))
        if not folder or not filename:
            continue
        parts = list(_relative_parts(folder, f"Work {work_id} project_folder", single=True))
        subfolder = normalize_text(work.get("project_subfolder"))
        if subfolder:
            parts.extend(_relative_parts(subfolder, f"Work {work_id} project_subfolder"))
        _relative_parts(filename, f"Work {work_id} project_filename", single=True)
        source_id = resolve_work_media_source_id(config, work.get("media_source_id"))
        directories[source_id, PurePosixPath(*parts).as_posix()] += 1
    return directories


def _physical_membership(
    directories: Counter[tuple[str, str]], roots: Mapping[str, WorkMediaSourceRoot],
) -> Counter[tuple[str, int, int]]:
    membership: Counter[tuple[str, int, int]] = Counter()
    for (source_id, directory), count in directories.items():
        path = resolve_work_media_path(roots[source_id], directory)
        try:
            record = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise ValueError(f"Registered Work folder could not be inspected: {directory}") from error
        if stat.S_ISDIR(record.st_mode):
            membership[source_id, record.st_dev, record.st_ino] += count
    return membership


def _folder_rows(
    source_root: WorkMediaSourceRoot, membership: Counter[tuple[str, int, int]],
) -> list[dict[str, Any]]:
    # Parents enter this mapping before descendants. Reverse traversal can then
    # sum complete branches once without reopening directories or Work files.
    direct: dict[str, int] = {}
    pending = [(source_root.root, "")]
    while pending:
        path, relative = pending.pop()
        try:
            with os.scandir(path) as listing:
                children = sorted(listing, key=lambda entry: (entry.name.casefold(), entry.name))
            for child in children:
                if not child.is_dir(follow_symlinks=False):
                    continue
                child_relative = f"{relative}/{child.name}" if relative else child.name
                folder = (source_root.root_subdir / child_relative).as_posix()
                encode_relative_target(folder)
                record = child.stat(follow_symlinks=False)
                direct[child_relative] = membership[source_root.source_id, record.st_dev, record.st_ino]
                pending.append((Path(child.path), child_relative))
        except OSError as error:
            folder = (source_root.root_subdir / relative).as_posix()
            raise ValueError(f"Work source folder could not be scanned: {folder}") from error

    totals = dict(direct)
    for relative in reversed(direct):
        parent = PurePosixPath(relative).parent.as_posix()
        if parent in totals:
            totals[parent] += totals[relative]
    rows = []
    for relative, count in direct.items():
        if count:
            continue
        folder = (source_root.root_subdir / relative).as_posix()
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
    config = load_pipeline_config(repo_root=repo_root)
    works = read_work_sources(repo_root)
    roots = {
        source_id: resolve_work_media_source_root(config, source_id, require_exists=True)
        for source_id in work_media_source_ids(config)
    }
    directories = _registered_directories(works, config)
    membership = _physical_membership(directories, roots)
    rows = [row for source_root in roots.values() for row in _folder_rows(source_root, membership)]
    rows.sort(key=lambda row: (row["folder"].casefold(), row["folder"]))
    return {"ok": True, "report": {"schema_version": REPORT_SCHEMA, "rows": rows}}
