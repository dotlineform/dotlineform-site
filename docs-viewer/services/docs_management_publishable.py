#!/usr/bin/env python3
"""Atomic checked-document publishability mutation for Docs Management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docs_source_model as source_model
import docs_write_rebuild as write_rebuild
from docs_management_context import log_event
from docs_management_document_target import (
    ManagedDocumentCollection,
    resolve_managed_document_collection,
    resolve_managed_document_target,
)


PARENT_REQUEST_KEYS = frozenset(
    {"scope", "doc_ids", "publishable", "confirm"}
)
SUB_SCOPE_REQUEST_KEYS = frozenset(
    {"scope", "sub_scope", "doc_ids", "publishable", "confirm"}
)


@dataclass(frozen=True)
class PublishableSourceUpdate:
    doc_id: str
    path: Path
    original_bytes: bytes
    source_text: str


@dataclass(frozen=True)
class PublishableSelectionPlan:
    collection: ManagedDocumentCollection
    publishable: bool
    requested_doc_ids: tuple[str, ...]
    unchanged_doc_ids: tuple[str, ...]
    updates: tuple[PublishableSourceUpdate, ...]

    def target(self) -> dict[str, str]:
        return self.collection.request_target()


class PublishableSelectionConflict(RuntimeError):
    """The checked source snapshot changed before the atomic write boundary."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "checked document sources changed"))
        self.payload = payload


