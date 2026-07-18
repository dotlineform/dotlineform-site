#!/usr/bin/env python3
"""Media planning and materialization for Docs staged source imports."""

from __future__ import annotations

import base64
import binascii
import re
import tempfile
from pathlib import Path
from typing import Any

from docs_import_common import (
    INLINE_RASTER_EXTENSIONS,
    MARKDOWN_INLINE_RASTER_IMAGE_PATTERN,
    normalize_scope,
    normalize_space,
    slugify,
    source_format_for_path,
)
from docs_scope_config import DOCS_SCOPE_CONFIGS, load_docs_scope_configs, published_media_config
from docs_media_storage import (
    docs_media_file,
    docs_publish_succeeded,
    publish_docs_media_files,
)
from docs_svg_sanitizer import sanitize_svg_bytes
from services.paths import marker_path


INLINE_SVG_PATTERN = re.compile(r"<svg\b[^>]*>.*?</svg>", re.IGNORECASE | re.DOTALL)
INLINE_MEDIA_SOURCE_KINDS = {"inline_data_url", "inline_svg"}


def scope_configs_for(repo_root: Path | None = None):
    return load_docs_scope_configs(repo_root) if repo_root is not None else DOCS_SCOPE_CONFIGS


def normalize_media_scope(scope: str, repo_root: Path | None = None) -> str:
    if repo_root is None:
        return normalize_scope(scope)
    value = str(scope or "").strip().lower()
    configs = scope_configs_for(repo_root)
    if value not in configs:
        raise ValueError(f"scope must be one of: {', '.join(sorted(configs))}")
    return value


def media_config_for(scope: str, media_class: str, repo_root: Path | None = None):
    normalized_scope = normalize_media_scope(scope, repo_root)
    return published_media_config(scope_configs_for(repo_root)[normalized_scope], media_class)

def next_inline_media_filename(staging_root: Path, doc_id: str, extension: str, used_filenames: set[str]) -> str:
    safe_doc_id = slugify(doc_id or "imported-doc")
    safe_extension = INLINE_RASTER_EXTENSIONS.get(extension.lower(), extension.lower()).lstrip(".")
    index = 1
    while True:
        filename = f"{safe_doc_id}-image-{index:02d}.{safe_extension}"
        if filename not in used_filenames and not (staging_root / filename).exists():
            used_filenames.add(filename)
            return filename
        index += 1


def inline_media_plan(
    scope: str,
    filename: str,
    title: str,
    *,
    repo_root: Path | None = None,
    staging_root: Path,
    workspace_root: Path,
    mime_type: str,
    size_bytes: int,
    source: str,
) -> dict[str, Any]:
    source_path = Path(filename)
    plan = build_media_plan(scope, "img", source_path, title, repo_root=repo_root)
    plan.update(
        {
            "source": source,
            "staging_path": marker_path(staging_root / filename, workspace_root=workspace_root),
            "mime_type": mime_type,
            "size_bytes": size_bytes,
        }
    )
    return plan


