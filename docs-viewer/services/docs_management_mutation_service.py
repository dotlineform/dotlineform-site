"""Docs source mutation service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_management_mutations as mutations
from docs_workspace_config import load_docs_stage, require_document_authoring
import docs_source_config_settings
import docs_sub_scope_lifecycle
import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_workspace_config import normalize_sub_scope_id
from docs_management_context import log_event


class SubScopeDocumentDeleteApplyError(RuntimeError):
    """A child delete was compensated after its generated rebuild failed."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "sub-scope document delete failed"))
        self.payload = payload


class DocumentCreateCommittedError(RuntimeError):
    """A create committed before its generated projection rebuild failed."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(
            str(
                payload.get("error")
                or "document was created but its projection rebuild failed"
            )
        )
        self.payload = payload


class DocumentPlacementCommittedError(RuntimeError):
    """Placement wrote source but did not complete every required result."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload["error"]))
        self.payload = payload


def create_committed_error_payload(
    plan: mutations.ManagementMutationPlan,
    error: Exception,
) -> Dict[str, Any]:
    payload = dict(plan.response)
    payload.update(
        {
            "ok": False,
            "operation": "create",
            "committed": True,
            "retry_create": False,
            "rebuild": {
                "ok": False,
                "error": str(error),
            },
            "dry_run": False,
            "summary_text": (
                f"Created {plan.response.get('doc_id', 'document')}, "
                "but its projection rebuild failed."
            ),
            "error": (
                "document was created but its projection rebuild failed: "
                f"{error}"
            ),
        }
    )
    return payload


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
            plan.sub_scope,
            [source_delete.path],
            restore_operation,
            suppression_reason="docs-sub-scope-document-delete-recovery",
            stage=plan.stage,
            **({"links_created_doc_ids": []} if plan.stage == "working" else {}),
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
            "stage": plan.stage,
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
    require_document_authoring(load_docs_stage(repo_root, plan.stage))
    payload = dict(plan.response)
    if plan.stage:
        payload["stage"] = plan.stage
    rebuild = None
    source_changes_applied = False

    if not dry_run and plan.has_source_changes:
        def write_operation() -> None:
            nonlocal source_changes_applied
            # Check all source revisions before creating a destination or
            # updating a referring document. Deletes carry the source revision
            # for a relocation even though its write has a new path.
            for source_write in (*plan.source_writes, *plan.source_deletes):
                if source_write.original_bytes is not None:
                    try:
                        current_bytes = source_write.path.read_bytes()
                    except FileNotFoundError:
                        current_bytes = b""
                    if current_bytes != source_write.original_bytes:
                        target = {
                            "stage": plan.stage,
                            "doc_id": str(plan.response.get("doc_id") or ""),
                        }
                        if plan.sub_scope:
                            target["sub_scope"] = plan.sub_scope
                        if isinstance(source_write, mutations.SourceWrite) and source_write.revision_target is not None:
                            target = source_write.revision_target
                        raise mutations.ManagedDocumentRevisionConflict(
                            mutations.revision_conflict_payload(
                                target=target,
                                requested_revision=mutations.source_revision(
                                    source_write.original_bytes
                                ),
                                current_revision=(
                                    mutations.source_revision(current_bytes)
                                    if current_bytes
                                    else ""
                                ),
                                operation=plan.revision_conflict_operation,
                                error=plan.revision_conflict_error,
                            )
                        )
            for copy in plan.media_copies:
                if copy.source.read_bytes() != copy.content:
                    raise ValueError("Source media changed before placement")
                if copy.destination.is_symlink() or (copy.destination.exists() and copy.destination.read_bytes() != copy.content):
                    raise ValueError("Destination media changed before placement")
            for copy in plan.media_copies:
                if not copy.destination.exists():
                    copy.destination.parent.mkdir(parents=True, exist_ok=True)
                    with copy.destination.open("xb") as output:
                        output.write(copy.content)
            for source_write in plan.source_writes:
                if source_write.create_only:
                    source_model.write_text_atomic_new(
                        source_write.path,
                        source_write.text,
                    )
                else:
                    source_model.write_text_atomic(
                        source_write.path,
                        source_write.text,
                    )
                source_changes_applied = True
            for source_delete in plan.source_deletes:
                source_delete.path.unlink()
            source_changes_applied = True

        try:
            if plan.rebuilds:
                rebuild = write_rebuild.perform_multi_collection_source_write_and_rebuild(
                    repo_root,
                    [
                        {
                            "stage": rebuild_plan.stage,
                            "sub_scope": rebuild_plan.sub_scope,
                            "changed_paths": list(rebuild_plan.changed_paths),
                            "docs_doc_ids": rebuild_plan.build_doc_ids,
                        }
                        for rebuild_plan in plan.rebuilds
                    ],
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                )
            elif plan.sub_scope:
                rebuild = write_rebuild.perform_sub_scope_source_write_and_rebuild(
                    repo_root,
                    plan.sub_scope,
                    plan.changed_paths,
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                    stage=plan.stage,
                )
            else:
                rebuild = write_rebuild.perform_source_write_and_rebuild(
                    repo_root,
                    plan.changed_paths,
                    write_operation,
                    suppression_reason=plan.suppression_reason or "docs-management",
                    stage=plan.stage,
                    docs_doc_ids=plan.build_doc_ids,
                )
        except mutations.ManagedDocumentRevisionConflict:
            raise
        except Exception as error:
            if source_changes_applied and plan.response.get("placement", {}).get("collection_changed"):
                raise DocumentPlacementCommittedError({
                    **plan.response, "ok": False, "committed": True,
                    "error": f"Document placement changed source, but its required results are incomplete: {error}",
                }) from error
            if plan.restore_deletes_on_rebuild_failure:
                recover_sub_scope_document_delete(repo_root, plan, error)
            if (
                plan.report_create_commit_on_rebuild_failure
                and source_changes_applied
            ):
                if plan.log_event_name:
                    log_event(
                        repo_root,
                        plan.log_event_name,
                        {
                            **plan.log_details,
                            "rebuild_ok": False,
                        },
                    )
                raise DocumentCreateCommittedError(
                    create_committed_error_payload(plan, error)
                ) from error
            raise
    if not dry_run and plan.log_event_name and plan.has_source_changes:
        log_event(repo_root, plan.log_event_name, plan.log_details)

    if plan.include_write_result_keys:
        payload["rebuild"] = rebuild
    payload["dry_run"] = dry_run
    return payload


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_create(repo_root, body), dry_run)


