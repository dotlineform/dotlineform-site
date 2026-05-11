#!/usr/bin/env python3
"""Service helpers for Docs Management staged source imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from docs_html_import import (
    generate_import_preview,
    list_staged_import_source_files,
    materialize_inline_raster_media,
    resolve_staged_import_source,
    retarget_inline_raster_media_plans,
)
from docs_management_mutations import metadata_search_doc_ids
from docs_scope_config import DOCS_SCOPE_CONFIGS
from docs_source_model import (
    ScopeDoc,
    current_doc_timestamp,
    default_hidden_for_scope,
    default_viewable_for_scope,
    format_source,
    load_scope_docs,
    normalize_scope,
    next_sort_order,
    scope_root,
    slugify,
    write_text_atomic,
)


LogEvent = Callable[[Path, str, Dict[str, Any]], None]
MakeBackupBundle = Callable[[Path, str, str, list[ScopeDoc], Optional[Dict[str, Any]]], Path]
MakeImportOverwriteBackup = Callable[[Path, str, ScopeDoc, Optional[Dict[str, Any]]], Path]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ImportSourceDependencies:
    log_event: LogEvent
    make_backup_bundle: MakeBackupBundle
    make_import_overwrite_backup: MakeImportOverwriteBackup
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}&mode=manage"


def handle_import_source_files(repo_root: Path) -> Dict[str, Any]:
    return {
        "ok": True,
        "files": list_staged_import_source_files(repo_root),
    }


def imported_body_markdown(preview: Dict[str, Any]) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    markdown = str(preview.get("markdown_preview") or "").strip()
    if markdown:
        return markdown + "\n"
    return f"# {title}\n"


def imported_source_text_for_create(preview: Dict[str, Any], docs: list[ScopeDoc], scope: str) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    timestamp = current_doc_timestamp()
    front_matter = {
        "doc_id": preview["proposed_doc_id"],
        "title": title,
        "added_date": timestamp,
        "last_updated": timestamp,
        "parent_id": "",
        "sort_order": next_sort_order(docs, ""),
        "published": True,
        "hidden": default_hidden_for_scope(scope),
    }
    return format_source(front_matter, imported_body_markdown(preview))


def imported_source_text_for_overwrite(preview: Dict[str, Any], target: ScopeDoc) -> str:
    title = str(preview.get("title") or target.title).strip() or target.title
    timestamp = current_doc_timestamp()
    front_matter = dict(target.front_matter)
    front_matter["doc_id"] = target.doc_id
    front_matter["title"] = title
    front_matter["added_date"] = str(front_matter.get("added_date") or front_matter.get("last_updated") or timestamp).strip()
    front_matter["last_updated"] = timestamp
    front_matter["parent_id"] = target.parent_id
    front_matter.setdefault("published", True)
    front_matter.setdefault("hidden", target.hidden)
    front_matter.pop("viewable", None)
    if target.sort_order is None:
        front_matter.pop("sort_order", None)
    else:
        front_matter["sort_order"] = target.sort_order
    return format_source(front_matter, imported_body_markdown(preview))


def apply_replacement_title_to_preview(preview: Dict[str, Any], replacement_title: str) -> None:
    title = str(replacement_title or "").strip()
    if not title:
        raise ValueError("replacement_title is required when the proposed doc_id collides")
    preview["title"] = title
    preview["title_source"] = "replacement_title"
    preview["proposed_doc_id"] = slugify(title)
    preview["proposed_doc_id_source"] = "replacement_title"
    markdown = str(preview.get("markdown_preview") or "")
    if markdown.startswith("# "):
        lines = markdown.splitlines()
        if lines:
            lines[0] = f"# {title}"
            preview["markdown_preview"] = "\n".join(lines)


def apply_replacement_doc_id_to_preview(preview: Dict[str, Any], replacement_doc_id: str) -> None:
    raw_doc_id = str(replacement_doc_id or "").strip()
    doc_id = slugify(raw_doc_id)
    if not doc_id:
        raise ValueError("replacement_doc_id is required when the proposed filename collides")
    preview["proposed_doc_id"] = doc_id
    preview["proposed_doc_id_source"] = "replacement_doc_id"


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
    preview = generate_import_preview(
        repo_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
    )
    if replacement_doc_id:
        apply_replacement_doc_id_to_preview(preview, replacement_doc_id)
        retarget_inline_raster_media_plans(repo_root, preview, scope)
    elif replacement_title:
        apply_replacement_title_to_preview(preview, replacement_title)
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

    requires_overwrite_confirmation = collision_doc is not None and not (overwrite_doc_id and confirm_overwrite)
    if requires_overwrite_confirmation:
        preview.setdefault("warnings", []).append(
            f"Proposed filename {preview['proposed_doc_id']}.md already exists in {scope}; enter a replacement doc_id before import."
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
                "requires_overwrite_confirmation": requires_overwrite_confirmation,
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
            "replacement_doc_id_required": bool(preview.get("replacement_doc_id_required")),
            "replacement_title_required": bool(preview.get("replacement_title_required")),
            "collision": collision,
            "import_preview": preview,
            "summary_text": (
                f"Replacement doc_id required for {preview['proposed_doc_id']}."
                if requires_overwrite_confirmation
                else f"Prepared import preview for {staged_filename}."
            ),
            "dry_run": dry_run,
        }

    backup_dir = None
    rebuild = None
    inline_media_written: list[dict[str, Any]] = []
    if collision_doc is not None:
        source_text = imported_source_text_for_overwrite(preview, collision_doc)
        overwrite_title = str(preview.get("title") or collision_doc.title).strip() or collision_doc.title
        search_doc_ids = metadata_search_doc_ids(
            docs,
            collision_doc.doc_id,
            title_changed=overwrite_title != collision_doc.title,
        )
        if not dry_run:
            backup_dir = dependencies.make_import_overwrite_backup(
                repo_root,
                scope,
                collision_doc,
                {
                    "staged_filename": staged_filename,
                    "include_prompt_meta": include_prompt_meta,
                    "source_path": preview.get("source_path"),
                    "title": preview.get("title"),
                },
            )

            def write_import_artifacts() -> None:
                nonlocal inline_media_written
                inline_media_written = materialize_inline_raster_media(
                    repo_root,
                    source_path=source_path,
                    import_preview=preview,
                    include_prompt_meta=include_prompt_meta,
                )
                write_text_atomic(collision_doc.path, source_text)

            rebuild = dependencies.perform_source_write_and_rebuild(
                repo_root,
                scope,
                [collision_doc.path],
                write_import_artifacts,
                suppression_reason="docs-import-html-overwrite",
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
            "operation": "overwrite",
            "doc_id": collision_doc.doc_id,
            "path": relative_path(repo_root, collision_doc.path),
            "viewer_url": viewer_url_for(scope, collision_doc.doc_id),
            "title": preview["title"],
            "record": {
                "doc_id": collision_doc.doc_id,
                "title": preview["title"],
                "parent_id": collision_doc.parent_id,
                "sort_order": collision_doc.sort_order,
                "published": True,
                "viewable": collision_doc.viewable,
            },
            "collision": collision,
            "import_preview": preview,
            "inline_media_written": inline_media_written,
            "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
            "rebuild": rebuild,
            "summary_text": f"Overwrote {collision_doc.doc_id} from {staged_filename}.",
            "dry_run": dry_run,
        }

    doc_id = preview["proposed_doc_id"]
    target_path = scope_root(repo_root, scope) / f"{doc_id}.md"
    source_text = imported_source_text_for_create(preview, docs, scope)
    if not dry_run:
        backup_dir = dependencies.make_backup_bundle(
            repo_root,
            scope,
            "import-create",
            [],
            {
                "staged_filename": staged_filename,
                "include_prompt_meta": include_prompt_meta,
                "doc_id": doc_id,
                "title": preview["title"],
                "path": relative_path(repo_root, target_path),
                "source_path": preview.get("source_path"),
            },
        )

        def write_import_artifacts() -> None:
            nonlocal inline_media_written
            inline_media_written = materialize_inline_raster_media(
                repo_root,
                source_path=source_path,
                import_preview=preview,
                include_prompt_meta=include_prompt_meta,
            )
            write_text_atomic(target_path, source_text)

        rebuild = dependencies.perform_source_write_and_rebuild(
            repo_root,
            scope,
            [target_path],
            write_import_artifacts,
            suppression_reason="docs-import-html-create",
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
        "operation": "create",
        "doc_id": doc_id,
        "path": relative_path(repo_root, target_path),
        "viewer_url": viewer_url_for(scope, doc_id),
        "title": preview["title"],
        "record": {
            "doc_id": doc_id,
            "title": preview["title"],
            "parent_id": "",
            "sort_order": next_sort_order(docs, ""),
            "published": True,
            "hidden": default_hidden_for_scope(scope),
            "viewable": default_viewable_for_scope(scope),
        },
        "collision": collision,
        "import_preview": preview,
        "inline_media_written": inline_media_written,
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "summary_text": f"Created {doc_id} from {staged_filename}.",
        "dry_run": dry_run,
    }
