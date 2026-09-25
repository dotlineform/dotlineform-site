"""Catalogue source-media resolution, derivative planning and conversion."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping

from catalogue.catalogue_output_paths import catalogue_workspace_config, output_path, thumbnail_directory
from catalogue_work_media_sources import (
    WorkMediaSourceRoot,
    resolve_work_media_path,
    resolve_work_media_source_id,
    resolve_work_media_source_root,
)
from pipeline_config import (
    env_var_name,
    env_var_value,
    load_pipeline_config,
)


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")

THUMB_SIZES = sorted({int(value) for value in PIPELINE_CONFIG["variants"]["thumb"]["sizes"]})
THUMB_SUFFIX = str(PIPELINE_CONFIG["variants"]["thumb"]["suffix"])
PRIMARY_WIDTHS = sorted({int(value) for value in PIPELINE_CONFIG["variants"]["primary"]["widths"]})
PRIMARY_SUFFIX = str(PIPELINE_CONFIG["variants"]["primary"]["suffix"])
ASSET_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
ENCODER_CODEC = str(PIPELINE_CONFIG["encoding"]["codec"])
WEBP_PRESET = str(PIPELINE_CONFIG["encoding"]["preset"])
THUMB_Q = int(PIPELINE_CONFIG["encoding"]["thumb_quality"])
PRIMARY_Q = int(PIPELINE_CONFIG["encoding"]["primary_quality"])
COMPRESSION_LEVEL = int(PIPELINE_CONFIG["encoding"]["compression_level"])



def detect_projects_base_dir(env: Dict[str, str] | None = None) -> Path:
    value = env_var_value(PIPELINE_CONFIG, "projects_base_dir", env)
    if not value:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} is required in .env.local for catalogue media builds.")
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
    if not text:
        return ""
    path = Path(text)
    if path.is_absolute() or len(path.parts) != 1 or text in {".", ".."} or "\\" in text:
        raise ValueError("project_filename must be a single safe path segment")
    return path.name


def resolve_record_work_media_root(
    record: Mapping[str, Any],
    *,
    env: Dict[str, str] | None = None,
) -> tuple[WorkMediaSourceRoot | None, Path | None, str]:
    projects_base_dir, availability_error = detect_projects_base_dir_optional(env)
    if projects_base_dir is None:
        return None, None, availability_error
    source_id = resolve_work_media_source_id(PIPELINE_CONFIG, record.get("media_source_id"))
    try:
        source_root = resolve_work_media_source_root(
            PIPELINE_CONFIG,
            source_id,
            environ={PROJECTS_BASE_DIR_ENV_NAME: str(projects_base_dir)},
            require_exists=True,
        )
    except ValueError as exc:
        return None, projects_base_dir, str(exc)
    return source_root, projects_base_dir, ""


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
    work_record = dict(record_override) if record_override is not None else records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    source_root, projects_base_dir, availability_error = resolve_record_work_media_root(work_record, env=env)
    project_folder = str(work_record.get("project_folder") or "").strip()
    project_subfolder = str(work_record.get("project_subfolder") or "").strip()
    project_filename = normalize_filename(work_record.get("project_filename"))
    if project_folder and project_filename and source_root is not None:
        try:
            media_path = resolve_work_media_path(
                source_root,
                project_folder,
                project_subfolder,
                project_filename,
            )
        except ValueError as exc:
            return None, "", projects_base_dir, str(exc)
        return media_path, "", projects_base_dir, availability_error
    if project_filename:
        return None, "missing_project_folder", projects_base_dir, availability_error
    return None, "missing_project_filename", projects_base_dir, availability_error


def thumb_output_paths(repo_root: Path, kind: str, item_id: str) -> list[Path]:
    root = thumbnail_directory(repo_root, kind)
    return [root / f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}" for size in THUMB_SIZES]


def build_local_media_task(
    *, repo_root: Path, kind: str, item_id: str, source_path: Path,
    projects_base_dir: Path, force: bool = False,
) -> Dict[str, Any]:
    """Plan one complete local rendition set; mtimes select conversion, bytes decide version."""
    if kind != "work":
        raise ValueError(f"unsupported local media kind: {kind}")
    if not source_path.is_file():
        raise ValueError(f"{item_id}: source image is unavailable")
    assets = catalogue_workspace_config(repo_root).assets
    outputs = [
        {"variant": "thumb", "size": size,
         "path": output_path(assets.work_thumbnails, f"{item_id}-{THUMB_SUFFIX}-{size}.{ASSET_FORMAT}")}
        for size in THUMB_SIZES
    ] + [
        {"variant": "primary", "size": width,
         "path": output_path(assets.work_primary, f"{item_id}-{PRIMARY_SUFFIX}-{width}.{ASSET_FORMAT}")}
        for width in PRIMARY_WIDTHS
    ]
    source_mtime = source_path.stat().st_mtime
    pending = force or any(not item["path"].is_file() or item["path"].stat().st_mtime < source_mtime for item in outputs)
    width, height = read_image_dims_px(source_path)
    if width is None or height is None or width < 1 or height < 1:
        raise ValueError(f"{item_id}: source image dimensions are unavailable")
    return {
        "kind": kind, "id": item_id, "source_path": display_source_path(source_path, projects_base_dir),
        "source_abs_path": str(source_path), "source_width_px": width, "source_height_px": height,
        "status": "pending" if pending else "current", "outputs": outputs,
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


def prepare_local_media_task(task: Mapping[str, Any], temporary_root: Path) -> tuple[dict[Path, bytes], bool]:
    """Convert into operation-owned temporary files; do not change assets or canonical data.

    Existing rendition bytes determine image change. Creating a missing rendition
    alone is repair, not a new version. The caller commits the complete set with
    its dimensions/version through the Catalogue write owner.
    """
    if task["status"] == "current":
        return {}, False
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required for local media generation")
    source = Path(task["source_abs_path"])
    prepared = {}
    changed = False
    for output in task["outputs"]:
        destination = output["path"]
        temporary = temporary_root / destination.name
        runner = run_ffmpeg_thumb if output["variant"] == "thumb" else run_ffmpeg_primary
        code, error = runner(source, output["size"], temporary)
        if code or not temporary.is_file() or not temporary.stat().st_size:
            raise RuntimeError(f"Local media generation failed for {task['id']}: {error or 'empty rendition'}")
        data = temporary.read_bytes()
        if destination.is_file() and destination.read_bytes() != data:
            changed = True
        prepared[destination] = data
    return prepared, changed
