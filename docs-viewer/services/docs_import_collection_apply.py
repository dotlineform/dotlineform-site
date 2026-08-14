#!/usr/bin/env python3
"""Synchronous package-order mutation and generation for Docs Import collections."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from docs_import_collection_plan import DocumentsCollectionPlan, collection_issue
from docs_import_collection_result import (
    safe_generation_result,
    shape_collection_result,
    utc_timestamp,
)
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    IMPORT_DOCUMENT_OVERWRITE,
    ImportDocumentApplyResult,
    ImportDocumentMediaContext,
    apply_import_document_source,
    import_document_event,
    materialize_import_document_media,
)
from docs_management_document_target import ManagedDocumentCollection
from docs_write_rebuild import (
    ScopeSourceSnapshotChanged,
    ScopeWriteRebuildFailure,
    SubScopeSourceSnapshotChanged,
    SubScopeWriteRebuildFailure,
)


LogEvent = Callable[[Path, str, dict[str, Any]], None]
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
class NoAppliedCollectionWrites(RuntimeError):
    """Stop the managed rebuild boundary when the first source write failed."""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


COLLECTION_APPLY_BODY_FIELDS = {
    "scope",
    "sub_scope",
    "staged_filename",
    "preview_only",
    "confirm",
    "export_id",
    "source_sha256",
    "trusted_metadata_sha256",
    "planned_identities",
    "planned_actions",
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
    current_metadata_sha256 = _clean_text(
        current_package.get("trusted_metadata_sha256")
    )
    if (
        current_metadata_sha256
        and _clean_text(body.get("trusted_metadata_sha256"))
        != current_metadata_sha256
    ):
        return {}, _refreshed_collection_plan(
            plan,
            [
                collection_issue(
                    "warning",
                    "package_identity_changed",
                    "trusted package metadata changed; review the refreshed plan",
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
            written_paths.extend(document_plan.changed_paths)
            event_name, event_details = import_document_event(
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
    result_payload["target"] = {"scope": plan.response["scope"]}
    log_event(
        repo_root,
        "docs-import-collection-apply",
        {
            "scope": plan.response["scope"],
            "staged_filename": plan.response["staged_filename"],
            "outcome": result_payload["outcome"],
            "counts": result_payload["counts"],
            "generation_status": result_payload["generation"]["status"],
        },
    )
    return result_payload


def _atomic_collection_result(
    repo_root: Path,
    plan: DocumentsCollectionPlan,
    records: list[dict[str, Any]],
    *,
    log_event: LogEvent,
    collection: ManagedDocumentCollection,
    generation: dict[str, Any],
    rollback: dict[str, Any],
    event_name: str,
) -> dict[str, Any]:
    warnings = copy.deepcopy(plan.response.get("warnings") or [])
    for record in records:
        warnings.extend(copy.deepcopy(record.get("warnings") or []))
    result_payload = shape_collection_result(
        source_format=plan.response["source_format"],
        scope=plan.response["scope"],
        staged_filename=plan.response["staged_filename"],
        package=plan.response.get("package") or {},
        records=records,
        generation=generation,
        warnings=warnings,
        manual_copy_instructions=[],
        timestamp=utc_timestamp(),
    )
    result_payload["target"] = collection.request_target()
    if collection.sub_scope:
        result_payload["sub_scope"] = collection.sub_scope
    result_payload["rollback"] = copy.deepcopy(rollback)
    event_details = {
        "scope": collection.scope,
        "staged_filename": plan.response["staged_filename"],
        "outcome": result_payload["outcome"],
        "counts": result_payload["counts"],
        "generation_status": result_payload["generation"]["status"],
        "rollback_status": result_payload["rollback"]["status"],
    }
    if collection.sub_scope:
        event_details["sub_scope"] = collection.sub_scope
    log_event(
        repo_root,
        event_name,
        event_details,
    )
    return result_payload


def _apply_import_content_collection_atomic(
    repo_root: Path,
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
    *,
    workspace_root: Path,
    log_event: LogEvent,
    collection: ManagedDocumentCollection,
    perform_atomic_boundary: Callable[
        [list[Path], Callable[[], None], dict[Path, bytes]],
        dict[str, Any],
    ],
    snapshot_changed_type: type[Exception],
    write_rebuild_failure_type: type[Exception],
    event_name: str,
    target_label: str,
) -> dict[str, Any]:
    _actions, refreshed = _resolve_collection_apply_request(plan, body)
    if refreshed is not None:
        return refreshed

    response_records = list(plan.response.get("records") or [])
    results = [_base_record_result(record, "pending") for record in response_records]
    document_plans = list(plan.document_plans)
    if (
        len(document_plans) != len(results)
        or any(document_plan is None for document_plan in document_plans)
        or any(
            document_plan is not None
            and document_plan.operation != IMPORT_DOCUMENT_OVERWRITE
            for document_plan in document_plans
        )
    ):
        return _refreshed_collection_plan(
            plan,
            [
                collection_issue(
                    "error",
                    "atomic_overwrite_plan_required",
                    f"exact {target_label} package apply requires one overwrite plan per record",
                )
            ],
        )

    snapshots: dict[Path, bytes] = {}
    for document_plan in document_plans:
        assert document_plan is not None
        target_path = document_plan.target_path.resolve()
        try:
            target_path.relative_to(collection.source_root.resolve())
        except ValueError as exc:
            raise ValueError(
                f"planned {target_label} target escapes configured collection",
            ) from exc
        current = target_path.read_bytes()
        if (
            document_plan.target is None
            or current != document_plan.target.source_text.encode("utf-8")
        ):
            return _refreshed_collection_plan(
                plan,
                [
                    collection_issue(
                        "warning",
                        "target_state_changed",
                        "canonical sources changed after planning; review a refreshed plan",
                    )
                ],
            )
        snapshots[target_path] = current

    changed_paths = [
        document_plan.target_path
        for document_plan in document_plans
        if document_plan is not None
    ]

    def write_atomic_collection() -> None:
        for index, document_plan in enumerate(document_plans):
            assert document_plan is not None
            apply_import_document_source(document_plan)
            results[index]["status"] = "overwritten"

    try:
        rebuild = perform_atomic_boundary(
            changed_paths,
            write_atomic_collection,
            snapshots,
        )
    except snapshot_changed_type:
        return _refreshed_collection_plan(
            plan,
            [
                collection_issue(
                    "warning",
                    "target_state_changed",
                    "canonical sources changed immediately before apply; review a refreshed plan",
                )
            ],
        )
    except write_rebuild_failure_type as exc:
        apply_error = _safe_error_message(exc, repo_root, workspace_root)
        raw_rollback = getattr(exc, "rollback", {})
        rollback_status = str(raw_rollback.get("status") or "failed")
        failure_message = (
            f"package apply failed and source snapshot restoration {rollback_status}: "
            f"{apply_error}"
        )
        for result in results:
            result["status"] = "failed"
            result["error"] = failure_message
        rollback = {
            "status": rollback_status,
            "sources_restored": bool(raw_rollback.get("sources_restored")),
            "rebuild": safe_generation_result(
                {
                    "status": (
                        "completed"
                        if isinstance(raw_rollback.get("rebuild"), dict)
                        else "not-run"
                    ),
                    "rebuild": raw_rollback.get("rebuild"),
                    "error": raw_rollback.get("error"),
                }
            )["rebuild"],
            "error": (
                _safe_error_message(
                    RuntimeError(_clean_text(raw_rollback.get("error"))),
                    repo_root,
                    workspace_root,
                )
                if _clean_text(raw_rollback.get("error"))
                else ""
            ),
        }
        return _atomic_collection_result(
            repo_root,
            plan,
            results,
            log_event=log_event,
            collection=collection,
            generation={"status": "failed", "rebuild": None, "error": apply_error},
            rollback=rollback,
            event_name=event_name,
        )

    for document_plan in document_plans:
        assert document_plan is not None
        event_name, event_details = import_document_event(
            repo_root,
            document_plan,
            plan.response["staged_filename"],
            include_prompt_meta=False,
        )
        log_event(repo_root, event_name, event_details)
    return _atomic_collection_result(
        repo_root,
        plan,
        results,
        log_event=log_event,
        collection=collection,
        generation={"status": "completed", "rebuild": rebuild, "error": ""},
        rollback={
            "status": "not-needed",
            "sources_restored": False,
            "rebuild": None,
            "error": "",
        },
        event_name=event_name,
    )


def apply_import_content_collection_atomic(
    repo_root: Path,
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
    *,
    workspace_root: Path,
    log_event: LogEvent,
    collection: ManagedDocumentCollection,
    perform_sub_scope_source_write_and_rebuild: PerformSourceWriteAndRebuild,
) -> dict[str, Any]:
    """Apply one exact child package or restore every source and its projection."""

    if not collection.sub_scope:
        raise ValueError("atomic collection apply requires a managed child collection")

    def perform_boundary(
        changed_paths: list[Path],
        write_operation: Callable[[], None],
        snapshots: dict[Path, bytes],
    ) -> dict[str, Any]:
        return perform_sub_scope_source_write_and_rebuild(
            repo_root,
            collection.scope,
            collection.sub_scope,
            changed_paths,
            write_operation,
            suppression_reason="docs-import-sub-scope-collection-apply",
            source_snapshots=snapshots,
        )

    return _apply_import_content_collection_atomic(
        repo_root,
        plan,
        body,
        workspace_root=workspace_root,
        log_event=log_event,
        collection=collection,
        perform_atomic_boundary=perform_boundary,
        snapshot_changed_type=SubScopeSourceSnapshotChanged,
        write_rebuild_failure_type=SubScopeWriteRebuildFailure,
        event_name="docs-import-sub-scope-collection-apply",
        target_label="sub-scope",
    )


def apply_import_content_collection_scope_atomic(
    repo_root: Path,
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
    *,
    workspace_root: Path,
    log_event: LogEvent,
    collection: ManagedDocumentCollection,
    perform_scope_source_write_and_rebuild_atomic: PerformSourceWriteAndRebuild,
) -> dict[str, Any]:
    """Apply one exact parent-scope package or restore its complete projection."""

    if collection.sub_scope:
        raise ValueError("scope collection apply requires a top-level collection")
    docs_doc_ids = list(
        dict.fromkeys(
            doc_id
            for document_plan in plan.document_plans
            if document_plan is not None
            for doc_id in document_plan.docs_doc_ids
        )
    )
    def perform_boundary(
        changed_paths: list[Path],
        write_operation: Callable[[], None],
        snapshots: dict[Path, bytes],
    ) -> dict[str, Any]:
        return perform_scope_source_write_and_rebuild_atomic(
            repo_root,
            collection.scope,
            changed_paths,
            write_operation,
            suppression_reason="docs-import-reviewed-scope-collection-apply",
            source_snapshots=snapshots,
            docs_doc_ids=docs_doc_ids,
        )

    return _apply_import_content_collection_atomic(
        repo_root,
        plan,
        body,
        workspace_root=workspace_root,
        log_event=log_event,
        collection=collection,
        perform_atomic_boundary=perform_boundary,
        snapshot_changed_type=ScopeSourceSnapshotChanged,
        write_rebuild_failure_type=ScopeWriteRebuildFailure,
        event_name="docs-import-reviewed-scope-collection-apply",
        target_label="scope",
    )


__all__ = [
    "apply_import_content_collection",
    "apply_import_content_collection_atomic",
    "apply_import_content_collection_scope_atomic",
]