class PublishableSelectionApplyError(RuntimeError):
    """The atomic write/rebuild failed and reports its rollback outcome."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "Set Publishable failed"))
        self.payload = payload


def _requested_doc_ids(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("doc_ids must be a non-empty array")
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_doc_id in value:
        if not isinstance(raw_doc_id, str) or raw_doc_id != raw_doc_id.strip():
            raise ValueError("every doc_id must be one exact non-blank string")
        doc_id = raw_doc_id
        if not doc_id:
            raise ValueError("every doc_id must be one exact non-blank string")
        if doc_id in seen:
            raise ValueError(f"duplicate doc_id in Set Publishable selection: {doc_id}")
        seen.add(doc_id)
        normalized.append(doc_id)
    return tuple(normalized)


def _collection_from_request(
    repo_root: Path,
    body: dict[str, Any],
) -> ManagedDocumentCollection:
    expected_keys = (
        SUB_SCOPE_REQUEST_KEYS if "sub_scope" in body else PARENT_REQUEST_KEYS
    )
    if frozenset(body) != expected_keys:
        expected = ", ".join(sorted(expected_keys))
        raise ValueError(f"Set Publishable must contain exactly {expected}")
    collection = resolve_managed_document_collection(
        repo_root,
        scope=body.get("scope"),
        sub_scope=body.get("sub_scope") if "sub_scope" in body else None,
    )
    if not source_model.collection_supports_publishable(
        collection.document_config
    ):
        label = (
            f"{collection.scope}/{collection.sub_scope}"
            if collection.sub_scope
            else collection.scope
        )
        raise ValueError(
            f"Set Publishable is not supported for local collection {label}"
        )
    return collection


def _updated_source_text(document: source_model.ScopeDoc, publishable: bool) -> str | None:
    updated_front_matter = dict(document.front_matter)
    if publishable:
        if "publishable" not in updated_front_matter:
            return None
        updated_front_matter.pop("publishable", None)
    else:
        if updated_front_matter.get("publishable") is False:
            return None
        updated_front_matter["publishable"] = False
    updated_front_matter = source_model.advance_front_matter_for_recent_edit(
        document.front_matter,
        document.body,
        updated_front_matter,
        document.body,
    )
    return source_model.format_source(updated_front_matter, document.body)


def plan_set_publishable(
    repo_root: Path,
    body: dict[str, Any],
) -> PublishableSelectionPlan:
    if body.get("confirm") is not True:
        raise ValueError("Set Publishable requires confirm=true")
    if not isinstance(body.get("publishable"), bool):
        raise ValueError("publishable must be true or false")
    collection = _collection_from_request(repo_root, body)
    requested_doc_ids = _requested_doc_ids(body.get("doc_ids"))
    publishable = bool(body["publishable"])
    updates: list[PublishableSourceUpdate] = []
    unchanged_doc_ids: list[str] = []

    for doc_id in requested_doc_ids:
        target = {**collection.request_target(), "doc_id": doc_id}
        resolved = resolve_managed_document_target(repo_root, target)
        source_text = _updated_source_text(resolved.document, publishable)
        if source_text is None:
            unchanged_doc_ids.append(doc_id)
            continue
        source_model.parse_collection_document_report(
            repo_root,
            resolved.parent_config,
            resolved.document_config,
            source_text,
            source_name=resolved.document.path.as_posix(),
        )
        updates.append(
            PublishableSourceUpdate(
                doc_id=doc_id,
                path=resolved.document.path,
                original_bytes=resolved.document.source_text.encode("utf-8"),
                source_text=source_text,
            )
        )

    return PublishableSelectionPlan(
        collection=collection,
        publishable=publishable,
        requested_doc_ids=requested_doc_ids,
        unchanged_doc_ids=tuple(unchanged_doc_ids),
        updates=tuple(updates),
    )


def _result_payload(
    plan: PublishableSelectionPlan,
    *,
    dry_run: bool,
    rebuild: dict[str, Any] | None,
) -> dict[str, Any]:
    updated_doc_ids = [update.doc_id for update in plan.updates]
    count = len(plan.requested_doc_ids)
    if updated_doc_ids:
        verb = "Included" if plan.publishable else "Excluded"
        summary = f"{verb} {count} checked document{'s' if count != 1 else ''} in next Publish."
    else:
        summary = f"No publishability changes for {count} checked document{'s' if count != 1 else ''}."
    return {
        "ok": True,
        "operation": "set_publishable",
        "target": plan.target(),
        "scope": plan.collection.scope,
        **(
            {"sub_scope": plan.collection.sub_scope}
            if plan.collection.sub_scope
            else {}
        ),
        "publishable": plan.publishable,
        "requested_doc_ids": list(plan.requested_doc_ids),
        "updated_doc_ids": updated_doc_ids,
        "unchanged_doc_ids": list(plan.unchanged_doc_ids),
        "document_count": count,
        "updated_count": len(updated_doc_ids),
        "rebuild": rebuild,
        "dry_run": dry_run,
        "summary_text": summary,
    }


def _failure_payload(
    plan: PublishableSelectionPlan,
    error: Exception,
    *,
    rollback: dict[str, Any] | None,
) -> dict[str, Any]:
    rollback_payload = rollback or {
        "status": "not_started",
        "sources_restored": True,
        "rebuild": None,
        "error": "",
    }
    return {
        "ok": False,
        "operation": "set_publishable",
        "target": plan.target(),
        "publishable": plan.publishable,
        "requested_doc_ids": list(plan.requested_doc_ids),
        "updated_doc_ids": [],
        "unchanged_doc_ids": list(plan.unchanged_doc_ids),
        "committed": rollback_payload.get("status") not in {
            "not_started",
            "completed",
        },
        "retry_safe": rollback_payload.get("status") in {"not_started", "completed"},
        "rollback": rollback_payload,
        "error": f"Set Publishable failed: {error}",
    }


def apply_set_publishable_plan(
    repo_root: Path,
    plan: PublishableSelectionPlan,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    if dry_run or not plan.updates:
        return _result_payload(plan, dry_run=dry_run, rebuild=None)

    snapshots = {
        update.path: update.original_bytes
        for update in plan.updates
    }

    def write_operation() -> None:
        for update in plan.updates:
            source_model.write_text_atomic(update.path, update.source_text)

    try:
        if plan.collection.sub_scope:
            rebuild = write_rebuild.perform_sub_scope_source_write_and_rebuild(
                repo_root,
                plan.collection.scope,
                plan.collection.sub_scope,
                [update.path for update in plan.updates],
                write_operation,
                suppression_reason="docs-set-publishable",
                source_snapshots=snapshots,
            )
        else:
            updated_doc_ids = [update.doc_id for update in plan.updates]
            rebuild = write_rebuild.perform_scope_source_write_and_rebuild_atomic(
                repo_root,
                plan.collection.scope,
                [update.path for update in plan.updates],
                write_operation,
                suppression_reason="docs-set-publishable",
                source_snapshots=snapshots,
                docs_doc_ids=updated_doc_ids,
                search_doc_ids=updated_doc_ids,
            )
    except (
        write_rebuild.ScopeSourceSnapshotChanged,
        write_rebuild.SubScopeSourceSnapshotChanged,
    ) as error:
        raise PublishableSelectionConflict(
            _failure_payload(plan, error, rollback=None)
        ) from error
    except (
        write_rebuild.ScopeWriteRebuildFailure,
        write_rebuild.SubScopeWriteRebuildFailure,
    ) as error:
        raise PublishableSelectionApplyError(
            _failure_payload(plan, error, rollback=error.rollback)
        ) from error

    log_event(
        repo_root,
        "docs-set-publishable",
        {
            **plan.target(),
            "doc_ids": [update.doc_id for update in plan.updates],
            "publishable": plan.publishable,
        },
    )
    return _result_payload(plan, dry_run=False, rebuild=rebuild)


def set_publishable(
    repo_root: Path,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    return apply_set_publishable_plan(
        repo_root,
        plan_set_publishable(repo_root, body),
        dry_run=dry_run,
    )
