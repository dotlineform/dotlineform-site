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
from catalogue_work_media_sources import (  # noqa: E402
    WorkMediaSourceRoot,
    resolve_work_media_path,
    resolve_work_media_source_id,
    resolve_work_media_source_root,
)
from docs_local_links import encode_relative_target  # noqa: E402
from pipeline_config import load_pipeline_config  # noqa: E402
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
    media_source_id: str
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
        media_source_id = resolve_work_media_source_id(PIPELINE_CONFIG, record.get("media_source_id"))
        sources.append(
            WorkSource(
                work_id=str(work_id),
                media_source_id=media_source_id,
                directory=PurePosixPath(*directory_parts).as_posix(),
                filename=filename_parts[0],
            )
        )
    return sources


def collect_detail_directories(records: Any) -> set[tuple[str, str]]:
    directories: set[tuple[str, str]] = set()
    for section in records.work_detail_sections.values():
        work_id = normalize_text(section.get("work_id"))
        details_subfolder = normalize_text(section.get("details_subfolder"))
        work = records.works.get(work_id)
        folder = normalize_text(work.get("project_folder")) if isinstance(work, dict) else ""
        if not folder or not details_subfolder:
            continue
        parts = [*_canonical_parts(folder, f"work {work_id} project_folder", single=True)]
        parts.extend(_canonical_parts(details_subfolder, f"work {work_id} details_subfolder"))
        media_source_id = resolve_work_media_source_id(
            PIPELINE_CONFIG,
            work.get("media_source_id") if isinstance(work, dict) else None,
        )
        directories.add((media_source_id, PurePosixPath(*parts).as_posix()))
    return directories


def _is_detail_directory(source_id: str, directory: str, detail_directories: set[tuple[str, str]]) -> bool:
    return any(
        source_id == detail_source_id
        and (directory == detail_directory or directory.startswith(f"{detail_directory}/"))
        for detail_source_id, detail_directory in detail_directories
    )


def _source_roots(paths: UncatalogedFilesPaths, sources: list[WorkSource]) -> dict[str, WorkMediaSourceRoot]:
    roots: dict[str, WorkMediaSourceRoot] = {}
    environ = {"DOTLINEFORM_PROJECTS_BASE_DIR": str(paths.projects_base_dir)}
    for source_id in sorted({source.media_source_id for source in sources}):
        roots[source_id] = resolve_work_media_source_root(
            PIPELINE_CONFIG,
            source_id,
            environ=environ,
            require_exists=True,
        )
    return roots


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


def _catalogued_file_identities(
    sources: list[WorkSource],
    source_roots: Mapping[str, WorkMediaSourceRoot],
) -> dict[str, set[tuple[int, int]]]:
    identities: dict[str, set[tuple[int, int]]] = {}
    for source in sources:
        source_root = source_roots[source.media_source_id]
        candidate = resolve_work_media_path(source_root, source.directory, source.filename)
        identity = _file_identity(candidate)
        if identity is None:
            continue
        identities.setdefault(source.media_source_id, set()).add(identity)
    return identities


def _uncataloged_rows(
    sources: list[WorkSource],
    detail_directories: set[tuple[str, str]],
    source_roots: Mapping[str, WorkMediaSourceRoot],
) -> list[dict[str, str]]:
    catalogued_identities = _catalogued_file_identities(sources, source_roots)
    represented_directories = sorted(
        {(source.media_source_id, source.directory) for source in sources},
        key=lambda value: (value[0].casefold(), value[0], value[1].casefold(), value[1]),
    )
    rows: list[dict[str, str]] = []
    for source_id, directory in represented_directories:
        if _is_detail_directory(source_id, directory, detail_directories):
            continue
        source_root = source_roots[source_id]
        try:
            resolved_directory = resolve_work_media_path(source_root, directory, require_exists=True)
        except FileNotFoundError:
            continue
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"represented directory could not be inspected: {directory}") from exc
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
            resolve_work_media_path(source_root, directory, child.name, require_exists=True)
            if identity in catalogued_identities.get(source_id, set()):
                continue
            decoded_target = PurePosixPath(source_root.root_subdir.as_posix(), directory, child.name).as_posix()
            rows.append(
                {
                    "folder": PurePosixPath(source_root.root_subdir.as_posix(), directory).as_posix(),
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
        sources = collect_work_sources(records)
        source_roots = _source_roots(self.paths, sources)
        rows = _uncataloged_rows(
            sources,
            collect_detail_directories(records),
            source_roots,
        )
        return {
            "report": {
                "schema_version": REPORT_SCHEMA_VERSION,
                "rows": rows,
            }
        }
