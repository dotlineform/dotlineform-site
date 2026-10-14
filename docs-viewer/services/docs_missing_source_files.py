#!/usr/bin/env python3
"""Inspect each refreshed Work's declared primary-source file."""

from __future__ import annotations

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
from docs_work_source_inspection import WorkSourceInspection, collect_work_sources  # noqa: E402
from pipeline_config import load_pipeline_config, work_media_source_config  # noqa: E402
from studio.shared.python.projects_directories import configured_projects_base  # noqa: E402


REPORT_SCHEMA_VERSION = "docs_missing_source_files_report_v1"


def missing_source_files_report(repo_root: Path) -> dict[str, object]:
    """Inspect distinct declared paths without listing directories or reading files.

    Carry missing parents and terminal metadata across Works sharing a source;
    emit a separate row for every Work whose declared leaf is absent/non-regular.
    Missing roots and unsafe or unreadable paths fail without repair or fallback.
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
        for source in sources:
            directory = directories[source.source_id, source.directory]
            try:
                metadata = inspection.file(directory, source.filename)
            except ValueError as error:
                raise ValueError(f"work {source.work_id} source path is invalid: {error}") from error
            if metadata is not None and stat.S_ISREG(metadata.st_mode):
                continue
            rows.append({
                "work_id": source.work_id,
                "work_title": source.title,
                "expected_source_path": f"{roots[source.source_id].subdir}/{source.directory}/{source.filename}",
            })
    rows.sort(key=lambda row: row["work_id"])
    return {"report": {"schema_version": REPORT_SCHEMA_VERSION, "rows": rows}}
