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
import docs_document_publication_lineage as publication_lineage
import docs_document_location as document_location
import docs_media_source_evidence as media_source_evidence
import docs_source_model as source_model
from docs_artifact_locations import ArtifactLocationAdapter


DOCUMENT_COPY_APPLY_SCHEMA_VERSION = "docs_document_copy_apply_v3"
DOCUMENT_COPY_ACTIVITY_EVENT = "docs-document-copy"
DOCUMENT_COPY_SUPPRESSION_REASON = "docs-document-copy"
PerformSourceWriteAndRebuild = Callable[..., dict[str, Any]]
PerformSubScopeSourceWriteAndRebuild = Callable[..., dict[str, Any]]
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


@dataclass(frozen=True)
class TargetMediaTransferResult:
    target_media_adapters: Mapping[str, ArtifactLocationAdapter]
    media_actions: tuple[dict[str, str], ...]
    build_source_actions: tuple[dict[str, str], ...]


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


def rewrite_transferred_viewer_links(
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


def _target_copy_viewer_url(
    raw_url: str,
    plan: transfer.DocumentTransferPlan,
    *,
    repo_root: Path,
    target_doc_id: str,
) -> str:
    _path, query_parts, fragment_suffix = _query_parts(raw_url)
    retained_parts = [
        part
        for part in query_parts
        if unquote_plus(part.partition("=")[0])
        not in {"scope", "doc", "subdoc"}
    ]
    target_parts: list[str] = []
    if plan.target_config.include_scope_param:
        target_parts.append(f"scope={quote(plan.target_scope, safe='')}")
    if plan.target_sub_scope:
        target_parts.append(
            "doc="
            + quote(
                transfer.collection_report_host_doc_id(
                    repo_root,
                    plan.target_collection,
                ),
                safe="",
            )
        )
        target_parts.append(f"subdoc={quote(target_doc_id, safe='')}")
    else:
        target_parts.append(f"doc={quote(target_doc_id, safe='')}")
    target_parts.extend(retained_parts)
    return (
        f"{plan.target_config.viewer_base_url}?"
        f"{'&'.join(target_parts)}{fragment_suffix}"
    )


def rewrite_document_copy_viewer_links(
    body: str,
    plan: transfer.DocumentTransferPlan,
    *,
    repo_root: Path,
    source_doc_id: str,
    require_complete_decisions: bool = True,
) -> tuple[str, int]:
    """Apply only the exact link decisions frozen for one copied document."""

    decisions = {
        decision.referenced_doc_id: decision
        for decision in plan.link_decisions
        if decision.source_doc_id == source_doc_id
    }
    observed: dict[str, int] = {}
    source_report_host_id = transfer.collection_report_host_doc_id(
        repo_root,
        plan.source_collection,
    )
    changed = 0

    def replace_url(match: re.Match[str]) -> str:
        nonlocal changed
        raw_url = match.group(0)
        referenced_doc_id = transfer.viewer_link_collection_doc_id(
            raw_url,
            plan.source_collection,
            report_host_doc_id=source_report_host_id,
        )
        if not referenced_doc_id:
            return raw_url
        decision = decisions.get(referenced_doc_id)
        if decision is None:
            raise DocumentTransferPlanStaleError(
                "document transfer plan is stale: exact source link decision "
                f"is missing for {source_doc_id!r} to {referenced_doc_id!r}"
            )
        observed[referenced_doc_id] = observed.get(referenced_doc_id, 0) + 1
        if decision.status == "retain":
            return raw_url
        if decision.status != "remap" or not decision.target_doc_id:
            raise DocumentTransferPlanStaleError(
                "document transfer plan is stale: exact source link decision "
                f"is invalid for {source_doc_id!r} to {referenced_doc_id!r}"
            )
        changed += 1
        return _target_copy_viewer_url(
            raw_url,
            plan,
            repo_root=repo_root,
            target_doc_id=decision.target_doc_id,
        )

    rewritten = transfer.ROOT_RELATIVE_VIEWER_URL_PATTERN.sub(replace_url, body)
    expected = {
        referenced_doc_id: decision.occurrence_count
        for referenced_doc_id, decision in decisions.items()
    }
    if require_complete_decisions and observed != expected:
        raise DocumentTransferPlanStaleError(
            "document transfer plan is stale: exact source link occurrences changed "
            f"for {source_doc_id!r}"
        )
    return rewritten, changed


def _media_reference_replacements(
    plan: transfer.DocumentTransferPlan,
) -> tuple[tuple[str, str], ...]:
    replacements: set[tuple[str, str]] = set()
    for item in plan.media:
        source_media = plan.source_config.media.types[item.media_type]
        target_media = plan.target_config.media.types[item.media_type]
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


def rewrite_transferred_media_links(
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
    *,
    repo_root: Path | None = None,
) -> DocumentCopyTransformation:
    """Render candidate Copy sources without writing documents or media."""

    if plan.mode != transfer.COPY_MODE:
        raise ValueError("document Copy transformation requires copy mode")
    if not plan.ok:
        raise ValueError("blocked document transfer cannot be transformed")
    if repo_root is None:
        if plan.source_sub_scope or plan.target_sub_scope:
            raise ValueError(
                "repo_root is required to transform an exact child collection"
            )
        repo_root = Path(".")

    transformed: list[DocumentCopySourceTransform] = []
    for planned_document in plan.documents:
        front_matter = dict(planned_document.source_doc.front_matter)
        front_matter["doc_id"] = planned_document.target_doc_id
        front_matter["last_updated"] = plan.operation_timestamp
        front_matter["parent_id"] = planned_document.target_parent_id
        replacement = planned_document.replacement_doc
        if planned_document.copy_action == transfer.COPY_ACTION_NEW:
            front_matter["added_date"] = plan.operation_timestamp
            front_matter.pop("publishable", None)
        elif (
            planned_document.copy_action == transfer.COPY_ACTION_REPLACE
            and replacement is not None
        ):
            front_matter["added_date"] = replacement.front_matter.get("added_date")
            if "publishable" in replacement.front_matter:
                front_matter["publishable"] = replacement.front_matter["publishable"]
            else:
                front_matter.pop("publishable", None)
        else:
            raise ValueError("document Copy transformation contains an invalid action")
        for decision in plan.custom_metadata:
            if decision.source_doc_id != planned_document.source_doc.doc_id:
                continue
            if decision.status == "omitted":
                front_matter.pop(decision.field_name, None)
            elif decision.status != "retained":
                raise ValueError(
                    "blocked custom metadata decision cannot be transformed"
                )
        body, viewer_link_rewrites = rewrite_document_copy_viewer_links(
            planned_document.source_doc.body,
            plan,
            repo_root=repo_root,
            source_doc_id=planned_document.source_doc.doc_id,
        )
        body, media_link_rewrites = rewrite_transferred_media_links(body, plan)
        transformed.append(
            DocumentCopySourceTransform(
                planned_document=planned_document,
                source_text=source_model.format_source(front_matter, body),
                viewer_link_rewrites=viewer_link_rewrites,
                media_link_rewrites=media_link_rewrites,
            )
        )
    return DocumentCopyTransformation(plan=plan, documents=tuple(transformed))


def _validate_transformation(
    repo_root: Path,
    transformation: DocumentCopyTransformation,
) -> None:
    plan = transformation.plan
    if len(transformation.documents) != len(plan.documents):
        raise DocumentTransferPlanStaleError(
            "document transfer plan is stale: transformed document count changed"
        )
    target_document_config = plan.target_collection.document_config
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
            "added_date": (
                planned.replacement_doc.front_matter.get("added_date")
                if planned.replacement_doc is not None
                else plan.operation_timestamp
            ),
            "last_updated": plan.operation_timestamp,
        }
        for key, value in expected.items():
            if str(front_matter.get(key) or "") != value:
                raise DocumentTransferPlanStaleError(
                    f"document transfer plan is stale: candidate {key} changed "
                    f"for {planned.target_doc_id!r}"
                )
        try:
            source_model.validate_publishable_front_matter(
                front_matter,
                collection_config=target_document_config,
                source_name=planned.target_path.name,
            )
        except ValueError as exc:
            raise DocumentTransferPlanStaleError(
                f"document transfer plan is stale: candidate publishability changed "
                f"for {planned.target_doc_id!r}: {exc}"
            ) from exc
        if source_model.collection_supports_publishable(target_document_config):
            if planned.replacement_doc is None:
                publishability_changed = not source_model.doc_is_publishable(
                    front_matter
                )
            else:
                replacement_front_matter = planned.replacement_doc.front_matter
                publishability_changed = (
                    ("publishable" in front_matter)
                    != ("publishable" in replacement_front_matter)
                    or front_matter.get("publishable")
                    != replacement_front_matter.get("publishable")
                )
            if publishability_changed:
                raise DocumentTransferPlanStaleError(
                    f"document transfer plan is stale: candidate publishability changed "
                    f"for {planned.target_doc_id!r}"
                )
        for decision in plan.custom_metadata:
            if decision.source_doc_id != planned.source_doc.doc_id:
                continue
            if decision.status == "omitted" and decision.field_name in front_matter:
                raise DocumentTransferPlanStaleError(
                    "document transfer plan is stale: omitted custom metadata "
                    f"remains for {planned.target_doc_id!r}"
                )
            if (
                decision.status == "retained"
                and front_matter.get(decision.field_name)
                != planned.source_doc.front_matter.get(decision.field_name)
            ):
                raise DocumentTransferPlanStaleError(
                    "document transfer plan is stale: retained custom metadata "
                    f"changed for {planned.target_doc_id!r}"
                )
        _remaining_body, remaining_viewer_links = rewrite_document_copy_viewer_links(
            body,
            plan,
            repo_root=repo_root,
            source_doc_id=planned.source_doc.doc_id,
            require_complete_decisions=False,
        )
        _remaining_body, remaining_media_links = rewrite_transferred_media_links(
            body,
            plan,
        )
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
    transformation = transform_document_copy(current_plan, repo_root=repo_root)
    _validate_transformation(repo_root, transformation)
    return transformation


