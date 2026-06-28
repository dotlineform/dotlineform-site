#!/usr/bin/env python3
"""Service helpers for Docs Management staged source imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

from docs_import_common import is_interactive_html_import_asset
from docs_import_markdown_package import retarget_markdown_package_media_plans
from docs_import_media import (
    materialize_inline_raster_media,
    retarget_inline_raster_media_plans,
)
from docs_import_preview import (
    generate_import_preview,
    list_staged_import_source_files,
    resolve_staged_import_source,
)
from docs_import_source_helpers import (
    apply_replacement_doc_id_to_preview,
    apply_replacement_title_to_preview,
    imported_source_text_for_create,
    imported_source_text_for_overwrite,
    import_summary_text,
    interactive_html_overwrite_summary,
    relative_path,
    viewer_url_for,
)
from docs_import_source_interactive import (
    ensure_interactive_html_targets_available,
    interactive_html_asset_plans,
    materialize_interactive_html_assets,
)
from docs_management_mutations import metadata_search_doc_ids
from docs_source_model import (
    default_viewable_for_scope,
    load_scope_docs,
    normalize_scope,
    scope_root,
    write_text_atomic,
)


LogEvent = Callable[[Path, str, Dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ImportSourceDependencies:
    log_event: LogEvent
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild


def handle_import_source_files(repo_root: Path) -> Dict[str, Any]:
    return {
        "ok": True,
        "files": list_staged_import_source_files(repo_root),
    }


def handle_import_source(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    dependencies: ImportSourceDependencies,
) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    include_prompt_meta = bool(body.get("include_prompt_meta"))
    overwrite_doc_id = str(body.get("overwrite_doc_id") or "").strip()
    confirm_overwrite = bool(body.get("confirm_overwrite"))
    preview_only = bool(body.get("preview_only"))
    replacement_doc_id = str(body.get("replacement_doc_id") or "").strip()
    replacement_title = str(body.get("replacement_title") or "").strip()
    source_path = resolve_staged_import_source(repo_root, staged_filename)
    if is_interactive_html_import_asset(source_path):
        raise ValueError("interactive HTML script files cannot be selected as the primary import source")
    preview = generate_import_preview(
        repo_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
    )
    interactive_plans = interactive_html_asset_plans(repo_root, scope)
    if interactive_plans:
        preview["interactive_html_plans"] = interactive_plans
        for interactive_plan in interactive_plans:
            if not interactive_plan.get("target_exists"):
                continue
            preview.setdefault("warnings", []).append(
                f"Interactive HTML asset target already exists: {interactive_plan['target_path']}."
            )
    if replacement_doc_id:
        apply_replacement_doc_id_to_preview(preview, replacement_doc_id)
        retarget_markdown_package_media_plans(repo_root, preview, scope)
        retarget_inline_raster_media_plans(repo_root, preview, scope)
    elif replacement_title:
        apply_replacement_title_to_preview(preview, replacement_title)
        retarget_markdown_package_media_plans(repo_root, preview, scope)
        retarget_inline_raster_media_plans(repo_root, preview, scope)

    docs = load_scope_docs(repo_root, scope)
    proposed_doc_id = str(preview["proposed_doc_id"])
    collision_doc = next(
        (doc for doc in docs if doc.doc_id == proposed_doc_id or doc.path.stem == proposed_doc_id),
        None,
    )
    collision = {
        "exists": collision_doc is not None,
        "doc_id": collision_doc.doc_id if collision_doc else "",
        "title": collision_doc.title if collision_doc else "",
        "path": relative_path(repo_root, collision_doc.path) if collision_doc else "",
        "stem": collision_doc.path.stem if collision_doc else "",
    }
    preview["doc_id_collision"] = collision
    replacement_required = collision_doc is not None and not (overwrite_doc_id and confirm_overwrite)
    preview["replacement_doc_id_required"] = replacement_required
    preview["replacement_title_required"] = replacement_required

    if overwrite_doc_id and collision_doc is None:
        raise ValueError("overwrite_doc_id is only allowed when the generated import target collides with an existing doc")
    if overwrite_doc_id and collision_doc and overwrite_doc_id != collision_doc.doc_id:
        raise ValueError(f"overwrite_doc_id must match the colliding doc_id {collision_doc.doc_id!r}")

    requires_doc_overwrite_confirmation = collision_doc is not None and not (overwrite_doc_id and confirm_overwrite)
    existing_interactive_plans = [plan for plan in interactive_plans if plan.get("target_exists")]
    requires_interactive_html_confirmation = bool(existing_interactive_plans and not confirm_overwrite)
    requires_overwrite_confirmation = requires_doc_overwrite_confirmation or requires_interactive_html_confirmation
    if requires_doc_overwrite_confirmation:
        preview.setdefault("warnings", []).append(
            f"Proposed filename {preview['proposed_doc_id']}.md already exists in {scope}; enter a replacement doc_id before import."
        )
    if requires_interactive_html_confirmation:
        for interactive_plan in existing_interactive_plans:
            preview.setdefault("warnings", []).append(
                f"Interactive HTML asset {interactive_plan['target_path']} already exists; confirm overwrite to replace it."
            )

    if dry_run or preview_only or requires_overwrite_confirmation:
        dependencies.log_event(
            repo_root,
            "docs-import-html-preview",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "source_format": preview.get("source_format"),
                "include_prompt_meta": include_prompt_meta,
                "proposed_doc_id": preview["proposed_doc_id"],
                "collision": collision["exists"],
                "inline_media_count": len(preview.get("media_plans") or []),
                "interactive_html_asset_count": len(interactive_plans),
                "requires_overwrite_confirmation": requires_overwrite_confirmation,
                "requires_doc_overwrite_confirmation": requires_doc_overwrite_confirmation,
                "requires_interactive_html_confirmation": requires_interactive_html_confirmation,
                "replacement_doc_id_required": bool(preview.get("replacement_doc_id_required")),
                "replacement_title_required": bool(preview.get("replacement_title_required")),
            },
        )
        return {
            "ok": True,
            "scope": scope,
            "staged_filename": staged_filename,
            "include_prompt_meta": include_prompt_meta,
            "preview_only": True,
            "requires_overwrite_confirmation": requires_overwrite_confirmation,
            "requires_doc_overwrite_confirmation": requires_doc_overwrite_confirmation,
            "requires_interactive_html_confirmation": requires_interactive_html_confirmation,
            "replacement_doc_id_required": bool(preview.get("replacement_doc_id_required")),
            "replacement_title_required": bool(preview.get("replacement_title_required")),
            "collision": collision,
            "import_preview": preview,
            "summary_text": (
                f"Replacement doc_id required for {preview['proposed_doc_id']}."
                if requires_doc_overwrite_confirmation
                else interactive_html_overwrite_summary(existing_interactive_plans)
                if requires_interactive_html_confirmation and existing_interactive_plans
                else f"Prepared import preview for {staged_filename}."
            ),
            "dry_run": dry_run,
        }

    rebuild = None
    inline_media_written: list[dict[str, Any]] = []
    interactive_html_written: list[Dict[str, Any]] = []
    ensure_interactive_html_targets_available(interactive_plans, allow_overwrite=confirm_overwrite)
    if collision_doc is not None:
        source_text = imported_source_text_for_overwrite(preview, collision_doc)
        overwrite_title = str(preview.get("title") or collision_doc.title).strip() or collision_doc.title
        search_doc_ids = metadata_search_doc_ids(
            docs,
            collision_doc.doc_id,
            title_changed=overwrite_title != collision_doc.title,
        )
        if not dry_run:
            def write_import_artifacts() -> None:
                nonlocal inline_media_written, interactive_html_written
                inline_media_written = materialize_inline_raster_media(
                    repo_root,
                    source_path=source_path,
                    import_preview=preview,
                    include_prompt_meta=include_prompt_meta,
                )
                interactive_html_written = materialize_interactive_html_assets(
                    repo_root,
                    interactive_plans,
                    allow_overwrite=confirm_overwrite,
                )
                write_text_atomic(collision_doc.path, source_text)

            rebuild = dependencies.perform_source_write_and_rebuild(
                repo_root,
                scope,
                [collision_doc.path],
                write_import_artifacts,
                suppression_reason="docs-import-html-overwrite",
                docs_doc_ids=[collision_doc.doc_id],
                search_doc_ids=search_doc_ids,
            )
        dependencies.log_event(
            repo_root,
            "docs-import-html-overwrite",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "source_format": preview.get("source_format"),
                "inline_media_count": len(preview.get("media_plans") or []),
                "interactive_html_asset_count": len(interactive_plans),
                "doc_id": collision_doc.doc_id,
                "path": relative_path(repo_root, collision_doc.path),
                "include_prompt_meta": include_prompt_meta,
            },
        )
        return {
            "ok": True,
            "scope": scope,
            "staged_filename": staged_filename,
            "include_prompt_meta": include_prompt_meta,
            "preview_only": False,
            "requires_overwrite_confirmation": False,
            "requires_doc_overwrite_confirmation": False,
            "requires_interactive_html_confirmation": False,
            "operation": "overwrite",
            "doc_id": collision_doc.doc_id,
            "path": relative_path(repo_root, collision_doc.path),
            "viewer_url": viewer_url_for(scope, collision_doc.doc_id),
            "title": preview["title"],
            "record": {
                "doc_id": collision_doc.doc_id,
                "title": preview["title"],
                "parent_id": collision_doc.parent_id,
                "viewable": collision_doc.viewable,
            },
            "collision": collision,
            "import_preview": preview,
            "inline_media_written": inline_media_written,
            "interactive_html_written": interactive_html_written,
            "rebuild": rebuild,
            "summary_text": import_summary_text(
                "overwrite",
                collision_doc.doc_id,
                staged_filename,
                interactive_html_written,
            ),
            "dry_run": dry_run,
        }

    doc_id = preview["proposed_doc_id"]
    target_path = scope_root(repo_root, scope) / f"{doc_id}.md"
    source_text = imported_source_text_for_create(preview, docs, scope)
    if not dry_run:
        def write_import_artifacts() -> None:
            nonlocal inline_media_written, interactive_html_written
            inline_media_written = materialize_inline_raster_media(
                repo_root,
                source_path=source_path,
                import_preview=preview,
                include_prompt_meta=include_prompt_meta,
            )
            interactive_html_written = materialize_interactive_html_assets(
                repo_root,
                interactive_plans,
                allow_overwrite=confirm_overwrite,
            )
            write_text_atomic(target_path, source_text)

        rebuild = dependencies.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target_path],
            write_import_artifacts,
            suppression_reason="docs-import-html-create",
            docs_doc_ids=[doc_id],
            search_doc_ids=[doc_id],
        )
    dependencies.log_event(
        repo_root,
        "docs-import-html-create",
        {
            "scope": scope,
            "staged_filename": staged_filename,
            "source_format": preview.get("source_format"),
            "inline_media_count": len(preview.get("media_plans") or []),
            "interactive_html_asset_count": len(interactive_plans),
            "doc_id": doc_id,
            "path": relative_path(repo_root, target_path),
            "include_prompt_meta": include_prompt_meta,
        },
    )
    return {
        "ok": True,
        "scope": scope,
        "staged_filename": staged_filename,
        "include_prompt_meta": include_prompt_meta,
        "preview_only": False,
        "requires_overwrite_confirmation": False,
        "requires_doc_overwrite_confirmation": False,
        "requires_interactive_html_confirmation": False,
        "operation": "create",
        "doc_id": doc_id,
        "path": relative_path(repo_root, target_path),
        "viewer_url": viewer_url_for(scope, doc_id),
        "title": preview["title"],
        "record": {
            "doc_id": doc_id,
            "title": preview["title"],
            "parent_id": "",
            "viewable": default_viewable_for_scope(scope),
        },
        "collision": collision,
        "import_preview": preview,
        "inline_media_written": inline_media_written,
        "interactive_html_written": interactive_html_written,
        "rebuild": rebuild,
        "summary_text": import_summary_text("create", doc_id, staged_filename, interactive_html_written),
        "dry_run": dry_run,
    }
