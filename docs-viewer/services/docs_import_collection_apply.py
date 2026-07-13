#!/usr/bin/env python3
"""Synchronous package-order mutation and generation for Docs Import collections."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from docs_import_collection_decisions import resolve_collection_apply_request
from docs_import_collection_plan import DocumentsCollectionPlan, collection_issue
from docs_import_collection_result import (
    shape_collection_result,
    utc_timestamp,
    write_collection_result_report,
)
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    ImportDocumentApplyResult,
    ImportDocumentMediaContext,
    apply_import_document_source,
    import_document_activity,
    materialize_import_document_media,
)
from docs_scope_config import load_docs_scope_configs


LogEvent = Callable[[Path, str, dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
class NoAppliedCollectionWrites(RuntimeError):
    """Stop the managed rebuild boundary when the first source write failed."""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_error_message(error: Exception, repo_root: Path, workspace_root: Path) -> str:
    return (
        _clean_text(error)
        .replace(str(workspace_root.resolve()), "$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing")
        .replace(str(repo_root.resolve()), ".")
    ) or error.__class__.__name__


def _base_record_result(record: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "record_index": record.get("record_index"),
        "record_identity": record.get("record_identity", ""),
        "doc_id": record.get("doc_id", ""),
        "title": record.get("title", ""),
        "status": status,
        "target_path": record.get("target_path", ""),
        "content_intent": record.get("content_intent", ""),
        "parent": copy.deepcopy(record.get("parent") or {}),
        "warnings": copy.deepcopy(record.get("warnings") or []),
        "errors": copy.deepcopy(record.get("errors") or []),
        "inline_media_written": [],
    }


def _manual_copy_instructions(record: dict[str, Any]) -> list[str]:
    instructions: list[str] = []
    for plan in record.get("media_plans") or []:
        if not isinstance(plan, dict) or not plan.get("manual_copy_required"):
            continue
        source_path = _clean_text(plan.get("source_path"))
        media_path = _clean_text(plan.get("media_path"))
        instructions.append(f"Copy {source_path} to {media_path}.")
    return instructions


def apply_import_content_collection(
    repo_root: Path,
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    log_event: LogEvent,
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild,
) -> dict[str, Any]:
    """Revalidate browser decisions, apply in package order, rebuild once, and report."""

    decisions, actions, refreshed = resolve_collection_apply_request(plan, body)
    if refreshed is not None:
        return refreshed

    response_records = list(plan.response.get("records") or [])
    results: list[dict[str, Any]] = []
    result_by_index: dict[int, dict[str, Any]] = {}
    manual_copy: list[str] = []
    for record in response_records:
        index = int(record["record_index"])
        action = actions[index]
        if action == "skip":
            result = _base_record_result(record, "skipped")
            decision = decisions[index]
            result["reason"] = _clean_text(record.get("decision_kind")) or "collision"
            if decision.note:
                result["note"] = decision.note
            log_event(
                repo_root,
                "docs-import-collection-record-skipped",
                {
                    "scope": plan.response["scope"],
                    "staged_filename": plan.response["staged_filename"],
                    "record_index": index,
                    "doc_id": record.get("doc_id", ""),
                    "reason": result["reason"],
                    "note": decision.note,
                },
            )
        else:
            result = _base_record_result(record, "pending")
        results.append(result)
        result_by_index[index] = result

    changed_paths = [
        document_plan.target_path
        for index, document_plan in enumerate(plan.document_plans)
        if document_plan is not None and actions.get(index) != "skip"
    ]
    docs_doc_ids: list[str] = []
    search_doc_ids: list[str] = []
    written_paths: list[Path] = []
    source_failed = False
    storage_mode = (
        load_docs_scope_configs(repo_root)[plan.response["scope"]]
        .import_media_storage.storage_mode
    )

    def write_collection_documents() -> None:
        nonlocal source_failed
        for index, document_plan in enumerate(plan.document_plans):
            if actions.get(index) == "skip":
                continue
            result = result_by_index[index]
            if document_plan is None:
                result["status"] = "failed"
                result["error"] = "refreshed document plan is unavailable"
                source_failed = True
                break
            media_context = ImportDocumentMediaContext(
                staging_root=staging_root,
                workspace_root=workspace_root,
                source_path=source_path,
                source_markdown=_clean_text(
                    document_plan.import_preview.get("_inline_media_source_markdown")
                ),
            )
            apply_result = ImportDocumentApplyResult()
            try:
                apply_result = materialize_import_document_media(
                    repo_root,
                    document_plan,
                    media_context=media_context,
                )
            except Exception as exc:
                if storage_mode == "r2_upload":
                    result["status"] = "failed"
                    result["error"] = _safe_error_message(exc, repo_root, workspace_root)
                    continue
                result["warnings"].append(collection_issue(
                    "warning",
                    "asset_materialization_failed",
                    _safe_error_message(exc, repo_root, workspace_root),
                    record_index=index,
                    doc_id=document_plan.doc_id,
                ))
            result["inline_media_written"] = list(apply_result.inline_media_written)
            try:
                apply_import_document_source(document_plan)
            except Exception as exc:
                result["status"] = "failed"
                result["error"] = _safe_error_message(exc, repo_root, workspace_root)
                source_failed = True
                break
            result["status"] = (
                "created" if document_plan.operation == IMPORT_DOCUMENT_CREATE else "overwritten"
            )
            docs_doc_ids.extend(document_plan.docs_doc_ids)
            search_doc_ids.extend(document_plan.search_doc_ids)
            written_paths.extend(document_plan.changed_paths)
            manual_copy.extend(_manual_copy_instructions(response_records[index]))
            event_name, event_details = import_document_activity(
                repo_root,
                document_plan,
                plan.response["staged_filename"],
                include_prompt_meta=False,
            )
            log_event(repo_root, event_name, event_details)

        if source_failed:
            failed_seen = False
            for result in results:
                if result["status"] == "failed":
                    failed_seen = True
                    continue
                if failed_seen and result["status"] == "pending":
                    result["status"] = "not-attempted"
                    result["reason"] = "stopped after the first source-write failure"
            if not docs_doc_ids:
                raise NoAppliedCollectionWrites("first collection source write failed")
        if not docs_doc_ids and any(result["status"] == "failed" for result in results):
            raise NoAppliedCollectionWrites("collection media publication prevented all source writes")

    generation: dict[str, Any] = {"status": "not-run", "rebuild": None, "error": ""}
    if changed_paths:
        try:
            rebuild = perform_source_write_and_rebuild(
                repo_root,
                plan.response["scope"],
                changed_paths,
                write_collection_documents,
                suppression_reason="docs-import-collection-apply",
                docs_doc_ids=docs_doc_ids,
                search_doc_ids=search_doc_ids,
                written_paths=written_paths,
            )
            generation = {"status": "completed", "rebuild": rebuild, "error": ""}
        except NoAppliedCollectionWrites:
            generation = {"status": "not-run", "rebuild": None, "error": ""}
        except Exception as exc:
            generation = {
                "status": "failed",
                "rebuild": None,
                "error": _safe_error_message(exc, repo_root, workspace_root),
            }

    timestamp = utc_timestamp()
    warnings = copy.deepcopy(plan.response.get("warnings") or [])
    for result in results:
        warnings.extend(copy.deepcopy(result.get("warnings") or []))
    result_payload = shape_collection_result(
        source_format=plan.response["source_format"],
        scope=plan.response["scope"],
        staged_filename=plan.response["staged_filename"],
        package=plan.response.get("package") or {},
        records=results,
        generation=generation,
        warnings=warnings,
        manual_copy_instructions=list(dict.fromkeys(manual_copy)),
        timestamp=timestamp,
    )
    try:
        result_payload["report_path"] = write_collection_result_report(
            result_payload,
            staging_root=staging_root,
            workspace_root=workspace_root,
        )
    except Exception as exc:
        result_payload["warnings"].append(collection_issue(
            "warning",
            "result_report_write_failed",
            _safe_error_message(exc, repo_root, workspace_root),
        ))
    log_event(
        repo_root,
        "docs-import-collection-apply",
        {
            "scope": plan.response["scope"],
            "staged_filename": plan.response["staged_filename"],
            "outcome": result_payload["outcome"],
            "counts": result_payload["counts"],
            "generation_status": result_payload["generation"]["status"],
            "report_path": result_payload["report_path"],
        },
    )
    return result_payload


__all__ = [
    "apply_import_content_collection",
]
