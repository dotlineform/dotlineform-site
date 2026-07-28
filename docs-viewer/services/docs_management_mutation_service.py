"""Docs source mutation service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_management_mutations as mutations
import docs_scope_create
import docs_scope_delete
import docs_scope_manifest
import docs_scope_rename
import docs_source_config_settings
import docs_sub_scope_lifecycle
import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_scope_config import normalize_sub_scope_id
from docs_management_context import log_event


class SubScopeDocumentDeleteApplyError(RuntimeError):
    """A child delete was compensated after its generated rebuild failed."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "sub-scope document delete failed"))
        self.payload = payload


def recover_sub_scope_document_delete(
    repo_root: Path,
    plan: mutations.ManagementMutationPlan,
    initial_error: Exception,
) -> None:
    restorable = [
        source_delete
        for source_delete in plan.source_deletes
        if source_delete.original_bytes is not None
    ]
    if len(restorable) != 1:
        raise initial_error

    source_delete = restorable[0]
    original_bytes = source_delete.original_bytes
    if original_bytes is None:
        raise initial_error

    def restore_operation() -> None:
        source_model.write_bytes_atomic(
            source_delete.path,
            original_bytes,
        )

    def source_matches_original() -> bool:
        try:
            return source_delete.path.read_bytes() == original_bytes
        except OSError:
            return False

    try:
        recovery_rebuild = write_rebuild.perform_sub_scope_source_write_and_rebuild(
            repo_root,
            plan.scope,
            plan.sub_scope,
            [source_delete.path],
            restore_operation,
            suppression_reason="docs-sub-scope-document-delete-recovery",
        )
    except Exception as recovery_error:
        source_restored = source_matches_original()
        recovery_rebuild = {
            "ok": False,
            "error": str(recovery_error),
        }
    else:
        source_restored = source_matches_original()

    target = dict(plan.response.get("target") or {})
    retry_safe = source_restored and recovery_rebuild.get("ok") is True
    raise SubScopeDocumentDeleteApplyError(
        {
            "ok": False,
            "operation": "apply",
            "target": target,
            "scope": plan.scope,
            "sub_scope": plan.sub_scope,
            "doc_id": plan.response.get("doc_id", ""),
            "source_revision": plan.response.get("source_revision", ""),
            "deleted_doc_ids": [],
            "delete_count": 0,
            "source_restored": source_restored,
            "recovery_rebuild": recovery_rebuild,
            "retry_safe": retry_safe,
            "error": f"sub-scope document delete rebuild failed: {initial_error}",
        }
    ) from initial_error


def execute_management_mutation_plan(repo_root: Path, plan: mutations.ManagementMutationPlan, dry_run: bool) -> Dict[str, Any]:
    payload = dict(plan.response)
    rebuild = None

    if not dry_run and plan.has_source_changes:
        def write_operation() -> None:
            for source_write in plan.source_writes:
                source_model.write_text_atomic(source_write.path, source_write.text)
            for source_delete in plan.source_deletes:
                if source_delete.original_bytes is not None:
                    try:
                        current_bytes = source_delete.path.read_bytes()
                    except FileNotFoundError:
                        current_bytes = b""
                    if current_bytes != source_delete.original_bytes:
                        target = dict(plan.response.get("target") or {})
                        raise mutations.ManagedDocumentRevisionConflict(
                            mutations.revision_conflict_payload(
                                target=target,
                                requested_revision=str(
                                    plan.response.get("source_revision") or ""
                                ),
                                current_revision=(
                                    mutations.source_revision(current_bytes)
                                    if current_bytes
                                    else ""
                                ),
                            )
                        )
                source_delete.path.unlink()

        try:
            if plan.rebuilds:
                rebuild = write_rebuild.perform_multi_scope_source_write_and_rebuild(
                    repo_root,
                    [
                        {
                            "scope": rebuild_plan.scope,
                            "changed_paths": list(rebuild_plan.changed_paths),
                            "docs_doc_ids": rebuild_plan.build_doc_ids,
                            "search_doc_ids": rebuild_plan.search_doc_ids,
                            "include_search": rebuild_plan.include_search,
                        }
                        for rebuild_plan in plan.rebuilds
                    ],
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                )
            elif plan.sub_scope:
                rebuild = write_rebuild.perform_sub_scope_source_write_and_rebuild(
                    repo_root,
                    plan.scope,
                    plan.sub_scope,
                    plan.changed_paths,
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                )
            else:
                rebuild = write_rebuild.perform_source_write_and_rebuild(
                    repo_root,
                    plan.scope,
                    plan.changed_paths,
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                    docs_doc_ids=plan.build_doc_ids,
                    search_doc_ids=plan.search_doc_ids,
                )
        except mutations.ManagedDocumentRevisionConflict:
            raise
        except Exception as error:
            if plan.restore_deletes_on_rebuild_failure:
                recover_sub_scope_document_delete(repo_root, plan, error)
            raise
        if plan.log_event_name:
            log_event(repo_root, plan.log_event_name, plan.log_details)

    if plan.include_write_result_keys:
        payload["rebuild"] = rebuild
    payload["dry_run"] = dry_run
    return payload


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_create(repo_root, body), dry_run)


