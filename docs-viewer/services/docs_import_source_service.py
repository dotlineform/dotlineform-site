#!/usr/bin/env python3
"""Service helpers for Docs Management staged source imports."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from docs_html_import import (
    HTML_STAGED_SUFFIXES,
    STAGING_REL_DIR,
    generate_import_preview,
    is_interactive_html_import_asset,
    list_staged_import_source_files,
    materialize_inline_raster_media,
    resolve_staged_import_source,
    retarget_markdown_package_media_plans,
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

INTERACTIVE_HTML_ASSET_REL_ROOT = Path("assets/docs/interactive")
INTERACTIVE_HTML_FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.html$")


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


def interactive_html_staged_paths(repo_root: Path) -> list[Path]:
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    if not staging_root.exists():
        return []
    return [
        path
        for path in sorted(staging_root.iterdir(), key=lambda candidate: candidate.name.lower())
        if path.is_file()
        and path.suffix.lower() in HTML_STAGED_SUFFIXES
        and is_interactive_html_import_asset(path)
    ]


def interactive_html_asset_plan_for_path(repo_root: Path, source_path: Path, scope: str) -> Dict[str, Any]:
    filename = f"{slugify(source_path.stem)}.html"
    if not INTERACTIVE_HTML_FILENAME_PATTERN.fullmatch(filename):
        raise ValueError(f"Interactive HTML asset filename must be a simple slug ending in .html: {filename}")

    normalized_scope = normalize_scope(scope)
    target_rel = INTERACTIVE_HTML_ASSET_REL_ROOT / normalized_scope / filename
    target_root = (repo_root / INTERACTIVE_HTML_ASSET_REL_ROOT / normalized_scope).resolve()
    target_path = (repo_root / target_rel).resolve()
    if not target_path.is_relative_to(target_root):
        raise ValueError(f"Interactive HTML target escapes scope asset root: {target_rel.as_posix()}")

    return {
        "source_path": relative_path(repo_root, source_path),
        "target_path": target_rel.as_posix(),
        "public_path": f"/assets/docs/interactive/{normalized_scope}/{filename}",
        "token": f"[[interactive-html:{filename}]]",
        "filename": filename,
        "display_name": Path(filename).stem,
        "result_type": "script file",
        "target_exists": target_path.exists(),
    }


def interactive_html_asset_plans(repo_root: Path, scope: str) -> list[Dict[str, Any]]:
    plans = [
        interactive_html_asset_plan_for_path(repo_root, path, scope)
        for path in interactive_html_staged_paths(repo_root)
    ]
    target_paths: set[str] = set()
    for plan in plans:
        target_path = str(plan.get("target_path") or "")
        if target_path in target_paths:
            raise ValueError(f"Multiple interactive HTML staged files resolve to {target_path}.")
        target_paths.add(target_path)
    return plans


def ensure_interactive_html_targets_available(plans: list[Dict[str, Any]], *, allow_overwrite: bool = False) -> None:
    for plan in plans:
        if plan.get("target_exists") and not allow_overwrite:
            raise FileExistsError(
                f"Interactive HTML asset already exists: {plan.get('target_path')}. "
                "Edit that asset directly or confirm overwrite to replace it during import."
            )


def materialize_interactive_html_asset(
    repo_root: Path,
    plan: Dict[str, Any],
    *,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    ensure_interactive_html_targets_available([plan], allow_overwrite=allow_overwrite)
    source_path = (repo_root / str(plan.get("source_path") or "")).resolve()
    target_path = (repo_root / str(plan.get("target_path") or "")).resolve()
    staging_root = (repo_root / STAGING_REL_DIR).resolve()
    target_root = (repo_root / INTERACTIVE_HTML_ASSET_REL_ROOT / target_path.parent.name).resolve()
    if not source_path.is_relative_to(staging_root):
        raise ValueError("Interactive HTML asset source escapes import staging root.")
    if not target_path.is_relative_to(target_root):
        raise ValueError("Interactive HTML asset target escapes scope asset root.")
    target_existed = target_path.exists()
    if target_existed and not allow_overwrite:
        raise FileExistsError(
            f"Interactive HTML asset already exists: {relative_path(repo_root, target_path)}"
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return {
        "source_path": relative_path(repo_root, source_path),
        "target_path": relative_path(repo_root, target_path),
        "public_path": str(plan.get("public_path") or ""),
        "token": str(plan.get("token") or ""),
        "filename": str(plan.get("filename") or target_path.name),
        "display_name": str(plan.get("display_name") or target_path.stem),
        "result_type": "script file",
        "size_bytes": target_path.stat().st_size,
        "overwrote": target_existed,
    }


def materialize_interactive_html_assets(
    repo_root: Path,
    plans: list[Dict[str, Any]],
    *,
    allow_overwrite: bool = False,
) -> list[Dict[str, Any]]:
    if not plans:
        return []
    ensure_interactive_html_targets_available(plans, allow_overwrite=allow_overwrite)
    return [
        materialize_interactive_html_asset(repo_root, plan, allow_overwrite=allow_overwrite)
        for plan in plans
    ]


def import_summary_text(
    operation: str,
    doc_id: str,
    staged_filename: str,
    interactive_html_written: list[Dict[str, Any]],
) -> str:
    action = "Created" if operation == "create" else "Overwrote"
    summary = f"{action} {doc_id} from {staged_filename}."
    if interactive_html_written:
        count = len(interactive_html_written)
        suffix = "" if count == 1 else "s"
        summary += f" Copied {count} interactive HTML script file{suffix}."
    return summary


def interactive_html_overwrite_summary(plans: list[Dict[str, Any]]) -> str:
    if len(plans) == 1:
        return f"Interactive HTML asset overwrite required for {plans[0]['target_path']}."
    return f"Interactive HTML asset overwrite required for {len(plans)} script files."


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

    backup_dir = None
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
                "sort_order": collision_doc.sort_order,
                "published": True,
                "viewable": collision_doc.viewable,
            },
            "collision": collision,
            "import_preview": preview,
            "inline_media_written": inline_media_written,
            "interactive_html_written": interactive_html_written,
            "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
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
            "sort_order": next_sort_order(docs, ""),
            "published": True,
            "hidden": default_hidden_for_scope(scope),
            "viewable": default_viewable_for_scope(scope),
        },
        "collision": collision,
        "import_preview": preview,
        "inline_media_written": inline_media_written,
        "interactive_html_written": interactive_html_written,
        "backup_dir": relative_path(repo_root, backup_dir) if backup_dir else "",
        "rebuild": rebuild,
        "summary_text": import_summary_text("create", doc_id, staged_filename, interactive_html_written),
        "dry_run": dry_run,
    }
