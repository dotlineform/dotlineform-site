#!/usr/bin/env python3
"""Media planning and materialization for Docs staged source imports."""

from __future__ import annotations

import base64
import binascii
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from docs_import_common import (
    INLINE_RASTER_EXTENSIONS,
    MARKDOWN_INLINE_RASTER_IMAGE_PATTERN,
    humanize,
    normalize_scope,
    normalize_space,
    relative_path,
    slugify,
    source_format_for_path,
)
from docs_scope_config import DOCS_SCOPE_CONFIGS, IMPORT_MEDIA_CONFIGS, MEDIA_PATH_PREFIXES, load_docs_scope_configs
from docs_media_storage import (
    docs_media_file,
    docs_publish_succeeded,
    local_media_route,
    publish_docs_media_files,
    scope_owned_media_root_for_scope,
)
from services.paths import marker_path


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


def media_config_for(scope: str, repo_root: Path | None = None):
    normalized_scope = normalize_media_scope(scope, repo_root)
    return scope_configs_for(repo_root)[normalized_scope].import_media_storage

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
) -> dict[str, Any]:
    source_path = Path(filename)
    plan = build_media_plan(scope, "img", source_path, title, repo_root=repo_root)
    plan.update(
        {
            "source": "inline_data_url",
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
        )
        plans.append(plan)
        inline_plans.append(plan)
        if plan["manual_copy_required"]:
            warnings.append(
                f"Copy {filename} to the media path {plan['media_path']} before the rendered doc can display it."
            )
        return f"![{match.group('alt')}]({plan['media_token']})"

    normalized = MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.sub(replace, markdown)
    if inline_plans:
        summary["markdown_preview"] = normalized
        summary["media_plans"] = plans


def retarget_inline_raster_media_plans(
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
        if isinstance(plan, dict) and plan.get("source") != "inline_data_url" and str(plan.get("source_path") or "")
    }
    markdown = str(summary.get("markdown_preview") or "")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []

    for index, plan in enumerate(plans):
        if not isinstance(plan, dict):
            continue
        if plan.get("source") != "inline_data_url":
            continue
        old_token = str(plan.get("media_token") or "")
        old_filename = str(plan.get("source_path") or "")
        extension = Path(old_filename).suffix.lstrip(".") or "png"
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


def package_media_target_path(repo_root: Path, staging_root: Path, plan: dict[str, Any], scope: str) -> Path:
    filename = str(plan.get("source_path") or "").strip()
    if not filename or Path(filename).name != filename:
        raise ValueError(f"Invalid package media filename: {filename!r}")
    if plan.get("storage_mode") == "repo_assets":
        target_rel = Path(str(plan.get("repo_asset_path") or ""))
        if not str(target_rel) or target_rel.name != filename:
            raise ValueError(f"Invalid package media repo asset path: {target_rel.as_posix()!r}")
        target_root = scope_owned_media_root_for_scope(repo_root, scope_configs_for(repo_root)[scope])
        target_path = (repo_root / target_rel).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Package media target escapes repo assets root: {target_rel.as_posix()!r}")
        return target_path
    if plan.get("storage_mode") == "staging_manual":
        target_root = staging_root.resolve()
        target_path = (target_root / filename).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Package media filename escapes staging root: {filename!r}")
        return target_path
    if plan.get("storage_mode") == "external_assets":
        media_class = str(plan.get("media_class") or "").strip()
        target_root = (
            scope_owned_media_root_for_scope(repo_root, scope_configs_for(repo_root)[scope])
            / media_class
        ).resolve()
        target_path = (target_root / filename).resolve()
        if not target_path.is_relative_to(target_root):
            raise ValueError(f"Package media filename escapes external media root: {filename!r}")
        return target_path
    raise ValueError("Docs Import media storage mode is not available for package media writes.")


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


def materialize_package_media_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    package_root: Path,
    plans: list[dict[str, Any]],
    scope: str,
) -> list[dict[str, Any]]:
    package_plans = [
        plan
        for plan in plans
        if plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}
    ]
    if not package_plans:
        return []
    normalized_scope = normalize_media_scope(scope, repo_root)
    written: list[dict[str, Any]] = []
    for plan in package_plans:
        source_path = package_media_source_path(package_root, plan)
        target_path = package_media_target_path(repo_root, staging_root, plan, normalized_scope)
        if target_path.exists():
            target_display = (
                str(plan.get("media_path") or "")
                if plan.get("storage_mode") == "external_assets"
                else marker_path(target_path, workspace_root=workspace_root)
                if target_path.is_relative_to(workspace_root.resolve())
                else relative_path(repo_root, target_path)
            )
            raise FileExistsError(f"Package media target already exists: {target_display}")
        if plan.get("source") == "markdown_package_image":
            conversion_result = convert_package_image_to_webp(
                source_path,
                target_path,
                max_width=int((plan.get("conversion") or {}).get("max_width") or 800),
            )
            size_bytes = target_path.stat().st_size
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            conversion_result = {}
            size_bytes = target_path.stat().st_size
        written.append(
            {
                "source_path": plan.get("source_path", ""),
                "source_original_path": plan.get("source_original_path", ""),
                "staging_path": plan.get("staging_path") or (
                    str(plan.get("media_path") or "")
                    if plan.get("storage_mode") == "external_assets"
                    else marker_path(target_path, workspace_root=workspace_root)
                    if target_path.is_relative_to(workspace_root.resolve())
                    else relative_path(repo_root, target_path)
                ),
                "size_bytes": size_bytes,
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
                "media_class": plan.get("media_class", ""),
                "kind": plan.get("kind", ""),
                "conversion": conversion_result,
            }
        )
    return written


