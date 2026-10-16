#!/usr/bin/env python3
"""Materialise native uploads for Docs source-editor insertion and replacement."""

from __future__ import annotations

import mimetypes
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

from docs_artifact_locations import (
    ArtifactLocation,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_import_common import (
    FILE_MEDIA_STAGED_SUFFIXES,
    RASTER_IMAGE_STAGED_SUFFIXES,
    SVG_STAGED_SUFFIXES,
    humanize,
    slugify,
)
from docs_import_media import build_media_plan
from docs_media_storage import validate_media_filename
from docs_mermaid_media import produce_mermaid_svg
from docs_workspace_config import (
    DocsStageConfig, DocsCollectionConfig, DocsWorkspaceConfig,
    managed_media_config, require_document_authoring, require_document_media,
)
from docs_staged_media_fragments import (
    build_file_link_fragment,
)
from docs_image_tokens import image_text, serialize_image_token
from docs_svg_sanitizer import SanitizedSvg, sanitize_svg_bytes
from docs_source_media_upload import MAX_MEDIA_BYTES, MAX_METADATA_BYTES, SourceMediaUpload, validate_upload
from docs_source_image_conversion import convert_source_image_to_webp
from docs_document_images import write_document_thumbnail
from docs_management_document_target import managed_document_target_request, resolve_managed_document_target


MEDIA_IMAGE = "image"
MEDIA_FILE = "file"
MEDIA_KINDS = {MEDIA_IMAGE, MEDIA_FILE}
MERMAID_STAGED_SUFFIXES = {".mmd"}
TOKEN_SAFE_MEDIA_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class PreparedMermaidMedia:
    source_identity: str
    published_identity: str
    source_bytes: bytes
    published_bytes: bytes
    source_adapter: ArtifactLocationAdapter
    published_adapter: ArtifactLocationAdapter
    sanitized: SanitizedSvg
    collision: str
    published_status: str
    source_status: str


@dataclass(frozen=True)
class SourceMediaContract:
    kind: str
    source_path: Path
    label: str
    media_class: str
    media_filename: str
    owner: DocsStageConfig | DocsCollectionConfig
    workspace: DocsWorkspaceConfig
    collection: str = ""
    doc_id: str = ""
    create_thumb: bool = False


def normalize_media_kind(value: Any) -> str:
    kind = str(value or "").strip().lower()
    if kind not in MEDIA_KINDS:
        raise ValueError("media_kind must be image or file")
    return kind


def media_suffixes(kind: str) -> set[str]:
    return (
        RASTER_IMAGE_STAGED_SUFFIXES | SVG_STAGED_SUFFIXES | MERMAID_STAGED_SUFFIXES
        if normalize_media_kind(kind) == MEDIA_IMAGE
        else FILE_MEDIA_STAGED_SUFFIXES
    )


def validate_media_identity(value: Any) -> str:
    return validate_media_filename(str(value or "").strip())


def published_media_filename(source_path: Path, *, kind: str) -> str:
    """Name converted raster WebP, normalize vector names and preserve safe file names.

    Image identity comes from the selected source stem and the stored format.
    Naming performs no storage lookup; byte comparison and confirmation own
    replacement within the configured collection and media family.
    """
    filename = validate_media_identity(source_path.name)
    kind = normalize_media_kind(kind)
    if kind == MEDIA_FILE and TOKEN_SAFE_MEDIA_FILENAME_PATTERN.fullmatch(filename):
        return filename
    suffix = source_path.suffix.lower()
    if kind == MEDIA_IMAGE and suffix in RASTER_IMAGE_STAGED_SUFFIXES:
        suffix = ".webp"
    return f"{slugify(source_path.stem)}{suffix}"


def normalize_label_text(value: Any, *, fallback: str) -> str:
    return " ".join(str(value or "").split()) or fallback


@contextmanager
def _prepared_media_source(
    source_path: Path,
    kind: str,
    media_filename: str,
) -> Iterator[tuple[Path, SanitizedSvg | None]]:
    is_image = normalize_media_kind(kind) == MEDIA_IMAGE
    is_svg = is_image and source_path.suffix.lower() == ".svg"
    is_raster = is_image and source_path.suffix.lower() in RASTER_IMAGE_STAGED_SUFFIXES
    if not is_svg and not is_raster and media_filename == source_path.name:
        yield source_path, None
        return
    sanitized = sanitize_svg_bytes(source_path.read_bytes()) if is_svg else None
    with tempfile.TemporaryDirectory(prefix="docs-source-media-publish-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        prepared_path = temp_root / media_filename
        if is_raster:
            convert_source_image_to_webp(source_path, prepared_path)
        elif sanitized:
            prepared_path.write_bytes(sanitized.bytes)
        else:
            shutil.copyfile(source_path, prepared_path)
        yield prepared_path, sanitized


def source_media_options() -> dict[str, dict[str, Any]]:
    """Supply both native choosers' suffixes and byte limits with Source load."""
    return {
        kind: {
            "accept": ",".join(sorted(media_suffixes(kind))),
            "max_file_bytes": MAX_MEDIA_BYTES, "max_metadata_bytes": MAX_METADATA_BYTES,
        }
        for kind in (MEDIA_IMAGE, MEDIA_FILE)
    }


def _source_media_request_contract(repo_root: Path, body: dict[str, Any], source_path: Path) -> SourceMediaContract:
    kind = normalize_media_kind(body.get("media_kind"))
    if any(key in body for key in ("staged_filename", "source_directory", "source_root", "source_path", "published_filename")):
        raise ValueError("Source media accepts native file bytes, not staged paths or caller-selected destinations")
    target = managed_document_target_request(body)
    resolved = resolve_managed_document_target(repo_root, target)
    config = resolved.document_config
    require_document_authoring(config)
    require_document_media(config)
    if source_path.suffix.lower() not in media_suffixes(kind):
        raise ValueError(f"Unsupported {kind} format; select one of: {', '.join(sorted(media_suffixes(kind)))}")
    fallback = humanize(source_path.stem) or ("Image" if kind == MEDIA_IMAGE else "File")
    label = normalize_label_text(body.get("label"), fallback=fallback)
    media_class = (
        "mermaid" if kind == MEDIA_IMAGE and source_path.suffix.lower() == ".mmd"
        else "svg" if kind == MEDIA_IMAGE and source_path.suffix.lower() == ".svg"
        else "img" if kind == MEDIA_IMAGE else "files"
    )
    media_filename = published_media_filename(source_path, kind=kind)
    create_thumb = body.get("create_thumb", False)
    if not isinstance(create_thumb, bool):
        raise ValueError("create_thumb must be a boolean")
    if create_thumb and media_class != "img":
        raise ValueError("Create thumb requires a raster image")
    if media_class == "mermaid":
        media_filename = Path(media_filename).with_suffix(".mmd").name
    return SourceMediaContract(
        kind=kind, source_path=source_path, label=label, media_class=media_class,
        media_filename=media_filename, owner=config, workspace=resolved.workspace, collection=resolved.collection,
        doc_id=resolved.doc_id, create_thumb=create_thumb,
    )


def _source_fragment(
    kind: str,
    label: str,
    media_path: str,
    *,
    body: dict[str, Any],
) -> str:
    if kind == MEDIA_FILE:
        return build_file_link_fragment(label, f"[[media:{media_path}]]")
    if type(body.get("add_caption")) is not bool:
        raise ValueError("add_caption must be a boolean")
    if body["add_caption"] and (not isinstance(body.get("caption"), str) or not image_text(body["caption"])):
        raise ValueError("caption is required when Add caption is checked")
    token = serialize_image_token(
        media_path=media_path, alt=label,
        caption=body.get("caption", "") if body["add_caption"] else "",
        summary=body.get("summary", ""),
        placement=body.get("placement"),
        fill_width=body.get("fill_width"),
    )
    if not token:
        raise ValueError("Image alt, presentation or media identity is invalid")
    return token


def _artifact_status(adapter: ArtifactLocationAdapter, identity: str, data: bytes) -> str:
    existing = adapter.stat(identity)
    if existing is None:
        return "new"
    return "unchanged" if adapter.verify_bytes(identity, data) else "replace"


def _prepared_mermaid_media(
    repo_root: Path,
    config: DocsStageConfig | DocsCollectionConfig,
    source_path: Path,
    source_filename: str,
) -> PreparedMermaidMedia:
    build = config.media.build_sources.get("mermaid")
    if build is None or build.producer != "mermaid" or build.publishes_to != "svg":
        raise ValueError("The workspace does not configure Mermaid source media")
    generated_media = config.media.types.get("svg")
    if generated_media is None or "mermaid" not in generated_media.build_inputs:
        raise ValueError("The workspace does not register Mermaid as an SVG build input")

    source_identity = source_filename
    published_identity = Path(source_filename).with_suffix(".svg").as_posix()
    source_bytes = source_path.read_bytes()
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        [generated_media.asset_location],
    )
    source_adapter = artifact_location_adapter(
        repo_root,
        build.location,
    )
    published_adapter = artifact_location_adapter(
        repo_root,
        generated_media.asset_location,
        served_path_prefix=generated_media.served_path_prefix,
        remote_client=remote_client,
    )

    with tempfile.TemporaryDirectory(prefix="docs-source-mermaid-render-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        temporary_source = artifact_location_adapter(
            temp_root,
            ArtifactLocation(provider="repository", path=Path("source")),
        )
        temporary_published = artifact_location_adapter(
            temp_root,
            ArtifactLocation(provider="repository", path=Path("published")),
        )
        temporary_source.replace(source_identity, source_bytes, content_type="text/plain")
        context = SimpleNamespace(
            source=temporary_source,
            generated=temporary_published,
            write=True,
            requested_generated_identities=(published_identity,),
        )
        outputs = produce_mermaid_svg(context)
        if outputs != (published_identity,):
            raise RuntimeError(f"Mermaid producer did not render {published_identity!r}")
        published_bytes = temporary_published.read(published_identity)

    sanitized = sanitize_svg_bytes(published_bytes)
    source_status = _artifact_status(source_adapter, source_identity, source_bytes)
    published_status = _artifact_status(published_adapter, published_identity, published_bytes)
    statuses = {source_status, published_status}
    collision = "replace" if "replace" in statuses else "unchanged" if statuses == {"unchanged"} else "new"
    return PreparedMermaidMedia(
        source_identity=source_identity,
        published_identity=published_identity,
        source_bytes=source_bytes,
        published_bytes=published_bytes,
        source_adapter=source_adapter,
        published_adapter=published_adapter,
        sanitized=sanitized,
        collision=collision,
        published_status=published_status,
        source_status=source_status,
    )


def _mermaid_preview_payload(
    repo_root: Path,
    contract: SourceMediaContract,
    prepared: PreparedMermaidMedia,
    *,
    body: dict[str, Any],
) -> dict[str, Any]:
    plan = build_media_plan(
        "svg",
        Path(prepared.published_identity),
        contract.label,
        repo_root=repo_root,
        media_config=managed_media_config(contract.owner, "svg"),
    )
    return {
        "ok": True,
        "collection": contract.collection,
        "media_kind": contract.kind,
        "media_format": "mermaid",
        "source_filename": contract.source_path.name,
        "source_identity": prepared.source_identity,
        "published_filename": Path(prepared.published_identity).name,
        "label": contract.label,
        "add_caption": contract.kind == MEDIA_IMAGE and body.get("add_caption") is True,
        "media_identity": plan["media_path"],
        "media_token": plan["media_token"],
        "markdown": _source_fragment(
            contract.kind,
            contract.label,
            plan["media_path"],
            body=body,
        ),
        "collision": prepared.collision,
        "requires_replace_confirmation": prepared.collision == "replace",
        "size_bytes": len(prepared.published_bytes),
        "svg": {
            "title": prepared.sanitized.title,
            "diagnostics": prepared.sanitized.diagnostics(),
        },
    }


def _needs_confirmation(preview: dict[str, Any], body: dict[str, Any]) -> bool:
    for field in ("confirm_replace", "confirm_sanitization"):
        if type(body.get(field, False)) is not bool:
            raise ValueError(f"{field} must be a boolean")
    diagnostics = (preview.get("svg") or {}).get("diagnostics") or {}
    return (
        preview["requires_replace_confirmation"] and not body.get("confirm_replace", False)
        or bool(diagnostics.get("warnings")) and not body.get("confirm_sanitization", False)
    )


def apply_source_media(
    repo_root: Path, body: dict[str, Any], upload: SourceMediaUpload, *, write: bool = True,
) -> dict[str, Any]:
    """Await required writes before returning insertion metadata, or ask for a decision.

    Native bytes live only in operation-owned temporary storage. A confirmation
    response is write-free; the browser resubmits the same File with its decision.
    Source Save and public publication remain independent.
    """
    filename = validate_upload(upload)
    try:
        with tempfile.TemporaryDirectory(prefix="docs-source-media-upload-") as temp_dir:
            source_path = Path(temp_dir) / filename
            source_path.write_bytes(upload.data)
            contract = _source_media_request_contract(repo_root, body, source_path)
            return _apply_source_media_contract(repo_root, contract, body, write=write)
    except OSError as error:
        raise RuntimeError(f"Media operation for {filename} did not complete: {error}") from error


def _apply_source_media_contract(
    repo_root: Path, contract: SourceMediaContract, body: dict[str, Any], *, write: bool,
) -> dict[str, Any]:
    config = contract.owner
    if contract.media_class == "mermaid":
        prepared = _prepared_mermaid_media(
            repo_root,
            config,
            contract.source_path,
            contract.media_filename,
        )
        preview = _mermaid_preview_payload(
            repo_root,
            contract,
            prepared,
            body=body,
        )
        if _needs_confirmation(preview, body):
            return {**preview, "requires_confirmation": True}
        stored: list[str] = []
        try:
            if write and prepared.source_status != "unchanged":
                prepared.source_adapter.replace(
                    prepared.source_identity,
                    prepared.source_bytes,
                    content_type="text/plain",
                )
                stored.append(f"Mermaid source {prepared.source_identity}")
                if not prepared.source_adapter.verify_bytes(prepared.source_identity, prepared.source_bytes):
                    raise RuntimeError("Canonical Mermaid source publication verification failed")
            if write and prepared.published_status != "unchanged":
                prepared.published_adapter.replace(
                    prepared.published_identity,
                    prepared.published_bytes,
                    content_type="image/svg+xml",
                )
                stored.append(f"SVG {prepared.published_identity}")
                if not prepared.published_adapter.verify_bytes(prepared.published_identity, prepared.published_bytes):
                    raise RuntimeError("Mermaid SVG publication verification failed")
        except (OSError, RuntimeError) as error:
            effects = ", ".join(stored) if stored else "no confirmed new media writes"
            raise RuntimeError(f"Mermaid operation failed after {effects}: {error}") from error
        published_status = (
            "unchanged"
            if prepared.published_status == "unchanged"
            else "overwritten"
            if prepared.published_status == "replace" and write
            else "uploaded"
            if write
            else "would_overwrite"
            if prepared.published_status == "replace"
            else "would_upload"
        )
        if write and prepared.published_status != "unchanged":
            from docs_publication_preparation import requeue_media

            requeue_media(repo_root, contract.workspace, contract.collection, "svg", prepared.published_identity)
        return {
            **preview,
            "requires_confirmation": False,
            "preview_only": not write,
            "source_publish": {
                "identity": prepared.source_identity,
                "status": prepared.source_status,
                "size": len(prepared.source_bytes),
            },
            "publish": {
                "collection": contract.collection,
                "media_class": "svg",
                "filename": prepared.published_identity,
                "size": len(prepared.published_bytes),
                "status": published_status,
                "reason": "",
            },
            "summary_text": (
                f"Added {contract.source_path.name} and rendered Mermaid SVG."
                if write and prepared.collision != "unchanged"
                else f"Verified {contract.source_path.name} and rendered Mermaid SVG."
                if write
                else f"Prepared Mermaid insertion preview for {contract.source_path.name}."
            ),
        }

    with _prepared_media_source(
        contract.source_path, contract.kind, contract.media_filename,
    ) as (prepared_path, sanitized):
        data = prepared_path.read_bytes()
        media_type = managed_media_config(config, contract.media_class)
        remote_client = authenticated_remote_client_for_locations(repo_root, [media_type.asset_location])
        adapter = artifact_location_adapter(
            repo_root, media_type.asset_location, served_path_prefix=media_type.served_path_prefix,
            remote_client=remote_client,
        )
        collision = _artifact_status(adapter, contract.media_filename, data)
        plan = build_media_plan(
            contract.media_class, Path(contract.media_filename), contract.label,
            repo_root=repo_root, media_config=media_type,
        )
        preview = {
            "ok": True, "doc_id": contract.doc_id, "collection": contract.collection,
            "media_kind": contract.kind, "source_filename": contract.source_path.name,
            "published_filename": contract.media_filename, "label": contract.label,
            "create_thumb": contract.create_thumb, "media_identity": plan["media_path"],
            "media_token": plan["media_token"],
            "markdown": _source_fragment(contract.kind, contract.label, plan["media_path"], body=body),
            "collision": collision, "requires_replace_confirmation": collision == "replace",
            "size_bytes": len(data),
            "svg": {"title": sanitized.title, "diagnostics": sanitized.diagnostics()} if sanitized else None,
        }
        if _needs_confirmation(preview, body):
            return {**preview, "requires_confirmation": True}
        if write and collision != "unchanged":
            content_type, _encoding = mimetypes.guess_type(contract.media_filename)
            adapter.replace(contract.media_filename, data, content_type=content_type or "application/octet-stream")
            if not adapter.verify_bytes(contract.media_filename, data):
                raise RuntimeError(f"Docs media insertion did not complete for {contract.media_filename}: stored bytes did not verify")
        status = (
            "unchanged" if collision == "unchanged"
            else "overwritten" if write and collision == "replace"
            else "uploaded" if write
            else "would_overwrite" if collision == "replace"
            else "would_upload"
        )
        if write and collision != "unchanged":
            from docs_publication_preparation import requeue_media

            requeue_media(repo_root, contract.workspace, contract.collection, contract.media_class, contract.media_filename)
        published = {
            "collection": contract.collection, "media_class": contract.media_class,
            "filename": contract.media_filename, "size": len(data), "status": status,
            "reason": "published bytes already match" if collision == "unchanged" else "" if write else "dry-run",
        }
    thumbnail = None
    if write and contract.create_thumb:
        try:
            thumbnail = write_document_thumbnail(
                repo_root, config, doc_id=contract.doc_id, source_path=contract.source_path,
            )
            from docs_publication_preparation import requeue_media

            requeue_media(repo_root, contract.workspace, contract.collection, "thumbs", thumbnail["filename"])
        except (ValueError, RuntimeError, OSError) as error:
            raise RuntimeError(f"Display image stored as {contract.media_filename}; thumbnail operation failed: {error}") from error
    return {
        **preview, "requires_confirmation": False, "preview_only": not write,
        "publish": published, "thumbnail": thumbnail,
        "summary_text": (
            f"Added {contract.source_path.name}."
            if write and status != "unchanged"
            else f"Verified {contract.source_path.name}." if write
            else f"Prepared insertion preview for {contract.source_path.name}."
        ),
    }
