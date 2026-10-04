"""Open exact draft Work source targets through configured media confinement."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_build_media import PIPELINE_CONFIG
from catalogue_work_media_sources import resolve_work_media_path, resolve_work_media_source_root
from docs_local_files import open_in_finder
from local_env import runtime_env


def _source_component(body: Mapping[str, Any], field: str) -> str:
    value = body.get(field)
    if (
        not isinstance(value, str) or not value or value != value.strip()
        or value in {".", ".."} or "/" in value or "\\" in value
    ):
        raise ValueError(f"{field} must be one exact source path segment")
    return value


def open_work_source_target(repo_root: Path, body: Mapping[str, Any], *, dry_run: bool = False) -> dict[str, Any]:
    """Open a selected directory or reveal an original, without saving the draft.

    Accept only a configured source identity and relative components. Missing
    targets, symlinks and unsupported platforms fail without substitute locations.
    """
    allowed = {"target", "media_source_id", "project_folder", "project_subfolder", "project_filename"}
    if set(body) - allowed:
        raise ValueError("Unsupported Work source opening fields")
    target = body.get("target")
    if not isinstance(target, str) or target not in {"project_folder", "project_subfolder", "project_filename"}:
        raise ValueError("Choose a project folder, subfolder or filename target")
    source_id = body.get("media_source_id")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("An exact Work media source identity is required")
    source = resolve_work_media_source_root(
        PIPELINE_CONFIG, source_id, environ=runtime_env(repo_root=repo_root), require_exists=True,
    )
    parts = [_source_component(body, "project_folder")]
    if target != "project_folder":
        subfolder = body.get("project_subfolder", "")
        if subfolder:
            parts.append(_source_component(body, "project_subfolder"))
        elif target == "project_subfolder":
            raise ValueError("Project subfolder is empty")
    reveal = target == "project_filename"
    if reveal:
        parts.append(_source_component(body, "project_filename"))
    path = resolve_work_media_path(source, *parts, require_exists=True)
    if not (path.is_file() if reveal else path.is_dir()):
        raise ValueError("The selected Work source target has the wrong file type")
    try:
        open_in_finder(
            repo_root, path, reveal=reveal, dry_run=dry_run,
            failure_message="Finder could not open the selected Work source target",
        )
    except OSError as error:
        raise RuntimeError("Finder could not open the selected Work source target") from error
    return {"ok": True, "target": target, "media_source_id": source.source_id}