def materialize_inline_raster_media(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    import_preview: dict[str, Any],
    include_prompt_meta: bool,
    source_markdown: str = "",
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

    normalized_scope = normalize_media_scope(str(import_preview.get("scope")), repo_root)
    inline_plans = [plan for plan in plans if plan.get("source") == "inline_data_url"]
    source_file_plans = [plan for plan in plans if plan.get("source") != "inline_data_url"]
    valid_inline_matches: list[tuple[re.Match[str], bytes]] = []
    if inline_plans:
        raw_markdown = source_markdown or raw_markdown_for_inline_media(
            source_path,
            include_prompt_meta=include_prompt_meta,
        )
        for match in MARKDOWN_INLINE_RASTER_IMAGE_PATTERN.finditer(raw_markdown):
            try:
                decoded = base64.b64decode(match.group("data"), validate=True)
            except (binascii.Error, ValueError):
                continue
            valid_inline_matches.append((match, decoded))

        if len(valid_inline_matches) < len(inline_plans):
            raise RuntimeError("Inline media extraction plan no longer matches the staged source.")

    if media_config_for(normalized_scope, repo_root).storage_mode == "r2_upload":
        return publish_r2_import_media(
            repo_root,
            staging_root=staging_root,
            source_path=source_path,
            plans=plans,
            inline_plans=inline_plans,
            valid_inline_matches=valid_inline_matches,
            scope=normalized_scope,
        )

    package_written = materialize_package_media_plans(
        repo_root,
        staging_root,
        workspace_root,
        source_path,
        plans,
        normalized_scope,
    ) if source_path.is_dir() else []

    written: list[dict[str, Any]] = list(package_written)
    for plan, (_, decoded) in zip(inline_plans, valid_inline_matches):
        filename = str(plan.get("source_path") or "").strip()
        if not filename or Path(filename).name != filename:
            raise ValueError(f"Invalid inline media filename: {filename!r}")
        if plan.get("storage_mode") == "repo_assets":
            target_rel = Path(str(plan.get("repo_asset_path") or ""))
            if not str(target_rel) or target_rel.name != filename:
                raise ValueError(f"Invalid inline media repo asset path: {target_rel.as_posix()!r}")
            scope = normalized_scope
            target_root = scope_owned_media_root_for_scope(repo_root, scope_configs_for(repo_root)[scope])
            target_path = (repo_root / target_rel).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Inline media target escapes repo assets root: {target_rel.as_posix()!r}")
        elif plan.get("storage_mode") == "staging_manual":
            target_root = staging_root.resolve()
            target_path = (target_root / filename).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Inline media filename escapes staging root: {filename!r}")
        elif plan.get("storage_mode") == "external_assets":
            media_class = str(plan.get("media_class") or "").strip()
            target_root = (
                scope_owned_media_root_for_scope(repo_root, scope_configs_for(repo_root)[normalized_scope])
                / media_class
            ).resolve()
            target_path = (target_root / filename).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Inline media filename escapes external media root: {filename!r}")
        else:
            raise ValueError("Docs Import media storage mode is not available for inline media writes.")
        if target_path.exists():
            relative_target = (
                str(plan.get("media_path") or "")
                if plan.get("storage_mode") == "external_assets"
                else marker_path(target_path, workspace_root=workspace_root)
                if target_path.is_relative_to(workspace_root.resolve())
                else relative_path(repo_root, target_path)
            )
            raise FileExistsError(f"Inline media target already exists: {relative_target}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(decoded)
        written.append(
            {
                "source_path": filename,
                "staging_path": plan.get("staging_path", ""),
                "size_bytes": len(decoded),
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
                "media_class": plan.get("media_class", ""),
            }
        )
    for plan in source_file_plans:
        if plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}:
            continue
        if plan.get("storage_mode") not in {"external_assets", "repo_assets"}:
            continue
        filename = str(plan.get("source_path") or "").strip()
        if not filename or Path(filename).name != filename:
            raise ValueError(f"Invalid source media filename: {filename!r}")
        if filename != source_path.name:
            raise ValueError(f"Source media filename {filename!r} does not match staged source {source_path.name!r}")
        if plan.get("storage_mode") == "repo_assets":
            target_rel = Path(str(plan.get("repo_asset_path") or ""))
            if not str(target_rel) or target_rel.name != filename:
                raise ValueError(f"Invalid source media repo asset path: {target_rel.as_posix()!r}")
            target_root = scope_owned_media_root_for_scope(
                repo_root,
                scope_configs_for(repo_root)[normalized_scope],
            )
            target_path = (repo_root / target_rel).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Source media target escapes repo assets root: {target_rel.as_posix()!r}")
            target_display = target_rel.as_posix()
        else:
            media_class = str(plan.get("media_class") or "").strip()
            target_root = (
                scope_owned_media_root_for_scope(repo_root, scope_configs_for(repo_root)[normalized_scope])
                / media_class
            ).resolve()
            target_path = (target_root / filename).resolve()
            if not target_path.is_relative_to(target_root):
                raise ValueError(f"Source media filename escapes external media root: {filename!r}")
            target_display = f"media/{media_class}/{filename}"
        if target_path.exists():
            raise FileExistsError(f"Source media target already exists: {target_display}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        written.append(
            {
                "source_path": filename,
                "staging_path": marker_path(source_path, workspace_root=workspace_root),
                "size_bytes": target_path.stat().st_size,
                "media_path": plan.get("media_path", ""),
                "media_token": plan.get("media_token", ""),
                "media_link": plan.get("media_link", plan.get("media_token", "")),
                "repo_asset_path": plan.get("repo_asset_path", ""),
                "public_path": plan.get("public_path", ""),
                "storage_mode": plan.get("storage_mode", ""),
                "media_class": plan.get("media_class", ""),
            }
        )
    return written


def publish_r2_import_media(
    repo_root: Path,
    *,
    staging_root: Path,
    source_path: Path,
    plans: list[dict[str, Any]],
    inline_plans: list[dict[str, Any]],
    valid_inline_matches: list[tuple[re.Match[str], bytes]],
    scope: str,
) -> list[dict[str, Any]]:
    """Prepare one import record's complete media set and publish before its source write."""

    config = scope_configs_for(repo_root)[scope]
    inline_bytes = {
        id(plan): decoded
        for plan, (_match, decoded) in zip(inline_plans, valid_inline_matches)
    }
    prepared: list[tuple[dict[str, Any], Path, Path, dict[str, Any]]] = []
    with tempfile.TemporaryDirectory(prefix="docs-media-r2-") as temp_dir:
        temp_root = Path(temp_dir).resolve()
        for plan in plans:
            filename = str(plan.get("source_path") or "").strip()
            media_class = str(plan.get("media_class") or "").strip()
            if not filename or Path(filename).name != filename:
                raise ValueError(f"Invalid R2 Docs media filename: {filename!r}")
            conversion_result: dict[str, Any] = {}
            source_kind = str(plan.get("source") or "")
            if source_kind == "inline_data_url":
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
                prepared_path = package_media_source_path(source_path, plan)
                prepared_root = source_path.resolve()
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
                "repo_asset_path": "",
                "public_path": "",
                "storage_mode": "r2_upload",
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


def media_path_prefix_for(scope: str, *, repo_root: Path | None = None) -> str:
    normalized_scope = normalize_media_scope(scope, repo_root)
    if repo_root is None:
        prefix = MEDIA_PATH_PREFIXES[normalized_scope]
    else:
        prefix = scope_configs_for(repo_root)[normalized_scope].media_path_prefix
    return prefix.as_posix().strip("/")


def media_path_for(scope: str, media_class: str, filename: str, *, repo_root: Path | None = None) -> str:
    return f"{media_path_prefix_for(scope, repo_root=repo_root)}/{media_class}/{filename}"


def repo_asset_rel_path_for(
    scope: str,
    media_class: str,
    filename: str,
    *,
    repo_root: Path | None = None,
) -> str:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, repo_root)
    return (config.repo_assets_path_prefix / media_class / filename).as_posix()