def management_viewer_url(scope: str, doc_id: str) -> str:
    return f"/docs/?scope={quote(scope, safe='')}&doc={quote(doc_id, safe='')}"


def management_collection_document_url(
    repo_root: Path,
    collection: transfer.ManagedDocumentCollection,
    doc_id: str,
) -> str:
    collection_url = document_location.management_collection_viewer_url(
        repo_root,
        collection.scope,
        collection.sub_scope,
    )
    return document_location.management_document_viewer_url(
        collection_url,
        doc_id,
        sub_scope=bool(collection.sub_scope),
    )


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


def apply_target_media_transfer(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
    *,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
    media_builder: MediaBuilder | None = None,
    target_media_adapters: Mapping[str, ArtifactLocationAdapter] | None = None,
) -> TargetMediaTransferResult:
    """Create or verify all planned target media without mutating the source."""

    media_types = {item.media_type for item in plan.media}
    source_media_adapters = transfer.published_transfer_adapters(
        repo_root,
        plan.source_config,
        media_types,
        client=source_media_client,
        env_files=env_files,
        environ=environ,
    )
    if target_media_adapters is None:
        target_media_adapters = transfer.published_transfer_adapters(
            repo_root,
            plan.target_config,
            media_types,
            client=target_media_client,
            env_files=env_files,
            environ=environ,
        )
    media_actions: list[dict[str, str]] = []
    build_source_actions: list[dict[str, str]] = []

    seen_build_sources: set[tuple[str, str]] = set()
    for item in plan.media:
        for build in item.build_sources:
            key = (build.build_type, build.source_identity)
            if key in seen_build_sources:
                continue
            seen_build_sources.add(key)
            status = _copy_or_reuse_artifact(
                source=transfer.transfer_build_source_adapter(
                    repo_root,
                    plan.source_config,
                    build.build_type,
                ),
                target=transfer.transfer_build_source_adapter(
                    repo_root,
                    plan.target_config,
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

    for item in plan.media:
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
    for item in plan.media:
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
            plan.target_config,
            write=True,
            client=target_media_client,
            requested_published_identities=requested_build_outputs,
            replace_existing=False,
        )
        for item in plan.media:
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

    return TargetMediaTransferResult(
        target_media_adapters=target_media_adapters,
        media_actions=tuple(media_actions),
        build_source_actions=tuple(build_source_actions),
    )


def apply_target_media_source_evidence(
    repo_root: Path,
    plan: transfer.DocumentTransferPlan,
) -> tuple[dict[str, str], ...]:
    """Apply the frozen Copy evidence decisions without replacing target truth."""

    actions: list[dict[str, str]] = []
    for item in plan.media:
        evidence = item.source_evidence
        if evidence is None:
            raise DocumentTransferPlanStaleError(
                "document transfer plan is stale: media source evidence is missing"
            )
        if evidence.status == transfer.MEDIA_SOURCE_EVIDENCE_COPY:
            existing = media_source_evidence.media_source_evidence_for(
                repo_root,
                plan.target_scope,
                item.media_type,
                item.identity,
            )
            if existing is None:
                media_source_evidence.record_media_source_evidence(
                    repo_root,
                    plan.target_scope,
                    media_type=item.media_type,
                    identity=item.identity,
                    source_root=evidence.source_root,
                    source_path=evidence.source_path,
                )
                status = "copied"
            else:
                status = "retained"
        elif evidence.status == transfer.MEDIA_SOURCE_EVIDENCE_RETAIN:
            status = "retained"
        elif evidence.status == transfer.MEDIA_SOURCE_EVIDENCE_UNRECORDED:
            status = "unrecorded"
        else:
            raise DocumentTransferPlanStaleError(
                "document transfer plan is stale: media source evidence status is invalid"
            )
        actions.append(
            {
                "media_type": item.media_type,
                "identity": item.identity,
                "status": status,
            }
        )
    return tuple(actions)


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
        "source": plan.source_collection.request_target(),
        "target": plan.target_collection.request_target(),
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
    perform_sub_scope_source_write_and_rebuild: (
        PerformSubScopeSourceWriteAndRebuild | None
    ) = None,
    activity_logger: ActivityLogger | None = None,
) -> dict[str, Any]:
    """Apply one confirmed New/Replace Copy plan at its exact target boundary."""

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
    target_media_adapters: dict[str, ArtifactLocationAdapter] = {}
    media_actions: list[dict[str, str]] = []
    build_source_actions: list[dict[str, str]] = []
    media_source_evidence_actions: list[dict[str, str]] = []
    phase = "media"
    media_complete = False
    rebuild_complete = False
    copy_results = [
        {
            "source_doc_id": item.planned_document.source_doc.doc_id,
            "target_doc_id": item.planned_document.target_doc_id,
            "action": item.planned_document.copy_action,
        }
        for item in transformation.documents
    ]
    created_doc_ids = [
        result["target_doc_id"]
        for result in copy_results
        if result["action"] == transfer.COPY_ACTION_NEW
    ]
    replaced_doc_ids = [
        result["target_doc_id"]
        for result in copy_results
        if result["action"] == transfer.COPY_ACTION_REPLACE
    ]

    try:
        target_media_adapters = transfer.published_transfer_adapters(
            repo_root,
            current_plan.target_config,
            {item.media_type for item in current_plan.media},
            client=target_media_client,
            env_files=env_files,
            environ=environ,
        )
        target_media = apply_target_media_transfer(
            repo_root,
            current_plan,
            source_media_client=source_media_client,
            target_media_client=target_media_client,
            env_files=env_files,
            environ=environ,
            media_builder=media_builder,
            target_media_adapters=target_media_adapters,
        )
        target_media_adapters = dict(target_media.target_media_adapters)
        media_actions = list(target_media.media_actions)
        build_source_actions = list(target_media.build_source_actions)
        media_complete = True

        phase = "media_source_evidence"
        media_source_evidence_actions = list(
            apply_target_media_source_evidence(repo_root, current_plan)
        )

        phase = "documents_and_rebuild"
        target_paths = [item.target_path for item in transformation.documents]
        written_paths: list[Path] = []

        def write_operation() -> None:
            for item in transformation.documents:
                if item.planned_document.copy_action == transfer.COPY_ACTION_REPLACE:
                    source_model.write_text_atomic(item.target_path, item.source_text)
                else:
                    source_model.write_text_atomic_new(item.target_path, item.source_text)
                written_paths.append(item.target_path)

        if current_plan.target_sub_scope:
            if perform_sub_scope_source_write_and_rebuild is None:
                from docs_write_rebuild import (
                    perform_sub_scope_source_write_and_rebuild as coordinated_sub_scope_write,
                )

                perform_sub_scope_source_write_and_rebuild = (
                    coordinated_sub_scope_write
                )
            rebuild = perform_sub_scope_source_write_and_rebuild(
                repo_root,
                current_plan.target_scope,
                current_plan.target_sub_scope,
                target_paths,
                write_operation,
                suppression_reason=DOCUMENT_COPY_SUPPRESSION_REASON,
            )
        else:
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
                docs_doc_ids=created_doc_ids,
                written_paths=written_paths,
                skip_media_builds=True,
            )
        rebuild_complete = True

        phase = "lineage"
        lineage_result: dict[str, Any] | None = None
        if current_plan.lineage is not None:
            lineage_table = publication_lineage.apply_copy_results(
                repo_root,
                source_scope=current_plan.source_scope,
                source_sub_scope=current_plan.source_sub_scope,
                editorial_scope=current_plan.target_scope,
                editorial_sub_scope=current_plan.target_sub_scope,
                results=copy_results,
            )
            lineage_result = {
                "schema_version": publication_lineage.LINEAGE_SCHEMA_VERSION,
                "record_count": len(lineage_table.records),
            }
            if perform_sub_scope_source_write_and_rebuild is None:
                raise RuntimeError("lineage source rebuild is unavailable")
            perform_sub_scope_source_write_and_rebuild(
                repo_root,
                current_plan.source_scope,
                current_plan.source_sub_scope,
                [],
                lambda: None,
                suppression_reason=DOCUMENT_COPY_SUPPRESSION_REASON,
            )

        phase = "activity"
        if activity_logger is None:
            from docs_management_context import log_event

            activity_logger = log_event
        effective_roots = [
            {
                "source_doc_id": item.source_doc.doc_id,
                "target_doc_id": item.target_doc_id,
                "target_viewer_url": management_collection_document_url(
                    repo_root,
                    current_plan.target_collection,
                    item.target_doc_id,
                ),
            }
            for item in current_plan.documents
            if item.effective_root
        ]
        activity_payload = {
            "source": current_plan.source_collection.request_target(),
            "requested_doc_ids": list(current_plan.requested_doc_ids),
            "target": current_plan.target_collection.request_target(),
            "effective_roots": effective_roots,
            "created_count": len(created_doc_ids),
            "unique_media_count": len(current_plan.media),
        }
        if current_plan.lineage is not None:
            activity_payload["replaced_count"] = len(replaced_doc_ids)
            activity_payload["copy_results"] = copy_results
        activity_logger(
            repo_root,
            DOCUMENT_COPY_ACTIVITY_EVENT,
            activity_payload,
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
    media_source_evidence_counts = {
        status: sum(
            item["status"] == status
            for item in media_source_evidence_actions
        )
        for status in ("copied", "retained", "unrecorded")
    }
    return {
        "schema_version": DOCUMENT_COPY_APPLY_SCHEMA_VERSION,
        "ok": True,
        "mode": transfer.COPY_MODE,
        "source": current_plan.source_collection.request_target(),
        "requested_doc_ids": list(current_plan.requested_doc_ids),
        "target": current_plan.target_collection.request_target(),
        "operation_timestamp": current_plan.operation_timestamp,
        "created_doc_ids": created_doc_ids,
        "replaced_doc_ids": replaced_doc_ids,
        "document_count": len(copy_results),
        "copy_results": copy_results,
        "effective_roots": effective_roots,
        "viewer_link_rewrites": transformation.viewer_link_rewrites,
        "media_link_rewrites": transformation.media_link_rewrites,
        "unique_media_count": len(current_plan.media),
        "media_counts": media_counts,
        "media": media_actions,
        "build_source_counts": build_source_counts,
        "build_sources": build_source_actions,
        "media_source_evidence_counts": media_source_evidence_counts,
        "media_source_evidence": media_source_evidence_actions,
        "retained_external_dependencies": [
            asdict(item)
            for item in current_plan.retained_external_dependencies
        ],
        "lineage": lineage_result,
        "rebuild": rebuild,
        "summary_text": (
            f"Copied {len(copy_results)} documents "
            f"({len(created_doc_ids)} New, {len(replaced_doc_ids)} Replace) and "
            f"{len(current_plan.media)} unique media items from "
            f"{current_plan.source_scope}"
            f"{'/' + current_plan.source_sub_scope if current_plan.source_sub_scope else ''} "
            f"to {current_plan.target_scope}"
            f"{'/' + current_plan.target_sub_scope if current_plan.target_sub_scope else ''}."
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
    "TargetMediaTransferResult",
    "apply_document_copy",
    "apply_target_media_source_evidence",
    "apply_target_media_transfer",
    "management_collection_document_url",
    "management_viewer_url",
    "revalidate_document_copy_plan",
    "rewrite_transferred_media_links",
    "rewrite_transferred_viewer_links",
    "rewrite_document_copy_viewer_links",
    "transform_document_copy",
]