def handle_update_metadata(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_metadata(repo_root, body), dry_run)


def handle_assign_field_group(
    repo_root: Path,
    body: Dict[str, Any],
    dry_run: bool,
) -> Dict[str, Any]:
    return execute_management_mutation_plan(
        repo_root,
        mutations.plan_assign_field_group(repo_root, body),
        dry_run,
    )


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
        docs_source_config_settings.apply_stage_settings_change(
            repo_root,
            {"default_doc_id": ""},
            stage=plan.stage,
        )
    return execute_management_mutation_plan(repo_root, plan, dry_run)


def handle_sub_scope_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    docs_sub_scope_lifecycle.require_confirmed(body)
    payload = docs_sub_scope_lifecycle.apply_create_sub_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_sub_scope_outputs=write_rebuild.rebuild_sub_scope_outputs,
        rebuild_stage_outputs=write_rebuild.rebuild_stage_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_sub_scope_create_apply",
            {
                "stage": body["stage"],
                "sub_scope": sub_scope,
                "created_count": len(payload.get("created_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_sub_scope_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    sub_scope = normalize_sub_scope_id(body.get("sub_scope"), field="sub_scope")
    docs_sub_scope_lifecycle.require_confirmed(body)
    payload = docs_sub_scope_lifecycle.apply_delete_sub_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_stage_outputs=write_rebuild.rebuild_stage_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_sub_scope_delete_apply",
            {
                "stage": body["stage"],
                "sub_scope": sub_scope,
                "deleted_count": len(payload.get("deleted_files", [])),
                "missing_count": len(payload.get("missing_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload
