"""Await create-only source persistence and prepared generation."""

from pathlib import Path
from typing import Any, Dict

import docs_management_mutations as mutations
import docs_source_model as source_model
from docs_management_context import log_event
from docs_document_rebuild import rebuild_prepared_document
from docs_write_rebuild import validate_changed_source_paths


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



def execute_management_mutation_plan(repo_root: Path, plan: mutations.ManagementMutationPlan, dry_run: bool) -> Dict[str, Any]:
    payload = dict(plan.response)
    payload.update(dry_run=dry_run, rebuild=None)
    if dry_run:
        return payload
    applied = False
    try:
        validate_changed_source_paths(plan.prepared_owner.source_root, plan.changed_paths)
        for write in plan.source_writes:
            if write.create_only:
                source_model.write_text_atomic_new(write.path, write.text)
            else:
                source_model.write_text_atomic(write.path, write.text)
            applied = True
        payload["rebuild"] = rebuild_prepared_document(
            repo_root, plan.prepared_owner, plan.prepared_document, parent_ids=plan.parent_ids,
        )["rebuild"]
    except Exception as error:
        if applied:
            if plan.log_event_name:
                log_event(repo_root, plan.log_event_name, {**plan.log_details, "rebuild_ok": False})
            raise DocumentCreateCommittedError(create_committed_error_payload(plan, error)) from error
        raise
    if plan.log_event_name:
        log_event(repo_root, plan.log_event_name, plan.log_details)
    return payload


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_create(repo_root, body), dry_run)
