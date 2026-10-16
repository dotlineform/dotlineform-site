"""Prepare native media identities without writes; Source Save owns processing and storage."""

from __future__ import annotations

from dataclasses import dataclass
import mimetypes
from pathlib import Path
import re
import tempfile
from typing import Any

from docs_artifact_locations import ArtifactLocationAdapter, artifact_location_adapter
from docs_document_images import document_thumbnail_filename, prepare_document_thumbnail
from docs_import_common import FILE_MEDIA_STAGED_SUFFIXES, RASTER_IMAGE_STAGED_SUFFIXES, SVG_STAGED_SUFFIXES, slugify
from docs_management_document_target import (
    ManagedDocumentTarget, managed_document_target_request, normalize_managed_document_target,
    resolve_managed_document_collection,
)
from docs_mermaid_renderer import MERMAID_TOOLCHAIN_ROOT, mermaid_toolchain_paths, render_mermaid_path
from docs_source_image_conversion import convert_source_image_to_webp, validate_static_raster
from docs_source_media_upload import MAX_MEDIA_BYTES, MAX_METADATA_BYTES, SourceMediaUpload, validate_upload_filename
from docs_svg_sanitizer import sanitize_svg_bytes
from docs_workspace_config import DocsStageConfig, DocsCollectionConfig, managed_media_config, require_document_authoring, require_document_media


TOKEN_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class SourceMediaIdentity:
    media_type: str
    identity: str
    logical_path: str
    mermaid_source: str


@dataclass(frozen=True)
class PreparedSourceMediaWrite:
    role: str
    media_type: str
    identity: str
    data: bytes
    content_type: str
    adapter: ArtifactLocationAdapter
    status: str


def media_suffixes(kind: str) -> set[str]:
    if kind == "image":
        return RASTER_IMAGE_STAGED_SUFFIXES | SVG_STAGED_SUFFIXES | {".mmd"}
    if kind == "file":
        return FILE_MEDIA_STAGED_SUFFIXES
    raise ValueError("media_kind must be image or file")


def source_media_options() -> dict[str, dict[str, Any]]:
    """Supply chooser suffixes and the Save file/metadata limits with Source load."""
    return {
        kind: {
            "accept": ",".join(sorted(media_suffixes(kind))),
            "max_file_bytes": MAX_MEDIA_BYTES,
            "max_total_file_bytes": MAX_MEDIA_BYTES,
            "max_metadata_bytes": MAX_METADATA_BYTES,
        }
        for kind in ("image", "file")
    }


def source_media_identity(
    config: DocsStageConfig | DocsCollectionConfig, doc_id: str, filename: str, kind: str,
) -> SourceMediaIdentity:
    """Construct destinations from an exact target and safe basename, without I/O."""
    source = Path(filename)
    suffix = source.suffix.lower()
    if suffix not in media_suffixes(kind):
        raise ValueError(f"Unsupported {kind} format: {filename}")
    mermaid = kind == "image" and suffix == ".mmd"
    media_type = "files" if kind == "file" else "img" if suffix in RASTER_IMAGE_STAGED_SUFFIXES else "svg"
    if kind == "file" and TOKEN_SAFE_FILENAME.fullmatch(filename):
        basename = filename
    else:
        basename = slugify(source.stem) + (".webp" if media_type == "img" else ".svg" if mermaid else suffix)
    identity = f"{doc_id}/{basename}"
    media = managed_media_config(config, media_type)
    return SourceMediaIdentity(
        media_type, identity, f"{media.reference_prefix.as_posix()}/{identity}",
        str(Path(identity).with_suffix(".mmd")) if mermaid else "",
    )


