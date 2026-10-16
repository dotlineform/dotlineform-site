"""Document thumbnail assignment and the bounded Docs-owned generation operation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping

from docs_document_identity import is_document_id
from docs_import_common import RASTER_IMAGE_STAGED_SUFFIXES


def has_document_thumbnail(metadata: Mapping[str, Any], *, collection: str = "") -> bool:
    """Read the optional canonical assignment; Catalogue owns its Work thumbnails."""
    if "thumbnail" not in metadata:
        return False
    if collection == "catalogue" or not isinstance(metadata["thumbnail"], bool):
        raise ValueError("thumbnail must be a boolean on an authored document")
    return metadata["thumbnail"]


def document_thumbnail_filename(doc_id: str, *, collection: str = "") -> str:
    """Derive the one flat thumbnail identity owned by an authored document."""
    if collection == "catalogue" or not is_document_id(doc_id, collection=collection):
        raise ValueError("thumbnail requires an exact authored document identity")
    return f"{doc_id}-thumb.webp"


def generated_thumbnail_filename(payload: Mapping[str, Any], *, doc_id: str, collection: str = "") -> str:
    """Read a by-ID projection's assignment without inspecting body HTML or files."""
    if "has_thumbnail" not in payload:
        return ""
    if not isinstance(payload["has_thumbnail"], bool):
        raise ValueError("has_thumbnail must be a boolean")
    return document_thumbnail_filename(doc_id, collection=collection) if payload["has_thumbnail"] else ""


def prepare_document_thumbnail(source_path: Path) -> bytes:
    """Prepare one 96px centred WebP from an already validated static raster.

    Save owns the selected write to the document's fixed flat identity.
    """
    if source_path.suffix.lower() not in RASTER_IMAGE_STAGED_SUFFIXES:
        raise ValueError("Create thumb requires a raster image")
    with tempfile.TemporaryDirectory(prefix="docs-thumbnail-") as temporary:
        output = Path(temporary) / "thumbnail.webp"
        try:
            result = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-i", str(source_path), "-map_metadata", "-1",
                "-vf", "scale='if(gt(iw,ih),-1,96)':'if(gt(iw,ih),96,-1)':flags=lanczos,crop=96:96",
                "-frames:v", "1", "-c:v", "libwebp", "-preset", "photo",
                "-q:v", "62", "-compression_level", "6", str(output),
            ], capture_output=True, text=True, check=False)
        except FileNotFoundError as error:
            raise RuntimeError("Thumbnail generation requires FFmpeg") from error
        if result.returncode != 0:
            raise RuntimeError("FFmpeg thumbnail generation failed: " + result.stderr.strip())
        return output.read_bytes()
