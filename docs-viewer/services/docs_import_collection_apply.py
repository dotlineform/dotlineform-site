#!/usr/bin/env python3
"""Synchronous package-order mutation and generation for Docs Import collections."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

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


LogEvent = Callable[[Path, str, dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
class NoAppliedCollectionWrites(RuntimeError):
    """Stop the managed rebuild boundary when the first source write failed."""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


COLLECTION_APPLY_BODY_FIELDS = {
    "scope",
    "staged_filename",
    "preview_only",
    "confirm",
    "export_id",
    "source_sha256",
    "planned_identities",
    "planned_actions",
    "activity_context",
}
PLANNED_ACTION_FIELDS = {"record_index", "action", "doc_id", "target_doc_id"}


def _refreshed_collection_plan(
    plan: DocumentsCollectionPlan,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = plan.as_dict()
    payload["preview_only"] = True
    payload["reconfirmation_required"] = True
    payload["ready_for_confirmation"] = False
    payload["revalidation_issues"] = copy.deepcopy(issues)
    return payload


def _validated_confirmed_actions(body: dict[str, Any]) -> list[dict[str, Any]]:
    extra_fields = sorted(set(body) - COLLECTION_APPLY_BODY_FIELDS)
    if extra_fields:
        raise ValueError("collection apply does not accept fields: " + ", ".join(extra_fields))
    if body.get("preview_only") is not False:
        raise ValueError("collection apply requires preview_only false")
    if body.get("confirm") is not True:
        raise ValueError("collection apply requires confirm true")
    raw_actions = body.get("planned_actions")
    if not isinstance(raw_actions, list):
        raise ValueError("collection apply requires planned_actions from the confirmed preview")
    actions: list[dict[str, Any]] = []
    seen_indices: set[int] = set()
    for raw in raw_actions:
        if not isinstance(raw, dict) or set(raw) != PLANNED_ACTION_FIELDS:
            raise ValueError(
                "planned action fields must be record_index, action, doc_id, target_doc_id"
            )
        record_index = raw.get("record_index")
        if (
            not isinstance(record_index, int)
            or isinstance(record_index, bool)
            or record_index < 0
        ):
            raise ValueError("planned action record_index must be a non-negative integer")
        if record_index in seen_indices:
            raise ValueError(f"duplicate planned action for record_index {record_index}")
        seen_indices.add(record_index)
        action = _clean_text(raw.get("action"))
        if action not in {"create", "overwrite"}:
            raise ValueError("planned action must be create or overwrite")
        actions.append(
            {
                "record_index": record_index,
                "action": action,
                "doc_id": _clean_text(raw.get("doc_id")),
                "target_doc_id": _clean_text(raw.get("target_doc_id")),
            }
        )
    return actions


def _resolve_collection_apply_request(
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
) -> tuple[dict[int, str], dict[str, Any] | None]:
    confirmed_actions = _validated_confirmed_actions(body)
    confirmed_export_id = _clean_text(body.get("export_id"))
    confirmed_source_sha256 = _clean_text(body.get("source_sha256"))
    if not confirmed_export_id or not confirmed_source_sha256:
        raise ValueError("collection apply requires confirmed export_id and source_sha256")
    current_package = (
        plan.response.get("package")
        if isinstance(plan.response.get("package"), dict)
        else {}
    )
    if (
        confirmed_export_id != _clean_text(current_package.get("export_id"))
        or confirmed_source_sha256 != _clean_text(current_package.get("source_sha256"))
    ):
        return {}, _refreshed_collection_plan(
            plan,
            [
                collection_issue(
                    "warning",
                    "package_identity_changed",
                    "staged package identity changed; review the refreshed plan",
                )
            ],
        )
    if plan.response.get("blockers"):
        return {}, _refreshed_collection_plan(
            plan,
            [collection_issue("error", "plan_blocked", "refreshed collection plan is blocked")],
        )
    current_actions = plan.response.get("planned_actions")
    if not isinstance(current_actions, list) or confirmed_actions != current_actions:
        return {}, _refreshed_collection_plan(
            plan,
            [
                collection_issue(
                    "warning",
                    "target_state_changed",
                    "planned package actions changed; review the refreshed plan",
                )
            ],
        )
    return {
        int(action["record_index"]): str(action["action"])
        for action in current_actions
    }, None


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
        "source_doc_id": record.get("source_doc_id", ""),
        "title": record.get("title", ""),
        "status": status,
        "target_path": record.get("target_path", ""),
        "content_intent": record.get("content_intent", ""),
        "parent": copy.deepcopy(record.get("parent") or {}),
        "warnings": copy.deepcopy(record.get("warnings") or []),
        "errors": copy.deepcopy(record.get("errors") or []),
        "inline_media_written": [],
    }


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
    """Revalidate one confirmed whole-package plan, apply in order, rebuild, and report."""

    _actions, refreshed = _resolve_collection_apply_request(plan, body)
    if refreshed is not None:
        return refreshed

    response_records = list(plan.response.get("records") or [])
    results: list[dict[str, Any]] = []
    result_by_index: dict[int, dict[str, Any]] = {}
    manual_copy: list[str] = []
    for record in response_records:
        index = int(record["record_index"])
        result = _base_record_result(record, "pending")
        results.append(result)
        result_by_index[index] = result

    changed_paths = [
        document_plan.target_path
        for index, document_plan in enumerate(plan.document_plans)
        if document_plan is not None
    ]
    docs_doc_ids: list[str] = []
    search_doc_ids: list[str] = []
    written_paths: list[Path] = []
    source_failed = False
    def write_collection_documents() -> None:
        nonlocal source_failed
        for index, document_plan in enumerate(plan.document_plans):
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
                source_svg_markup=_clean_text(
                    document_plan.import_preview.get("_inline_svg_source_markup")
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
                result["status"] = "failed"
                result["error"] = _safe_error_message(exc, repo_root, workspace_root)
                continue
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