def handle_update_metadata(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_metadata(repo_root, body), dry_run)


def handle_move(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_move(repo_root, body), dry_run)


def handle_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    if "sub_scope" in body:
        return execute_management_mutation_plan(
            repo_root,
            mutations.plan_sub_scope_delete_apply(repo_root, body),
            dry_run,
        )
    plan = mutations.plan_delete_apply(repo_root, body)
    if plan.response.get("default_doc_id_changed") and not dry_run:
        docs_source_config_settings.apply_scope_settings_change(
            repo_root,
            plan.scope,
            {"default_doc_id": ""},
        )
    return execute_management_mutation_plan(repo_root, plan, dry_run)


def handle_scope_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id"))
    payload = docs_scope_create.apply_create_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_scope_outputs=write_rebuild.rebuild_scope_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_scope_create_apply",
            {
                "scope": scope_id,
                "created_count": len(payload.get("created_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_scope_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id") or body.get("scope"))
    docs_scope_manifest.require_confirmed(body)
    preview = docs_scope_delete.plan_delete_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "scope delete is not allowed")
    payload = docs_scope_delete.apply_delete_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_all_docs_outputs=write_rebuild.rebuild_all_docs_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_scope_delete_apply",
            {
                "scope": scope_id,
                "deleted_count": len(payload.get("deleted_files", [])),
                "missing_count": len(payload.get("missing_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_scope_rename_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    old_scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id") or body.get("old_scope_id"))
    new_scope_id = docs_scope_manifest.normalize_scope_id(body.get("new_scope_id"))
    docs_scope_manifest.require_confirmed(body)
    preview = docs_scope_rename.plan_rename_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "scope rename is not allowed")
    payload = docs_scope_rename.apply_rename_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_scope_outputs=write_rebuild.rebuild_scope_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_scope_rename_apply",
            {
                "scope": old_scope_id,
                "new_scope": new_scope_id,
                "moved_count": len(payload.get("move_paths", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_sub_scope_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    parent_scope = docs_scope_manifest.normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    docs_scope_manifest.require_confirmed(body)
    docs_sub_scope_lifecycle.plan_create_sub_scope_preview(repo_root, body)
    payload = docs_sub_scope_lifecycle.apply_create_sub_scope(repo_root, body, dry_run=dry_run)
    if not dry_run:
        log_event(
            repo_root,
            "docs_sub_scope_create_apply",
            {
                "scope": parent_scope,
                "sub_scope": sub_scope,
                "created_count": len(payload.get("created_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_sub_scope_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    parent_scope = docs_scope_manifest.normalize_scope_id(body.get("parent_scope") or body.get("scope"))
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    docs_scope_manifest.require_confirmed(body)
    preview = docs_sub_scope_lifecycle.plan_delete_sub_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "sub-scope delete is not allowed")
    payload = docs_sub_scope_lifecycle.apply_delete_sub_scope(repo_root, body, dry_run=dry_run)
    if not dry_run:
        log_event(
            repo_root,
            "docs_sub_scope_delete_apply",
            {
                "scope": parent_scope,
                "sub_scope": sub_scope,
                "deleted_count": len(payload.get("deleted_files", [])),
                "missing_count": len(payload.get("missing_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload
