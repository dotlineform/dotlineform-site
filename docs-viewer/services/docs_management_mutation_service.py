"""Docs source mutation service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import docs_management_mutations as mutations
import docs_scope_manifest
import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_management_context import log_event, make_backup_bundle, make_scope_lifecycle_backup, relative_path


def execute_management_mutation_plan(repo_root: Path, plan: mutations.ManagementMutationPlan, dry_run: bool) -> Dict[str, Any]:
    payload = dict(plan.response)
    backup_dir = None
    rebuild = None

    if not dry_run and plan.has_source_changes:
        if plan.backup_operation:
            backup_dir = make_backup_bundle(
                repo_root,
                plan.scope,
                plan.backup_operation,
                list(plan.backup_docs),
                plan.backup_metadata,
            )

        def write_operation() -> None:
            for source_write in plan.source_writes:
                source_model.write_text_atomic(source_write.path, source_write.text)
            for source_delete in plan.source_deletes:
                source_delete.path.unlink()

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
        if plan.log_event_name:
            log_event(repo_root, plan.log_event_name, plan.log_details)

    if plan.include_write_result_keys:
        payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
        payload["rebuild"] = rebuild
    payload["dry_run"] = dry_run
    return payload


def handle_create(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_create(repo_root, body), dry_run)


def handle_update_metadata(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_metadata(repo_root, body), dry_run)


def handle_update_viewability_bulk(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_viewability_bulk(repo_root, body), dry_run)


def handle_update_viewability(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_update_viewability(repo_root, body), dry_run)


def handle_move(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_move(repo_root, body), dry_run)


def handle_normalize_order(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_normalize_order(repo_root, body), dry_run)


def handle_delete_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    return execute_management_mutation_plan(repo_root, mutations.plan_delete_apply(repo_root, body), dry_run)


def handle_scope_create_apply(repo_root: Path, body: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    scope_id = docs_scope_manifest.normalize_scope_id(body.get("scope_id"))
    docs_scope_manifest.require_confirmed(body)
    docs_scope_manifest.plan_create_scope_preview(repo_root, body)
    backup_dir = None if dry_run else make_scope_lifecycle_backup(repo_root, scope_id, "create")
    payload = docs_scope_manifest.apply_create_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_scope_outputs=write_rebuild.rebuild_scope_outputs,
    )
    payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
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
    preview = docs_scope_manifest.plan_delete_scope_preview(repo_root, body)
    if not preview.get("allowed"):
        blockers = preview.get("blockers") if isinstance(preview.get("blockers"), list) else []
        raise ValueError("; ".join(str(blocker) for blocker in blockers) or "scope delete is not allowed")
    backup_dir = None if dry_run else make_scope_lifecycle_backup(repo_root, scope_id, "delete")
    payload = docs_scope_manifest.apply_delete_scope(
        repo_root,
        body,
        dry_run=dry_run,
        rebuild_all_docs_outputs=write_rebuild.rebuild_all_docs_outputs,
    )
    payload["backup_dir"] = relative_path(repo_root, backup_dir) if backup_dir else ""
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
