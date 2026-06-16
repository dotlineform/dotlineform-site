"""Catalogue scoped-build media planning and readiness helpers."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Sequence

from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, records_from_json_source, slug_id
from catalogue import catalogue_public_paths as public_paths
from catalogue.moment_sources import (
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    build_moment_metadata_entry,
    load_moment_metadata_records,
    normalize_moment_filename,
)
from pipeline_config import (
    env_var_name,
    env_var_value,
    load_pipeline_config,
    source_moments_images_subdir,
    source_works_root_subdir,
)


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")
CATALOGUE_PROSE_STAGING_REL_DIR = Path("var/docs/catalogue/import-staging")
MOMENT_PROSE_STAGING_REL_DIR = CATALOGUE_PROSE_STAGING_REL_DIR / "moments"
CATALOGUE_MEDIA_STAGING_REL_DIR = Path("var/catalogue/media")

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

MediaPlanBuilder = Callable[..., Dict[str, Any]]
FfmpegRunner = Callable[[Path, int, Path], tuple[int, str]]


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "site-tools" / "config" / "site-tools.json").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def detect_projects_base_dir(env: Dict[str, str] | None = None) -> Path:
    value = env_var_value(PIPELINE_CONFIG, "projects_base_dir", env)
    if not value:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} is required in var/local/site.env for moment source builds.")
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


def parse_sips_pixel_dims(output: str) -> tuple[int | None, int | None]:
    width = None
    height = None
    for line in output.splitlines():
        width_match = re.search(r"pixelWidth:\s*([0-9]+)", line)
        if width_match:
            width = int(width_match.group(1))
        height_match = re.search(r"pixelHeight:\s*([0-9]+)", line)
        if height_match:
            height = int(height_match.group(1))
    return width, height


def read_image_dims_px(path: Path | None) -> tuple[int | None, int | None]:
    if path is None or not path.exists() or shutil.which("sips") is None:
        return None, None
    proc = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None, None
    return parse_sips_pixel_dims(proc.stdout)


def repo_relative_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve())).replace(os.sep, "/")
    except ValueError:
        return str(path.resolve())


def resolve_work_media_source(
    records: Any,
    work_id: str,
    *,
    env: Dict[str, str] | None = None,
    record_override: Mapping[str, Any] | None = None,
) -> tuple[Path | None, str, Path | None, str]:
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    work_record = dict(record_override) if record_override is not None else records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    works_root = (projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)) if projects_base_dir else None
    project_folder = str(work_record.get("project_folder") or "").strip()
    project_subfolder = str(work_record.get("project_subfolder") or "").strip()
    project_filename = normalize_filename(work_record.get("project_filename"))
    if project_folder and project_filename and works_root is not None:
        media_path = works_root / project_folder
        if project_subfolder:
            media_path = media_path / project_subfolder
        return media_path / project_filename, "", projects_base_dir, availability_error
    if project_filename:
        return None, "missing_project_folder", projects_base_dir, availability_error
    return None, "missing_project_filename", projects_base_dir, availability_error


def resolve_detail_media_source(
    records: Any,
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
    section_id = str(detail_record.get("section_id") or "").strip()
    section_record = records.work_detail_sections.get(section_id) if hasattr(records, "work_detail_sections") else {}
    details_subfolder = str(
        (section_record or {}).get("details_subfolder")
        or detail_record.get("details_subfolder")
        or detail_record.get("project_subfolder")
        or ""
    ).strip()
    project_filename = normalize_filename(detail_record.get("project_filename"))
    if not project_filename:
        return None, "missing_project_filename", projects_base_dir, availability_error
    if not project_folder:
        return None, "missing_project_folder", projects_base_dir, availability_error
    if works_root is None:
        return None, "", projects_base_dir, availability_error
    media_path = works_root / project_folder
    if details_subfolder:
        media_path = media_path / details_subfolder
    return media_path / project_filename, "", projects_base_dir, availability_error


def thumb_output_dir(repo_root: Path, kind: str) -> Path:
    return repo_root / public_paths.thumb_output_dir(kind)


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


def thumb_output_paths_for_kind(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    if kind == "moment":
        root = repo_root / public_paths.thumb_output_dir(kind)
        return [root / f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]
    return thumb_output_paths(repo_root, kind, item_id)


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
    force: bool = False,
) -> Dict[str, Any]:
    staged_source_path = media_staging_input_path(repo_root, kind, item_id, source_path)
    staged_thumb_paths = staged_thumb_output_paths(repo_root, kind, item_id)
    staged_primary_paths = staged_primary_output_paths(repo_root, kind, item_id)
    asset_thumb_paths = thumb_output_paths_for_kind(repo_root, kind, item_id)
    output_paths = [*staged_primary_paths, *asset_thumb_paths]
    state = local_media_state(source_path, output_paths, staged_source_path)
    force_refresh = bool(force and source_path is not None and source_path.exists())
    if force_refresh and state == "current":
        state = "pending"
    source_width_px, source_height_px = read_image_dims_px(source_path)
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
    if source_width_px is not None and source_height_px is not None:
        task["source_width_px"] = source_width_px
        task["source_height_px"] = source_height_px
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
        task["pending_staged_source"] = force_refresh or path_needs_refresh(staged_source_path, source_mtime)
        pending_thumb_outputs: list[Dict[str, Any]] = []
        pending_primary_outputs: list[Dict[str, Any]] = []
        pending_asset_thumbs: list[Dict[str, Any]] = []
        for size, path, asset_path in zip(THUMB_SIZES, staged_thumb_paths, asset_thumb_paths):
            if force_refresh or path_needs_refresh(asset_path, source_mtime):
                pending_thumb_outputs.append(
                    {
                        "variant": "thumb",
                        "size": size,
                        "path": repo_relative_path(path, repo_root),
                        "absolute_path": str(path.resolve()),
                    }
                )
        for width, path in zip(PRIMARY_WIDTHS, staged_primary_paths):
            if force_refresh or path_needs_refresh(path, source_mtime):
                pending_primary_outputs.append(
                    {
                        "variant": "primary",
                        "width": width,
                        "path": repo_relative_path(path, repo_root),
                        "absolute_path": str(path.resolve()),
                    }
                )
        for size, path, staged_path in zip(THUMB_SIZES, asset_thumb_paths, staged_thumb_paths):
            if force_refresh or path_needs_refresh(path, source_mtime):
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
    force: bool = False,
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
                    force=force,
                )
            )
    else:
        source_dir = Path(str(scope.get("source_dir") or "")).expanduser() if scope.get("source_dir") else None
        records = records_from_json_source(source_dir) if source_dir is not None else None
        if records is None:
            return {"tasks": [], "counts": {"pending": 0, "current": 0, "blocked": 0, "unavailable": 0}}
        work_media_sources = scope.get("work_media_sources") if isinstance(scope.get("work_media_sources"), dict) else {}
        for work_id in scope.get("work_ids", []):
            normalized_work_id = str(work_id)
            record_override = work_media_sources.get(normalized_work_id) if isinstance(work_media_sources.get(normalized_work_id), dict) else None
            source_path, missing_reason, projects_base_dir, availability_error = resolve_work_media_source(
                records,
                normalized_work_id,
                env=env,
                record_override=record_override,
            )
            tasks.append(
                build_local_media_task(
                    repo_root=repo_root,
                    kind="work",
                    item_id=normalized_work_id,
                    source_path=source_path,
                    availability_error=availability_error,
                    blocked_reason=missing_reason,
                    projects_base_dir=projects_base_dir,
                    force=force,
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
                    force=force,
                )
            )
    counts = {
        "pending": sum(1 for task in tasks if task.get("status") == "pending"),
        "current": sum(1 for task in tasks if task.get("status") == "current"),
        "blocked": sum(1 for task in tasks if task.get("status") == "blocked"),
        "unavailable": sum(1 for task in tasks if task.get("status") == "unavailable"),
    }
    return {"tasks": tasks, "counts": counts}


def thumbnail_skip_reason_text(reason: str) -> str:
    mapping = {
        "missing_project_folder": "project folder is missing",
        "missing_project_filename": "project filename is missing",
        "missing_file": "configured source media file is missing",
    }
    return mapping.get(reason, reason or "source media is not available")


def build_thumbnail_only_task(
    *,
    repo_root: Path,
    kind: str,
    item_id: str,
    source_path: Path | None,
    availability_error: str = "",
    missing_reason: str = "",
    projects_base_dir: Path | None = None,
    force: bool = False,
) -> Dict[str, Any]:
    output_paths = thumb_output_paths_for_kind(repo_root, kind, item_id)
    task: Dict[str, Any] = {
        "kind": kind,
        "id": item_id,
        "source_path": display_source_path(source_path, projects_base_dir),
        "source_abs_path": str(source_path.resolve()) if source_path is not None else "",
        "output_paths": [repo_relative_path(path, repo_root) for path in output_paths],
        "pending_outputs": [],
        "status": "current",
    }
    if availability_error:
        task["status"] = "skipped"
        task["reason"] = availability_error
        return task
    if missing_reason:
        task["status"] = "skipped"
        task["reason"] = thumbnail_skip_reason_text(missing_reason)
        return task
    if source_path is None or not source_path.exists():
        task["status"] = "skipped"
        task["reason"] = thumbnail_skip_reason_text("missing_file")
        return task

    source_mtime = source_path.stat().st_mtime
    pending_outputs: list[Dict[str, Any]] = []
    for size, path in zip(THUMB_SIZES, output_paths):
        if force or path_needs_refresh(path, source_mtime):
            pending_outputs.append(
                {
                    "size": size,
                    "path": repo_relative_path(path, repo_root),
                    "absolute_path": str(path.resolve()),
                }
            )
    if pending_outputs:
        task["status"] = "pending"
        task["pending_outputs"] = pending_outputs
    return task


def build_catalogue_thumbnail_only_plan(
    repo_root: Path,
    *,
    source_dir: Path,
    env: Dict[str, str] | None = None,
    force: bool = False,
) -> Dict[str, Any]:
    records = records_from_json_source(source_dir)
    tasks: list[Dict[str, Any]] = []
    for work_id in sorted(records.works):
        source_path, missing_reason, projects_base_dir, availability_error = resolve_work_media_source(records, work_id, env=env)
        tasks.append(
            build_thumbnail_only_task(
                repo_root=repo_root,
                kind="work",
                item_id=work_id,
                source_path=source_path,
                availability_error=availability_error,
                missing_reason=missing_reason,
                projects_base_dir=projects_base_dir,
                force=force,
            )
        )
    for detail_uid in sorted(records.work_details):
        source_path, missing_reason, projects_base_dir, availability_error = resolve_detail_media_source(records, detail_uid, env=env)
        tasks.append(
            build_thumbnail_only_task(
                repo_root=repo_root,
                kind="work_details",
                item_id=detail_uid,
                source_path=source_path,
                availability_error=availability_error,
                missing_reason=missing_reason,
                projects_base_dir=projects_base_dir,
                force=force,
            )
        )
    moment_records = load_moment_metadata_records(source_dir)
    for moment_id in sorted(moment_records):
        source_path: Path | None
        missing_reason: str
        projects_base_dir: Path | None
        availability_error: str
        _, source_path, missing_reason, projects_base_dir, availability_error = resolve_moment_media_source(
            repo_root,
            f"{moment_id}.md",
            metadata=moment_records[moment_id],
            env=env,
        )
        tasks.append(
            build_thumbnail_only_task(
                repo_root=repo_root,
                kind="moment",
                item_id=moment_id,
                source_path=source_path,
                availability_error=availability_error,
                missing_reason=missing_reason,
                projects_base_dir=projects_base_dir,
                force=force,
            )
        )
    counts = {
        "pending": sum(1 for task in tasks if task.get("status") == "pending"),
        "current": sum(1 for task in tasks if task.get("status") == "current"),
        "skipped": sum(1 for task in tasks if task.get("status") == "skipped"),
    }
    return {"tasks": tasks, "counts": counts}


def execute_catalogue_thumbnail_only_plan(
    repo_root: Path,
    *,
    source_dir: Path,
    write: bool,
    env: Dict[str, str] | None = None,
    force: bool = False,
    plan_builder: MediaPlanBuilder | None = None,
    thumb_runner: FfmpegRunner | None = None,
) -> Dict[str, Any]:
    using_default_runner = thumb_runner is None
    build_plan = plan_builder or build_catalogue_thumbnail_only_plan
    run_thumb = thumb_runner or run_ffmpeg_thumb
    plan = build_plan(repo_root, source_dir=source_dir, env=env, force=force)
    tasks = plan["tasks"]
    pending_tasks = [task for task in tasks if task.get("status") == "pending"]
    if write and pending_tasks and using_default_runner and shutil.which("ffmpeg") is None:
        return {
            "label": "Regenerate Catalogue Thumbnails",
            "status": "failed",
            "summary": "ffmpeg is required for thumbnail regeneration.",
            "generated": {"work": [], "work_details": [], "moment": []},
            "planned": {"work": [], "work_details": [], "moment": []},
            "current": {"work": [], "work_details": [], "moment": []},
            "skipped": {"work": [], "work_details": [], "moment": []},
            "exit_code": 1,
            "stderr_tail": "ffmpeg not found on PATH",
        }

    generated: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    planned: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    current: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    skipped: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
    messages: list[str] = []

    for task in tasks:
        kind = str(task.get("kind") or "")
        item_id = str(task.get("id") or "")
        status = str(task.get("status") or "")
        if kind not in generated:
            continue
        if status == "current":
            current[kind].append(item_id)
            continue
        if status == "skipped":
            skipped[kind].append(item_id)
            reason = str(task.get("reason") or "").strip()
            messages.append(f"{kind} {item_id}: {reason}" if reason else f"{kind} {item_id}: skipped")
            continue
        if status != "pending":
            continue
        if not write:
            planned[kind].append(item_id)
            continue
        source_path = Path(str(task.get("source_abs_path") or "")).resolve()
        pending_outputs = task.get("pending_outputs") if isinstance(task.get("pending_outputs"), list) else []
        for output_spec in pending_outputs:
            output_path = Path(str(output_spec.get("absolute_path") or "")).resolve()
            size = int(output_spec.get("size") or THUMB_SIZES[0])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            exit_code, stderr_tail = run_thumb(source_path, size, output_path)
            if exit_code != 0:
                return {
                    "label": "Regenerate Catalogue Thumbnails",
                    "status": "failed",
                    "summary": f"Thumbnail regeneration failed for {kind} {item_id}.",
                    "generated": generated,
                    "planned": planned,
                    "current": current,
                    "skipped": skipped,
                    "exit_code": exit_code,
                    "stderr_tail": stderr_tail,
                }
        generated[kind].append(item_id)

    summary_parts: list[str] = []
    generated_total = sum(len(values) for values in generated.values())
    planned_total = sum(len(values) for values in planned.values())
    current_total = sum(len(values) for values in current.values())
    skipped_total = sum(len(values) for values in skipped.values())
    if generated_total:
        summary_parts.append(f"generated thumbnails for {generated_total} record(s)")
    if planned_total:
        summary_parts.append(f"would generate thumbnails for {planned_total} record(s)")
    if current_total:
        summary_parts.append(f"{current_total} already current")
    if skipped_total:
        summary_parts.append(f"{skipped_total} skipped")
    summary = "; ".join(summary_parts) if summary_parts else "No thumbnail changes needed."
    if messages:
        summary = f"{summary} {'; '.join(messages[:3])}".strip()
    return {
        "label": "Regenerate Catalogue Thumbnails",
        "status": "completed",
        "summary": summary,
        "generated": generated,
        "planned": planned,
        "current": current,
        "skipped": skipped,
        "exit_code": 0,
        "stdout_tail": summary,
    }


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
    force: bool = False,
    plan_builder: MediaPlanBuilder | None = None,
    thumb_runner: FfmpegRunner | None = None,
    primary_runner: FfmpegRunner | None = None,
) -> Dict[str, Any]:
    using_default_thumb_runner = thumb_runner is None
    using_default_primary_runner = primary_runner is None
    build_plan = plan_builder or build_local_media_plan
    run_thumb = thumb_runner or run_ffmpeg_thumb
    run_primary = primary_runner or run_ffmpeg_primary
    plan = build_plan(repo_root, scope=scope, env=env, force=force)
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
    if write and pending_tasks and (using_default_thumb_runner or using_default_primary_runner) and shutil.which("ffmpeg") is None:
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
    cleaned_staged_thumbs: Dict[str, list[str]] = {"work": [], "work_details": [], "moment": []}
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
            exit_code, stderr_tail = run_thumb(staged_source, size, output_path)
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
            exit_code, stderr_tail = run_primary(staged_source, width, output_path)
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
            try:
                staged_thumb.unlink()
                cleaned_staged_thumbs[kind].append(repo_relative_path(staged_thumb, repo_root))
            except OSError as exc:
                staged_thumb_display = repo_relative_path(staged_thumb, repo_root)
                messages.append(f"{kind} {item_id}: could not remove staged thumbnail {staged_thumb_display}: {exc}")
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
        "cleaned_staged_thumbs": cleaned_staged_thumbs,
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


def build_work_readiness(records: Any, work_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    repo_root = detect_repo_root()
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    work_record = records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    media_path, media_missing_reason, _, _ = resolve_work_media_source(records, work_id, env=env)
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
    ]
    return {"items": items}


def build_series_readiness(records: Any, series_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    repo_root = detect_repo_root()
    series_record = records.series.get(series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")

    return {"items": []}


def build_detail_readiness(records: Any, detail_uid: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
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


def build_moment_readiness(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    filename = normalize_moment_filename(moment_file)
    moment_id = filename[:-3]
    _resolved_id, media_path, media_missing_reason, projects_base_dir, availability_error = resolve_moment_media_source(
        repo_root,
        filename,
        metadata=metadata,
        env=env,
    )
    prose_path = repo_root / MOMENT_PROSE_STAGING_REL_DIR / filename

    items = [
        build_media_readiness_item(
            repo_root=repo_root,
            kind="moment",
            item_id=moment_id,
            key="moment_media",
            title="moment media",
            source_path=media_path,
            missing_reason=media_missing_reason,
            projects_base_dir=projects_base_dir,
            availability_error=availability_error,
        ),
        build_readiness_item(
            key="moment_prose",
            title="moment prose",
            path=prose_path,
            projects_base_dir=repo_root,
            ready_summary=f"Staged prose is ready at {display_source_path(prose_path, repo_root)}.",
            missing_file_summary=f"No staged prose file exists at {display_source_path(prose_path, repo_root)}.",
            next_step_ready="Use Import staged prose to write the permanent source file.",
            next_step_missing_file="Add staged Markdown at the expected ID-based path before importing prose.",
            action={
                "kind": "prose-import",
                "target_kind": "moment",
                "moment_id": moment_id,
                "label": "Import staged prose",
            },
        ),
    ]
    return {"items": items}
