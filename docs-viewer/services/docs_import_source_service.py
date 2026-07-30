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
    EXPORT_ONLY_COLLECTION_SOURCE_FORMAT,
    document_package_source_format,
)
from docs_import_markdown_package import retarget_markdown_package_media_plans
from docs_import_media import retarget_inline_media_plans
from docs_import_preview import (
    generate_import_preview,
    list_staged_import_source_files,
    resolve_staged_import_source,
)
from docs_import_review_source_folder import (
    EDITED_REVIEW_SOURCE_FORMAT,
    is_review_source_markdown,
    recognize_edited_review_source_folder,
)
from docs_import_review_source_collection import (
    apply_edited_review_source_collection,
    plan_edited_review_source_collection,
)
from docs_import_source_helpers import (
    interactive_html_overwrite_summary,
)
from docs_import_source_interactive import (
    ensure_interactive_html_targets_available,
    interactive_html_asset_plans,
)
from docs_management_document_target import (
    ManagedDocumentCollection,
)
import docs_source_model as source_model
from docs_source_model import (
    allocate_doc_id,
    current_doc_timestamp,
)
from docs_document_packages.workspace import configured_workspace_paths, marker_path, workspace_status


LogEvent = Callable[[Path, str, Dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class ImportSourceDependencies:
    log_event: LogEvent
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild
    perform_scope_source_write_and_rebuild_atomic: PerformSourceWriteAndRebuild
    perform_sub_scope_source_write_and_rebuild: PerformSourceWriteAndRebuild


def load_ordinary_import_collection_docs(
    repo_root: Path,
    collection: ManagedDocumentCollection,
) -> list[source_model.ScopeDoc]:
    if not collection.sub_scope:
        return []
    return source_model.load_document_collection_docs_for_config(
        repo_root,
        collection.parent_config,
        collection.document_config,
    )


def allocate_ordinary_import_doc_id(
    collection: ManagedDocumentCollection,
    added_date: str,
    docs: list[source_model.ScopeDoc],
) -> str:
    documents_root = collection.source_root
    if not documents_root.is_dir():
        raise ValueError(
            f"missing source root for import target "
            f"{collection.scope}/{collection.sub_scope or '(parent)'}: "
            f"{documents_root}",
        )
    unavailable = {
        identity
        for document in docs
        for identity in (document.doc_id, document.path.stem)
    }
    for _attempt in range(100):
        doc_id = allocate_doc_id(added_date)
        if (
            doc_id not in unavailable
            and not (documents_root / f"{doc_id}.md").exists()
        ):
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
    registered_source_formats: dict[str, str] = {}
    blocked_package_filenames: set[str] = set()
    edited_review_sources: dict[str, dict[str, Any]] = {}
    for path in workspace_paths.import_staging.iterdir():
        try:
            edited_review_source = recognize_edited_review_source_folder(
                repo_root,
                candidate=path,
                staging_root=workspace_paths.import_staging,
                metadata_root=workspace_paths.meta,
            )
        except (FileNotFoundError, OSError, ValueError):
            blocked_package_filenames.add(path.name)
            continue
        if edited_review_source is not None:
            registered_source_formats[path.name] = EDITED_REVIEW_SOURCE_FORMAT
            edited_review_sources[path.name] = (
                edited_review_source.listing_projection()
            )
            continue
        source_format = document_package_source_format(
            repo_root,
            path,
            metadata_root=workspace_paths.meta,
        )
        if source_format == EXPORT_ONLY_COLLECTION_SOURCE_FORMAT:
            blocked_package_filenames.add(path.name)
        elif source_format:
            registered_source_formats[path.name] = source_format
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
        "files": [
            {
                **record,
                **edited_review_sources.get(
                    str(record.get("filename") or ""),
                    {},
                ),
            }
            for record in files
            if str(record.get("filename") or "") not in blocked_package_filenames
        ],
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
    destination: ManagedDocumentCollection,
) -> Dict[str, Any]:
    scope = destination.scope
    sub_scope = destination.sub_scope
    staged_filename = str(body.get("staged_filename") or "").strip()
    include_prompt_meta = bool(body.get("include_prompt_meta"))
    confirm_interactive_html_overwrite = bool(body.get("confirm_interactive_html_overwrite"))
    preview_only = bool(body.get("preview_only"))
    source_path = resolve_staged_import_source(staging_root, staged_filename)
    edited_review_source = recognize_edited_review_source_folder(
        repo_root,
        candidate=source_path,
        staging_root=staging_root,
        metadata_root=metadata_root,
    )
    if edited_review_source is not None:
        if sub_scope or edited_review_source.source_sub_scope:
            raise ValueError(
                "Edited review source folders for configured sub-scopes are not "
                "available until ERS-1.4.",
            )
        if edited_review_source.source_scope != scope:
            raise ValueError(
                "Edited review source folder belongs to scope "
                f"{edited_review_source.source_scope!r}, not {scope!r}.",
            )
        if not (dry_run or preview_only):
            return apply_edited_review_source_collection(
                repo_root,
                folder=edited_review_source,
                collection=destination,
                body=body,
                staging_root=staging_root,
                workspace_root=workspace_root,
                log_event=dependencies.log_event,
                perform_scope_source_write_and_rebuild_atomic=(
                    dependencies.perform_scope_source_write_and_rebuild_atomic
                ),
            )
        plan = plan_edited_review_source_collection(
            repo_root,
            folder=edited_review_source,
            collection=destination,
            staging_root=staging_root,
            workspace_root=workspace_root,
        )
        payload = plan.as_dict()
        dependencies.log_event(
            repo_root,
            "docs-import-reviewed-scope-collection-preview",
            {
                "scope": scope,
                "staged_filename": staged_filename,
                "source_format": EDITED_REVIEW_SOURCE_FORMAT,
                "records": payload["counts"]["records"],
                "collisions": payload["counts"]["collisions"],
                "record_errors": payload["counts"]["record_errors"],
                "blockers": payload["counts"]["blockers"],
                "ready_for_confirmation": payload["ready_for_confirmation"],
            },
        )
        payload["dry_run"] = dry_run
        return payload
    if is_review_source_markdown(source_path):
        raise ValueError(
            "A review source cannot be imported by itself. Stage and select the "
            "complete edited review source folder.",
        )
    source_format = document_package_source_format(
        repo_root,
        source_path,
        metadata_root=metadata_root,
        allow_sub_scope_return_import=bool(
            sub_scope
            and getattr(destination.document_config, "supports_return_import", False)
        ),
    )
    if source_format == EXPORT_ONLY_COLLECTION_SOURCE_FORMAT:
        raise ValueError(
            "Export-only document packages cannot enter Docs Import."
        )
    if source_format == COLLECTION_SOURCE_FORMAT:
        if sub_scope and not getattr(
            destination.document_config,
            "supports_return_import",
            False,
        ):
            raise ValueError(
                "Returned document packages are not supported for this configured "
                "sub-scope destination.",
            )
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
                collection=destination if sub_scope else None,
                perform_sub_scope_source_write_and_rebuild=(
                    dependencies.perform_sub_scope_source_write_and_rebuild
                    if sub_scope
                    else None
                ),
            )
        plan = plan_document_package_collection(
            repo_root,
            scope=scope,
            staged_filename=staged_filename,
            staging_root=staging_root,
            workspace_root=workspace_root,
            metadata_root=metadata_root,
            collection=destination if sub_scope else None,
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
                **({"sub_scope": sub_scope} if sub_scope else {}),
            },
        )
        payload["dry_run"] = dry_run
        return payload
    if is_interactive_html_import_asset(source_path):
        raise ValueError("interactive HTML script files cannot be selected as the primary import source")
    docs = load_ordinary_import_collection_docs(repo_root, destination)
    preview = generate_import_preview(
        repo_root,
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
        retain_private_media_source=True,
    )
    preview["target"] = destination.request_target()
    if sub_scope:
        preview["sub_scope"] = sub_scope
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
        preview_event = {
            "scope": scope,
            "staged_filename": staged_filename,
            "source_format": preview.get("source_format"),
            "include_prompt_meta": include_prompt_meta,
            "proposed_doc_id": preview["proposed_doc_id"],
            "inline_media_count": len(preview.get("media_plans") or []),
            "interactive_html_asset_count": len(interactive_plans),
            "requires_interactive_html_confirmation": requires_interactive_html_confirmation,
        }
        if sub_scope:
            preview_event["sub_scope"] = sub_scope
        dependencies.log_event(
            repo_root,
            "docs-import-source-preview",
            preview_event,
        )
        response = {
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
        if sub_scope:
            response["sub_scope"] = sub_scope
        return response

    ensure_interactive_html_targets_available(
        interactive_plans,
        allow_overwrite=confirm_interactive_html_overwrite,
    )
    source_doc_id = str(preview["proposed_doc_id"])
    create_added_date = current_doc_timestamp()
    create_doc_id = allocate_ordinary_import_doc_id(
        destination,
        create_added_date,
        docs,
    )
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
        docs=docs,
        import_preview=preview,
        create_doc_id=create_doc_id,
        create_added_date=create_added_date,
        collection=destination,
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

    if sub_scope:
        rebuild = dependencies.perform_sub_scope_source_write_and_rebuild(
            repo_root,
            scope,
            sub_scope,
            plan.changed_paths,
            write_import_document,
            suppression_reason=plan.suppression_reason,
        )
    else:
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
    response = {
        "ok": True,
        "scope": scope,
        "staged_filename": staged_filename,
        "include_prompt_meta": include_prompt_meta,
        "preview_only": False,
        "requires_interactive_html_confirmation": False,
        "import_preview": plan.import_preview,
        **result,
    }
    if sub_scope:
        response["sub_scope"] = sub_scope
    return response
