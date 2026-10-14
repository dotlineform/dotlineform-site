#!/usr/bin/env python3
"""Inspect represented Work folders for unregistered primary-source images."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_output_workspace  # noqa: E402
from catalogue.catalogue_report_inputs import WORK_SOURCES_PATH, read_catalogue_report_input  # noqa: E402
from catalogue.catalogue_media_files import IMAGE_EXTENSIONS  # noqa: E402
from docs_local_links import encode_relative_target  # noqa: E402
from docs_work_source_inspection import (  # noqa: E402
    InspectedDirectory, WorkSourceInspection, collect_work_sources, regular_file_identity,
)
from pipeline_config import load_pipeline_config, work_media_source_config  # noqa: E402
from studio.shared.python.projects_directories import configured_projects_base  # noqa: E402


REPORT_SCHEMA_VERSION = "docs_uncataloged_files_report_v1"


def _candidate_identity(
    inspection: WorkSourceInspection, directory: InspectedDirectory, child: os.DirEntry[str],
) -> tuple[int, int] | None:
    metadata = inspection.entry(directory, child)
    if metadata is not None and stat.S_ISLNK(metadata.st_mode):
        # Preserve the existing candidate policy: dangling/non-file links supply
        # no image; a link to a regular file fails rather than becoming a row.
        # Only this exceptional classification needs a followed metadata read.
        try:
            target_metadata = child.stat()
        except FileNotFoundError:
            return None
        except OSError as error:
            raise ValueError("Work source file could not be inspected") from error
        if regular_file_identity(target_metadata) is not None:
            raise ValueError("Work media path must not contain symlinks")
        return None
    return regular_file_identity(metadata)


def uncataloged_files_report(repo_root: Path) -> dict[str, object]:
    """Read saved registrations and inspect represented directories once per run.

    Reuse terminal metadata for declared and listed files. Physical identity
    preserves case/Unicode/hard-link equivalence within each configured source.
    No recursive inventory, media contents, canonical fallback or write occurs.
    """
    works = read_catalogue_report_input(catalogue_output_workspace(repo_root), WORK_SOURCES_PATH)
    source_config = work_media_source_config(load_pipeline_config(repo_root=repo_root))
    sources = collect_work_sources(works, source_config)
    rows = []
    if sources:
        inspection = WorkSourceInspection(configured_projects_base())
        roots = inspection.source_roots(source_config["roots"], {source.source_id for source in sources})
        directories = {
            (source_id, relative): inspection.directory(roots[source_id], relative)
            for source_id, relative in dict.fromkeys((source.source_id, source.directory) for source in sources)
        }
        registered: dict[str, set[tuple[int, int]]] = {}
        for source in sources:
            directory = directories[source.source_id, source.directory]
            identity = regular_file_identity(inspection.file(directory, source.filename))
            if identity is not None:
                registered.setdefault(source.source_id, set()).add(identity)

        for (source_id, relative), directory in directories.items():
            if not directory.present:
                continue
            folder = f"{roots[source_id].subdir}/{relative}"
            identities = registered.get(source_id, set())
            try:
                with os.scandir(directory.path) as children:
                    for child in children:
                        if child.name.startswith(".") or Path(child.name).suffix.lower() not in IMAGE_EXTENSIONS:
                            continue
                        identity = _candidate_identity(inspection, directory, child)
                        if identity is None:
                            continue
                        local_target = encode_relative_target(f"{folder}/{child.name}")
                        if identity not in identities:
                            rows.append({"folder": folder, "file_name": child.name, "local_target": local_target})
            except OSError as error:
                raise ValueError(f"represented directory could not be listed: {relative}") from error
    rows.sort(key=lambda row: (row["folder"].casefold(), row["folder"], row["file_name"].casefold(), row["file_name"]))
    return {"report": {"schema_version": REPORT_SCHEMA_VERSION, "rows": rows}}