def repo_asset_public_path_for(
    scope: str,
    media_class: str,
    filename: str,
    *,
    repo_root: Path | None = None,
) -> str:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, repo_root)
    return f"{config.repo_assets_public_path_prefix}/{media_class}/{filename}"


def media_link_for(
    scope: str,
    media_class: str,
    filename: str,
    *,
    repo_root: Path | None = None,
) -> str:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, repo_root)
    if config.storage_mode == "repo_assets":
        return repo_asset_public_path_for(normalized_scope, media_class, filename, repo_root=repo_root)
    if config.storage_mode == "staging_manual":
        return media_token(normalized_scope, media_class, filename, repo_root=repo_root)
    if config.storage_mode == "r2_upload":
        return media_token(normalized_scope, media_class, filename, repo_root=repo_root)
    if config.storage_mode == "external_assets":
        return local_media_route(normalized_scope, media_class, filename)
    raise ValueError(f"Unsupported Docs Import media storage mode: {config.storage_mode!r}")


def build_media_plan(
    scope: str,
    media_class: str,
    source_path: Path,
    title: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    normalized_scope = normalize_media_scope(scope, repo_root)
    config = media_config_for(normalized_scope, repo_root)
    link = media_link_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
    if config.storage_mode == "repo_assets":
        media_path = repo_asset_rel_path_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
    elif config.storage_mode == "external_assets":
        media_path = f"media/{media_class}/{source_path.name}"
    else:
        media_path = media_path_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
    return {
        "storage_mode": config.storage_mode,
        "manual_copy_required": config.storage_mode == "staging_manual",
        "media_class": media_class,
        "source_path": source_path.name,
        "media_path": media_path,
        "media_token": link,
        "media_link": link,
        "title": title,
        "repo_asset_path": (
            repo_asset_rel_path_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
            if config.storage_mode == "repo_assets"
            else ""
        ),
        "public_path": (
            repo_asset_public_path_for(normalized_scope, media_class, source_path.name, repo_root=repo_root)
            if config.storage_mode == "repo_assets"
            else ""
        ),
    }


def build_image_summary(source_path: Path, scope: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    title = humanize(source_path.stem) or "Imported Image"
    plan = build_media_plan(scope, "img", source_path, title, repo_root=repo_root)
    markdown = f"# {title}\n\n![{title}]({plan['media_token']})"
    warnings = []
    if plan["manual_copy_required"]:
        warnings.append(
            f"Copy {source_path.name} to the media path {plan['media_path']} before the rendered doc can display it."
        )
    return {
        "title": title,
        "title_source": "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": 0,
            "links": 0,
            "images": 1,
            "svg": 0,
            "details": 0,
            "size_bytes": source_path.stat().st_size,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 1,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "media_plan": plan,
    }


def build_file_media_summary(source_path: Path, scope: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    title = humanize(source_path.stem) or "Imported File"
    plan = build_media_plan(scope, "files", source_path, title, repo_root=repo_root)
    markdown = f"# {title}\n\n[Download {title}]({plan['media_token']})"
    warnings = []
    if plan["manual_copy_required"]:
        warnings.append(
            f"Copy {source_path.name} to the media path {plan['media_path']} before the rendered download link will work."
        )
    return {
        "title": title,
        "title_source": "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": 0,
            "links": 1,
            "images": 0,
            "svg": 0,
            "details": 0,
            "size_bytes": source_path.stat().st_size,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "media_plan": plan,
    }
