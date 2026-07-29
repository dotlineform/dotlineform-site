#!/usr/bin/env python3
"""Plan and execute first-class canonical tag plus document creation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

import docs_source_model as docs_source
import docs_write_rebuild as write_rebuild
from docs_document_identity import (
    allocate_doc_id,
    current_doc_timestamp,
)
from tags import tag_registry_mutations as tag_registry
from tags import tag_source_model as tag_source
from tags import tag_write_transactions as tag_transactions


ANALYSIS_SCOPE = "analysis"
TAG_SUB_SCOPE = "tags"


@dataclass(frozen=True)
class TagDocumentCreatePlan:
    """One create-only Registry and Analysis tag-document transaction."""

    registry_path: Path
    original_registry_bytes: bytes
    updated_registry: Dict[str, Any]
    updated_registry_bytes: bytes
    document_path: Path
    document_source: str
    stats: Dict[str, Any]


class TagDocumentCreateApplyError(RuntimeError):
    """A failed tag create with explicit compensation evidence."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "tag document creation failed"))
        self.payload = payload


def _validate_registry_create_container(registry_payload: Dict[str, Any]) -> None:
    """Require the supported Registry container without auditing its links."""

    if registry_payload.get("tag_registry_version") != tag_source.TAG_REGISTRY_VERSION:
        raise ValueError(
            f"tag creation requires {tag_source.TAG_REGISTRY_VERSION}"
        )
    raw_tags = registry_payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("registry tags must be an array")


def render_tag_document_source(
    *,
    tag_id: str,
    group: str,
    description: str,
    doc_id: str,
    added_date: str,
) -> str:
    """Render a newly linked tag document with scalar group metadata."""

    last_updated = added_date.split(" ", 1)[0]
    body = f"# {tag_id}\n"
    if description:
        body += f"\n{description}\n"
    return docs_source.format_source(
        {
            "doc_id": doc_id,
            "title": tag_id,
            "added_date": added_date,
            "last_updated": last_updated,
            "group": group,
            "parent_id": "",
            "viewable": True,
        },
        body,
    )


def build_tag_document_create_plan(
    repo_root: Path,
    *,
    group: Any,
    tag_id: Any,
    description: Any,
    now_utc: str,
    added_date: str | None = None,
    token_factory: Callable[[int], str] | None = None,
) -> TagDocumentCreatePlan:
    """Plan one linked creation against the configured Analysis/tags root."""

    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    original_registry_bytes = registry_path.read_bytes()
    registry_payload = tag_source.load_registry(registry_path)
    _validate_registry_create_container(registry_payload)
    documents_root = write_rebuild.current_sub_scope_source_root(
        repo_root,
        ANALYSIS_SCOPE,
        TAG_SUB_SCOPE,
    ).resolve()

    document_timestamp = str(added_date or current_doc_timestamp()).strip()
    allocation_kwargs: Dict[str, Any] = {}
    if token_factory is not None:
        allocation_kwargs["token_factory"] = token_factory
    doc_id = allocate_doc_id(
        document_timestamp,
        **allocation_kwargs,
    )
    document_path = (documents_root / f"{doc_id}.md").resolve()
    if document_path.parent != documents_root:
        raise ValueError("document destination escapes configured Analysis/tags root")

    updated_registry, stats = tag_registry.create_registry_tag(
        registry_payload,
        group=group,
        tag_id=tag_id,
        description=description,
        doc_id=doc_id,
        now_utc=now_utc,
    )
    document_source = render_tag_document_source(
        tag_id=str(stats["tag_id"]),
        group=str(stats["group"]),
        description=str(stats["description"]),
        doc_id=doc_id,
        added_date=document_timestamp,
    )
    return TagDocumentCreatePlan(
        registry_path=registry_path,
        original_registry_bytes=original_registry_bytes,
        updated_registry=updated_registry,
        updated_registry_bytes=tag_transactions.canonical_json_bytes(
            updated_registry
        ),
        document_path=document_path,
        document_source=document_source,
        stats=stats,
    )


