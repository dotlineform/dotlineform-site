"""Document image naming and the bounded Docs-owned thumbnail operation."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping

from docs_artifact_locations import artifact_location_adapter
from docs_document_identity import is_document_id
from docs_import_common import RASTER_IMAGE_STAGED_SUFFIXES, slugify
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, managed_media_config


def has_document_thumbnail(metadata: Mapping[str, Any], *, collection: str = "") -> bool:
    """Read the optional canonical assignment; Catalogue owns its Work thumbnails."""
    if "thumbnail" not in metadata:
        return False
    if collection == "catalogue" or not isinstance(metadata["thumbnail"], bool):
        raise ValueError("thumbnail must be a boolean on an authored document")
    return metadata["thumbnail"]


def document_thumbnail_filename(doc_id: str, *, collection: str = "") -> str:
    """Derive an authored document's immutable thumbnail identity within its owner."""
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


def next_document_image_filename(
    repo_root: Path, config: DocsStageConfig | DocsCollectionConfig,
    *, title: str, doc_id: str, suffix: str, media_type: str = "img",
) -> str:
    """Allocate a title/ID basename with numbered suffixes for additional images.

    Existing media is retained. The caller carries this identity through the
    synchronous insertion; titles are never used to rename earlier images.
    """
    collection = getattr(config, "collection", "")
    if collection == "catalogue" or not is_document_id(doc_id, collection=collection):
        raise ValueError("image naming requires an exact authored document identity")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("image naming requires a document title")
    if suffix.lower() not in RASTER_IMAGE_STAGED_SUFFIXES | {".svg", ".mmd"}:
        raise ValueError("image naming requires a supported extension")
    media = managed_media_config(config, "svg" if media_type == "mermaid" else media_type)
    adapter = artifact_location_adapter(repo_root, media.asset_location)
    stem = f"{slugify(title)[:160].rstrip('-')}-{doc_id}"
    index = 1
    while True:
        filename = f"{stem}{'' if index == 1 else '-' + str(index)}{suffix.lower()}"
        stored_filename = Path(filename).with_suffix(".svg").name if media_type == "mermaid" else filename
        if adapter.stat(stored_filename) is None:
            return filename
        index += 1


def write_document_thumbnail(
    repo_root: Path, config: DocsStageConfig | DocsCollectionConfig,
    *, doc_id: str, source_path: Path,
) -> dict[str, Any]:
    """Generate one 96px centred WebP and immediately replace its fixed identity.

    Uses the Works recipe, including upscaling small inputs. No primary variants,
    existing-thumbnail inspection, deferred commit or rollback are performed.
    Source cancellation leaves completed media writes in place.
    """
    if source_path.suffix.lower() not in RASTER_IMAGE_STAGED_SUFFIXES:
        raise ValueError("Create thumb requires a raster image")
    filename = document_thumbnail_filename(doc_id, collection=getattr(config, "collection", ""))
    media = managed_media_config(config, "thumbs")
    with tempfile.TemporaryDirectory(prefix="docs-thumbnail-") as temporary:
        output = Path(temporary) / filename
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
        data = output.read_bytes()
    adapter = artifact_location_adapter(repo_root, media.asset_location, served_path_prefix=media.served_path_prefix)
    adapter.replace(filename, data, content_type="image/webp")
    if not adapter.verify_bytes(filename, data):
        raise RuntimeError("Thumbnail media write verification failed")
    return {"filename": filename, "size_bytes": len(data)}
