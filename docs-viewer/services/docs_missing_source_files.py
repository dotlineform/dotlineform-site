#!/usr/bin/env python3
"""Build the local Missing Source Files report."""

from __future__ import annotations

import re
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
from pipeline_config import load_pipeline_config, work_media_source_root_subdir  # noqa: E402
from studio.shared.python.projects_directories import configured_projects_base  # noqa: E402


REPORT_SCHEMA_VERSION = "docs_missing_source_files_report_v1"
WORK_ID_PATTERN = re.compile(r"\A[0-9]{5}\Z")
PIPELINE_CONFIG = load_pipeline_config(Path(__file__))


@dataclass(frozen=True)
class MissingSourceFilesPaths:
    projects_base_dir: Path
    catalogue_source_dir: Path


@dataclass(frozen=True)
class WorkSource:
    work_id: str
    work_title: str
    media_source_id: str
    source_relative_path: str
    expected_source_path: str


def default_missing_source_files_paths(
    repo_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> MissingSourceFilesPaths:
    return MissingSourceFilesPaths(
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
    for source_id, record in sorted(records.works.items()):
        work_id = str(source_id)
        folder = normalize_text(record.get("project_folder"))
        subfolder = normalize_text(record.get("project_subfolder"))
        filename = normalize_text(record.get("project_filename"))
        if not folder or not filename:
            continue
        if not WORK_ID_PATTERN.fullmatch(work_id):
            raise ValueError("Canonical Work contains an invalid work_id")
        work_title = normalize_text(record.get("title"))
        if not work_title:
            raise ValueError(f"Canonical Work {work_id} has no title")
        path_parts = list(_canonical_parts(folder, f"work {work_id} project_folder", single=True))
        if subfolder:
            path_parts.extend(_canonical_parts(subfolder, f"work {work_id} project_subfolder"))
        path_parts.extend(_canonical_parts(filename, f"work {work_id} project_filename", single=True))
        media_source_id = resolve_work_media_source_id(PIPELINE_CONFIG, record.get("media_source_id"))
        source_subdir = work_media_source_root_subdir(PIPELINE_CONFIG, media_source_id)
        source_relative_path = PurePosixPath(*path_parts).as_posix()
        sources.append(
            WorkSource(
                work_id=work_id,
                work_title=work_title,
                media_source_id=media_source_id,
                source_relative_path=source_relative_path,
                expected_source_path=PurePosixPath(source_subdir.as_posix(), source_relative_path).as_posix(),
            )
        )
    return sources


def _source_roots(paths: MissingSourceFilesPaths, sources: list[WorkSource]) -> dict[str, WorkMediaSourceRoot]:
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


def _is_regular_source_file(source: WorkSource, source_root: WorkMediaSourceRoot) -> bool:
    try:
        resolved = resolve_work_media_path(
            source_root,
            source.source_relative_path,
            require_exists=False,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError(f"work {source.work_id} source path is invalid: {exc}") from exc
    try:
        record = resolved.stat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ValueError(f"work {source.work_id} source path could not be inspected") from exc
    return stat.S_ISREG(record.st_mode)


def missing_source_rows(
    sources: list[WorkSource],
    source_roots: Mapping[str, WorkMediaSourceRoot],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in sources:
        if _is_regular_source_file(source, source_roots[source.media_source_id]):
            continue
        rows.append(
            {
                "work_id": source.work_id,
                "work_title": source.work_title,
                "expected_source_path": source.expected_source_path,
            }
        )
    return rows


class MissingSourceFilesProducer:
    def __init__(
        self,
        *,
        repo_root: Path,
        paths: MissingSourceFilesPaths | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.paths = paths or default_missing_source_files_paths(self.repo_root, environ=environ)

    def run(self) -> dict[str, object]:
        records = records_from_json_source(self.paths.catalogue_source_dir)
        sources = collect_work_sources(records)
        rows = missing_source_rows(sources, _source_roots(self.paths, sources))
        return {
            "report": {
                "schema_version": REPORT_SCHEMA_VERSION,
                "rows": rows,
            }
        }
