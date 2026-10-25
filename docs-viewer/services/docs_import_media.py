#!/usr/bin/env python3
"""Media planning and materialization for Docs staged source imports."""

from __future__ import annotations

import base64
import binascii
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docs_import_common import (
    INLINE_RASTER_EXTENSIONS,
    MARKDOWN_INLINE_RASTER_IMAGE_PATTERN,
    normalize_space,
)
from docs_image_tokens import serialize_image_token
from docs_workspace_config import (
    DocsManagedMediaConfig, DocsStageConfig, DocsCollectionConfig,
    managed_media_config,
)
from docs_media_storage import (
    docs_media_file,
    docs_publish_succeeded,
    publish_docs_media_files,
)
from docs_svg_sanitizer import SanitizedSvg, sanitize_svg_bytes
from docs_artifact_locations import normalize_artifact_identity
from studio.shared.python.projects_directories import projects_path_marker


INLINE_SVG_PATTERN = re.compile(r"<svg\b[^>]*>.*?</svg>", re.IGNORECASE | re.DOTALL)
INLINE_SVG_XML_ESCAPE_PATTERN = re.compile(
    r"<!\[CDATA\[.*?\]\]>|<!--.*?-->|<\?.*?\?>|&(?!(?:#\w+|[\w:][\w.:-]*);)",
    re.DOTALL,
)
INLINE_SVG_XLINK_DECLARATION_PATTERN = re.compile(
    r"""<(?i:svg)\b(?:[^>"']|"[^"]*"|'[^']*')*?\sxmlns:xlink\s*=""",
)
INLINE_MEDIA_SOURCE_KINDS = {"inline_data_url", "inline_svg"}


@dataclass
class ImportMediaPreparation:
    """One conversion's resolved owner, identity and prepared inline bytes."""

    config: DocsStageConfig | DocsCollectionConfig
    doc_id: str = ""
    inline_bytes: dict[tuple[str, str], bytes] = field(default_factory=dict)


def sanitize_inline_svg_markup(markup: str) -> SanitizedSvg:
    """Make HTML's ampersands and implicit XLink binding explicit for SVG XML."""
    # Preserve literal XML sections and entity-shaped references. The sanitizer
    # still owns XML validity, including unsupported or malformed references.
    escaped = INLINE_SVG_XML_ESCAPE_PATTERN.sub(
        lambda match: "&amp;" if match.group(0) == "&" else match.group(0),
        markup,
    )
    # HTML supplies the XLink namespace implicitly; an extracted XML root must
    # declare it. Skip quoted attribute values when looking for an existing binding.
    if "xlink:" in escaped and not INLINE_SVG_XLINK_DECLARATION_PATTERN.match(escaped):
        escaped = re.sub(
            r"^<svg\b",
            r'\g<0> xmlns:xlink="http://www.w3.org/1999/xlink"',
            escaped,
            count=1,
            flags=re.IGNORECASE,
        )
    return sanitize_svg_bytes(escaped)


def next_inline_media_filename(staging_root: Path, extension: str, used_filenames: set[str]) -> str:
    safe_extension = INLINE_RASTER_EXTENSIONS.get(extension.lower(), extension.lower()).lstrip(".")
    index = 1
    while True:
        filename = f"image-{index:02d}.{safe_extension}"
        if filename not in used_filenames and not (staging_root / filename).exists():
            used_filenames.add(filename)
            return filename
        index += 1


def inline_media_plan(
    filename: str,
    title: str,
    *,
    media_class: str = "img",
    preparation: ImportMediaPreparation,
    staging_root: Path,
    workspace_root: Path,
    mime_type: str,
    size_bytes: int,
    source: str,
) -> dict[str, Any]:
    source_path = Path(filename)
    plan = build_media_plan(
        media_class, source_path, title,
        media_config=managed_media_config(preparation.config, media_class),
        artifact_identity=f"{preparation.doc_id}/{filename}",
    )
    plan.update(
        {
            "source": source,
            "staging_path": projects_path_marker(staging_root / filename, workspace_root),
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        }
    )
    return plan