def apply_inline_raster_media_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    summary: dict[str, Any],
    scope: str,
) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    if "data:image/" not in markdown:
        return

    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
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

        filename = next_inline_media_filename(staging_root, proposed_doc_id, extension, used_filenames)
        title = alt or f"Inline image {len(inline_plans) + 1:02d}"
        plan = inline_media_plan(
            scope,
            filename,
            title,
            repo_root=repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            mime_type=f"image/{'jpeg' if extension == 'jpg' else extension}",
            size_bytes=len(decoded),
            source="inline_data_url",
        )
        plans.append(plan)
        inline_plans.append(plan)
        return f"![{match.group('alt')}]({plan['media_token']})"

    normalized = MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def apply_inline_svg_media_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    summary: dict[str, Any],
    scope: str,
    *,
    source_svg_markup: str = "",
) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    if "<svg" not in markdown.lower():
        return

    markdown_matches = list(INLINE_SVG_PATTERN.finditer(markdown))
    source_fragments = [
        match.group(0)
        for match in INLINE_SVG_PATTERN.finditer(source_svg_markup or markdown)
    ]
    if len(source_fragments) != len(markdown_matches):
        raise ValueError("HTML inline SVG extraction no longer matches the structured document conversion")

    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
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
        sanitized = sanitize_svg_bytes(source_fragments[source_index])
        source_index += 1
        filename = next_inline_media_filename(staging_root, proposed_doc_id, "svg", used_filenames)
        title = sanitized.title or f"Inline image {len(inline_plans) + 1:02d}"
        plan = inline_media_plan(
            scope,
            filename,
            title,
            repo_root=repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            mime_type="image/svg+xml",
            size_bytes=len(sanitized.bytes),
            source="inline_svg",
        )
        plans.append(plan)
        inline_plans.append(plan)
        warnings.extend(sanitized.warnings)
        safe_alt = title.replace("[", r"\[").replace("]", r"\]")
        return f"![{safe_alt}]({plan['media_token']})"

    normalized = INLINE_SVG_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def retarget_inline_media_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    summary: dict[str, Any],
    scope: str,
) -> None:
    plans = summary.get("media_plans")
    if not isinstance(plans, list) or not plans:
        return

    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
    used_filenames: set[str] = {
        str(plan.get("source_path") or "")
        for plan in plans
        if isinstance(plan, dict)
        and plan.get("source") not in INLINE_MEDIA_SOURCE_KINDS
        and str(plan.get("source_path") or "")
    }
    markdown = str(summary.get("markdown_preview") or "")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []

    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            continue
        if plan.get("source") not in INLINE_MEDIA_SOURCE_KINDS:
            continue
        old_token = str(plan.get("media_token") or "")
        old_filename = str(plan.get("source_path") or "")
        extension = Path(old_filename).suffix.lstrip(".") or "png"
        source_kind = str(plan.get("source") or "")
        new_filename = next_inline_media_filename(staging_root, proposed_doc_id, extension, used_filenames)
        new_plan = inline_media_plan(
            scope,
            new_filename,
            str(plan.get("title") or f"Inline image {index + 1:02d}"),
            repo_root=repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            mime_type=str(plan.get("mime_type") or f"image/{'jpeg' if extension == 'jpg' else extension}"),
            size_bytes=int(plan.get("size_bytes") or 0),
            source=source_kind,
        )
        if old_token:
            markdown = markdown.replace(old_token, new_plan["media_token"], 1)
        if old_filename != new_filename:
            old_media_path = media_path_for(scope, "img", old_filename, repo_root=repo_root)
            for warning_index, warning in enumerate(warnings):
                if isinstance(warning, str) and old_filename in warning:
                    warnings[warning_index] = warning.replace(old_filename, new_filename).replace(
                        old_media_path,
                        new_plan["media_path"],
                    )
        plans[index] = new_plan
    summary["markdown_preview"] = markdown

