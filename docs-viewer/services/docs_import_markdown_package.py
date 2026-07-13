#!/usr/bin/env python3
"""Markdown package discovery and media-link rewriting for Docs imports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from docs_import_common import (
    APPLE_NOTES_CAPTION_SPAN_PATTERN,
    FILE_MEDIA_STAGED_SUFFIXES,
    MARKDOWN_IMAGE_REWRITE_PATTERN,
    MARKDOWN_LINK_REWRITE_PATTERN,
    MARKDOWN_STAGED_SUFFIXES,
    RASTER_IMAGE_STAGED_SUFFIXES,
    humanize,
    normalize_scope,
    normalize_space,
    slugify,
)
from docs_import_media import build_media_plan
from docs_media_storage import local_media_root_for_scope
from docs_scope_config import load_docs_scope_configs
from services.paths import marker_path

def retarget_markdown_package_media_plans(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    package_root: Path,
    summary: dict[str, Any],
    scope: str,
) -> None:
    plans = summary.get("media_plans")
    if not isinstance(plans, list) or not plans:
        return
    package_indices = [
        index
        for index, plan in enumerate(plans)
        if isinstance(plan, dict) and plan.get("source") in {"markdown_package_image", "markdown_package_attachment"}
    ]
    if not package_indices:
        return

    package_root = package_root.resolve()
    proposed_doc_id = str(summary.get("proposed_doc_id") or summary.get("title") or "imported-doc")
    used_filenames: set[str] = set()
    markdown = str(summary.get("markdown_preview") or "")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    image_index = 0

    for index in package_indices:
        plan = plans[index]
        assert isinstance(plan, dict)
        old_token = str(plan.get("media_token") or "")
        old_filename = str(plan.get("source_path") or "")
        old_title = str(plan.get("title") or "")
        kind = str(plan.get("kind") or "")
        source_relative = str(plan.get("package_relative_source_path") or "")
        source_path = (package_root / source_relative).resolve()
        if not source_path.is_relative_to(package_root):
            raise ValueError("Package media source escapes package root.")
        media_class = "img" if kind == "image" else "files"
        suffix = "image" if kind == "image" else "attachment"
        extension = "webp" if kind == "image" else Path(old_filename).suffix.lstrip(".")
        if kind == "image":
            image_index += 1
            new_title = readable_package_image_title(proposed_doc_id, image_index)
        else:
            new_title = str(plan.get("title") or humanize(source_path.stem) or old_filename)
        new_filename = next_package_media_filename(
            repo_root,
            staging_root,
            scope,
            proposed_doc_id,
            media_class,
            suffix,
            extension,
            used_filenames,
        )
        new_plan = build_package_media_plan(
            repo_root,
            staging_root,
            workspace_root,
            scope,
            package_root=package_root,
            source_path=source_path,
            filename=new_filename,
            title=new_title,
            kind=kind,
        )
        if old_token:
            if kind == "image" and old_title:
                old_markdown = f'![{old_title}]({old_token} "{old_title}")'
                new_markdown = f'![{new_title}]({new_plan["media_token"]} "{new_title}")'
                if old_markdown in markdown:
                    markdown = markdown.replace(old_markdown, new_markdown, 1)
                else:
                    markdown = markdown.replace(old_token, new_plan["media_token"], 1)
            else:
                markdown = markdown.replace(old_token, new_plan["media_token"], 1)
        if old_filename != new_filename:
            for warning_index, warning in enumerate(warnings):
                if isinstance(warning, str) and old_filename in warning:
                    warnings[warning_index] = warning.replace(old_filename, new_filename).replace(
                        str(plan.get("media_path") or ""),
                        new_plan["media_path"],
                    )
        plans[index] = new_plan
    summary["markdown_preview"] = markdown

def normalize_apple_notes_caption_spans(markdown: str) -> str:
    def replace(match: re.Match[str]) -> str:
        attrs = f"{match.group('attrs') or ''}{match.group('tail') or ''}"
        attrs = re.sub(r'\sstyle="[^"]*"', "", attrs, flags=re.IGNORECASE)
        style = str(match.group("style") or "")
        style_parts = [
            part.strip()
            for part in style.split(";")
            if part.strip() and not part.strip().lower().startswith("font-size:")
        ]
        style_parts.insert(0, "font-size: var(--font-caption)")
        body = str(match.group("body") or "").strip()
        normalized_attrs = normalize_space(attrs)
        attr_text = f" {normalized_attrs}" if normalized_attrs else ""
        return f'<span{attr_text} style="{"; ".join(style_parts)};">{body}</span>'

    return APPLE_NOTES_CAPTION_SPAN_PATTERN.sub(replace, markdown or "")

def is_external_or_special_markdown_target(target: str) -> bool:
    value = str(target or "").strip()
    if not value:
        return True
    if value.startswith("#"):
        return True
    parsed = urlsplit(value)
    return bool(parsed.scheme or parsed.netloc)


def resolve_package_link_target(package_root: Path, markdown_path: Path, target: str) -> Path | None:
    if is_external_or_special_markdown_target(target):
        return None
    parsed = urlsplit(str(target or ""))
    if parsed.query or parsed.fragment:
        return None
    raw_path = unquote(parsed.path or "")
    if not raw_path or raw_path.startswith("/"):
        return None
    resolved = (markdown_path.parent / raw_path).resolve()
    package_resolved = package_root.resolve()
    if not resolved.is_relative_to(package_resolved):
        return None
    return resolved


def package_source_original_path(source_path: Path, workspace_root: Path) -> str:
    return marker_path(source_path, workspace_root=workspace_root)


def next_package_media_filename(
    repo_root: Path,
    staging_root: Path,
    scope: str,
    doc_id: str,
    media_class: str,
    suffix: str,
    extension: str,
    used_filenames: set[str],
) -> str:
    normalized_scope = normalize_scope(scope)
    safe_doc_id = slugify(doc_id or "imported-doc")
    safe_extension = extension.lower().lstrip(".")
    staging_root = staging_root.resolve()
    scope_config = load_docs_scope_configs(repo_root)[normalized_scope]
    storage_mode = scope_config.import_media_storage.storage_mode
    local_asset_root = (
        (local_media_root_for_scope(repo_root, scope_config) / media_class).resolve()
        if storage_mode in {"external_assets", "repo_assets"}
        else None
    )
    index = 1
    while True:
        filename = f"{safe_doc_id}-{suffix}-{index:02d}.{safe_extension}"
        local_asset_path = (local_asset_root / filename).resolve() if local_asset_root is not None else None
        if (
            filename not in used_filenames
            and not (staging_root / filename).exists()
            and not (local_asset_path and local_asset_path.exists())
        ):
            used_filenames.add(filename)
            return filename
        index += 1


def build_package_media_plan(
    repo_root: Path,
    staging_root: Path,
    workspace_root: Path,
    scope: str,
    *,
    package_root: Path,
    source_path: Path,
    filename: str,
    title: str,
    kind: str,
) -> dict[str, Any]:
    media_class = "img" if kind == "image" else "files"
    plan = build_media_plan(scope, media_class, Path(filename), title, repo_root=repo_root)
    source_rel = package_source_original_path(source_path, workspace_root)
    plan.update(
        {
            "source": f"markdown_package_{kind}",
            "kind": kind,
            "source_original_path": source_rel,
            "package_relative_source_path": source_path.resolve().relative_to(package_root.resolve()).as_posix(),
        }
    )
    if kind == "image":
        plan["conversion"] = {
            "format": "webp",
            "max_width": 800,
            "resize_only_if_wider": True,
        }
    if plan["manual_copy_required"]:
        plan["staging_path"] = marker_path(staging_root / filename, workspace_root=workspace_root)
    return plan


def package_media_warning(plan: dict[str, Any]) -> str:
    if plan.get("kind") == "attachment":
        return (
            f"Copy {plan.get('source_path')} to the media path {plan.get('media_path')} "
            "before the rendered download link will work."
        )
    return (
        f"Copy {plan.get('source_path')} to the media path {plan.get('media_path')} "
        "before the rendered doc can display it."
    )


def readable_package_image_title(doc_id: str, image_index: int) -> str:
    base = slugify(doc_id or "imported-doc").replace("-", " ") or "imported doc"
    return f"{base} image {image_index:02d}"


def find_package_markdown_file(package_root: Path) -> Path:
    markdown_files = sorted(
        [
            path
            for path in package_root.rglob("*")
            if path.is_file() and path.suffix.lower() in MARKDOWN_STAGED_SUFFIXES
        ],
        key=lambda path: path.relative_to(package_root).as_posix().lower(),
    )
    if not markdown_files:
        raise ValueError(f"Markdown package {package_root.name!r} does not contain a Markdown file.")
    if len(markdown_files) > 1:
        names = ", ".join(path.relative_to(package_root).as_posix() for path in markdown_files[:5])
        if len(markdown_files) > 5:
            names += ", ..."
        raise ValueError(f"Markdown package {package_root.name!r} contains multiple Markdown files: {names}")
    return markdown_files[0]


def rewrite_markdown_package_media_links(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    package_root: Path,
    markdown_path: Path,
    summary: dict[str, Any],
    scope: str,
) -> None:
    markdown = str(summary.get("markdown_preview") or "")
    doc_id = str(summary.get("proposed_doc_id") or package_root.name or "imported-doc")
    plans: list[dict[str, Any]] = []
    warnings = summary.setdefault("warnings", [])
    used_filenames: set[str] = set()
    plans_by_target: dict[str, dict[str, Any]] = {}
    unresolved_count = 0
    unsupported_count = 0

    def plan_for_image(target: str, alt: str) -> dict[str, Any] | None:
        nonlocal unresolved_count, unsupported_count
        source = resolve_package_link_target(package_root, markdown_path, target)
        if source is None:
            return None
        key = source.as_posix()
        if key in plans_by_target:
            return plans_by_target[key]
        if not source.exists() or not source.is_file():
            unresolved_count += 1
            warnings.append(f"Package image target was not found: {target}")
            return None
        suffix = source.suffix.lower()
        if suffix not in RASTER_IMAGE_STAGED_SUFFIXES:
            unsupported_count += 1
            warnings.append(f"Unsupported package image type {suffix or '(none)'} for {target}; left the link unchanged.")
            return None
        image_index = len([plan for plan in plans if plan.get("kind") == "image"]) + 1
        filename = next_package_media_filename(repo_root, staging_root, scope, doc_id, "img", "image", "webp", used_filenames)
        title = readable_package_image_title(doc_id, image_index)
        plan = build_package_media_plan(
            repo_root,
            staging_root,
            workspace_root,
            scope,
            package_root=package_root,
            source_path=source,
            filename=filename,
            title=title,
            kind="image",
        )
        plans.append(plan)
        plans_by_target[key] = plan
        if plan["manual_copy_required"]:
            warnings.append(package_media_warning(plan))
        return plan

    def plan_for_attachment(target: str, label: str) -> dict[str, Any] | None:
        nonlocal unresolved_count, unsupported_count
        source = resolve_package_link_target(package_root, markdown_path, target)
        if source is None:
            return None
        key = source.as_posix()
        if key in plans_by_target:
            return plans_by_target[key]
        if not source.exists() or not source.is_file():
            unresolved_count += 1
            warnings.append(f"Package attachment target was not found: {target}")
            return None
        suffix = source.suffix.lower()
        if suffix in RASTER_IMAGE_STAGED_SUFFIXES:
            return None
        if suffix not in FILE_MEDIA_STAGED_SUFFIXES:
            unsupported_count += 1
            warnings.append(f"Unsupported package attachment type {suffix or '(none)'} for {target}; left the link unchanged.")
            return None
        filename = next_package_media_filename(repo_root, staging_root, scope, doc_id, "files", "attachment", suffix, used_filenames)
        title = normalize_space(label) or humanize(source.stem) or f"Attachment {len([plan for plan in plans if plan.get('kind') == 'attachment']) + 1:02d}"
        plan = build_package_media_plan(
            repo_root,
            staging_root,
            workspace_root,
            scope,
            package_root=package_root,
            source_path=source,
            filename=filename,
            title=title,
            kind="attachment",
        )
        plans.append(plan)
        plans_by_target[key] = plan
        if plan["manual_copy_required"]:
            warnings.append(package_media_warning(plan))
        return plan

    def replace_image(match: re.Match[str]) -> str:
        target = match.group("target")
        if str(target or "").startswith("data:image/"):
            return match.group(0)
        plan = plan_for_image(target, match.group("alt"))
        if not plan:
            return match.group(0)
        title = str(plan.get("title") or "").replace('"', r"\"")
        return f"![{plan['title']}]({plan['media_token']} \"{title}\")"

    def replace_link(match: re.Match[str]) -> str:
        plan = plan_for_attachment(match.group("target"), match.group("label"))
        if not plan:
            return match.group(0)
        return f"[{match.group('label')}]({plan['media_token']}{match.group('title') or ''})"

    markdown = MARKDOWN_IMAGE_REWRITE_PATTERN.sub(replace_image, markdown)
    markdown = MARKDOWN_LINK_REWRITE_PATTERN.sub(replace_link, markdown)
    summary["markdown_preview"] = markdown
    if plans:
        summary["media_plans"] = plans
    summary["source_stats"]["images"] = int(summary["source_stats"].get("images") or 0)
    summary["source_stats"]["attachments"] = len([plan for plan in plans if plan.get("kind") == "attachment"])
    summary["package_media_summary"] = {
        "planned": len(plans),
        "images": len([plan for plan in plans if plan.get("kind") == "image"]),
        "attachments": len([plan for plan in plans if plan.get("kind") == "attachment"]),
        "unresolved": unresolved_count,
        "unsupported": unsupported_count,
    }
