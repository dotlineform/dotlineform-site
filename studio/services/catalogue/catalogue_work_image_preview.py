"""Inspect one selected Work source and return a disposable in-memory preview."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping

from catalogue.catalogue_build_media import PIPELINE_CONFIG, read_image_dims_px
from catalogue.catalogue_media_files import IMAGE_EXTENSIONS
from catalogue_work_media_sources import resolve_work_media_path, resolve_work_media_source_root
from local_env import runtime_env


def prepare_work_image_preview(repo_root: Path, body: Mapping[str, Any]) -> tuple[bytes, int, int]:
    """Read only the confined selected original; create no files or retained state."""
    fields = {"media_source_id", "project_folder", "project_subfolder", "project_filename"}
    if set(body) - fields:
        raise ValueError("Unsupported Work image preview fields")
    for field in fields:
        value = body.get(field, "")
        if not isinstance(value, str) or (field != "project_subfolder" and not value):
            raise ValueError(f"{field} must be a source identity or path component")
    source = resolve_work_media_source_root(
        PIPELINE_CONFIG, body["media_source_id"], environ=runtime_env(repo_root=repo_root),
        require_exists=True,
    )
    path = resolve_work_media_path(
        source, body["project_folder"], body.get("project_subfolder", ""), body["project_filename"],
        require_exists=True,
    )
    if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError("Select a supported Work source image")
    width, height = read_image_dims_px(path)
    if width is None or height is None or width < 1 or height < 1:
        raise ValueError("Selected source image dimensions are unavailable")
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(path),
                "-map", "0:v:0", "-frames:v", "1", "-map_metadata", "-1",
                "-vf", "scale=w='min(iw,512)':h='min(ih,512)':force_original_aspect_ratio=decrease:flags=bilinear",
                "-c:v", "libwebp", "-preset", "photo", "-q:v", "75", "-compression_level", "1",
                "-f", "webp", "pipe:1",
            ],
            capture_output=True, check=False,
        )
    except OSError as error:
        raise RuntimeError("Could not start Work image preview conversion") from error
    if proc.returncode or not proc.stdout:
        raise RuntimeError(f"Work image preview conversion failed: {proc.stderr.decode('utf-8', errors='replace').strip()}")
    return proc.stdout, width, height
