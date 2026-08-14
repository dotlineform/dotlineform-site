#!/usr/bin/env python3
"""Confirmed, target-first apply boundary for multi-document Move transfers."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import docs_document_transfer as transfer
import docs_document_transfer_apply as transfer_apply
import docs_source_model as source_model
from docs_artifact_locations import ArtifactLocationAdapter
from docs_media_inventory import document_media_references


DOCUMENT_MOVE_APPLY_SCHEMA_VERSION = "docs_document_move_apply_v1"
DOCUMENT_MOVE_ACTIVITY_EVENT = "docs-document-move"
DOCUMENT_MOVE_SUPPRESSION_REASON = "docs-document-move"
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
MediaBuilder = Callable[..., list[dict[str, object]]]
ActivityLogger = Callable[[Path, str, dict[str, Any]], None]


class DocumentMoveApplyError(RuntimeError):
    """A Move mutation failed, with exact observed source and target state."""

    def __init__(self, message: str, result: dict[str, Any]) -> None:
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class DocumentMoveSourceTransform:
    planned_document: transfer.TransferDocumentPlan
    source_text: str
    viewer_link_rewrites: int
    media_link_rewrites: int

    @property
    def source_path(self) -> Path:
        return self.planned_document.source_doc.path

    @property
    def target_path(self) -> Path:
        return self.planned_document.target_path


@dataclass(frozen=True)
class DocumentMoveTransformation:
    plan: transfer.DocumentTransferPlan
    documents: tuple[DocumentMoveSourceTransform, ...]

    @property
    def viewer_link_rewrites(self) -> int:
        return sum(document.viewer_link_rewrites for document in self.documents)

    @property
    def media_link_rewrites(self) -> int:
        return sum(document.media_link_rewrites for document in self.documents)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform_document_move(
    plan: transfer.DocumentTransferPlan,
) -> DocumentMoveTransformation:
    """Render candidate Move sources without writing documents or media."""

    if plan.mode != transfer.MOVE_MODE:
        raise ValueError("document Move transformation requires move mode")
    if not plan.ok:
        raise ValueError("blocked document transfer cannot be transformed")

    transformed: list[DocumentMoveSourceTransform] = []
    for planned_document in plan.documents:
        front_matter = dict(planned_document.source_doc.front_matter)
        front_matter["parent_id"] = planned_document.target_parent_id
        body, viewer_link_rewrites = transfer_apply.rewrite_transferred_viewer_links(
            planned_document.source_doc.body,
            plan,
        )
        body, media_link_rewrites = transfer_apply.rewrite_transferred_media_links(
            body,
            plan,
        )
        transformed.append(
            DocumentMoveSourceTransform(
                planned_document=planned_document,
                source_text=source_model.format_source(front_matter, body),
                viewer_link_rewrites=viewer_link_rewrites,
                media_link_rewrites=media_link_rewrites,
            )
        )
    return DocumentMoveTransformation(plan=plan, documents=tuple(transformed))


def _validate_transformation(transformation: DocumentMoveTransformation) -> None:
    plan = transformation.plan
    if len(transformation.documents) != len(plan.documents):
        raise transfer_apply.DocumentTransferPlanStaleError(
            "document transfer plan is stale: transformed document count changed"
        )
    for transformed in transformation.documents:
        planned = transformed.planned_document
        try:
            front_matter, body = source_model.parse_source_text(
                transformed.source_text,
                source_name=planned.target_path.name,
            )
        except ValueError as exc:
            raise transfer_apply.DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate source for "
                f"{planned.target_doc_id!r} is invalid: {exc}"
            ) from exc
        expected_front_matter = dict(planned.source_doc.front_matter)
        expected_front_matter["parent_id"] = planned.target_parent_id
        if front_matter != expected_front_matter:
            raise transfer_apply.DocumentTransferPlanStaleError(
                f"document transfer plan is stale: canonical fields changed for "
                f"{planned.target_doc_id!r}"
            )
        if planned.target_doc_id != planned.source_doc.doc_id:
            raise transfer_apply.DocumentTransferPlanStaleError(
                f"document transfer plan is stale: Move identity changed for "
                f"{planned.source_doc.doc_id!r}"
            )
        _remaining_body, remaining_viewer_links = (
            transfer_apply.rewrite_transferred_viewer_links(body, plan)
        )
        _remaining_body, remaining_media_links = (
            transfer_apply.rewrite_transferred_media_links(body, plan)
        )
        if remaining_viewer_links or remaining_media_links:
            raise transfer_apply.DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate links remain stale "
                f"for {planned.target_doc_id!r}"
            )


def revalidate_document_move_plan(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocumentMoveTransformation:
    if not isinstance(plan, transfer.DocumentTransferPlan):
        raise transfer_apply.DocumentTransferPlanStaleError(
            "document transfer plan is stale: planned transfer is required"
        )
    if plan.mode != transfer.MOVE_MODE:
        raise transfer_apply.DocumentTransferPlanStaleError(
            "document transfer plan is stale: transfer mode is not move"
        )
    try:
        current_plan = transfer.restore_document_transfer_apply_plan(
            repo_root,
            plan.apply_plan_payload(),
            source_media_client=source_media_client,
            target_media_client=target_media_client,
            env_files=env_files,
            environ=environ,
        )
    except ValueError as exc:
        raise transfer_apply.DocumentTransferPlanStaleError(str(exc)) from exc
    transformation = transform_document_move(current_plan)
    _validate_transformation(transformation)
    return transformation


def _artifact_observation(
    adapter: ArtifactLocationAdapter | None,
    identity: str,
    *,
    expected_sha256: str,
    produced: bool = False,
) -> dict[str, Any]:
    if adapter is None:
        return {"state": "unavailable"}
    try:
        if adapter.stat(identity) is None:
            return {"state": "missing"}
        data = adapter.read(identity)
    except Exception as exc:
        return {"state": "unavailable", "detail": str(exc)}
    observed_sha256 = _sha256(data)
    return {
        "state": (
            "present"
            if produced
            else "exact"
            if observed_sha256 == expected_sha256
            else "different"
        ),
        "size": len(data),
        "sha256": observed_sha256,
    }


def _document_observation(path: Path, expected_text: str) -> dict[str, Any]:
    if not path.is_file():
        return {"state": "missing"}
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"state": "unavailable", "detail": str(exc)}
    expected = expected_text.encode("utf-8")
    return {
        "state": "exact" if data == expected else "different",
        "size": len(data),
        "sha256": _sha256(data),
    }


def _published_adapters_or_empty(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    target: bool,
    client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, ArtifactLocationAdapter]:
    try:
        return transfer.published_transfer_adapters(
            repo_root,
            plan.target_config if target else plan.source_config,
            {item.media_type for item in plan.media},
            client=client,
            env_files=env_files,
            environ=environ,
        )
    except Exception:
        return {}


def _scope_evidence(
    repo_root: Path,
    transformation: DocumentMoveTransformation,
    *,
    target: bool,
    media_adapters: Mapping[str, ArtifactLocationAdapter],
) -> dict[str, Any]:
    plan = transformation.plan
    documents = []
    for item in transformation.documents:
        documents.append(
            {
                "doc_id": item.planned_document.source_doc.doc_id,
                **_document_observation(
                    item.target_path if target else item.source_path,
                    (
                        item.source_text
                        if target
                        else item.planned_document.source_doc.source_text
                    ),
                ),
            }
        )
    media = [
        {
            "media_type": item.media_type,
            "identity": item.identity,
            "shared_outside_document_ids": list(
                item.shared_outside_document_ids
            ),
            **_artifact_observation(
                media_adapters.get(item.media_type),
                item.identity,
                expected_sha256=item.source_sha256,
                produced=target and item.target_status == "produce",
            ),
        }
        for item in plan.media
    ]
    build_sources: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    config = plan.target_config if target else plan.source_config
    for item in plan.media:
        for build in item.build_sources:
            key = (build.build_type, build.source_identity)
            if key in seen:
                continue
            seen.add(key)
            try:
                adapter = transfer.transfer_build_source_adapter(
                    repo_root,
                    config,
                    build.build_type,
                )
            except Exception:
                adapter = None
            build_sources.append(
                {
                    "build_type": build.build_type,
                    "identity": build.source_identity,
                    **_artifact_observation(
                        adapter,
                        build.source_identity,
                        expected_sha256=build.source_sha256,
                    ),
                }
            )
    return {
        "documents": documents,
        "media": media,
        "build_sources": build_sources,
    }


def _failure_result(
    repo_root: Path,
    transformation: DocumentMoveTransformation,
    *,
    phase: str,
    error: Exception,
    source_media_client: object | None,
    target_media_client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
    target_media_complete: bool,
    target_rebuild_complete: bool,
    source_rebuild_complete: bool,
    source_media_cleanup_complete: bool,
) -> dict[str, Any]:
    plan = transformation.plan
    source_adapters = _published_adapters_or_empty(
        repo_root,
        plan,
        target=False,
        client=source_media_client,
        env_files=env_files,
        environ=environ,
    )
    target_adapters = _published_adapters_or_empty(
        repo_root,
        plan,
        target=True,
        client=target_media_client,
        env_files=env_files,
        environ=environ,
    )
    return {
        "schema_version": DOCUMENT_MOVE_APPLY_SCHEMA_VERSION,
        "ok": False,
        "mode": transfer.MOVE_MODE,
        "source_scope": plan.source_scope,
        "target_scope": plan.target_scope,
        "operation_timestamp": plan.operation_timestamp,
        "phase": phase,
        "error": {"type": type(error).__name__, "message": str(error)},
        "target_media_complete": target_media_complete,
        "target_rebuild_complete": target_rebuild_complete,
        "source_rebuild_complete": source_rebuild_complete,
        "source_media_cleanup_complete": source_media_cleanup_complete,
        "target_state": _scope_evidence(
            repo_root,
            transformation,
            target=True,
            media_adapters=target_adapters,
        ),
        "source_state": _scope_evidence(
            repo_root,
            transformation,
            target=False,
            media_adapters=source_adapters,
        ),
    }


def _delete_source_documents(
    transformation: DocumentMoveTransformation,
) -> None:
    for item in transformation.documents:
        if not item.source_path.is_file():
            raise FileNotFoundError(
                f"source document does not exist: {item.source_path.name}"
            )
        if (
            item.source_path.read_text(encoding="utf-8")
            != item.planned_document.source_doc.source_text
        ):
            raise transfer_apply.DocumentTransferPlanStaleError(
                f"document transfer plan is stale: source document changed for "
                f"{item.planned_document.source_doc.doc_id!r}"
            )
    for item in transformation.documents:
        item.source_path.unlink()


def _cleanup_source_media(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    source_media_client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[dict[str, str]]]:
    source_adapters = transfer.published_transfer_adapters(
        repo_root,
        plan.source_config,
        {item.media_type for item in plan.media},
        client=source_media_client,
        env_files=env_files,
        environ=environ,
    )
    removed_media: list[dict[str, str]] = []
    retained_shared_media: list[dict[str, Any]] = []
    removed_build_sources: list[dict[str, str]] = []
    remaining_references: dict[tuple[str, str], set[str]] = {}
    for reference in document_media_references(repo_root, plan.source_config):
        remaining_references.setdefault(
            (reference.media_type, reference.identity),
            set(),
        ).add(reference.doc_id)
    shared_document_ids = {
        (item.media_type, item.identity): tuple(
            sorted(
                remaining_references.get(
                    (item.media_type, item.identity),
                    set(),
                )
            )
        )
        for item in plan.media
    }
    shared_build_sources = {
        (build.build_type, build.source_identity)
        for item in plan.media
        if shared_document_ids[(item.media_type, item.identity)]
        for build in item.build_sources
    }

    for item in plan.media:
        outside_document_ids = shared_document_ids[
            (item.media_type, item.identity)
        ]
        if outside_document_ids:
            retained_shared_media.append(
                {
                    "media_type": item.media_type,
                    "identity": item.identity,
                    "outside_document_ids": list(outside_document_ids),
                }
            )
            continue
        adapter = source_adapters[item.media_type]
        adapter.delete(item.identity)
        if adapter.stat(item.identity) is not None:
            raise RuntimeError(
                f"source media was not deleted: {item.media_type}/{item.identity}"
            )
        removed_media.append(
            {"media_type": item.media_type, "identity": item.identity}
        )

    seen_build_sources: set[tuple[str, str]] = set()
    for item in plan.media:
        for build in item.build_sources:
            key = (build.build_type, build.source_identity)
            if key in seen_build_sources or key in shared_build_sources:
                continue
            seen_build_sources.add(key)
            adapter = transfer.transfer_build_source_adapter(
                repo_root,
                plan.source_config,
                build.build_type,
            )
            adapter.delete(build.source_identity)
            if adapter.stat(build.source_identity) is not None:
                raise RuntimeError(
                    f"source build input was not deleted: "
                    f"{build.build_type}/{build.source_identity}"
                )
            removed_build_sources.append(
                {
                    "build_type": build.build_type,
                    "identity": build.source_identity,
                }
            )
    return removed_media, retained_shared_media, removed_build_sources


def apply_document_move(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    confirm: bool,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
    media_builder: MediaBuilder | None = None,
    perform_source_write_and_rebuild: PerformSourceWriteAndRebuild | None = None,
    activity_logger: ActivityLogger | None = None,
) -> dict[str, Any]:
    """Apply one confirmed Move plan, completing the target before source cleanup."""

    if confirm is not True:
        raise ValueError("confirm must be true to move documents")
    transformation = revalidate_document_move_plan(
        repo_root,
        plan,
        source_media_client=source_media_client,
        target_media_client=target_media_client,
        env_files=env_files,
        environ=environ,
    )
    current_plan = transformation.plan
    phase = "target_media"
    target_media_complete = False
    target_rebuild_complete = False
    source_rebuild_complete = False
    source_media_cleanup_complete = False

    try:
        target_media = transfer_apply.apply_target_media_transfer(
            repo_root,
            current_plan,
            source_media_client=source_media_client,
            target_media_client=target_media_client,
            env_files=env_files,
            environ=environ,
            media_builder=media_builder,
        )
        target_media_complete = True

        if perform_source_write_and_rebuild is None:
            from docs_write_rebuild import (
                perform_source_write_and_rebuild as coordinated_write,
            )

            perform_source_write_and_rebuild = coordinated_write

        moved_doc_ids = [
            item.planned_document.source_doc.doc_id
            for item in transformation.documents
        ]
        target_paths = [item.target_path for item in transformation.documents]
        target_written_paths: list[Path] = []

        def write_target_documents() -> None:
            for item in transformation.documents:
                source_model.write_text_atomic_new(item.target_path, item.source_text)
                target_written_paths.append(item.target_path)

        phase = "target_documents_and_rebuild"
        target_rebuild = perform_source_write_and_rebuild(
            repo_root,
            current_plan.target_scope,
            target_paths,
            write_target_documents,
            suppression_reason=DOCUMENT_MOVE_SUPPRESSION_REASON,
            docs_doc_ids=moved_doc_ids,
            written_paths=target_written_paths,
            skip_media_builds=True,
        )
        target_rebuild_complete = True

        source_paths = [item.source_path for item in transformation.documents]
        phase = "source_documents_and_rebuild"
        source_rebuild = perform_source_write_and_rebuild(
            repo_root,
            current_plan.source_scope,
            source_paths,
            lambda: _delete_source_documents(transformation),
            suppression_reason=DOCUMENT_MOVE_SUPPRESSION_REASON,
            docs_doc_ids=moved_doc_ids,
            written_paths=[],
            skip_media_builds=True,
        )
        source_rebuild_complete = True

        phase = "source_media_cleanup"
        (
            removed_media,
            retained_shared_media,
            removed_build_sources,
        ) = _cleanup_source_media(
            repo_root,
            current_plan,
            source_media_client=source_media_client,
            env_files=env_files,
            environ=environ,
        )
        source_media_cleanup_complete = True

        effective_roots = [
            {
                "source_doc_id": item.source_doc.doc_id,
                "target_doc_id": item.target_doc_id,
                "target_viewer_url": transfer_apply.management_viewer_url(
                    current_plan.target_scope,
                    item.target_doc_id,
                ),
            }
            for item in current_plan.documents
            if item.effective_root
        ]
        phase = "activity"
        if activity_logger is None:
            from docs_management_context import log_event

            activity_logger = log_event
        activity_logger(
            repo_root,
            DOCUMENT_MOVE_ACTIVITY_EVENT,
            {
                "source_scope": current_plan.source_scope,
                "requested_doc_ids": list(current_plan.requested_doc_ids),
                "target_scope": current_plan.target_scope,
                "effective_roots": effective_roots,
                "moved_count": len(moved_doc_ids),
                "unique_media_count": len(current_plan.media),
                "removed_source_media_count": len(removed_media),
                "retained_shared_media_count": len(retained_shared_media),
            },
        )
    except Exception as exc:
        result = _failure_result(
            repo_root,
            transformation,
            phase=phase,
            error=exc,
            source_media_client=source_media_client,
            target_media_client=target_media_client,
            env_files=env_files,
            environ=environ,
            target_media_complete=target_media_complete,
            target_rebuild_complete=target_rebuild_complete,
            source_rebuild_complete=source_rebuild_complete,
            source_media_cleanup_complete=source_media_cleanup_complete,
        )
        raise DocumentMoveApplyError(
            f"document Move failed during {phase}: {exc}",
            result,
        ) from exc

    media_actions = list(target_media.media_actions)
    build_source_actions = list(target_media.build_source_actions)
    media_counts = {
        status: sum(item["status"] == status for item in media_actions)
        for status in ("created", "reused", "produced")
    }
    build_source_counts = {
        status: sum(item["status"] == status for item in build_source_actions)
        for status in ("created", "reused")
    }
    return {
        "schema_version": DOCUMENT_MOVE_APPLY_SCHEMA_VERSION,
        "ok": True,
        "mode": transfer.MOVE_MODE,
        "source_scope": current_plan.source_scope,
        "requested_doc_ids": list(current_plan.requested_doc_ids),
        "target_scope": current_plan.target_scope,
        "operation_timestamp": current_plan.operation_timestamp,
        "moved_doc_ids": moved_doc_ids,
        "document_count": len(moved_doc_ids),
        "effective_roots": effective_roots,
        "viewer_link_rewrites": transformation.viewer_link_rewrites,
        "media_link_rewrites": transformation.media_link_rewrites,
        "unique_media_count": len(current_plan.media),
        "target_media_counts": media_counts,
        "target_media": media_actions,
        "target_build_source_counts": build_source_counts,
        "target_build_sources": build_source_actions,
        "removed_source_media": removed_media,
        "retained_shared_source_media": retained_shared_media,
        "removed_source_build_sources": removed_build_sources,
        "retained_external_dependencies": [
            asdict(item)
            for item in current_plan.retained_external_dependencies
        ],
        "target_rebuild": target_rebuild,
        "source_rebuild": source_rebuild,
        "summary_text": (
            f"Moved {len(moved_doc_ids)} documents and "
            f"{len(current_plan.media)} unique media items from "
            f"{current_plan.source_scope} to {current_plan.target_scope}; "
            f"retained {len(retained_shared_media)} shared source media items."
        ),
    }


__all__ = [
    "DOCUMENT_MOVE_ACTIVITY_EVENT",
    "DOCUMENT_MOVE_APPLY_SCHEMA_VERSION",
    "DOCUMENT_MOVE_SUPPRESSION_REASON",
    "DocumentMoveApplyError",
    "DocumentMoveSourceTransform",
    "DocumentMoveTransformation",
    "apply_document_move",
    "revalidate_document_move_plan",
    "transform_document_move",
]
