#!/usr/bin/env python3
"""Read the local filesystem and saved inputs for the Projects report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_output_paths import catalogue_workspace_config  # noqa: E402
from catalogue.catalogue_report_inputs import WORK_SOURCES_PATH, SERIES_PATH, read_catalogue_report_input  # noqa: E402
from docs_local_links import encode_relative_target  # noqa: E402
from docs_workspace_config import location_child, select_workspace_stage  # noqa: E402
from studio.shared.python.projects_directories import list_projects_directory  # noqa: E402


def project_state_inputs(repo_root: Path) -> dict[str, Any]:
    """Scan immediate project folders and read each saved input once.

    The browser owns placement, counts, viewer links and presentation. This
    handoff contains only consumed facts, without source paths or a saved report.
    Catalogue's reader owns its saved representation; document authoring/build
    owns manifest records. Missing inputs fail without repair or live fallbacks.
    """
    workspace = catalogue_workspace_config(repo_root)
    working = select_workspace_stage(workspace, "working")
    collection = next((item for item in working.collections if item.collection == "works"), None)
    if collection is None:
        raise ValueError("Docs Viewer collection is not configured: works")
    manifest_path = location_child(
        collection.generated.documents.location, Path("manage-manifest.json")
    ).path
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("Projects Manage manifest is unavailable or invalid") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("docs"), list):
        raise ValueError("Projects Manage manifest must contain a document list")

    listing = list_projects_directory("projects")
    folders = []
    for record in listing["directories"]:
        key = record["source_directory"]
        if not record["label"].startswith("."):
            folders.append({"key": key, "local_target": encode_relative_target(key)})
    works = read_catalogue_report_input(workspace.catalogue.working, WORK_SOURCES_PATH)
    series = read_catalogue_report_input(workspace.catalogue.working, SERIES_PATH)
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "folders": folders,
        "documents": [
            {key: record[key] for key in ("doc_id", "title", "subject") if key in record}
            for record in manifest["docs"]
        ],
        "works": [
            {"work_id": work_id, **{
                key: record[key] for key in ("project_folder", "series_id") if key in record
            }}
            for work_id, record in works.items()
        ],
        "series": [{"series_id": series_id, "title": record["title"]} for series_id, record in series.items()],
    }
