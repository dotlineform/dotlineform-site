"""Docs source mutation service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_management_mutations as mutations
from docs_workspace_config import load_docs_stage, require_document_authoring
import docs_source_config_settings
import docs_collection_lifecycle
import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_workspace_config import normalize_collection_id
from docs_management_context import log_event


class CollectionDocumentDeleteApplyError(RuntimeError):
    """A child delete was compensated after its generated rebuild failed."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "collection document delete failed"))
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


def recover_collection_document_delete(
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
        recovery_rebuild = write_rebuild.perform_collection_source_write_and_rebuild(
            repo_root,
            plan.collection,
            [source_delete.path],
            restore_operation,
            suppression_reason="docs-collection-document-delete-recovery",
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
    raise CollectionDocumentDeleteApplyError(
        {
            "ok": False,
            "operation": "apply",
            "target": target,
            "stage": plan.stage,
            "collection": plan.collection,
            "doc_id": plan.response.get("doc_id", ""),
            "source_revision": plan.response.get("source_revision", ""),
            "deleted_doc_ids": [],
            "delete_count": 0,
            "source_restored": source_restored,
            "recovery_rebuild": recovery_rebuild,
            "retry_safe": retry_safe,
            "error": f"collection document delete rebuild failed: {initial_error}",
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
                        if plan.collection:
                            target["collection"] = plan.collection
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
            if plan.collection:
                rebuild = write_rebuild.perform_collection_source_write_and_rebuild(
                    repo_root,
                    plan.collection,
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
            if plan.restore_deletes_on_rebuild_failure:
                recover_collection_document_delete(repo_root, plan, error)
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
    if "collection" in body:
        return execute_management_mutation_plan(
            repo_root,
            mutations.plan_collection_delete_apply(repo_root, body),
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


def handle_collection_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    collection = normalize_collection_id(body.get("collection"), field="collection")
    docs_collection_lifecycle.require_confirmed(body)
    payload = docs_collection_lifecycle.apply_create_collection(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_collection_outputs=write_rebuild.rebuild_collection_outputs,
        rebuild_stage_outputs=write_rebuild.rebuild_stage_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_collection_create_apply",
            {
                "stage": body["stage"],
                "collection": collection,
                "created_count": len(payload.get("created_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload


def handle_collection_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    collection = normalize_collection_id(body.get("collection"), field="collection")
    docs_collection_lifecycle.require_confirmed(body)
    payload = docs_collection_lifecycle.apply_delete_collection(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_stage_outputs=write_rebuild.rebuild_stage_outputs,
    )
    if not dry_run:
        log_event(
            repo_root,
            "docs_collection_delete_apply",
            {
                "stage": body["stage"],
                "collection": collection,
                "deleted_count": len(payload.get("deleted_files", [])),
                "missing_count": len(payload.get("missing_files", [])),
                "changed_count": len(payload.get("changed_files", [])),
            },
        )
    return payload