def raw_markdown_for_inline_media(source_path: Path, *, include_prompt_meta: bool) -> str:
    source_format = source_format_for_path(source_path)
    if source_format == "html":
        from docs_html_markdown import html_to_markdown

        source_html = source_path.read_text(encoding="utf-8", errors="replace")
        return html_to_markdown(source_html, include_prompt_meta=include_prompt_meta).markdown
    if source_format == "markdown":
        from docs_import_preview import build_markdown_summary

        summary = build_markdown_summary(source_path.read_text(encoding="utf-8", errors="replace"), source_path.stem)
        return str(summary.get("markdown_preview") or "")
    if source_format == "markdown_package":
        from docs_import_markdown_package import find_package_markdown_file, normalize_apple_notes_caption_spans

        markdown_path = find_package_markdown_file(source_path)
        return normalize_apple_notes_caption_spans(markdown_path.read_text(encoding="utf-8", errors="replace"))
    return ""


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
    workspace_root: Path,
    source_path: Path,
    import_preview: dict[str, Any],
    include_prompt_meta: bool,
    source_markdown: str = "",
    source_svg_markup: str = "",
) -> list[dict[str, Any]]:
    del workspace_root
    plans: list[dict[str, Any]] = []
    raw_plans = import_preview.get("media_plans")
    if isinstance(raw_plans, list):
        plans.extend(plan for plan in raw_plans if isinstance(plan, dict))
    raw_plan = import_preview.get("media_plan")
    if isinstance(raw_plan, dict):
        plans.append(raw_plan)
    if not plans:
        return []

    normalized_scope = normalize_media_scope(str(import_preview.get("scope")), repo_root)
    inline_plans = [plan for plan in plans if plan.get("source") in INLINE_MEDIA_SOURCE_KINDS]
    inline_bytes: dict[int, bytes] = {}
    if inline_plans:
        raw_markdown = source_markdown or raw_markdown_for_inline_media(
            source_path,
            include_prompt_meta=include_prompt_meta,
        )
        raster_plans = [plan for plan in inline_plans if plan.get("source") == "inline_data_url"]
        raster_bytes: list[bytes] = []
        for match in MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.finditer(raw_markdown):
            try:
                decoded = base64.b64decode(match.group("data"), validate=True)
            except (binascii.Error, ValueError):
                continue
            raster_bytes.append(decoded)
        if len(raster_bytes) != len(raster_plans):
            raise RuntimeError("Inline raster media extraction plan no longer matches the staged source.")
        inline_bytes.update({id(plan): data for plan, data in zip(raster_plans, raster_bytes)})

        svg_plans = [plan for plan in inline_plans if plan.get("source") == "inline_svg"]
        raw_svg_markup = source_svg_markup
        if not raw_svg_markup and source_path.is_file():
            try:
                if source_format_for_path(source_path) == "html":
                    raw_svg_markup = source_path.read_text(encoding="utf-8", errors="replace")
            except ValueError:
                pass
        svg_bytes = [
            sanitize_svg_bytes(match.group(0)).bytes
            for match in INLINE_SVG_PATTERN.finditer(raw_svg_markup or raw_markdown)
        ]
        if len(svg_bytes) != len(svg_plans):
            raise RuntimeError("Inline SVG media extraction plan no longer matches the staged source.")
        inline_bytes.update({id(plan): data for plan, data in zip(svg_plans, svg_bytes)})

    return publish_import_media(
        repo_root,
        staging_root=staging_root,
        source_path=source_path,
        plans=plans,
        inline_bytes=inline_bytes,
        scope=normalized_scope,
    )


def publish_import_media(
    repo_root: Path,
    *,
    staging_root: Path,
    source_path: Path,
    plans: list[dict[str, Any]],
    inline_bytes: dict[int, bytes],
    scope: str,
) -> list[dict[str, Any]]:
    """Prepare one import record's complete media set and publish before its source write."""

    config = scope_configs_for(repo_root)[scope]
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
                decoded = inline_bytes.get(id(plan))
                if decoded is None:
                    raise RuntimeError("Inline media extraction plan no longer matches the staged source.")
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
                filename=str(plan.get("source_path") or ""),
            )
            for plan, prepared_path, prepared_root, _conversion in prepared
        ]
        results = publish_docs_media_files(repo_root, media_files, write=True, force=False)
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
                    (str(plan.get("media_class") or ""), str(plan.get("source_path") or ""))
                ],
            }
            for plan, prepared_path, _prepared_root, conversion in prepared
        ]


def media_token(scope: str, media_class: str, filename: str, *, repo_root: Path | None = None) -> str:
    media_path = media_path_for(scope, media_class, filename, repo_root=repo_root)
    return f"[[media:{media_path}]]"


def media_path_for(scope: str, media_class: str, filename: str, *, repo_root: Path | None = None) -> str:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, media_class, repo_root)
    return f"{config.reference_prefix.as_posix().strip('/')}/{filename}"


def media_link_for(
    scope: str,
    media_class: str,
    filename: str,
    *,
    repo_root: Path | None = None,
) -> str:
    return media_token(scope, media_class, filename, repo_root=repo_root)


def build_media_plan(
    scope: str,
    media_class: str,
    source_path: Path,
    title: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, media_class, repo_root)
    link = media_link_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
    media_path = media_path_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
    return {
        "location_provider": config.location.provider,
        "artifact_identity": source_path.name,
        "media_class": media_class,
        "source_path": source_path.name,
        "media_path": media_path,
        "media_token": link,
        "media_link": link,
        "served_reference": f"{config.served_path_prefix}/{source_path.name}",
        "title": title,
    }