def prepare_source_media_identity(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Return insertion identity only; no File bytes, document read, processing or writes."""
    required = {"doc_id", "filename", "media_kind"}
    if not required.issubset(body) or set(body) - required - {"collection"}:
        raise ValueError("Media identity requires an exact target, filename and media_kind")
    if not isinstance(body["filename"], str):
        raise ValueError("filename must be a native basename")
    filename = validate_upload_filename(body["filename"])
    target = normalize_managed_document_target(managed_document_target_request(body))
    resolved = resolve_managed_document_collection(repo_root, collection=target.get("collection"))
    config = resolved.document_config
    require_document_authoring(config)
    require_document_media(config)
    identity = source_media_identity(config, target["doc_id"], filename, body["media_kind"])
    return {"ok": True, **target, "media_identity": identity.logical_path}


def prepare_source_media(
    repo_root: Path, resolved: ManagedDocumentTarget, selections: list[dict[str, Any]], uploads: list[SourceMediaUpload],
) -> tuple[list[PreparedSourceMediaWrite], list[dict[str, Any]]]:
    """Process supplied files once and compare only their selected exact destinations.

    The upload boundary owns envelopes, sizes and matched file fields; the browser owns final-buffer
    membership and replacement intent. All preparation precedes permanent writes.
    """
    if not selections:
        return [], []
    config = resolved.document_config
    require_document_media(config)
    adapters = {}
    writes = []
    notes = []
    targets = set()
    toolchain = None

    def output(role: str, media_type: str, identity: str, data: bytes, replace: bool) -> None:
        key = role, media_type, identity
        if key in targets:
            raise FileExistsError(f"Competing pending media target {media_type}/{identity}; resolve the filename conflict")
        targets.add(key)
        adapter_key = role, media_type
        if adapter_key not in adapters:
            location = (config.media.build_sources[media_type].location if role == "build-source"
                        else managed_media_config(config, media_type).asset_location)
            adapters[adapter_key] = artifact_location_adapter(repo_root, location)
        adapter = adapters[adapter_key]
        existing = adapter.stat(identity)
        matches = existing is not None and existing.size == len(data) and adapter.verify_bytes(identity, data)
        status = "new" if existing is None else "unchanged" if matches else "replace"
        if status == "replace" and not replace:
            raise FileExistsError(f"Filename conflict at {media_type}/{identity}; use Edit to replace that file or choose another filename")
        content_type = "text/plain" if role == "build-source" else mimetypes.guess_type(identity)[0] or "application/octet-stream"
        writes.append(PreparedSourceMediaWrite(role, media_type, identity, data, content_type, adapter, status))

    with tempfile.TemporaryDirectory(prefix="docs-source-save-media-") as temporary:
        root = Path(temporary)
        for index, (selection, upload) in enumerate(zip(selections, uploads)):
            try:
                if (not isinstance(selection, dict) or set(selection) != {"media_kind", "body", "thumbnail", "replace"}
                        or any(type(selection[key]) is not bool for key in ("body", "thumbnail", "replace"))
                        or not (selection["body"] or selection["thumbnail"])):
                    raise ValueError("Invalid selected media outputs or replacement intent")
                identity = source_media_identity(config, resolved.doc_id, upload.filename, selection["media_kind"])
                if selection["thumbnail"] and identity.media_type != "img":
                    raise ValueError("Create thumb requires a raster image")
                if identity.media_type == "img" or identity.mermaid_source:
                    source = root / str(index) / upload.filename
                    source.parent.mkdir()
                    source.write_bytes(upload.data)
                if identity.media_type == "img":
                    validate_static_raster(source)
                    if selection["body"]:
                        converted = root / f"{index}-display.webp"
                        convert_source_image_to_webp(source, converted)
                        output("source", "img", identity.identity, converted.read_bytes(), selection["replace"])
                elif identity.mermaid_source:
                    build = config.media.build_sources.get("mermaid")
                    if build is None or build.producer != "mermaid" or build.publishes_to != "svg":
                        raise ValueError("The workspace does not configure editable Mermaid source media")
                    if toolchain is None:
                        toolchain = mermaid_toolchain_paths(MERMAID_TOOLCHAIN_ROOT)
                    rendered = render_mermaid_path(
                        identity.mermaid_source, source, executable=toolchain[0], config=toolchain[1],
                        background="white", output_path=source.parent / "diagram.svg",
                    )
                    output("build-source", "mermaid", identity.mermaid_source, upload.data, selection["replace"])
                    output("source", "svg", identity.identity, rendered.bytes, selection["replace"])
                    if rendered.sanitization.warnings:
                        notes.append({"filename": upload.filename, **rendered.sanitization.diagnostics()})
                elif identity.media_type == "svg" and selection["media_kind"] == "image":
                    sanitized = sanitize_svg_bytes(upload.data)
                    output("source", "svg", identity.identity, sanitized.bytes, selection["replace"])
                    if sanitized.warnings:
                        notes.append({"filename": upload.filename, **sanitized.diagnostics()})
                else:
                    output("source", identity.media_type, identity.identity, upload.data, selection["replace"])
                if selection["thumbnail"]:
                    output(
                        "source", "thumbs", document_thumbnail_filename(resolved.doc_id, collection=resolved.collection),
                        prepare_document_thumbnail(source), True,
                    )
            except (ValueError, OSError, RuntimeError) as error:
                raise ValueError(f"Media preparation for {upload.filename} failed: {error}") from error
    return writes, notes


def write_prepared_source_media(writes: list[PreparedSourceMediaWrite], effects: list[dict[str, Any]]) -> None:
    """Store and verify prepared bytes, retaining exact effects when a later write fails."""
    for item in writes:
        effect = {"role": item.role, "media_type": item.media_type, "identity": item.identity, "status": "attempted"}
        effects.append(effect)
        if item.status == "unchanged":
            effect["status"] = "unchanged"
            continue
        try:
            item.adapter.replace(item.identity, item.data, content_type=item.content_type)
            effect["status"] = "written"
            if not item.adapter.verify_bytes(item.identity, item.data):
                raise RuntimeError("stored bytes did not verify")
            effect["status"] = "verified"
        except (ValueError, OSError, RuntimeError) as error:
            raise RuntimeError(f"{item.media_type}/{item.identity}: {error}") from error