def apply_inline_raster_media_plans(
    preparation: ImportMediaPreparation,
    staging_root: Path,
    workspace_root: Path,
    summary: dict[str, Any],
) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    if "data:image/" not in markdown:
        return

    existing_plans = summary.get("media_plans")
    plans: list[dict[str, Any]] = list(existing_plans) if isinstance(existing_plans, list) else []
    used_filenames: set[str] = {
        str(plan.get("source_path") or "")
        for plan in plans
        if isinstance(plan, dict) and str(plan.get("source_path") or "")
    }
    inline_plans: list[dict[str, Any]] = []
    warnings = summary.setdefault("warnings", [])

    def replace(match: re.Match[str]) -> str:
        subtype = match.group("subtype").lower()
        extension = INLINE_RASTER_EXTENSIONS.get(subtype)
        alt = normalize_space(match.group("alt"))
        if not extension:
            warnings.append(f"Unsupported inline image media type image/{subtype}; left the data URL inline.")
            return match.group(0)
        try:
            decoded = base64.b64decode(match.group("data"), validate=True)
        except (binascii.Error, ValueError):
            warnings.append(f"Could not decode inline image data for {alt or 'an imported image'}; left the data URL inline.")
            return match.group(0)

        filename = next_inline_media_filename(staging_root, extension, used_filenames)
        title = alt or f"Inline image {len(inline_plans) + 1:02d}"
        plan = inline_media_plan(
            filename,
            title,
            preparation=preparation,
            staging_root=staging_root,
            workspace_root=workspace_root,
            mime_type=f"image/{'jpeg' if extension == 'jpg' else extension}",
            size_bytes=len(decoded),
            source="inline_data_url",
        )
        plans.append(plan)
        preparation.inline_bytes[("img", filename)] = decoded
        inline_plans.append(plan)
        return f"![{match.group('alt')}]({plan['media_token']})"

    normalized = MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def apply_inline_svg_media_plans(
    preparation: ImportMediaPreparation,
    staging_root: Path,
    workspace_root: Path,
    summary: dict[str, Any],
    *,
    source_svg_markup: str,
) -> None:
    """Prepare extracted SVG bytes and emit canonical, Source-editable image tokens."""
    markdown = str(summary.get("markdown_preview") or "")
    if "<svg" not in markdown.lower():
        return

    markdown_matches = list(INLINE_SVG_PATTERN.finditer(markdown))
    source_fragments = [
        match.group(0)
        for match in INLINE_SVG_PATTERN.finditer(source_svg_markup)
    ]
    if len(source_fragments) != len(markdown_matches):
        raise ValueError("HTML inline SVG extraction no longer matches the structured document conversion")

    existing_plans = summary.get("media_plans")
    plans: list[dict[str, Any]] = list(existing_plans) if isinstance(existing_plans, list) else []
    used_filenames: set[str] = {
        str(plan.get("source_path") or "")
        for plan in plans
        if isinstance(plan, dict) and str(plan.get("source_path") or "")
    }
    inline_plans: list[dict[str, Any]] = []
    warnings = summary.setdefault("warnings", [])
    source_index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal source_index
        sanitized = sanitize_inline_svg_markup(source_fragments[source_index])
        source_index += 1
        filename = next_inline_media_filename(staging_root, "svg", used_filenames)
        title = sanitized.title or f"Inline image {len(inline_plans) + 1:02d}"
        plan = inline_media_plan(
            filename,
            title,
            media_class="svg",
            preparation=preparation,
            staging_root=staging_root,
            workspace_root=workspace_root,
            mime_type="image/svg+xml",
            size_bytes=len(sanitized.bytes),
            source="inline_svg",
        )
        plans.append(plan)
        preparation.inline_bytes[("svg", filename)] = sanitized.bytes
        inline_plans.append(plan)
        warnings.extend(sanitized.warnings)
        return serialize_image_token(
            media_path=plan["media_path"], alt=title,
            placement="full", fill_width=False,
        )

    normalized = INLINE_SVG_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def package_media_source_path(package_root: Path, plan: dict[str, Any]) -> Path:
    source_rel = str(plan.get("package_relative_source_path") or "").strip()
    if not source_rel:
        raise ValueError("Package media plan is missing package_relative_source_path.")
    source_path = (package_root / source_rel).resolve()
    if not source_path.is_relative_to(package_root.resolve()):
        raise ValueError(f"Package media source escapes package root: {source_rel}")
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"Package media source does not exist: {source_rel}")
    return source_path


def convert_package_image_to_webp(source_path: Path, target_path: Path, *, max_width: int = 800) -> dict[str, Any]:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for Markdown package image conversion. "
            "Install requirements.txt before importing package images."
        ) from exc

    with Image.open(source_path) as image:
        if getattr(image, "is_animated", False):
            raise ValueError(f"Animated image conversion is not supported for Markdown package imports: {source_path.name}")
        image = ImageOps.exif_transpose(image)
        original_width, original_height = image.size
        output = image
        resized = False
        if original_width > max_width:
            ratio = max_width / float(original_width)
            output = image.resize((max_width, max(1, round(original_height * ratio))), Image.Resampling.LANCZOS)
            resized = True
        if output.mode in {"RGBA", "LA"} or (output.mode == "P" and "transparency" in output.info):
            output = output.convert("RGBA")
        else:
            output = output.convert("RGB")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        output.save(target_path, "WEBP", quality=85, method=6)
        output_width, output_height = output.size
    return {
        "original_width": original_width,
        "original_height": original_height,
        "output_width": output_width,
        "output_height": output_height,
        "resized": resized,
    }

