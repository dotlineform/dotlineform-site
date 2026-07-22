#!/usr/bin/env python3
"""Service helpers for Docs Management staged source imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

from docs_import_common import is_interactive_html_import_asset
from docs_import_content import CONTENT_FORMAT_MARKDOWN, CONTENT_INTENT_REPLACE, ImportContent
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    ImportDocumentApplyResult,
    ImportDocumentMediaContext,
    apply_import_document,
    import_document_activity,
    import_document_result,
    plan_import_document,
)
from docs_import_document_package_collection import (
    apply_document_package_collection,
    plan_document_package_collection,
)
from docs_import_document_package import (
    COLLECTION_SOURCE_FORMAT,
    document_package_source_format,
)
from docs_import_markdown_package import retarget_markdown_package_media_plans
from docs_import_media import retarget_inline_media_plans
from docs_import_preview import (
    generate_import_preview,
    list_staged_import_source_files,
    resolve_staged_import_source,
)
from docs_import_source_helpers import (
    interactive_html_overwrite_summary,
)
from docs_import_source_interactive import (
    ensure_interactive_html_targets_available,
    interactive_html_asset_plans,
)
from docs_source_model import (
    allocate_doc_id,
    current_doc_timestamp,
    normalize_scope,
    scope_root,
)
from docs_document_packages.workspace import configured_workspace_paths, marker_path, workspace_status


LogEvent = Callable[[Path, str, Dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ImportSourceDependencies:
    log_event: LogEvent
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild


def allocate_ordinary_import_doc_id(repo_root: Path, scope: str, added_date: str) -> str:
    documents_root = scope_root(repo_root, scope)
    if not documents_root.is_dir():
        raise ValueError(f"missing source root for scope {scope}: {documents_root}")
    for _attempt in range(100):
        doc_id = allocate_doc_id(added_date)
        if not (documents_root / f"{doc_id}.md").exists():
            return doc_id
    raise RuntimeError("could not allocate an available ordinary import document identity")


def handle_import_source_files(repo_root: Path) -> Dict[str, Any]:
    status = workspace_status(repo_root, required_paths=("import_staging",))
    if not status["available"]:
        return {
            "ok": True,
            "available": False,
            "staging_root": status["root"],
            "message": status["message"],
            "files": [],
        }
    workspace_paths = configured_workspace_paths(repo_root)
    registered_source_formats = {
        path.name: source_format
        for path in workspace_paths.import_staging.iterdir()
        if (
            source_format := document_package_source_format(
                repo_root,
                path,
                metadata_root=workspace_paths.meta,
            )
        )
    }
    files = list_staged_import_source_files(
        workspace_paths.import_staging,
        workspace_paths.root,
        registered_source_formats=registered_source_formats,
    )
    return {
        "ok": True,
        "available": True,
        "staging_root": marker_path(workspace_paths.import_staging, workspace_root=workspace_paths.root),
        "message": "",
        "files": files,
    }


def handle_import_source(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
    dependencies: ImportSourceDependencies,
    *,
    staging_root: Path,
    workspace_root: Path,
    metadata_root: Path,
) -> Dict[str, Any]:
    scope = normalize_scope(body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    include_prompt_meta = bool(body.get("include_prompt_meta"))
    confirm_interactive_html_overwrite = bool(body.get("confirm_interactive_html_overwrite"))
    preview_only = bool(body.get("preview_only"))
    source_path = resolve_staged_import_source(staging_root, staged_filename)
    source_format = document_package_source_format(
        repo_root,
        source_path,
        metadata_root=metadata_root,
    )
    if source_format == COLLECTION_SOURCE_FORMAT:
        if not (dry_run or preview_only):
            return apply_document_package_collection(
                repo_root,
                scope=scope,
                staged_filename=staged_filename,
                body=body,
                staging_root=staging_root,
                workspace_root=workspace_root,
                metadata_root=metadata_root,
                log_event=dependencies.log_event,
                perform_source_write_and_rebuild=dependencies.perform_source_write_and_rebuild,
            )
        plan = plan_document_package_collection(
            repo_root,
            scope=scope,
            staged_filename=staged_filename,
            staging_root=staging_root,
            workspace_root=workspace_root,
            metadata_root=metadata_root,
        )
        payload = plan.as_dict()
        dependencies.log_event(
            repo_root,
            "docs-import-collection-preview",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "source_format": source_format,
                "records": payload["counts"]["records"],
                "collisions": payload["counts"]["collisions"],
                "record_errors": payload["counts"]["record_errors"],
                "blockers": payload["counts"]["blockers"],
                "ready_for_confirmation": payload["ready_for_confirmation"],
            },
        )
        payload["dry_run"] = dry_run
        return payload
    if is_interactive_html_import_asset(source_path):
        raise ValueError("interactive HTML script files cannot be selected as the primary import source")
    preview = generate_import_preview(
        repo_root,
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
        retain_private_media_source=True,
    )
    private_media_source_markdown = str(preview.pop("_inline_media_source_markdown", "") or "")
    preview.pop("_inline_svg_source_markup", None)
    interactive_plans = interactive_html_asset_plans(repo_root, staging_root, workspace_root, scope)
    if interactive_plans:
        preview["interactive_html_plans"] = interactive_plans
        for interactive_plan in interactive_plans:
            if not interactive_plan.get("target_exists"):
                continue
            preview.setdefault("warnings", []).append(
                f"Interactive HTML asset target already exists: {interactive_plan['target_path']}."
            )
    existing_interactive_plans = [plan for plan in interactive_plans if plan.get("target_exists")]
    requires_interactive_html_confirmation = bool(
        existing_interactive_plans and not confirm_interactive_html_overwrite
    )
    if requires_interactive_html_confirmation:
        for interactive_plan in existing_interactive_plans:
            preview.setdefault("warnings", []).append(
                f"Interactive HTML asset {interactive_plan['target_path']} already exists; confirm overwrite to replace it."
            )

    if dry_run or preview_only or requires_interactive_html_confirmation:
        dependencies.log_event(
            repo_root,
            "docs-import-source-preview",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "source_format": preview.get("source_format"),
                "include_prompt_meta": include_prompt_meta,
                "proposed_doc_id": preview["proposed_doc_id"],
                "inline_media_count": len(preview.get("media_plans") or []),
                "interactive_html_asset_count": len(interactive_plans),
                "requires_interactive_html_confirmation": requires_interactive_html_confirmation,
            },
        )
        return {
            "ok": True,
            "scope": scope,
            "staged_filename": staged_filename,
            "include_prompt_meta": include_prompt_meta,
            "preview_only": True,
            "requires_interactive_html_confirmation": requires_interactive_html_confirmation,
            "import_preview": preview,
            "summary_text": (
                interactive_html_overwrite_summary(existing_interactive_plans)
                if requires_interactive_html_confirmation and existing_interactive_plans
                else f"Prepared import preview for {staged_filename}."
            ),
            "dry_run": dry_run,
        }

    ensure_interactive_html_targets_available(
        interactive_plans,
        allow_overwrite=confirm_interactive_html_overwrite,
    )
    source_doc_id = str(preview["proposed_doc_id"])
    create_added_date = current_doc_timestamp()
    create_doc_id = allocate_ordinary_import_doc_id(repo_root, scope, create_added_date)
    preview["proposed_doc_id"] = create_doc_id
    preview["proposed_doc_id_source"] = "allocated-local-identity"
    if source_path.is_dir():
        retarget_markdown_package_media_plans(
            repo_root,
            staging_root,
            workspace_root,
            source_path,
            preview,
            scope,
        )
    retarget_inline_media_plans(repo_root, staging_root, workspace_root, preview, scope)
    title = str(preview.get("title") or "Imported Doc").strip()
    record = ImportContent(
        source_kind="staged-source",
        source_identity=staged_filename,
        record_identity=staged_filename,
        doc_id=source_doc_id,
        title=title,
        content_intent=CONTENT_INTENT_REPLACE,
        content_format=CONTENT_FORMAT_MARKDOWN,
        content=str(preview.get("markdown_preview") or ""),
        parent_id="",
    )
    plan = plan_import_document(
        repo_root,
        scope,
        record,
        operation=IMPORT_DOCUMENT_CREATE,
        docs=[],
        import_preview=preview,
        create_doc_id=create_doc_id,
        create_added_date=create_added_date,
    )
    media_context = ImportDocumentMediaContext(
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=source_path,
        include_prompt_meta=include_prompt_meta,
        interactive_html_plans=tuple(interactive_plans),
        allow_interactive_html_overwrite=confirm_interactive_html_overwrite,
        source_markdown=private_media_source_markdown,
    )
    apply_result = ImportDocumentApplyResult()

    def write_import_document() -> None:
        nonlocal apply_result
        apply_result = apply_import_document(
            repo_root,
            plan,
            media_context=media_context,
        )

    rebuild = dependencies.perform_source_write_and_rebuild(
        repo_root,
        scope,
        plan.changed_paths,
        write_import_document,
        suppression_reason=plan.suppression_reason,
        docs_doc_ids=plan.docs_doc_ids,
        search_doc_ids=list(plan.search_doc_ids),
    )
    event_name, event_details = import_document_activity(
        repo_root,
        plan,
        staged_filename,
        include_prompt_meta=include_prompt_meta,
    )
    dependencies.log_event(repo_root, event_name, event_details)
    result = import_document_result(
        repo_root,
        plan,
        source_label=staged_filename,
        apply_result=apply_result,
        rebuild=rebuild,
        dry_run=dry_run,
    )
    return {
        "ok": True,
        "scope": scope,
        "staged_filename": staged_filename,
        "include_prompt_meta": include_prompt_meta,
        "preview_only": False,
        "requires_interactive_html_confirmation": False,
        "import_preview": plan.import_preview,
        **result,
    }
