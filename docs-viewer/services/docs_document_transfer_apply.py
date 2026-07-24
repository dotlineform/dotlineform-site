#!/usr/bin/env python3
"""Confirmed, stale-safe apply boundary for multi-document Copy transfers."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote, unquote_plus

import docs_document_transfer as transfer
import docs_source_model as source_model
from docs_artifact_locations import ArtifactLocationAdapter


DOCUMENT_COPY_APPLY_SCHEMA_VERSION = "docs_document_copy_apply_v1"
DOCUMENT_COPY_ACTIVITY_EVENT = "docs-document-copy"
DOCUMENT_COPY_SUPPRESSION_REASON = "docs-document-copy"
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
MediaBuilder = Callable[..., list[dict[str, object]]]
ActivityLogger = Callable[[Path, str, dict[str, Any]], None]


class DocumentTransferPlanStaleError(ValueError):
    """The bounded transfer receipt no longer matches current source or target state."""


class DocumentTransferApplyError(RuntimeError):
    """A Copy mutation failed after revalidation, with exact observed target state."""

    def __init__(self, message: str, result: dict[str, Any]) -> None:
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class DocumentCopySourceTransform:
    planned_document: transfer.TransferDocumentPlan
    source_text: str
    viewer_link_rewrites: int
    media_link_rewrites: int

    @property
    def target_path(self) -> Path:
        return self.planned_document.target_path


@dataclass(frozen=True)
class DocumentCopyTransformation:
    plan: transfer.DocumentTransferPlan
    documents: tuple[DocumentCopySourceTransform, ...]

    @property
    def viewer_link_rewrites(self) -> int:
        return sum(document.viewer_link_rewrites for document in self.documents)

    @property
    def media_link_rewrites(self) -> int:
        return sum(document.media_link_rewrites for document in self.documents)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _query_parts(url: str) -> tuple[str, list[str], str]:
    without_fragment, separator, fragment = url.partition("#")
    path, query_separator, query = without_fragment.partition("?")
    if not query_separator:
        return path, [], f"{separator}{fragment}" if separator else ""
    suffix = f"{separator}{fragment}" if separator else ""
    return path, query.split("&"), suffix


def _query_entries(parts: list[str], key: str) -> list[tuple[int, str]]:
    entries: list[tuple[int, str]] = []
    for index, part in enumerate(parts):
        raw_key, separator, raw_value = part.partition("=")
        if unquote_plus(raw_key) == key:
            entries.append((index, unquote_plus(raw_value) if separator else ""))
    return entries


def _source_scope_for_viewer_url(
    path: str,
    query_parts: list[str],
    plan: transfer.DocumentTransferPlan,
) -> str:
    scope_entries = _query_entries(query_parts, "scope")
    if len(scope_entries) > 1:
        return ""
    if scope_entries:
        return scope_entries[0][1]
    if (
        path == plan.source_config.viewer_base_url
        and not plan.source_config.include_scope_param
    ):
        return plan.source_scope
    return ""


def _target_viewer_url(
    query_parts: list[str],
    fragment_suffix: str,
    *,
    target_doc_id: str,
    plan: transfer.DocumentTransferPlan,
) -> str:
    doc_index = _query_entries(query_parts, "doc")[0][0]
    scope_entries = _query_entries(query_parts, "scope")
    scope_index = scope_entries[0][0] if scope_entries else None
    updated_parts: list[str] = []
    for index, part in enumerate(query_parts):
        if index == doc_index:
            updated_parts.append(f"doc={quote(target_doc_id, safe='')}")
        elif index == scope_index:
            if plan.target_config.include_scope_param:
                updated_parts.append(f"scope={quote(plan.target_scope, safe='')}")
        else:
            updated_parts.append(part)
    if plan.target_config.include_scope_param and scope_index is None:
        updated_parts.insert(0, f"scope={quote(plan.target_scope, safe='')}")
    return (
        f"{plan.target_config.viewer_base_url}?"
        f"{'&'.join(updated_parts)}{fragment_suffix}"
    )


def rewrite_copied_viewer_links(
    body: str,
    plan: transfer.DocumentTransferPlan,
) -> tuple[str, int]:
    id_map = plan.id_map
    changed = 0

    def replace_url(match: re.Match[str]) -> str:
        nonlocal changed
        url = match.group(0)
        path, query_parts, fragment_suffix = _query_parts(url)
        if _source_scope_for_viewer_url(path, query_parts, plan) != plan.source_scope:
            return url
        doc_entries = _query_entries(query_parts, "doc")
        if len(doc_entries) != 1:
            return url
        target_doc_id = id_map.get(doc_entries[0][1])
        if not target_doc_id:
            return url
        changed += 1
        return _target_viewer_url(
            query_parts,
            fragment_suffix,
            target_doc_id=target_doc_id,
            plan=plan,
        )

    return transfer.ROOT_RELATIVE_VIEWER_URL_PATTERN.sub(replace_url, body), changed


def _media_reference_replacements(
    plan: transfer.DocumentTransferPlan,
) -> tuple[tuple[str, str], ...]:
    replacements: set[tuple[str, str]] = set()
    for item in plan.media:
        source_media = plan.source_config.published.media[item.media_type]
        target_media = plan.target_config.published.media[item.media_type]
        for source_prefix, target_prefix in (
            (
                source_media.reference_prefix.as_posix().rstrip("/"),
                target_media.reference_prefix.as_posix().rstrip("/"),
            ),
            (
                source_media.served_path_prefix.rstrip("/"),
                target_media.served_path_prefix.rstrip("/"),
            ),
        ):
            source_reference = f"{source_prefix}/{item.identity}"
            target_reference = f"{target_prefix}/{item.identity}"
            if source_reference != target_reference:
                replacements.add((source_reference, target_reference))
    return tuple(sorted(replacements, key=lambda item: (-len(item[0]), item[0])))


def rewrite_copied_media_links(
    body: str,
    plan: transfer.DocumentTransferPlan,
) -> tuple[str, int]:
    changed = 0
    rewritten = body
    for source_reference, target_reference in _media_reference_replacements(plan):
        pattern = re.compile(
            rf"{re.escape(source_reference)}(?![A-Za-z0-9._~%/-])"
        )
        rewritten, count = pattern.subn(target_reference, rewritten)
        changed += count
    return rewritten, changed


def transform_document_copy(
    plan: transfer.DocumentTransferPlan,
) -> DocumentCopyTransformation:
    """Render candidate Copy sources without writing documents or media."""

    if plan.mode != transfer.COPY_MODE:
        raise ValueError("document Copy transformation requires copy mode")
    if not plan.ok:
        raise ValueError("blocked document transfer cannot be transformed")

    transformed: list[DocumentCopySourceTransform] = []
    for planned_document in plan.documents:
        front_matter = dict(planned_document.source_doc.front_matter)
        front_matter["doc_id"] = planned_document.target_doc_id
        front_matter["added_date"] = plan.operation_timestamp
        front_matter["last_updated"] = plan.operation_timestamp
        front_matter["parent_id"] = planned_document.target_parent_id
        front_matter.pop("viewable", None)
        body, viewer_link_rewrites = rewrite_copied_viewer_links(
            planned_document.source_doc.body,
            plan,
        )
        body, media_link_rewrites = rewrite_copied_media_links(body, plan)
        transformed.append(
            DocumentCopySourceTransform(
                planned_document=planned_document,
                source_text=source_model.format_source(front_matter, body),
                viewer_link_rewrites=viewer_link_rewrites,
                media_link_rewrites=media_link_rewrites,
            )
        )
    return DocumentCopyTransformation(plan=plan, documents=tuple(transformed))


def _validate_transformation(transformation: DocumentCopyTransformation) -> None:
    plan = transformation.plan
    if len(transformation.documents) != len(plan.documents):
        raise DocumentTransferPlanStaleError(
            "document transfer plan is stale: transformed document count changed"
        )
    target_viewable = source_model.default_viewable_for_config(plan.target_config)
    for transformed in transformation.documents:
        planned = transformed.planned_document
        try:
            front_matter, body = source_model.parse_source_text(
                transformed.source_text,
                source_name=planned.target_path.name,
            )
        except ValueError as exc:
            raise DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate source for "
                f"{planned.target_doc_id!r} is invalid: {exc}"
            ) from exc
        expected = {
            "doc_id": planned.target_doc_id,
            "parent_id": planned.target_parent_id,
            "added_date": plan.operation_timestamp,
            "last_updated": plan.operation_timestamp,
        }
        for key, value in expected.items():
            if str(front_matter.get(key) or "") != value:
                raise DocumentTransferPlanStaleError(
                    f"document transfer plan is stale: candidate {key} changed "
                    f"for {planned.target_doc_id!r}"
                )
        if source_model.doc_is_viewable(front_matter) is not target_viewable:
            raise DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate viewability changed "
                f"for {planned.target_doc_id!r}"
            )
        _remaining_body, remaining_viewer_links = rewrite_copied_viewer_links(body, plan)
        _remaining_body, remaining_media_links = rewrite_copied_media_links(body, plan)
        if remaining_viewer_links or remaining_media_links:
            raise DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate links remain stale "
                f"for {planned.target_doc_id!r}"
            )


def revalidate_document_copy_plan(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocumentCopyTransformation:
    if not isinstance(plan, transfer.DocumentTransferPlan):
        raise DocumentTransferPlanStaleError(
            "document transfer plan is stale: planned transfer is required"
        )
    if plan.mode != transfer.COPY_MODE:
        raise DocumentTransferPlanStaleError(
            "document transfer plan is stale: transfer mode is not copy"
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
        raise DocumentTransferPlanStaleError(str(exc)) from exc
    transformation = transform_document_copy(current_plan)
    _validate_transformation(transformation)
    return transformation


def management_viewer_url(scope: str, doc_id: str) -> str:
    return f"/docs/?scope={quote(scope, safe='')}&doc={quote(doc_id, safe='')}"


def _content_type(identity: str) -> str:
    return mimetypes.guess_type(identity)[0] or "application/octet-stream"


def _copy_or_reuse_artifact(
    *,
    source: ArtifactLocationAdapter,
    target: ArtifactLocationAdapter,
    identity: str,
    expected_sha256: str,
    target_status: str,
    role: str,
) -> str:
    source_bytes = source.read(identity)
    if _sha256(source_bytes) != expected_sha256:
        raise DocumentTransferPlanStaleError(
            f"document transfer plan is stale: {role} source bytes changed "
            f"for {identity!r}"
        )
    if target_status == "create":
        target.write(identity, source_bytes, content_type=_content_type(identity))
        if not target.verify_bytes(identity, source_bytes):
            raise RuntimeError(f"{role} target bytes did not verify for {identity!r}")
        return "created"
    if target_status == "reuse":
        if not target.verify_bytes(identity, source_bytes):
            raise DocumentTransferPlanStaleError(
                f"document transfer plan is stale: reusable {role} bytes changed "
                f"for {identity!r}"
            )
        return "reused"
    raise DocumentTransferPlanStaleError(
        f"document transfer plan is stale: {role} target status "
        f"{target_status!r} is invalid for {identity!r}"
    )


def _artifact_observation(
    adapter: ArtifactLocationAdapter | None,
    identity: str,
    *,
    expected_sha256: str = "",
    produced: bool = False,
) -> dict[str, Any]:
    if adapter is None:
        return {"state": "unavailable"}
    try:
        stat = adapter.stat(identity)
        if stat is None:
            return {"state": "missing"}
        data = adapter.read(identity)
    except Exception as exc:
        return {"state": "unavailable", "detail": str(exc)}
    observed_sha256 = _sha256(data)
    if produced:
        state = "present"
    else:
        state = "exact" if observed_sha256 == expected_sha256 else "different"
    return {
        "state": state,
        "size": len(data),
        "sha256": observed_sha256,
    }


def _document_observation(
    transformed: DocumentCopySourceTransform,
) -> dict[str, Any]:
    path = transformed.target_path
    if not path.is_file():
        return {"state": "missing"}
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"state": "unavailable", "detail": str(exc)}
    expected = transformed.source_text.encode("utf-8")
    return {
        "state": "exact" if data == expected else "different",
        "size": len(data),
        "sha256": _sha256(data),
    }


def _target_evidence(
    repo_root: Path,
    transformation: DocumentCopyTransformation,
    *,
    target_media_adapters: Mapping[str, ArtifactLocationAdapter],
) -> dict[str, Any]:
    plan = transformation.plan
    media: list[dict[str, Any]] = []
    for item in plan.media:
        observation = _artifact_observation(
            target_media_adapters.get(item.media_type),
            item.identity,
            expected_sha256=item.source_sha256,
            produced=item.target_status == "produce",
        )
        media.append(
            {
                "media_type": item.media_type,
                "identity": item.identity,
                "planned_status": item.target_status,
                **observation,
            }
        )

    build_sources: list[dict[str, Any]] = []
    seen_build_sources: set[tuple[str, str]] = set()
    for item in plan.media:
        for build in item.build_sources:
            key = (build.build_type, build.source_identity)
            if key in seen_build_sources:
                continue
            seen_build_sources.add(key)
            try:
                adapter = transfer.transfer_build_source_adapter(
                    repo_root,
                    plan.target_config,
                    build.build_type,
                )
            except Exception:
                adapter = None
            build_sources.append(
                {
                    "build_type": build.build_type,
                    "identity": build.source_identity,
                    "planned_status": build.target_status,
                    **_artifact_observation(
                        adapter,
                        build.source_identity,
                        expected_sha256=build.source_sha256,
                    ),
                }
            )

    documents = [
        {
            "source_doc_id": item.planned_document.source_doc.doc_id,
            "target_doc_id": item.planned_document.target_doc_id,
            **_document_observation(item),
        }
        for item in transformation.documents
    ]
    return {
        "media": media,
        "build_sources": build_sources,
        "documents": documents,
    }


def _failure_result(
    repo_root: Path,
    transformation: DocumentCopyTransformation,
    *,
    phase: str,
    error: Exception,
    target_media_adapters: Mapping[str, ArtifactLocationAdapter],
    media_complete: bool,
    rebuild_complete: bool,
) -> dict[str, Any]:
    plan = transformation.plan
    return {
        "schema_version": DOCUMENT_COPY_APPLY_SCHEMA_VERSION,
        "ok": False,
        "mode": transfer.COPY_MODE,
        "source_scope": plan.source_scope,
        "target_scope": plan.target_scope,
        "operation_timestamp": plan.operation_timestamp,
        "phase": phase,
        "error": {"type": type(error).__name__, "message": str(error)},
        "media_complete": media_complete,
        "rebuild_complete": rebuild_complete,
        "target_state": _target_evidence(
            repo_root,
            transformation,
            target_media_adapters=target_media_adapters,
        ),
    }


def apply_document_copy(
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
    """Apply one confirmed Copy plan without overwriting target artifacts."""

    if confirm is not True:
        raise ValueError("confirm must be true to copy documents")
    transformation = revalidate_document_copy_plan(
        repo_root,
        plan,
        source_media_client=source_media_client,
        target_media_client=target_media_client,
        env_files=env_files,
        environ=environ,
    )
    current_plan = transformation.plan
    media_types = {item.media_type for item in current_plan.media}
    target_media_adapters: dict[str, ArtifactLocationAdapter] = {}
    media_actions: list[dict[str, str]] = []
    build_source_actions: list[dict[str, str]] = []
    phase = "media"
    media_complete = False
    rebuild_complete = False

    try:
        source_media_adapters = transfer.published_transfer_adapters(
            repo_root,
            current_plan.source_config,
            media_types,
            client=source_media_client,
            env_files=env_files,
            environ=environ,
        )
        target_media_adapters = transfer.published_transfer_adapters(
            repo_root,
            current_plan.target_config,
            media_types,
            client=target_media_client,
            env_files=env_files,
            environ=environ,
        )

        seen_build_sources: set[tuple[str, str]] = set()
        for item in current_plan.media:
            for build in item.build_sources:
                key = (build.build_type, build.source_identity)
                if key in seen_build_sources:
                    continue
                seen_build_sources.add(key)
                status = _copy_or_reuse_artifact(
                    source=transfer.transfer_build_source_adapter(
                        repo_root,
                        current_plan.source_config,
                        build.build_type,
                    ),
                    target=transfer.transfer_build_source_adapter(
                        repo_root,
                        current_plan.target_config,
                        build.build_type,
                    ),
                    identity=build.source_identity,
                    expected_sha256=build.source_sha256,
                    target_status=build.target_status,
                    role=f"{build.build_type} build source",
                )
                build_source_actions.append(
                    {
                        "build_type": build.build_type,
                        "identity": build.source_identity,
                        "status": status,
                    }
                )

        for item in current_plan.media:
            if item.build_sources:
                if item.target_status == "reuse":
                    status = _copy_or_reuse_artifact(
                        source=source_media_adapters[item.media_type],
                        target=target_media_adapters[item.media_type],
                        identity=item.identity,
                        expected_sha256=item.source_sha256,
                        target_status="reuse",
                        role=f"{item.media_type} published media",
                    )
                    media_actions.append(
                        {
                            "media_type": item.media_type,
                            "identity": item.identity,
                            "status": status,
                        }
                    )
                elif item.target_status != "produce":
                    raise DocumentTransferPlanStaleError(
                        f"document transfer plan is stale: built media target status "
                        f"{item.target_status!r} is invalid for {item.identity!r}"
                    )
                continue
            status = _copy_or_reuse_artifact(
                source=source_media_adapters[item.media_type],
                target=target_media_adapters[item.media_type],
                identity=item.identity,
                expected_sha256=item.source_sha256,
                target_status=item.target_status,
                role=f"{item.media_type} published media",
            )
            media_actions.append(
                {
                    "media_type": item.media_type,
                    "identity": item.identity,
                    "status": status,
                }
            )

        requested_build_outputs: dict[str, set[str]] = {}
        for item in current_plan.media:
            if item.target_status != "produce":
                continue
            if target_media_adapters[item.media_type].stat(item.identity) is not None:
                raise DocumentTransferPlanStaleError(
                    f"document transfer plan is stale: target media "
                    f"{item.media_type}/{item.identity} is no longer absent"
                )
            for build in item.build_sources:
                requested_build_outputs.setdefault(build.build_type, set()).add(
                    item.identity
                )
        if requested_build_outputs:
            if media_builder is None:
                from docs_builder.media_builds import (
                    run_registered_media_builds as registered_media_builder,
                )

                media_builder = registered_media_builder
            media_builder(
                repo_root,
                current_plan.target_config,
                write=True,
                client=target_media_client,
                requested_published_identities=requested_build_outputs,
                replace_existing=False,
            )
            for item in current_plan.media:
                if item.target_status != "produce":
                    continue
                if target_media_adapters[item.media_type].stat(item.identity) is None:
                    raise RuntimeError(
                        f"target media producer did not create "
                        f"{item.media_type}/{item.identity}"
                    )
                media_actions.append(
                    {
                        "media_type": item.media_type,
                        "identity": item.identity,
                        "status": "produced",
                    }
                )
        media_complete = True

        phase = "documents_and_rebuild"
        created_doc_ids = [
            item.planned_document.target_doc_id
            for item in transformation.documents
        ]
        target_paths = [item.target_path for item in transformation.documents]
        written_paths: list[Path] = []

        def write_operation() -> None:
            for item in transformation.documents:
                source_model.write_text_atomic_new(item.target_path, item.source_text)
                written_paths.append(item.target_path)

        if perform_source_write_and_rebuild is None:
            from docs_write_rebuild import (
                perform_source_write_and_rebuild as coordinated_write,
            )

            perform_source_write_and_rebuild = coordinated_write
        rebuild = perform_source_write_and_rebuild(
            repo_root,
            current_plan.target_scope,
            target_paths,
            write_operation,
            suppression_reason=DOCUMENT_COPY_SUPPRESSION_REASON,
            include_search=True,
            docs_doc_ids=created_doc_ids,
            search_doc_ids=created_doc_ids,
            written_paths=written_paths,
            skip_media_builds=True,
        )
        rebuild_complete = True

        phase = "activity"
        if activity_logger is None:
            from docs_management_context import log_event

            activity_logger = log_event
        effective_roots = [
            {
                "source_doc_id": item.source_doc.doc_id,
                "target_doc_id": item.target_doc_id,
                "target_viewer_url": management_viewer_url(
                    current_plan.target_scope,
                    item.target_doc_id,
                ),
            }
            for item in current_plan.documents
            if item.effective_root
        ]
        activity_logger(
            repo_root,
            DOCUMENT_COPY_ACTIVITY_EVENT,
            {
                "source_scope": current_plan.source_scope,
                "requested_doc_ids": list(current_plan.requested_doc_ids),
                "target_scope": current_plan.target_scope,
                "effective_roots": effective_roots,
                "created_count": len(created_doc_ids),
                "unique_media_count": len(current_plan.media),
            },
        )
    except Exception as exc:
        result = _failure_result(
            repo_root,
            transformation,
            phase=phase,
            error=exc,
            target_media_adapters=target_media_adapters,
            media_complete=media_complete,
            rebuild_complete=rebuild_complete,
        )
        raise DocumentTransferApplyError(
            f"document Copy failed during {phase}: {exc}",
            result,
        ) from exc

    media_counts = {
        status: sum(item["status"] == status for item in media_actions)
        for status in ("created", "reused", "produced")
    }
    build_source_counts = {
        status: sum(item["status"] == status for item in build_source_actions)
        for status in ("created", "reused")
    }
    return {
        "schema_version": DOCUMENT_COPY_APPLY_SCHEMA_VERSION,
        "ok": True,
        "mode": transfer.COPY_MODE,
        "source_scope": current_plan.source_scope,
        "requested_doc_ids": list(current_plan.requested_doc_ids),
        "target_scope": current_plan.target_scope,
        "operation_timestamp": current_plan.operation_timestamp,
        "created_doc_ids": created_doc_ids,
        "document_count": len(created_doc_ids),
        "effective_roots": effective_roots,
        "viewer_link_rewrites": transformation.viewer_link_rewrites,
        "media_link_rewrites": transformation.media_link_rewrites,
        "unique_media_count": len(current_plan.media),
        "media_counts": media_counts,
        "media": media_actions,
        "build_source_counts": build_source_counts,
        "build_sources": build_source_actions,
        "retained_external_dependencies": [
            asdict(item)
            for item in current_plan.retained_external_dependencies
        ],
        "rebuild": rebuild,
        "summary_text": (
            f"Copied {len(created_doc_ids)} documents and "
            f"{len(current_plan.media)} unique media items from "
            f"{current_plan.source_scope} to {current_plan.target_scope}."
        ),
    }


__all__ = [
    "DOCUMENT_COPY_ACTIVITY_EVENT",
    "DOCUMENT_COPY_APPLY_SCHEMA_VERSION",
    "DOCUMENT_COPY_SUPPRESSION_REASON",
    "DocumentCopySourceTransform",
    "DocumentCopyTransformation",
    "DocumentTransferApplyError",
    "DocumentTransferPlanStaleError",
    "apply_document_copy",
    "management_viewer_url",
    "revalidate_document_copy_plan",
    "rewrite_copied_media_links",
    "rewrite_copied_viewer_links",
    "transform_document_copy",
]