def materialize_import_media(
    repo_root: Path,
    *,
    staging_root: Path,
    source_path: Path,
    import_preview: dict[str, Any],
    inline_bytes: dict[tuple[str, str], bytes],
    config: DocsStageConfig | DocsCollectionConfig,
) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    raw_plans = import_preview.get("media_plans")
    if isinstance(raw_plans, list):
        plans.extend(plan for plan in raw_plans if isinstance(plan, dict))
    raw_plan = import_preview.get("media_plan")
    if isinstance(raw_plan, dict):
        plans.append(raw_plan)
    if not plans:
        return []

    return publish_import_media(
        repo_root,
        staging_root=staging_root,
        source_path=source_path,
        plans=plans,
        inline_bytes=inline_bytes,
        config=config,
    )


def publish_import_media(
    repo_root: Path,
    *,
    staging_root: Path,
    source_path: Path,
    plans: list[dict[str, Any]],
    inline_bytes: dict[tuple[str, str], bytes],
    config: DocsStageConfig | DocsCollectionConfig,
) -> list[dict[str, Any]]:
    """Prepare one import record's complete media set and publish before its source write."""

    prepared: list[tuple[dict[str, Any], Path, Path, dict[str, Any]]] = []
    with tempfile.TemporaryDirectory(prefix="docs-media-publish-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        for plan in plans:
            filename = str(plan.get("source_path") or "").strip()
            media_class = str(plan.get("media_class") or "").strip()
            if not filename or Path(filename).name != filename:
                raise ValueError(f"Invalid Docs media filename: {filename!r}")
            conversion_result: dict[str, Any] = {}
            source_kind = str(plan.get("source") or "")
            if source_kind in INLINE_MEDIA_SOURCE_KINDS:
                decoded = inline_bytes[(media_class, filename)]
                prepared_path = temp_root / media_class / filename
                prepared_path.parent.mkdir(parents=True, exist_ok=True)
                prepared_path.write_bytes(decoded)
                prepared_root = temp_root
            elif source_kind == "markdown_package_image":
                package_source = package_media_source_path(source_path, plan)
                prepared_path = temp_root / media_class / filename
                conversion_result = convert_package_image_to_webp(
                    package_source,
                    prepared_path,
                    max_width=int((plan.get("conversion") or {}).get("max_width") or 800),
                )
                prepared_root = temp_root
            elif source_kind == "markdown_package_attachment":
                package_source = package_media_source_path(source_path, plan)
                prepared_path = temp_root / media_class / filename
                prepared_path.parent.mkdir(parents=True, exist_ok=True)
                prepared_path.write_bytes(package_source.read_bytes())
                prepared_root = temp_root
            else:
                if source_path.is_dir() or source_path.name != filename:
                    raise ValueError("Staged Docs media source does not match its publication plan")
                prepared_path = source_path.resolve()
                prepared_root = staging_root.resolve()
            prepared.append((plan, prepared_path, prepared_root, conversion_result))

        media_files = [
            docs_media_file(
                config,
                media_class=str(plan.get("media_class") or ""),
                local_path=prepared_path,
                source_root=prepared_root,
                filename=plan["artifact_identity"],
            )
            for plan, prepared_path, prepared_root, _conversion in prepared
        ]
        results = publish_docs_media_files(repo_root, media_files, config=config, write=True, force=False)
        if not docs_publish_succeeded(results):
            failures = ", ".join(
                f"{result.media_class}/{result.filename}: {result.status}"
                for result in results
                if result.status not in {"unchanged", "uploaded", "overwritten"}
            )
            raise RuntimeError(f"Docs media publication did not complete: {failures}")

        status_by_identity = {
            (result.media_class, result.filename): result.status
            for result in results
        }
        return [
            {
                "source_path": plan.get("source_path", ""),
                "source_original_path": plan.get("source_original_path", ""),
                "size_bytes": prepared_path.stat().st_size,
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "location_provider": plan.get("location_provider", ""),
                "artifact_identity": plan.get("artifact_identity", ""),
                "media_class": plan.get("media_class", ""),
                "kind": plan.get("kind", ""),
                "conversion": conversion,
                "publish_status": status_by_identity[
                    (str(plan.get("media_class") or ""), plan["artifact_identity"])
                ],
            }
            for plan, prepared_path, _prepared_root, conversion in prepared
        ]


def build_media_plan(
    media_class: str,
    source_path: Path,
    title: str,
    *,
    media_config: DocsManagedMediaConfig,
    artifact_identity: str,
) -> dict[str, Any]:
    config = media_config
    identity = normalize_artifact_identity(artifact_identity)
    media_path = f"{config.reference_prefix.as_posix()}/{identity}"
    link = f"[[media:{media_path}]]"
    return {
        "location_provider": config.asset_location.provider,
        "artifact_identity": identity,
        "media_class": media_class,
        "source_path": source_path.name,
        "media_path": media_path,
        "media_token": link,
        "media_link": link,
        "served_reference": f"{config.served_path_prefix}/{identity}",
        "title": title,
    }
