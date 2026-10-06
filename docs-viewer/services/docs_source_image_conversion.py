"""Docs-owned conversion of native static raster uploads to display WebP."""

from __future__ import annotations

from pathlib import Path
import subprocess


DISPLAY_LONG_EDGE = 800
DISPLAY_QUALITY = 82
WEBP_PRESET = "photo"
WEBP_COMPRESSION_LEVEL = 6
RASTER_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def _validate_static_raster(source_path: Path) -> None:
    """Inspect raster format/frame count before FFmpeg decodes and converts pixels."""
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Docs image conversion requires Pillow; install requirements.txt") from error
    try:
        with Image.open(source_path) as image:
            if image.format not in RASTER_FORMATS:
                raise ValueError("Select a JPEG, PNG, static WebP or single-frame GIF image")
            if getattr(image, "n_frames", 1) != 1:
                raise ValueError("Animated images are not supported; select a static image")
    except (OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError("Selected raster image could not be read") from error


def convert_source_image_to_webp(source_path: Path, output_path: Path) -> None:
    """Prepare one proportional 800px-long-edge image, including small-input upscaling.

    Encoding starts with the Works primary recipe but is owned independently by
    Docs Viewer. The operation writes only its temporary output, never the input.
    """
    _validate_static_raster(source_path)
    scale = (
        f"scale='if(gte(iw,ih),{DISPLAY_LONG_EDGE},-1)':"
        f"'if(gte(iw,ih),-1,{DISPLAY_LONG_EDGE})':flags=lanczos"
    )
    try:
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(source_path), "-map_metadata", "-1", "-vf", scale,
            "-frames:v", "1", "-c:v", "libwebp", "-preset", WEBP_PRESET,
            "-q:v", str(DISPLAY_QUALITY), "-compression_level", str(WEBP_COMPRESSION_LEVEL),
            str(output_path),
        ], capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        raise RuntimeError("Docs image conversion requires FFmpeg") from error
    if result.returncode != 0:
        raise RuntimeError("FFmpeg display-image conversion failed: " + result.stderr.strip())
    if not output_path.is_file() or not output_path.stat().st_size:
        raise RuntimeError("FFmpeg display-image conversion produced no image")
