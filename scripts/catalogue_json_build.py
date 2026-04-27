#!/usr/bin/env python3
"""Scoped JSON-source catalogue build helper."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

from build_activity import append_build_activity
from catalogue_source import DEFAULT_SOURCE_DIR, normalize_status, records_from_json_source, slug_id
from moment_sources import (
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
    build_moment_metadata_entry,
    has_front_matter_text,
    load_moment_metadata_records,
    moment_metadata_payload,
    normalize_moment_filename,
    normalize_moment_metadata_record,
    validate_moment_metadata_record,
)
from pipeline_config import (
    env_var_name,
    env_var_value,
    load_pipeline_config,
    source_moments_images_subdir,
    source_moments_root_subdir,
    source_works_root_subdir,
)
from series_ids import normalize_series_id


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")
CATALOGUE_PROSE_STAGING_REL_DIR = Path("var/docs/catalogue/import-staging")
MOMENT_PROSE_STAGING_REL_DIR = CATALOGUE_PROSE_STAGING_REL_DIR / "moments"
CATALOGUE_MEDIA_STAGING_REL_DIR = Path("var/catalogue/media")

DEFAULT_ARTIFACTS = [
    "work-pages",
    "work-json",
    "series-pages",
    "series-index-json",
    "works-index-json",
    "recent-index-json",
]
DEFAULT_MOMENT_ARTIFACTS = ["moments"]
THUMB_SIZES = sorted({int(value) for value in PIPELINE_CONFIG["variants"]["thumb"]["sizes"]})
THUMB_SUFFIX = str(PIPELINE_CONFIG["variants"]["thumb"]["suffix"])
PRIMARY_WIDTHS = sorted({int(value) for value in PIPELINE_CONFIG["variants"]["compatibility"]["generate_widths"]})
PRIMARY_SUFFIX = str(PIPELINE_CONFIG["variants"]["primary"]["suffix"])
ASSET_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
ENCODER_CODEC = str(PIPELINE_CONFIG["encoding"]["codec"])
WEBP_PRESET = str(PIPELINE_CONFIG["encoding"]["preset"])
THUMB_Q = int(PIPELINE_CONFIG["encoding"]["thumb_quality"])
PRIMARY_Q = int(PIPELINE_CONFIG["encoding"]["primary_quality"])
COMPRESSION_LEVEL = int(PIPELINE_CONFIG["encoding"]["compression_level"])


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def detect_projects_base_dir(env: Dict[str, str] | None = None) -> Path:
    env = env or os.environ
    value = env_var_value(PIPELINE_CONFIG, "projects_base_dir", env)
    if not value:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} is required for moment source builds.")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} does not exist: {path}")
    return path


def detect_projects_base_dir_optional(env: Dict[str, str] | None = None) -> tuple[Path | None, str]:
    try:
        return detect_projects_base_dir(env), ""
    except ValueError as exc:
        return None, str(exc)


def display_source_path(path: Path | None, projects_base_dir: Path | None = None) -> str:
    if path is None:
        return ""
    normalized = path.resolve()
    if projects_base_dir is not None:
        try:
            return str(normalized.relative_to(projects_base_dir.resolve())).replace(os.sep, "/")
        except ValueError:
            pass
    return str(normalized)


def normalize_filename(value: Any) -> str:
    text = str(value or "").strip()
    return Path(text).name if text else ""


def repo_relative_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace(os.sep, "/")
    except ValueError:
        return str(path.resolve())


def resolve_work_media_source(
    records,
    work_id: str,
    *,
    env: Dict[str, str] | None = None,
) -> tuple[Path | None, str, Path | None, str]:
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    work_record = records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    works_root = (projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)) if projects_base_dir else None
    project_folder = str(work_record.get("project_folder") or "").strip()
    project_filename = normalize_filename(work_record.get("project_filename"))
    if project_folder and project_filename and works_root is not None:
        return works_root / project_folder / project_filename, "", projects_base_dir, availability_error
    if project_filename:
        return None, "missing_project_folder", projects_base_dir, availability_error
    return None, "missing_project_filename", projects_base_dir, availability_error


def resolve_detail_media_source(
    records,
    detail_uid: str,
    *,
    env: Dict[str, str] | None = None,
) -> tuple[Path | None, str, Path | None, str]:
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    detail_record = records.work_details.get(detail_uid)
    if not isinstance(detail_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")

    works_root = (projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)) if projects_base_dir else None
    work_id = slug_id(detail_record.get("work_id"))
    work_record = records.works.get(work_id)
    project_folder = str(work_record.get("project_folder") or "").strip() if isinstance(work_record, dict) else ""
    project_subfolder = str(detail_record.get("project_subfolder") or "").strip()
    project_filename = normalize_filename(detail_record.get("project_filename"))
    if not project_filename:
        return None, "missing_project_filename", projects_base_dir, availability_error
    if not project_folder:
        return None, "missing_project_folder", projects_base_dir, availability_error
    if works_root is None:
        return None, "", projects_base_dir, availability_error
    media_path = works_root / project_folder
    if project_subfolder:
        media_path = media_path / project_subfolder
    return media_path / project_filename, "", projects_base_dir, availability_error


def thumb_output_dir(repo_root: Path, kind: str) -> Path:
    if kind == "work":
        return repo_root / "assets" / "works" / "img"
    if kind == "work_details":
        return repo_root / "assets" / "work_details" / "img"
    raise ValueError(f"unsupported local media kind: {kind}")


def media_staging_kind_dir(kind: str) -> str:
    if kind == "work":
        return "works"
    if kind == "work_details":
        return "work_details"
    if kind == "moment":
        return "moments"
    raise ValueError(f"unsupported local media kind: {kind}")


def media_staging_input_path(repo_root: Path, kind: str, item_id: str, source_path: Path | None) -> Path:
    suffix = source_path.suffix if source_path is not None and source_path.suffix else ".jpg"
    return repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / media_staging_kind_dir(kind) / "make_srcset_images" / f"{item_id}{suffix}"


def media_srcset_root(repo_root: Path, kind: str) -> Path:
    return repo_root / CATALOGUE_MEDIA_STAGING_REL_DIR / media_staging_kind_dir(kind) / "srcset_images"


def staged_thumb_output_paths(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    root = media_srcset_root(repo_root, kind) / "thumb"
    return [root / f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]


def staged_primary_output_paths(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    root = media_srcset_root(repo_root, kind) / "primary"
    return [root / f"{item_id}-{PRIMARY_SUFFIX}-{width}.{ASSET_FORMAT}" for width in PRIMARY_WIDTHS]


def thumb_output_paths(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    root = thumb_output_dir(repo_root, kind)
    return [root / f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]


def local_output_state(source_path: Path | None, output_paths: Sequence[Path]) -> str:
    if source_path is None or not source_path.exists():
        return "blocked"
    if not output_paths:
        return "current"
    if not all(path.exists() for path in output_paths):
        return "pending"
    try:
        source_mtime = source_path.stat().st_mtime
        if all(path.stat().st_mtime >= source_mtime for path in output_paths):
            return "current"
    except OSError:
        return "pending"
    return "pending"


def local_thumb_state(source_path: Path | None, output_paths: Sequence[Path]) -> str:
    return local_output_state(source_path, output_paths)


def local_media_state(source_path: Path | None, output_paths: Sequence[Path], staged_source_path: Path | None = None) -> str:
    paths = list(output_paths)
    if staged_source_path is not None:
        paths = [staged_source_path, *paths]
    return local_output_state(source_path, paths)


def path_needs_refresh(path: Path, source_mtime: float) -> bool:
    try:
        return not path.exists() or path.stat().st_mtime < source_mtime
    except OSError:
        return True


def build_media_readiness_item(
    *,
    repo_root: Path,
    kind: str,
    item_id: str,
    key: str,
    title: str,
    source_path: Path | None,
    missing_reason: str,
    projects_base_dir: Path | None,
    availability_error: str,
) -> Dict[str, Any]:
    source_display = display_source_path(source_path, projects_base_dir)
    outputs = thumb_output_paths_for_kind(repo_root, kind, item_id)
    output_display = ", ".join(repo_relative_path(path, repo_root) for path in outputs)
    state = local_thumb_state(source_path, outputs)

    if availability_error:
        return {
            "key": key,
            "title": title,
            "status": "unavailable",
            "summary": availability_error,
            "next_step": "Start the local Studio service with the projects base directory configured.",
            "source_path": source_display,
            "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
            "exists": False,
        }
    if state == "current":
        return {
            "key": key,
            "title": title,
            "status": "ready",
            "summary": f"Source media is ready and local thumbnails are current in {output_display}.",
            "next_step": "Local thumbnails are current for this record.",
            "source_path": source_display,
            "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
            "exists": True,
        }
    if source_path and source_path.exists():
        return {
            "key": key,
            "title": title,
            "status": "pending_generation",
            "summary": f"Source media is ready at {source_display}, but local thumbnails need generation or refresh.",
            "next_step": "Run Save + Rebuild to generate local thumbnails.",
            "source_path": source_display,
            "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
            "exists": True,
        }
    if missing_reason == "missing_project_folder":
        return {
            "key": key,
            "title": title,
            "status": "missing_metadata",
            "summary": "Project folder is missing, so the source path cannot be resolved.",
            "next_step": "Set project folder metadata and save before rebuilding media.",
            "source_path": source_display,
            "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
            "exists": False,
        }
    if missing_reason:
        return {
            "key": key,
            "title": title,
            "status": "not_configured",
            "summary": "No source file is configured yet.",
            "next_step": "Set the source filename in metadata and save before rebuilding media.",
            "source_path": source_display,
            "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
            "exists": False,
        }
    return {
        "key": key,
        "title": title,
        "status": "missing_file",
        "summary": f"Configured source media is missing at {source_display}." if source_display else "Configured source media file is missing.",
        "next_step": "Create or restore the source media file, or update the filename before rebuilding media.",
        "source_path": source_display,
        "generated_paths": [repo_relative_path(path, repo_root) for path in outputs],
        "exists": False,
    }


def resolve_moment_media_source(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> tuple[str, Path | None, str, Path | None, str]:
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    if projects_base_dir is None:
        filename = normalize_moment_filename(moment_file)
        return filename[:-3], None, "", None, availability_error
    filename = normalize_moment_filename(moment_file)
    moment_id = filename[:-3]
    records = load_moment_metadata_records(repo_root / DEFAULT_SOURCE_DIR)
    record = metadata if metadata is not None else records.get(moment_id)
    if not record:
        return moment_id, None, "missing_moment_file", projects_base_dir, availability_error
    entry = build_moment_metadata_entry(
        moment_id,
        record,
        prose_root=repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR,
        moments_images_root=projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG),
    )
    source_image_path = Path(str(entry.get("source_image_path") or "")).resolve() if entry.get("source_image_path") else None
    if source_image_path:
        return moment_id, source_image_path, "", projects_base_dir, availability_error
    return moment_id, None, "missing_image_file", projects_base_dir, availability_error


def thumb_output_paths_for_kind(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    if kind == "moment":
        root = repo_root / "assets" / "moments" / "img"
        return [root / f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]
    return thumb_output_paths(repo_root, kind, item_id)


def media_blocked_reason_text(reason: str) -> str:
    mapping = {
        "missing_project_folder": "project folder is missing",
        "missing_project_filename": "project filename is missing",
        "missing_moment_file": "moment source file is missing",
        "missing_image_file": "moment image file is missing",
    }
    return mapping.get(reason, reason or "media source is not available")


def build_local_media_task(
    *,
    repo_root: Path,
    kind: str,
    item_id: str,
    source_path: Path | None,
    availability_error: str = "",
    blocked_reason: str = "",
    projects_base_dir: Path | None = None,
) -> Dict[str, Any]:
    staged_source_path = media_staging_input_path(repo_root, kind, item_id, source_path)
    staged_thumb_paths = staged_thumb_output_paths(repo_root, kind, item_id)
    staged_primary_paths = staged_primary_output_paths(repo_root, kind, item_id)
    asset_thumb_paths = thumb_output_paths_for_kind(repo_root, kind, item_id)
    output_paths = [*staged_thumb_paths, *staged_primary_paths, *asset_thumb_paths]
    state = local_media_state(source_path, output_paths, staged_source_path)
    task: Dict[str, Any] = {
        "kind": kind,
        "id": item_id,
        "source_path": display_source_path(source_path, projects_base_dir),
        "source_abs_path": str(source_path.resolve()) if source_path is not None else "",
        "staged_source_path": repo_relative_path(staged_source_path, repo_root),
        "staged_source_abs_path": str(staged_source_path.resolve()),
        "output_paths": [repo_relative_path(path, repo_root) for path in output_paths],
        "staged_thumb_paths": [repo_relative_path(path, repo_root) for path in staged_thumb_paths],
        "staged_primary_paths": [repo_relative_path(path, repo_root) for path in staged_primary_paths],
        "asset_thumb_paths": [repo_relative_path(path, repo_root) for path in asset_thumb_paths],
        "status": state,
    }
    if availability_error:
        task["status"] = "unavailable"
        task["reason"] = availability_error
        return task
    if blocked_reason:
        task["status"] = "blocked"
        task["reason"] = media_blocked_reason_text(blocked_reason)
        return task
    if state == "pending":
        source_mtime = source_path.stat().st_mtime if source_path and source_path.exists() else 0.0
        task["pending_staged_source"] = path_needs_refresh(staged_source_path, source_mtime)
        pending_thumb_outputs: list[Dict[str, Any]] = []
        pending_primary_outputs: list[Dict[str, Any]] = []
        pending_asset_thumbs: list[Dict[str, Any]] = []
        for size, path in zip(THUMB_SIZES, staged_thumb_paths):
            if path_needs_refresh(path, source_mtime):
                pending_thumb_outputs.append(
                    {
                        "variant": "thumb",
                        "size": size,
                        "path": repo_relative_path(path, repo_root),
                        "absolute_path": str(path.resolve()),
                    }
                )
        for width, path in zip(PRIMARY_WIDTHS, staged_primary_paths):
            if path_needs_refresh(path, source_mtime):
                pending_primary_outputs.append(
                    {
                        "variant": "primary",
                        "width": width,
                        "path": repo_relative_path(path, repo_root),
                        "absolute_path": str(path.resolve()),
                    }
                )
        for size, path, staged_path in zip(THUMB_SIZES, asset_thumb_paths, staged_thumb_paths):
            if path_needs_refresh(path, source_mtime):
                pending_asset_thumbs.append(
                    {
                        "size": size,
                        "path": repo_relative_path(path, repo_root),
                        "absolute_path": str(path.resolve()),
                        "staged_path": repo_relative_path(staged_path, repo_root),
                        "staged_absolute_path": str(staged_path.resolve()),
                    }
                )
        task["pending_thumb_outputs"] = pending_thumb_outputs
        task["pending_primary_outputs"] = pending_primary_outputs
        task["pending_asset_thumbs"] = pending_asset_thumbs
    return task


def build_local_media_plan(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    scope_kind = str(scope.get("kind") or "work").strip().lower()
    tasks: list[Dict[str, Any]] = []
    if scope_kind == "moment":
        metadata = scope.get("moment_metadata") if isinstance(scope.get("moment_metadata"), dict) else None
        for moment_id in scope.get("moment_ids", []):
            moment_file = str(scope.get("moment_file") or f"{moment_id}.md")
            resolved_moment_id, source_path, missing_reason, projects_base_dir, availability_error = resolve_moment_media_source(
                repo_root,
                moment_file,
                metadata=metadata,
                env=env,
            )
            tasks.append(
                build_local_media_task(
                    repo_root=repo_root,
                    kind="moment",
                    item_id=resolved_moment_id,
                    source_path=source_path,
                    availability_error=availability_error,
                    blocked_reason=missing_reason,
                    projects_base_dir=projects_base_dir,
                )
            )
    else:
        source_dir = Path(str(scope.get("source_dir") or "")).expanduser() if scope.get("source_dir") else None
        records = records_from_json_source(source_dir) if source_dir is not None else None
        if records is None:
            return {"tasks": [], "counts": {"pending": 0, "current": 0, "blocked": 0, "unavailable": 0}}
        for work_id in scope.get("work_ids", []):
            source_path, missing_reason, projects_base_dir, availability_error = resolve_work_media_source(records, str(work_id), env=env)
            tasks.append(
                build_local_media_task(
                    repo_root=repo_root,
                    kind="work",
                    item_id=str(work_id),
                    source_path=source_path,
                    availability_error=availability_error,
                    blocked_reason=missing_reason,
                    projects_base_dir=projects_base_dir,
                )
            )
        detail_uid = str(scope.get("detail_uid") or "").strip()
        if detail_uid:
            source_path, missing_reason, projects_base_dir, availability_error = resolve_detail_media_source(records, detail_uid, env=env)
            tasks.append(
                build_local_media_task(
                    repo_root=repo_root,
                    kind="work_details",
                    item_id=detail_uid,
                    source_path=source_path,
                    availability_error=availability_error,
                    blocked_reason=missing_reason,
                    projects_base_dir=projects_base_dir,
                )
            )
    counts = {
        "pending": sum(1 for task in tasks if task.get("status") == "pending"),
        "current": sum(1 for task in tasks if task.get("status") == "current"),
        "blocked": sum(1 for task in tasks if task.get("status") == "blocked"),
        "unavailable": sum(1 for task in tasks if task.get("status") == "unavailable"),
    }
    return {"tasks": tasks, "counts": counts}


def run_ffmpeg_thumb(src: Path, size: int, dest: Path) -> tuple[int, str]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(src),
        "-map_metadata",
        "-1",
        "-vf",
        f"scale='if(gt(iw,ih),-1,{size})':'if(gt(iw,ih),{size},-1)':flags=lanczos,crop={size}:{size}",
        "-c:v",
        ENCODER_CODEC,
        "-preset",
        WEBP_PRESET,
        "-q:v",
        str(THUMB_Q),
        "-compression_level",
        str(COMPRESSION_LEVEL),
        str(dest),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return proc.returncode, (proc.stderr or proc.stdout or "").strip()


def run_ffmpeg_primary(src: Path, width: int, dest: Path) -> tuple[int, str]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(src),
        "-map_metadata",
        "-1",
        "-vf",
        f"scale=w='min(iw,{width})':h=-2:flags=lanczos",
        "-c:v",
        ENCODER_CODEC,
        "-preset",
        WEBP_PRESET,
        "-q:v",
        str(PRIMARY_Q),
        "-compression_level",
        str(COMPRESSION_LEVEL),
        str(dest),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return proc.returncode, (proc.stderr or proc.stdout or "").strip()


def execute_local_media_plan(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    write: bool,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    plan = build_local_media_plan(repo_root, scope=scope, env=env)
    tasks = plan["tasks"]
    if not tasks:
        return {
            "label": "Generate Local Media Derivatives",
            "status": "skipped",
            "summary": "No local media targets in this scope.",
            "generated": {"work": [], "work_details": [], "moment": []},
            "planned": {"work": [], "work_details": [], "moment": []},
            "current": {"work": [], "work_details": [], "moment": []},
            "blocked": {"work": [], "work_details": [], "moment": []},
            "exit_code": 0,
        }

    pending_tasks = [task for task in tasks if task.get("status") == "pending"]
    if pending_tasks and shutil.which("ffmpeg") is None:
        return {
            "label": "Generate Local Media Derivatives",
            "status": "failed",
            "summary": "ffmpeg is required for local media generation.",
            "generated": {"work": [], "work_details": [], "moment": []},
            "planned": {"work": [], "work_details": [], "moment": []},
            "current": {"work": [], "work_details": [], "moment": []},
            "blocked": {"work": [], "work_details": [], "moment": []},
            "exit_code": 1,
            "stderr_tail": "ffmpeg not found on PATH",
        }

    generated: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    planned: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    current: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    blocked: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    messages: list[str] = []

    for task in tasks:
        kind = str(task.get("kind") or "")
        item_id = str(task.get("id") or "")
        status = str(task.get("status") or "")
        if status == "current":
            current[kind].append(item_id)
            continue
        if status in {"blocked", "unavailable"}:
            blocked[kind].append(item_id)
            reason = str(task.get("reason") or "").strip()
            if reason:
                messages.append(f"{kind} {item_id}: {reason}")
            continue
        if status != "pending":
            continue
        if not write:
            planned[kind].append(item_id)
            continue
        actual_source = Path(str(task.get("source_abs_path") or "")).resolve() if str(task.get("source_abs_path") or "").strip() else None
        if actual_source is None:
            reason = str(task.get("reason") or "missing source path").strip()
            blocked[kind].append(item_id)
            messages.append(f"{kind} {item_id}: {reason}")
            continue
        staged_source = Path(str(task.get("staged_source_abs_path") or "")).resolve()
        if bool(task.get("pending_staged_source")):
            staged_source.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(actual_source, staged_source)
        if not staged_source.exists():
            blocked[kind].append(item_id)
            messages.append(f"{kind} {item_id}: staged source copy failed")
            continue
        pending_thumb_outputs = task.get("pending_thumb_outputs") if isinstance(task.get("pending_thumb_outputs"), list) else []
        for output_spec in pending_thumb_outputs:
            output_path = Path(str(output_spec.get("absolute_path") or "")).resolve()
            size = int(output_spec.get("size") or THUMB_SIZES[0])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            exit_code, stderr_tail = run_ffmpeg_thumb(staged_source, size, output_path)
            if exit_code != 0:
                return {
                    "label": "Generate Local Media Derivatives",
                    "status": "failed",
                    "summary": f"Local media generation failed for {kind} {item_id}.",
                    "generated": generated,
                    "planned": planned,
                    "current": current,
                    "blocked": blocked,
                    "exit_code": exit_code,
                    "stderr_tail": stderr_tail,
                }
        pending_primary_outputs = task.get("pending_primary_outputs") if isinstance(task.get("pending_primary_outputs"), list) else []
        for output_spec in pending_primary_outputs:
            output_path = Path(str(output_spec.get("absolute_path") or "")).resolve()
            width = int(output_spec.get("width") or PRIMARY_WIDTHS[-1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            exit_code, stderr_tail = run_ffmpeg_primary(staged_source, width, output_path)
            if exit_code != 0:
                return {
                    "label": "Generate Local Media Derivatives",
                    "status": "failed",
                    "summary": f"Local primary media generation failed for {kind} {item_id}.",
                    "generated": generated,
                    "planned": planned,
                    "current": current,
                    "blocked": blocked,
                    "exit_code": exit_code,
                    "stderr_tail": stderr_tail,
                }
        pending_asset_thumbs = task.get("pending_asset_thumbs") if isinstance(task.get("pending_asset_thumbs"), list) else []
        for output_spec in pending_asset_thumbs:
            staged_thumb = Path(str(output_spec.get("staged_absolute_path") or "")).resolve()
            output_path = Path(str(output_spec.get("absolute_path") or "")).resolve()
            if not staged_thumb.exists():
                return {
                    "label": "Generate Local Media Derivatives",
                    "status": "failed",
                    "summary": f"Local thumbnail staging failed for {kind} {item_id}.",
                    "generated": generated,
                    "planned": planned,
                    "current": current,
                    "blocked": blocked,
                    "exit_code": 1,
                    "stderr_tail": f"missing staged thumbnail: {repo_relative_path(staged_thumb, repo_root)}",
                }
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staged_thumb, output_path)
        generated[kind].append(item_id)

    summary_parts: list[str] = []
    generated_total = sum(len(values) for values in generated.values())
    planned_total = sum(len(values) for values in planned.values())
    current_total = sum(len(values) for values in current.values())
    blocked_total = sum(len(values) for values in blocked.values())
    if generated_total:
        summary_parts.append(f"generated local media for {generated_total} record(s)")
    if planned_total:
        summary_parts.append(f"would generate local media for {planned_total} record(s)")
    if current_total:
        summary_parts.append(f"{current_total} already current")
    if blocked_total:
        summary_parts.append(f"{blocked_total} blocked")
    summary = "; ".join(summary_parts) if summary_parts else "No local media changes needed."
    if messages:
        summary = f"{summary} {'; '.join(messages[:3])}".strip()
    return {
        "label": "Generate Local Media Derivatives",
        "status": "completed",
        "summary": summary,
        "generated": generated,
        "planned": planned,
        "current": current,
        "blocked": blocked,
        "exit_code": 0,
        "stdout_tail": summary,
    }


def build_readiness_item(
    *,
    key: str,
    title: str,
    path: Path | None,
    projects_base_dir: Path | None,
    availability_error: str = "",
    missing_reason: str = "",
    ready_summary: str,
    missing_file_summary: str,
    next_step_ready: str = "",
    next_step_missing_file: str = "",
    next_step_missing_metadata: str = "",
    next_step_unavailable: str = "",
    action: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    source_path = display_source_path(path, projects_base_dir)
    exists = bool(path and path.exists())

    if availability_error:
        status = "unavailable"
        summary = availability_error
        next_step = next_step_unavailable or "Start the local Studio service with the projects base directory configured."
    elif exists:
        status = "ready"
        summary = ready_summary
        next_step = next_step_ready
    elif missing_reason == "missing_project_folder":
        status = "missing_metadata"
        summary = "Project folder is missing, so the source path cannot be resolved."
        next_step = next_step_missing_metadata or "Set project_folder and save the source record before checking readiness again."
    elif missing_reason == "missing_primary_work_id":
        status = "missing_metadata"
        summary = "Primary work is missing, so the series prose path cannot be resolved."
        next_step = next_step_missing_metadata or "Set primary_work_id and save the source record before checking readiness again."
    elif missing_reason == "primary_work_missing":
        status = "missing_metadata"
        summary = "Primary work does not exist in the current source records."
        next_step = next_step_missing_metadata or "Fix primary_work_id before checking readiness again."
    elif missing_reason:
        status = "not_configured"
        summary = "No source file is configured yet."
        next_step = next_step_missing_metadata or "Set the source filename in metadata and save before checking readiness again."
    else:
        status = "missing_file"
        summary = missing_file_summary
        next_step = next_step_missing_file or "Create or restore the source file, then check readiness again."

    item: Dict[str, Any] = {
        "key": key,
        "title": title,
        "status": status,
        "summary": summary,
        "next_step": next_step,
        "source_path": source_path,
        "exists": exists,
    }
    if action and status == "ready":
        item["action"] = action
    return item


def build_work_readiness(records, work_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    repo_root = detect_repo_root()
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    work_record = records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    media_path, media_missing_reason, _, _ = resolve_work_media_source(records, work_id, env=env)
    prose_path = repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / "works" / f"{work_id}.md"

    items = [
        build_media_readiness_item(
            repo_root=repo_root,
            kind="work",
            item_id=work_id,
            key="work_media",
            title="work media",
            source_path=media_path,
            missing_reason=media_missing_reason,
            projects_base_dir=projects_base_dir,
            availability_error=availability_error,
        ),
        build_readiness_item(
            key="work_prose",
            title="work prose",
            path=prose_path,
            projects_base_dir=repo_root,
            ready_summary=f"Staged prose is ready at {display_source_path(prose_path, repo_root)}.",
            missing_file_summary=f"No staged prose file exists at {display_source_path(prose_path, repo_root)}.",
            next_step_ready="Use Import staged prose to write the permanent source file.",
            next_step_missing_file="Add staged Markdown at the expected ID-based path before importing prose.",
            action={
                "kind": "prose-import",
                "target_kind": "work",
                "work_id": work_id,
                "label": "Import staged prose",
            },
        ),
    ]
    return {"items": items}


def build_series_readiness(records, series_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    repo_root = detect_repo_root()
    series_record = records.series.get(series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")

    prose_path = repo_root / CATALOGUE_PROSE_STAGING_REL_DIR / "series" / f"{series_id}.md"

    items = [
        build_readiness_item(
            key="series_prose",
            title="series prose",
            path=prose_path,
            projects_base_dir=repo_root,
            ready_summary=f"Staged prose is ready at {display_source_path(prose_path, repo_root)}.",
            missing_file_summary=f"No staged prose file exists at {display_source_path(prose_path, repo_root)}.",
            next_step_ready="Use Import staged prose to write the permanent source file.",
            next_step_missing_file="Add staged Markdown at the expected ID-based path before importing prose.",
            action={
                "kind": "prose-import",
                "target_kind": "series",
                "series_id": series_id,
                "label": "Import staged prose",
            },
        ),
    ]
    return {"items": items}


def build_detail_readiness(records, detail_uid: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    repo_root = detect_repo_root()
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    detail_record = records.work_details.get(detail_uid)
    if not isinstance(detail_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")
    media_path, media_missing_reason, _, _ = resolve_detail_media_source(records, detail_uid, env=env)

    items = [
        build_media_readiness_item(
            repo_root=repo_root,
            kind="work_details",
            item_id=detail_uid,
            key="detail_media",
            title="detail media",
            source_path=media_path,
            missing_reason=media_missing_reason,
            projects_base_dir=projects_base_dir,
            availability_error=availability_error,
        ),
    ]
    return {"items": items}


def build_moment_paths(projects_base_dir: Path, moment_file: str) -> Dict[str, Path]:
    filename = normalize_moment_filename(moment_file)
    moments_root = projects_base_dir / source_moments_root_subdir(PIPELINE_CONFIG)
    moments_images_root = projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG)
    source_path = moments_root / filename
    return {
        "moments_root": moments_root,
        "moments_images_root": moments_images_root,
        "source_path": source_path,
    }


def build_moment_import_metadata(
    source_dir: Path,
    moment_id: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    records = load_moment_metadata_records(source_dir)
    existing = records.get(moment_id, {})
    merged = {**existing, **(metadata or {}), "moment_id": moment_id}
    return normalize_moment_metadata_record(moment_id, merged)


def preview_moment_source(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    staged: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    filename = normalize_moment_filename(moment_file)
    moment_id = filename[:-3]
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    staging_path = repo_root / MOMENT_PROSE_STAGING_REL_DIR / filename
    target_path = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    source_path = staging_path if staged else target_path
    source_rel_path = (MOMENT_PROSE_STAGING_REL_DIR if staged else CATALOGUE_MOMENT_PROSE_REL_DIR) / filename
    metadata_record = build_moment_import_metadata(source_dir, moment_id, metadata)
    preview: Dict[str, Any] = {
        "kind": "moment",
        "moment_id": moment_id,
        "moment_file": filename,
        "source_path": str(source_rel_path),
        "staging_path": str(MOMENT_PROSE_STAGING_REL_DIR / filename),
        "target_path": str(CATALOGUE_MOMENT_PROSE_REL_DIR / filename),
        "metadata_path": str(DEFAULT_SOURCE_DIR / MOMENT_METADATA_FILENAME),
        "public_url": f"/moments/{moment_id}/",
        "generated_page_path": str(Path("_moments") / f"{moment_id}.md"),
        "generated_json_path": str(Path("assets/moments/index") / f"{moment_id}.json"),
        "moments_index_path": "assets/data/moments_index.json",
        "search_scope": "catalogue",
        "source_exists": source_path.exists(),
        "target_exists": target_path.exists(),
        "errors": [],
        "valid": False,
        "title": metadata_record.get("title") or "",
        "status": metadata_record.get("status") or "",
        "date": metadata_record.get("date") or "",
        "date_display": metadata_record.get("date_display") or "",
        "published_date": metadata_record.get("published_date") or "",
        "image_file": metadata_record.get("source_image_file") or f"{moment_id}.jpg",
        "image_alt": metadata_record.get("image_alt") or "",
    }

    if not source_path.exists():
        preview["errors"] = [f"Missing {'staged ' if staged else ''}moment prose file: {source_rel_path}"]
        return preview

    source_text = source_path.read_text(encoding="utf-8")
    if has_front_matter_text(source_text):
        prefix = "Staged moment prose" if staged else "Moment prose source"
        preview["errors"] = [f"{prefix} must be body-only Markdown without front matter."]
        return preview

    projects_base_dir, _availability_error = detect_projects_base_dir_optional(env)
    source_image_file = str(metadata_record.get("source_image_file") or f"{moment_id}.jpg")
    source_image_path = (projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG) / source_image_file) if projects_base_dir else None
    preview["source_image_path"] = str(Path("moments") / "images" / Path(source_image_file).name)
    preview["source_image_exists"] = bool(source_image_path and source_image_path.exists())
    preview["generated_page_exists"] = (repo_root / "_moments" / f"{moment_id}.md").exists()
    preview["generated_json_exists"] = (repo_root / "assets/moments/index" / f"{moment_id}.json").exists()
    preview["in_moments_index"] = False

    moments_index_path = repo_root / "assets/data/moments_index.json"
    if moments_index_path.exists():
        try:
            moments_index_text = moments_index_path.read_text(encoding="utf-8")
            payload = json.loads(moments_index_text)
            moments_map = payload.get("moments") if isinstance(payload, dict) else {}
            moment_index_ids = (
                {str(key).strip().lower() for key in moments_map.keys()}
                if isinstance(moments_map, dict)
                else set()
            )
            preview["in_moments_index"] = moment_id in moment_index_ids
            if not preview["in_moments_index"]:
                preview["in_moments_index"] = f'"{moment_id}":' in moments_index_text
        except Exception:
            preview["in_moments_index"] = False

    errors = validate_moment_metadata_record(metadata_record)
    preview["errors"] = errors
    preview["valid"] = not errors
    preview["effective_force"] = False
    preview["refresh_published"] = bool(metadata_record.get("status") == "published")
    source_label = MOMENT_PROSE_STAGING_REL_DIR / filename if staged else CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    action = "Import" if staged else "Build"
    preview["summary"] = f"{action} moment {moment_id} from {source_label}, rebuild the moment payloads, and rebuild catalogue search."
    return preview


def normalize_series_ids(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            series_id = normalize_series_id(token)
            if series_id in seen:
                continue
            seen.add(series_id)
            out.append(series_id)
    return out


def validate_buildable_series_scope(records, series_ids: Sequence[str]) -> None:
    work_series_ids_by_work_id: dict[str, list[str]] = {}
    for work_id, work_record in records.works.items():
        raw_series_ids = work_record.get("series_ids", [])
        if isinstance(raw_series_ids, list):
            work_series_ids_by_work_id[work_id] = normalize_series_ids(raw_series_ids)
        else:
            work_series_ids_by_work_id[work_id] = []

    errors: list[str] = []
    for series_id in series_ids:
        series_record = records.series.get(series_id)
        if not isinstance(series_record, dict):
            errors.append(f"series {series_id}: not found in source records")
            continue
        status = normalize_status(series_record.get("status"))
        if status not in {"draft", "published"}:
            continue
        raw_primary_work_id = str(series_record.get("primary_work_id") or "").strip()
        if not raw_primary_work_id:
            errors.append(f"series {series_id}: missing primary_work_id for runtime build")
            continue
        primary_work_id = slug_id(raw_primary_work_id)
        if primary_work_id not in records.works:
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} not found in works")
            continue
        if series_id not in work_series_ids_by_work_id.get(primary_work_id, []):
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} is not in that work's series_ids")

    if errors:
        raise ValueError("series build precondition failed: " + "; ".join(errors[:20]))


def build_scope_for_work(
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    *,
    detail_uid: str = "",
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    normalized_work_id = slug_id(work_id)
    records = records_from_json_source(source_dir)
    work_record = records.works.get(normalized_work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {normalized_work_id}")

    current_series_ids = normalize_series_ids(work_record.get("series_ids", []))
    requested_extra_series_ids = normalize_series_ids(extra_series_ids or [])
    series_ids = normalize_series_ids([*current_series_ids, *requested_extra_series_ids])
    validate_buildable_series_scope(records, series_ids)
    scope = {
        "work_ids": [normalized_work_id],
        "series_ids": series_ids,
        "current_series_ids": current_series_ids,
        "extra_series_ids": [series_id for series_id in requested_extra_series_ids if series_id not in current_series_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "refresh_published": True,
        "summary": summarize_scope([normalized_work_id], series_ids),
    }
    readiness = build_work_readiness(records, normalized_work_id, env=env)
    if detail_uid:
        normalized_detail_uid = str(detail_uid or "").strip()
        readiness["items"].extend(build_detail_readiness(records, normalized_detail_uid, env=env).get("items", []))
        scope["detail_uid"] = normalized_detail_uid
    scope["readiness"] = readiness
    return scope


def build_scope_for_series(
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    *,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    normalized_series_id = normalize_series_id(series_id)
    records = records_from_json_source(source_dir)
    series_record = records.series.get(normalized_series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {normalized_series_id}")

    current_work_ids: list[str] = []
    for work_id, work_record in records.works.items():
        series_ids = work_record.get("series_ids", [])
        if isinstance(series_ids, list) and normalized_series_id in normalize_series_ids(series_ids):
            current_work_ids.append(work_id)
    current_work_ids = sorted(current_work_ids)

    requested_extra_work_ids: list[str] = []
    seen_extra: set[str] = set()
    for raw in extra_work_ids or []:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            work_id = slug_id(token)
            if work_id in seen_extra:
                continue
            seen_extra.add(work_id)
            requested_extra_work_ids.append(work_id)

    work_ids = sorted({*current_work_ids, *requested_extra_work_ids})
    validate_buildable_series_scope(records, [normalized_series_id])
    scope = {
        "kind": "series",
        "work_ids": work_ids,
        "series_ids": [normalized_series_id],
        "current_work_ids": current_work_ids,
        "extra_work_ids": [work_id for work_id in requested_extra_work_ids if work_id not in current_work_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "refresh_published": True,
        "summary": summarize_scope(work_ids, [normalized_series_id]),
    }
    scope["readiness"] = build_series_readiness(records, normalized_series_id, env=env)
    return scope


def build_scope_for_moment(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    force: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    preview = preview_moment_source(repo_root, moment_file, metadata=metadata, env=env)
    if not preview.get("valid"):
        errors = preview.get("errors") or []
        raise ValueError("; ".join(str(error) for error in errors) or "moment source preview failed")
    moment_id = str(preview.get("moment_id") or "").strip().lower()
    moment_metadata = build_moment_import_metadata(repo_root / DEFAULT_SOURCE_DIR, moment_id, metadata)
    return {
        "kind": "moment",
        "moment_ids": [moment_id],
        "moment_file": str(preview.get("moment_file") or ""),
        "moment_metadata": moment_metadata,
        "work_ids": [],
        "series_ids": [],
        "generate_only": list(DEFAULT_MOMENT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "moment-source",
        "summary": summarize_moment_scope([moment_id]),
        "effective_force": bool(force),
        "refresh_published": True,
        "preview": preview,
    }


def summarize_scope(work_ids: Sequence[str], series_ids: Sequence[str]) -> str:
    work_text = ", ".join(work_ids) if work_ids else "none"
    series_text = ", ".join(series_ids) if series_ids else "none"
    return f"Build works [{work_text}], series [{series_text}], aggregate indexes, and catalogue search."


def summarize_moment_scope(moment_ids: Sequence[str]) -> str:
    moment_text = ", ".join(moment_ids) if moment_ids else "none"
    return f"Build moments [{moment_text}], rebuild the moments index, and rebuild catalogue search."


def resolve_bundle_bin(env: Dict[str, str] | None = None) -> str:
    env = env or os.environ
    home = Path(env.get("HOME", "")).expanduser()
    shim = home / ".rbenv/shims/bundle"
    if shim.exists() and os.access(shim, os.X_OK):
        return str(shim)
    return env.get("BUNDLE_BIN", "bundle")


def build_generate_command(
    repo_root: Path,
    source_dir: Path,
    scope: Dict[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_work_pages.py"),
        "--internal-json-source-run",
        "--source-dir",
        str(source_dir),
        "--work-ids",
        ",".join(scope["work_ids"]),
    ]
    series_ids = list(scope.get("series_ids", []))
    if series_ids:
        cmd += ["--series-ids", ",".join(series_ids)]
    for artifact in scope.get("generate_only", []):
        cmd += ["--only", str(artifact)]
    if write:
        cmd.append("--write")
    if refresh_published:
        cmd.append("--refresh-published")
    if force:
        cmd.append("--force")
    return cmd


def build_generate_moment_command(
    repo_root: Path,
    source_dir: Path,
    scope: Dict[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_work_pages.py"),
        "--internal-json-source-run",
        "--source-dir",
        str(source_dir),
        "--only",
        "moments",
        "--moment-ids",
        ",".join(scope["moment_ids"]),
    ]
    if write:
        cmd.append("--write")
    if refresh_published:
        cmd.append("--refresh-published")
    if force:
        cmd.append("--force")
    return cmd


def build_search_command(repo_root: Path, *, write: bool, force: bool, env: Dict[str, str] | None = None) -> list[str]:
    bundle_bin = resolve_bundle_bin(env)
    cmd = [
        bundle_bin,
        "exec",
        "ruby",
        str(repo_root / "scripts" / "build_search.rb"),
        "--scope",
        "catalogue",
    ]
    if write:
        cmd.append("--write")
    if force:
        cmd.append("--force")
    return cmd


def run_scoped_build_scope(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    env = os.environ.copy()
    scope_kind = str(scope.get("kind") or "work").strip().lower()
    refresh_published = True
    effective_force = bool(force)
    media_step = execute_local_media_plan(repo_root, scope=scope, write=write, env=env)
    if scope_kind == "moment":
        commands = [
            (
                "Generate Moment Pages",
                build_generate_moment_command(
                    repo_root,
                    repo_root / DEFAULT_SOURCE_DIR,
                    scope,
                    write=write,
                    force=effective_force,
                    refresh_published=refresh_published,
                ),
            ),
            ("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=effective_force, env=env)),
        ]
    else:
        commands = [
            (
                "Generate Work Pages",
                build_generate_command(
                    repo_root,
                    Path(scope["source_dir"]),
                    scope,
                    write=write,
                    force=effective_force,
                    refresh_published=refresh_published,
                ),
            ),
            ("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=effective_force, env=env)),
        ]
    steps: list[Dict[str, Any]] = []
    status = "completed"
    failed_step = ""
    failure_message = ""

    steps.append(
        {
            "label": media_step.get("label", "Generate Local Media Derivatives"),
            "command": [],
            "exit_code": int(media_step.get("exit_code", 0)),
            "stdout_tail": str(media_step.get("stdout_tail") or media_step.get("summary") or "").strip(),
            "stderr_tail": str(media_step.get("stderr_tail") or "").strip(),
            "status": str(media_step.get("status") or "completed"),
        }
    )
    if media_step.get("status") == "failed":
        status = "failed"
        failed_step = str(media_step.get("label") or "Generate Local Media Derivatives")
        failure_message = str(media_step.get("stderr_tail") or media_step.get("summary") or "Local media generation failed.")

    if status != "failed":
        for label, cmd in commands:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_root),
                env=env,
                text=True,
                capture_output=True,
            )
            steps.append(
                {
                    "label": label,
                    "command": cmd,
                    "exit_code": proc.returncode,
                    "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-8:]) if proc.stdout else "",
                    "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-8:]) if proc.stderr else "",
                }
            )
            if proc.returncode != 0:
                status = "failed"
                failed_step = label
                failure_message = proc.stderr.strip() or proc.stdout.strip() or f"{label} failed with exit code {proc.returncode}"
                break

    response: Dict[str, Any] = {
        "scope": scope,
        "status": status,
        "write": bool(write),
        "force": effective_force,
        "refresh_published": refresh_published,
        "steps": steps,
        "media": {
            "generated": media_step.get("generated", {"work": [], "work_details": [], "moment": []}),
            "current": media_step.get("current", {"work": [], "work_details": [], "moment": []}),
            "blocked": media_step.get("blocked", {"work": [], "work_details": [], "moment": []}),
            "status": media_step.get("status", "completed"),
            "summary": media_step.get("summary", ""),
        },
    }
    if failed_step:
        response["failed_step"] = failed_step
        response["error"] = failure_message

    if write and log_activity:
        if scope_kind == "moment":
            append_build_activity(
                repo_root,
                build_activity_entry_for_scoped_moment_build(
                    time_utc=utc_now(),
                    status=status,
                    moment_ids=scope.get("moment_ids", []),
                    generated_moment_ids=(response.get("media") or {}).get("generated", {}).get("moment", []),
                    failed_step=failed_step,
                    force=effective_force,
                    refresh_published=refresh_published,
                ),
            )
        else:
            append_build_activity(
                repo_root,
                build_activity_entry_for_scoped_json_build(
                    time_utc=utc_now(),
                    status=status,
                    work_ids=scope["work_ids"],
                    series_ids=scope["series_ids"],
                    generated_work_ids=(response.get("media") or {}).get("generated", {}).get("work", []),
                    generated_detail_uids=(response.get("media") or {}).get("generated", {}).get("work_details", []),
                    failed_step=failed_step,
                    force=effective_force,
                    refresh_published=refresh_published,
                ),
            )
    return response


def run_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    detail_uid: str = "",
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    scope = build_scope_for_work(source_dir, work_id, extra_series_ids=extra_series_ids, detail_uid=detail_uid)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, log_activity=log_activity)


def run_series_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    scope = build_scope_for_series(source_dir, series_id, extra_work_ids=extra_work_ids)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, log_activity=log_activity)


def run_moment_scoped_build(
    repo_root: Path,
    *,
    moment_file: str,
    metadata: Dict[str, Any] | None = None,
    write: bool,
    force: bool = False,
    log_activity: bool = True,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    scope = build_scope_for_moment(repo_root, moment_file, metadata=metadata, force=force, env=env)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, log_activity=log_activity)


def build_activity_entry_for_scoped_json_build(
    *,
    time_utc: str,
    status: str,
    work_ids: Sequence[str],
    series_ids: Sequence[str],
    generated_work_ids: Sequence[str] = (),
    generated_detail_uids: Sequence[str] = (),
    failed_step: str = "",
    force: bool = False,
    refresh_published: bool = False,
) -> Dict[str, Any]:
    work_ids_list = list(work_ids)
    series_ids_list = list(series_ids)
    generated_work_ids_list = sorted(str(value) for value in generated_work_ids if str(value).strip())
    generated_detail_uids_list = sorted(str(value) for value in generated_detail_uids if str(value).strip())
    media_generated_count = len(generated_work_ids_list) + len(generated_detail_uids_list)
    summary = (
        f"Scoped JSON build updated {len(work_ids_list)} work records, {len(series_ids_list)} series, rebuilt catalogue search, and generated local media for {media_generated_count} record(s)."
        if status == "completed"
        else f"Scoped JSON build failed for {len(work_ids_list)} work records."
    )
    return {
        "id": f"{time_utc}-build_catalogue_json-{work_ids_list[0] if work_ids_list else 'none'}",
        "time_utc": time_utc,
        "script": "build_catalogue_json",
        "status": status,
        "dry_run": False,
        "planner_mode": "json-source-scoped",
        "summary": summary,
        "changes": {
            "source": {
                "works": sorted(work_ids_list),
                "series": sorted(series_ids_list),
                "work_details": [],
            },
            "workbook": {
                "works": [],
                "series": [],
                "work_details": [],
                "moments": [],
            },
            "media": {
                "work": generated_work_ids_list,
                "work_details": generated_detail_uids_list,
                "moment": [],
            },
        },
        "actions": {
            "generate_work_ids": len(work_ids_list),
            "generate_series_ids": len(series_ids_list),
            "generate_local_media": media_generated_count > 0,
            "rebuild_search": True,
            "force_generate": bool(force),
            "refresh_published": bool(refresh_published),
        },
        "results": {
            "source_mode": "json",
            "work_ids": sorted(work_ids_list),
            "generated_work_media_ids": generated_work_ids_list,
            "generated_detail_media_ids": generated_detail_uids_list,
            "failed_step": failed_step,
        },
    }


def build_activity_entry_for_scoped_moment_build(
    *,
    time_utc: str,
    status: str,
    moment_ids: Sequence[str],
    generated_moment_ids: Sequence[str] = (),
    failed_step: str = "",
    force: bool = False,
    refresh_published: bool = False,
) -> Dict[str, Any]:
    moment_ids_list = sorted(str(moment_id) for moment_id in moment_ids if str(moment_id).strip())
    generated_moment_ids_list = sorted(str(moment_id) for moment_id in generated_moment_ids if str(moment_id).strip())
    summary = (
        f"Scoped moment build updated {len(moment_ids_list)} moment records, rebuilt catalogue search, and generated local media for {len(generated_moment_ids_list)} moment record(s)."
        if status == "completed"
        else f"Scoped moment build failed for {len(moment_ids_list)} moment records."
    )
    first_id = moment_ids_list[0] if moment_ids_list else "none"
    return {
        "id": f"{time_utc}-build_catalogue_moment-{first_id}",
        "time_utc": time_utc,
        "script": "build_catalogue_moment",
        "status": status,
        "dry_run": False,
        "planner_mode": "moment-source-scoped",
        "summary": summary,
        "changes": {
            "source": {
                "works": [],
                "series": [],
                "work_details": [],
                "moments": moment_ids_list,
            },
            "workbook": {
                "works": [],
                "series": [],
                "work_details": [],
                "moments": [],
            },
            "media": {
                "work": [],
                "work_details": [],
                "moment": generated_moment_ids_list,
            },
        },
        "actions": {
            "generate_moment_ids": len(moment_ids_list),
            "generate_local_media": bool(generated_moment_ids_list),
            "rebuild_search": True,
            "force_generate": bool(force),
            "refresh_published": bool(refresh_published),
        },
        "results": {
            "source_mode": "moment-source",
            "moment_ids": moment_ids_list,
            "generated_moment_media_ids": generated_moment_ids_list,
            "failed_step": failed_step,
        },
    }


def print_preview(scope: Dict[str, Any], repo_root: Path, source_dir: Path, *, force: bool) -> None:
    print(scope["summary"])
    print(f"Source mode: {scope['source_mode']}")
    if scope.get("kind") == "moment":
        print(f"Moment IDs: {', '.join(scope['moment_ids']) if scope['moment_ids'] else 'none'}")
        print(f"Moment file: {scope.get('moment_file') or 'none'}")
    else:
        print(f"Work IDs: {', '.join(scope['work_ids']) if scope['work_ids'] else 'none'}")
        print(f"Series IDs: {', '.join(scope['series_ids']) if scope['series_ids'] else 'none'}")
    print("Published refresh: yes")
    print(f"Search rebuild: {'yes' if scope['rebuild_search'] else 'no'}")
    media_plan = build_local_media_plan(repo_root, scope=scope)
    media_counts = media_plan.get("counts", {})
    print(
        "Local media: "
        f"pending {int(media_counts.get('pending', 0))}, "
        f"current {int(media_counts.get('current', 0))}, "
        f"blocked {int(media_counts.get('blocked', 0))}, "
        f"unavailable {int(media_counts.get('unavailable', 0))}"
    )
    print("Commands:")
    commands = (
        [
            build_generate_moment_command(
                repo_root,
                repo_root / DEFAULT_SOURCE_DIR,
                scope,
                write=False,
                force=bool(force),
                refresh_published=True,
            ),
            build_search_command(repo_root, write=False, force=bool(force)),
        ]
        if scope.get("kind") == "moment"
        else [
            build_generate_command(repo_root, source_dir, scope, write=False, force=force, refresh_published=True),
            build_search_command(repo_root, write=False, force=force),
        ]
    )
    for cmd in commands:
        print("  + " + " ".join(cmd))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scoped JSON-source catalogue build helper.")
    parser.add_argument("--work-id", default="", help="Target work_id")
    parser.add_argument("--series-id", default="", help="Target series_id")
    parser.add_argument("--moment-file", default="", help="Target moment markdown filename, for example keys.md")
    parser.add_argument("--extra-series-ids", default="", help="Additional series ids to include")
    parser.add_argument("--extra-work-ids", default="", help="Additional work ids to include for a series scope")
    parser.add_argument("--repo-root", default="", help="Repo root (auto-detected when omitted)")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Canonical JSON source dir")
    parser.add_argument("--write", action="store_true", help="Run generation and search rebuild")
    parser.add_argument("--force", action="store_true", help="Force generation and search rewrites even when content versions match")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else detect_repo_root()
    source_dir = (repo_root / args.source_dir).resolve()
    work_id = str(args.work_id or "").strip()
    series_id = str(args.series_id or "").strip()
    moment_file = str(args.moment_file or "").strip()
    if sum(1 for value in (work_id, series_id, moment_file) if value) != 1:
        raise SystemExit("Pass exactly one of --work-id, --series-id, or --moment-file.")
    if moment_file:
        scope = build_scope_for_moment(repo_root, moment_file, force=args.force)
    elif series_id:
        scope = build_scope_for_series(source_dir, series_id, extra_work_ids=args.extra_work_ids.split(","))
    else:
        scope = build_scope_for_work(source_dir, work_id, extra_series_ids=args.extra_series_ids.split(","))
    if not args.write:
        print_preview(scope, repo_root, source_dir, force=args.force)
        return

    result = (
        run_moment_scoped_build(
            repo_root,
            moment_file=moment_file,
            write=True,
            force=args.force,
            log_activity=True,
        )
        if moment_file
        else run_series_scoped_build(
            repo_root,
            source_dir=source_dir,
            series_id=series_id,
            extra_work_ids=args.extra_work_ids.split(","),
            write=True,
            force=args.force,
            log_activity=True,
        )
        if series_id
        else run_scoped_build(
            repo_root,
            source_dir=source_dir,
            work_id=work_id,
            extra_series_ids=args.extra_series_ids.split(","),
            write=True,
            force=args.force,
            log_activity=True,
        )
    )
    if result["status"] != "completed":
        raise SystemExit(str(result.get("error") or "Scoped JSON build failed."))
    print(scope["summary"])


if __name__ == "__main__":
    main()