def relative_repo_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def create_response_payload(
    repo_root: Path,
    plan: TagDocumentCreatePlan,
) -> Dict[str, Any]:
    return {
        **plan.stats,
        "document_target": {
            "scope": ANALYSIS_SCOPE,
            "sub_scope": TAG_SUB_SCOPE,
            "doc_id": plan.stats["doc_id"],
        },
        "document_path": relative_repo_path(repo_root, plan.document_path),
    }


def _sources_match_original(plan: TagDocumentCreatePlan) -> bool:
    try:
        registry_matches = (
            plan.registry_path.read_bytes() == plan.original_registry_bytes
        )
    except OSError:
        registry_matches = False
    return registry_matches and not plan.document_path.exists()


def _restore_sources(plan: TagDocumentCreatePlan) -> None:
    try:
        registry_bytes = plan.registry_path.read_bytes()
    except FileNotFoundError:
        registry_bytes = b""
    if registry_bytes == plan.updated_registry_bytes:
        docs_source.write_bytes_atomic(
            plan.registry_path,
            plan.original_registry_bytes,
        )
    elif registry_bytes != plan.original_registry_bytes:
        raise RuntimeError(
            "tag Registry changed during create compensation; refusing overwrite"
        )

    if plan.document_path.exists():
        current_source = plan.document_path.read_text(encoding="utf-8")
        if current_source != plan.document_source:
            raise RuntimeError(
                "created tag document changed during compensation; refusing delete"
            )
        plan.document_path.unlink()


def execute_tag_document_create(
    repo_root: Path,
    plan: TagDocumentCreatePlan,
) -> Dict[str, Any]:
    """Commit one plan, rebuilding once or compensating both source writes."""

    write_completed = False

    def write_operation() -> None:
        nonlocal write_completed
        if plan.registry_path.read_bytes() != plan.original_registry_bytes:
            raise RuntimeError(
                "tag Registry changed before create; retry from current data"
            )
        docs_source.write_text_atomic_new(
            plan.document_path,
            plan.document_source,
        )
        try:
            tag_transactions.atomic_write(
                plan.registry_path,
                plan.updated_registry,
            )
        except Exception:
            _restore_sources(plan)
            raise
        write_completed = True

    try:
        rebuild = write_rebuild.perform_sub_scope_source_write_and_rebuild(
            repo_root,
            ANALYSIS_SCOPE,
            TAG_SUB_SCOPE,
            [plan.document_path],
            write_operation,
            suppression_reason="studio-tag-document-create",
        )
    except Exception as initial_error:
        if not write_completed:
            source_restored = _sources_match_original(plan)
            raise TagDocumentCreateApplyError(
                {
                    "ok": False,
                    **create_response_payload(repo_root, plan),
                    "source_restored": source_restored,
                    "recovery_rebuild": {
                        "ok": True,
                        "skipped": True,
                        "reason": "create write did not commit",
                    },
                    "retry_safe": source_restored,
                    "error": f"tag document create write failed: {initial_error}",
                }
            ) from initial_error

        try:
            recovery_rebuild = (
                write_rebuild.perform_sub_scope_source_write_and_rebuild(
                    repo_root,
                    ANALYSIS_SCOPE,
                    TAG_SUB_SCOPE,
                    [plan.document_path],
                    lambda: _restore_sources(plan),
                    suppression_reason="studio-tag-document-create-recovery",
                )
            )
        except Exception as recovery_error:
            recovery_rebuild = {
                "ok": False,
                "error": str(recovery_error),
            }
        source_restored = _sources_match_original(plan)
        retry_safe = source_restored and recovery_rebuild.get("ok") is True
        raise TagDocumentCreateApplyError(
            {
                "ok": False,
                **create_response_payload(repo_root, plan),
                "source_restored": source_restored,
                "recovery_rebuild": recovery_rebuild,
                "retry_safe": retry_safe,
                "error": (
                    "tag document create rebuild failed; "
                    f"creation was not completed: {initial_error}"
                ),
            }
        ) from initial_error

    return {
        **create_response_payload(repo_root, plan),
        "rebuild": rebuild,
    }


__all__ = [
    "ANALYSIS_SCOPE",
    "TAG_SUB_SCOPE",
    "TagDocumentCreateApplyError",
    "TagDocumentCreatePlan",
    "build_tag_document_create_plan",
    "create_response_payload",
    "execute_tag_document_create",
    "render_tag_document_source",
]
