#!/usr/bin/env python3
"""Confirmed, stale-safe apply boundary for Docs Viewer subtree copies."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import docs_source_model as source_model
import docs_subtree_copy as subtree_copy
from docs_scope_config import DocsScopeConfig, load_docs_scope_configs


COPY_SUBTREE_APPLY_SCHEMA_VERSION = "docs_copy_subtree_apply_v1"
COPY_SUBTREE_SUPPRESSION_REASON = "docs-copy-subtree"
COPY_SUBTREE_ACTIVITY_EVENT = "docs-copy-subtree"
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
ActivityLogger = Callable[[Path, str, dict[str, Any]], None]


class CopySubtreePlanStaleError(ValueError):
    """The source, configuration, or planned identities changed after preview."""


class CopySubtreeTargetCollisionError(ValueError):
    """A planned target identity or source path is no longer available."""


def _stale(message: str) -> CopySubtreePlanStaleError:
    return CopySubtreePlanStaleError(f"copy subtree plan is stale: {message}")


def _current_configs(
    repo_root: Path,
    plan: subtree_copy.CopySubtreePlan,
) -> tuple[DocsScopeConfig, DocsScopeConfig]:
    try:
        configs = load_docs_scope_configs(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        raise _stale(f"scope configuration is unavailable: {exc}") from exc
    source_config = configs.get(plan.source_scope)
    target_config = configs.get(plan.target_scope)
    if source_config is None:
        raise _stale(f"source scope {plan.source_scope!r} is no longer configured")
    if target_config is None:
        raise _stale(f"target scope {plan.target_scope!r} is no longer configured")
    if source_config != plan.source_config:
        raise _stale(f"source scope {plan.source_scope!r} configuration changed")
    if target_config != plan.target_config:
        raise _stale(f"target scope {plan.target_scope!r} configuration changed")
    return source_config, target_config


def _current_source_subtree(
    repo_root: Path,
    plan: subtree_copy.CopySubtreePlan,
    source_config: DocsScopeConfig,
) -> list[source_model.ScopeDoc]:
    try:
        subtree_copy.require_copy_source_root(repo_root, source_config, require_writable=False)
        source_docs = source_model.load_scope_docs_for_config(repo_root, source_config)
        current = source_model.subtree_docs_in_tree_order(
            source_docs,
            plan.root.source_doc.doc_id,
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise _stale(f"source subtree is unavailable: {exc}") from exc
    planned = [document.source_doc for document in plan.documents]
    if [doc.doc_id for doc in current] != [doc.doc_id for doc in planned]:
        raise _stale("source subtree membership or order changed")
    for current_doc, planned_doc in zip(current, planned):
        if current_doc.path.resolve() != planned_doc.path.resolve():
            raise _stale(f"source path changed for {planned_doc.doc_id!r}")
        if current_doc.source_text != planned_doc.source_text:
            raise _stale(f"source content changed for {planned_doc.doc_id!r}")
    return source_docs


def _validate_target_identities(
    repo_root: Path,
    plan: subtree_copy.CopySubtreePlan,
    target_config: DocsScopeConfig,
    source_docs: list[source_model.ScopeDoc],
) -> None:
    try:
        target_root = subtree_copy.require_copy_source_root(
            repo_root,
            target_config,
            require_writable=True,
        )
    except (OSError, ValueError) as exc:
        raise _stale(f"target scope is unavailable: {exc}") from exc
    source_identities = {
        identity.lower()
        for doc in source_docs
        for identity in (doc.doc_id, doc.path.stem)
        if identity
    }
    planned_ids: set[str] = set()
    for index, document in enumerate(plan.documents):
        target_doc_id = document.target_doc_id
        if not source_model.is_immutable_doc_id(target_doc_id):
            raise _stale(f"planned target identity {target_doc_id!r} is invalid")
        if not source_model.doc_id_matches_added_date(target_doc_id, plan.copy_timestamp):
            raise _stale(f"planned target identity {target_doc_id!r} does not match the copy timestamp")
        if target_doc_id in planned_ids or target_doc_id.lower() in source_identities:
            raise _stale(f"planned target identity {target_doc_id!r} is not unique")
        expected_path = target_root / f"{target_doc_id}.md"
        if document.target_path.resolve() != expected_path.resolve():
            raise _stale(f"planned target filename does not match identity {target_doc_id!r}")
        if expected_path.exists():
            raise CopySubtreeTargetCollisionError(
                f"copy subtree target collision for {target_doc_id!r}"
            )
        expected_parent_id = "" if index == 0 else plan.id_map.get(document.source_doc.parent_id, "")
        if document.target_parent_id != expected_parent_id:
            raise _stale(f"planned target parent is invalid for {target_doc_id!r}")
        if expected_parent_id and expected_parent_id not in planned_ids:
            raise _stale(f"planned target parent is ordered after {target_doc_id!r}")
        planned_ids.add(target_doc_id)

    try:
        target_docs = source_model.load_scope_docs_for_config(repo_root, target_config)
    except (OSError, ValueError) as exc:
        raise _stale(f"target scope is unavailable: {exc}") from exc
    unavailable_target = {
        identity.lower()
        for doc in target_docs
        for identity in (doc.doc_id, doc.path.stem)
        if identity
    }
    for target_doc_id in planned_ids:
        if target_doc_id.lower() in unavailable_target:
            raise CopySubtreeTargetCollisionError(
                f"copy subtree target collision for {target_doc_id!r}"
            )


def _validate_transformation(
    transformation: subtree_copy.CopySubtreeTransformation,
) -> None:
    plan = transformation.plan
    if len(transformation.documents) != len(plan.documents):
        raise _stale("transformed source count changed")
    target_viewable = source_model.default_viewable_for_config(plan.target_config)
    for transformed in transformation.documents:
        planned = transformed.planned_document
        try:
            front_matter, body = source_model.parse_source_text(
                transformed.source_text,
                source_name=planned.target_path.name,
            )
        except ValueError as exc:
            raise _stale(f"candidate source for {planned.target_doc_id!r} is invalid: {exc}") from exc
        if str(front_matter.get("doc_id") or "") != planned.target_doc_id:
            raise _stale(f"candidate identity changed for {planned.target_doc_id!r}")
        if str(front_matter.get("parent_id") or "") != planned.target_parent_id:
            raise _stale(f"candidate parent changed for {planned.target_doc_id!r}")
        if front_matter.get("added_date") != plan.copy_timestamp:
            raise _stale(f"candidate added_date changed for {planned.target_doc_id!r}")
        if front_matter.get("last_updated") != plan.copy_timestamp:
            raise _stale(f"candidate last_updated changed for {planned.target_doc_id!r}")
        if source_model.doc_is_viewable(front_matter) is not target_viewable:
            raise _stale(f"candidate viewability changed for {planned.target_doc_id!r}")
        _remaining_body, remaining_links = subtree_copy.rewrite_copied_viewer_links(body, plan)
        if remaining_links:
            raise _stale(f"candidate viewer links remain stale for {planned.target_doc_id!r}")


def revalidate_copy_subtree_plan(
    repo_root: Path,
    plan: subtree_copy.CopySubtreePlan,
) -> subtree_copy.CopySubtreeTransformation:
    if not isinstance(plan, subtree_copy.CopySubtreePlan) or not plan.documents:
        raise _stale("planned documents are required")
    if plan.source_scope == plan.target_scope:
        raise _stale("target scope matches source scope")
    if not source_model.is_doc_timestamp(plan.copy_timestamp):
        raise _stale("copy timestamp is invalid")
    source_config, target_config = _current_configs(repo_root, plan)
    source_docs = _current_source_subtree(repo_root, plan, source_config)
    _validate_target_identities(repo_root, plan, target_config, source_docs)
    transformation = subtree_copy.transform_copy_subtree(plan)
    _validate_transformation(transformation)
    return transformation


def management_viewer_url(scope: str, doc_id: str) -> str:
    return f"/docs/?scope={quote(scope, safe='')}&doc={quote(doc_id, safe='')}"


def apply_copy_subtree(
    repo_root: Path,
    plan: subtree_copy.CopySubtreePlan,
    *,
    confirm: bool,
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild | None = None,
    activity_logger: ActivityLogger | None = None,
) -> dict[str, Any]:
    if confirm is not True:
        raise ValueError("confirm must be true to copy a document subtree")
    transformation = revalidate_copy_subtree_plan(repo_root, plan)
    created_doc_ids = [document.planned_document.target_doc_id for document in transformation.documents]
    target_paths = [document.target_path for document in transformation.documents]
    written_paths: list[Path] = []

    def write_operation() -> None:
        for document in transformation.documents:
            source_model.write_text_atomic_new(document.target_path, document.source_text)
            written_paths.append(document.target_path)

    if perform_source_write_and_rebuild is None:
        from docs_write_rebuild import perform_source_write_and_rebuild as coordinated_write

        perform_source_write_and_rebuild = coordinated_write
    rebuild = perform_source_write_and_rebuild(
        repo_root,
        plan.target_scope,
        target_paths,
        write_operation,
        suppression_reason=COPY_SUBTREE_SUPPRESSION_REASON,
        include_search=True,
        docs_doc_ids=created_doc_ids,
        search_doc_ids=created_doc_ids,
        written_paths=written_paths,
    )

    if activity_logger is None:
        from docs_management_context import log_event

        activity_logger = log_event
    activity_logger(
        repo_root,
        COPY_SUBTREE_ACTIVITY_EVENT,
        {
            "source_scope": plan.source_scope,
            "source_doc_id": plan.root.source_doc.doc_id,
            "target_scope": plan.target_scope,
            "new_root_doc_id": plan.root.target_doc_id,
            "created_count": len(created_doc_ids),
        },
    )
    return {
        "schema_version": COPY_SUBTREE_APPLY_SCHEMA_VERSION,
        "ok": True,
        "source_scope": plan.source_scope,
        "source_root_doc_id": plan.root.source_doc.doc_id,
        "target_scope": plan.target_scope,
        "new_root_doc_id": plan.root.target_doc_id,
        "created_doc_ids": created_doc_ids,
        "document_count": len(created_doc_ids),
        "copy_timestamp": plan.copy_timestamp,
        "target_viewer_url": management_viewer_url(plan.target_scope, plan.root.target_doc_id),
        "viewer_link_rewrites": transformation.viewer_link_rewrites,
        "rebuild": rebuild,
        "summary_text": (
            f"Copied {len(created_doc_ids)} documents from {plan.source_scope} "
            f"to {plan.target_scope}."
        ),
    }


__all__ = [
    "COPY_SUBTREE_ACTIVITY_EVENT",
    "COPY_SUBTREE_APPLY_SCHEMA_VERSION",
    "COPY_SUBTREE_SUPPRESSION_REASON",
    "CopySubtreePlanStaleError",
    "CopySubtreeTargetCollisionError",
    "apply_copy_subtree",
    "management_viewer_url",
    "revalidate_copy_subtree_plan",
]
