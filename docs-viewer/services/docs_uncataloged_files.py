#!/usr/bin/env python3
"""Build the local Uncataloged Files report."""

from __future__ import annotations

import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools/config/site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_source import (  # noqa: E402
    DEFAULT_SOURCE_DIR,
    normalize_text,
    records_from_json_source,
)
from docs_local_links import encode_relative_target  # noqa: E402
from pipeline_config import load_pipeline_config, source_works_root_subdir  # noqa: E402
from studio.shared.python.projects_directories import configured_projects_base  # noqa: E402


REPORT_SCHEMA_VERSION = "docs_uncataloged_files_report_v1"
PIPELINE_CONFIG = load_pipeline_config(Path(__file__))


@dataclass(frozen=True)
class UncatalogedFilesPaths:
    projects_base_dir: Path
    catalogue_source_dir: Path


@dataclass(frozen=True)
class WorkSource:
    work_id: str
    directory: str
    filename: str


def default_uncataloged_files_paths(
    repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> UncatalogedFilesPaths:
    return UncatalogedFilesPaths(
        projects_base_dir=configured_projects_base(environ=environ),
        catalogue_source_dir=repo_root.resolve() / DEFAULT_SOURCE_DIR,
    )


def _canonical_parts(value: Any, label: str, *, single: bool = False) -> tuple[str, ...]:
    text = normalize_text(value)
    if not text or text.startswith("/") or text.endswith("/") or "\\" in text:
        raise ValueError(f"{label} must be a canonical relative POSIX path")
    parts = tuple(text.split("/"))
    if (
        any(not part or part in {".", ".."} for part in parts)
        or any(any(ord(character) < 32 or ord(character) == 127 for character in part) for part in parts)
        or (single and len(parts) != 1)
    ):
        raise ValueError(f"{label} must be a canonical relative POSIX path")
    return parts


def collect_work_sources(records: Any) -> list[WorkSource]:
    sources: list[WorkSource] = []
    for work_id, record in sorted(records.works.items()):
        folder = normalize_text(record.get("project_folder"))
        subfolder = normalize_text(record.get("project_subfolder"))
        filename = normalize_text(record.get("project_filename"))
        if not folder or not filename:
            continue
        directory_parts = list(_canonical_parts(folder, f"work {work_id} project_folder", single=True))
        if subfolder:
            directory_parts.extend(_canonical_parts(subfolder, f"work {work_id} project_subfolder"))
        filename_parts = _canonical_parts(filename, f"work {work_id} project_filename", single=True)
        sources.append(
            WorkSource(
                work_id=str(work_id),
                directory=PurePosixPath(*directory_parts).as_posix(),
                filename=filename_parts[0],
            )
        )
    return sources


def collect_detail_directories(records: Any) -> set[str]:
    directories: set[str] = set()
    for section in records.work_detail_sections.values():
        work_id = normalize_text(section.get("work_id"))
        details_subfolder = normalize_text(section.get("details_subfolder"))
        work = records.works.get(work_id)
        folder = normalize_text(work.get("project_folder")) if isinstance(work, dict) else ""
        if not folder or not details_subfolder:
            continue
        parts = [*_canonical_parts(folder, f"work {work_id} project_folder", single=True)]
        parts.extend(_canonical_parts(details_subfolder, f"work {work_id} details_subfolder"))
        directories.add(PurePosixPath(*parts).as_posix())
    return directories


def _is_detail_directory(directory: str, detail_directories: set[str]) -> bool:
    return any(
        directory == detail_directory or directory.startswith(f"{detail_directory}/")
        for detail_directory in detail_directories
    )


def _projects_root(paths: UncatalogedFilesPaths) -> tuple[Path, str]:
    try:
        base = paths.projects_base_dir.resolve(strict=True)
        source_root_name = source_works_root_subdir(PIPELINE_CONFIG)
        root = (base / source_root_name).resolve(strict=True)
        root.relative_to(base)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("Projects source root is unavailable or outside the configured base") from exc
    if not root.is_dir():
        raise ValueError("Projects source root is not a directory")
    return root, source_root_name


def _contained_resolved(path: Path, root: Path, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"{label} is unavailable or outside the Projects source root") from exc
    return resolved


def _file_identity(path: Path) -> tuple[int, int] | None:
    try:
        record = path.stat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValueError("Work source file could not be inspected") from exc
    if not stat.S_ISREG(record.st_mode):
        return None
    return record.st_dev, record.st_ino


def _catalogued_file_identities(sources: list[WorkSource], projects_root: Path) -> set[tuple[int, int]]:
    identities: set[tuple[int, int]] = set()
    for source in sources:
        candidate = projects_root.joinpath(*PurePosixPath(source.directory).parts, source.filename)
        identity = _file_identity(candidate)
        if identity is None:
            continue
        _contained_resolved(candidate, projects_root, f"work {source.work_id} source file")
        identities.add(identity)
    return identities


def _uncataloged_rows(
    sources: list[WorkSource],
    detail_directories: set[str],
    projects_root: Path,
    source_root_name: str,
) -> list[dict[str, str]]:
    catalogued_identities = _catalogued_file_identities(sources, projects_root)
    represented_directories = sorted(
        {source.directory for source in sources},
        key=lambda value: (value.casefold(), value),
    )
    rows: list[dict[str, str]] = []
    for directory in represented_directories:
        if _is_detail_directory(directory, detail_directories):
            continue
        candidate = projects_root.joinpath(*PurePosixPath(directory).parts)
        try:
            resolved_directory = candidate.resolve(strict=True)
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"represented directory could not be inspected: {directory}") from exc
        try:
            resolved_directory.relative_to(projects_root)
        except ValueError as exc:
            raise ValueError(f"represented directory is outside the Projects source root: {directory}") from exc
        if not resolved_directory.is_dir():
            continue
        try:
            children = sorted(
                resolved_directory.iterdir(),
                key=lambda path: (path.name.casefold(), path.name),
            )
        except OSError as exc:
            raise ValueError(f"represented directory could not be listed: {directory}") from exc
        for child in children:
            if child.name.startswith("."):
                continue
            identity = _file_identity(child)
            if identity is None:
                continue
            _contained_resolved(child, projects_root, f"source file {directory}/{child.name}")
            if identity in catalogued_identities:
                continue
            decoded_target = PurePosixPath(source_root_name, directory, child.name).as_posix()
            rows.append(
                {
                    "folder": directory,
                    "file_name": child.name,
                    "local_target": encode_relative_target(decoded_target),
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            row["folder"].casefold(),
            row["folder"],
            row["file_name"].casefold(),
            row["file_name"],
        ),
    )


class UncatalogedFilesProducer:
    def __init__(
        self,
        *,
        repo_root: Path,
        paths: UncatalogedFilesPaths | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.paths = paths or default_uncataloged_files_paths(self.repo_root, environ=environ)

    def run(self) -> dict[str, object]:
        records = records_from_json_source(self.paths.catalogue_source_dir)
        projects_root, source_root_name = _projects_root(self.paths)
        sources = collect_work_sources(records)
        rows = _uncataloged_rows(
            sources,
            collect_detail_directories(records),
            projects_root,
            source_root_name,
        )
        return {
            "report": {
                "schema_version": REPORT_SCHEMA_VERSION,
                "rows": rows,
            }
        }
