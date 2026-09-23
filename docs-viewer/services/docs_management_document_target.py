#!/usr/bin/env python3
"""Confined source targets and inventories for managed Docs documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import docs_source_model as source_model
from docs_workspace_config import (
    DocsStageConfig,
    DocsCollectionConfig,
    COLLECTION_ID_PATTERN,
    document_source_path,
    load_docs_stage,
    STAGES,
    resolve_workspace_path,
)
from docs_collection_customisations import (
    collection_customisation_authoring_subject_fields,
    collection_customisation_metadata_record,
)
from docs_document_subjects import (
    AUTHORING_SUBJECT_FIELDS,
    FOLDER_PATH_FIELD,
    normalize_authoring_subject,
)
from docs_report_source import ReportSourceContract


PARENT_TARGET_KEYS = frozenset({"stage", "doc_id"})
NAMED_DOCUMENT_TARGET_KEYS = frozenset({"stage", "collection", "doc_id"})
PARENT_COLLECTION_TARGET_KEYS = frozenset({"stage"})
NAMED_COLLECTION_TARGET_KEYS = frozenset({"stage", "collection"})


@dataclass(frozen=True)
class ManagedDocumentTarget:
    collection: str
    doc_id: str
    parent_config: DocsStageConfig
    document_config: DocsStageConfig | DocsCollectionConfig
    source_root: Path
    document: source_model.SourceDoc
    stage: str

    def request_target(self) -> dict[str, str]:
        target = {"stage": self.stage, "doc_id": self.doc_id}
        if self.collection:
            target["collection"] = self.collection
        return target


@dataclass(frozen=True)
class ManagedDocumentCollection:
    collection: str
    parent_config: DocsStageConfig
    document_config: DocsStageConfig | DocsCollectionConfig
    source_root: Path
    stage: str

    def request_target(self) -> dict[str, str]:
        target = {"stage": self.stage}
        if self.collection:
            target["collection"] = self.collection
        return target


def required_target_text(value: Any, *, field: str, lowercase: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a non-blank string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized.lower() if lowercase else normalized


def required_target_stage(value: Any) -> str:
    stage = required_target_text(value, field="stage")
    if stage not in STAGES:
        raise ValueError("stage must be working or pre-publish")
    return stage


def normalize_managed_document_target(target: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(target, Mapping):
        raise ValueError("managed document target must be an object")
    keys = frozenset(target)
    if keys not in {PARENT_TARGET_KEYS, NAMED_DOCUMENT_TARGET_KEYS}:
        raise ValueError(
            "managed document target must contain exactly stage and doc_id, "
            "with collection only for a collection document"
        )
    normalized = {
        "stage": required_target_stage(target.get("stage")),
        "doc_id": required_target_text(target.get("doc_id"), field="doc_id"),
    }
    if not source_model.is_immutable_doc_id(normalized["doc_id"]):
        raise ValueError("doc_id must use immutable document identity")
    if "collection" in target:
        normalized["collection"] = required_target_text(
            target.get("collection"),
            field="collection",
            lowercase=True,
        )
    return normalized


def normalize_managed_document_collection_target(
    target: Mapping[str, Any],
) -> dict[str, str]:
    if not isinstance(target, Mapping):
        raise ValueError("managed document collection target must be an object")
    keys = frozenset(target)
    if keys not in {
        PARENT_COLLECTION_TARGET_KEYS,
        NAMED_COLLECTION_TARGET_KEYS,
    }:
        raise ValueError(
            "managed document collection target must contain exactly stage, "
            "with collection only for a configured child collection"
        )
    normalized = {"stage": required_target_stage(target.get("stage"))}
    if "collection" in target:
        normalized["collection"] = required_target_text(
            target.get("collection"),
            field="collection",
            lowercase=True,
        )
    return normalized


def managed_document_target_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if "scope" in request:
        raise ValueError("scope is retired; document requests require stage and doc_id")
    if "sub_scope" in request:
        raise ValueError("sub_scope is retired; use collection")
    target = {
        "stage": request.get("stage"),
        "doc_id": request.get("doc_id"),
    }
    if "collection" in request:
        target["collection"] = request.get("collection")
    return target


def resolve_managed_document_collection(
    repo_root: Path,
    *,
    collection: Any | None = None,
    stage: str,
    require_existing_source_root: bool = True,
) -> ManagedDocumentCollection:
    """Resolve the configured destination; creation skips directory preflight."""
    parent_config = load_docs_stage(repo_root, stage)

    normalized_collection = ""
    document_config: DocsStageConfig | DocsCollectionConfig = parent_config
    if collection is not None:
        normalized_collection = required_target_text(
            collection,
            field="collection",
            lowercase=True,
        )
        if not COLLECTION_ID_PATTERN.fullmatch(normalized_collection):
            raise ValueError("collection must identify one configured collection")
        matching = [
            candidate
            for candidate in parent_config.collections
            if candidate.collection == normalized_collection
        ]
        if not matching:
            raise ValueError(
                f"unknown collection {normalized_collection!r}"
            )
        document_config = matching[0]

    source_root = resolve_workspace_path(repo_root, document_source_path(document_config)).resolve()
    if not source_root.is_relative_to(parent_config.workspace_root.path):
        raise ValueError("source root escapes the configured Docs workspace")
    if require_existing_source_root and not source_root.is_dir():
        target_label = f"{stage}/{normalized_collection or 'ordinary documents'}"
        raise FileNotFoundError(f"source root not found for managed document target {target_label}")
    return ManagedDocumentCollection(
        collection=normalized_collection,
        parent_config=parent_config,
        document_config=document_config,
        source_root=source_root,
        stage=parent_config.stage,
    )


def resolve_managed_document_collection_target(
    repo_root: Path,
    target: Mapping[str, Any],
) -> ManagedDocumentCollection:
    normalized = normalize_managed_document_collection_target(target)
    return resolve_managed_document_collection(
        repo_root,
        collection=normalized.get("collection"),
        stage=normalized["stage"],
    )


def confined_source_path(source_root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(source_root)
    except ValueError as exc:
        raise ValueError("source path escapes configured document root") from exc
    if not resolved.is_file():
        raise FileNotFoundError(
            f"managed source document {candidate.stem!r} was not found"
        )
    return resolved


def confined_document_path(source_root: Path, doc_id: str) -> Path:
    if doc_id in {".", ".."} or "/" in doc_id or "\\" in doc_id or "\0" in doc_id:
        raise ValueError("doc_id must identify one direct-child source document")
    return confined_source_path(source_root, source_root / f"{doc_id}.md")


def source_doc_from_path(
    *,
    path: Path,
    requested_doc_id: str | None = None,
    report_contract: ReportSourceContract | None = None,
) -> source_model.SourceDoc:
    source_text = path.read_bytes().decode("utf-8")
    front_matter, body = source_model.parse_source_text(source_text, source_name=path.name)
    existing_doc_id = str(front_matter.get("doc_id") or "").strip()
    if not existing_doc_id:
        label = requested_doc_id or path.name
        raise ValueError(f"managed source document {label!r} is missing front-matter doc_id")
    if requested_doc_id is not None and existing_doc_id != requested_doc_id:
        raise ValueError(
            f"managed source front-matter doc_id {existing_doc_id!r} "
            f"does not match requested doc_id {requested_doc_id!r}"
        )
    title = str(front_matter.get("title") or source_model.humanize(existing_doc_id)).strip()
    report = (
        source_model.parse_document_report(
            source_text,
            front_matter,
            body,
            source_name=path.as_posix(),
            contract=report_contract,
        )
        if report_contract is not None
        else None
    )
    return source_model.SourceDoc(
        path=path,
        source_text=source_text,
        front_matter=dict(front_matter),
        body=body,
        doc_id=existing_doc_id,
        title=title or existing_doc_id,
        ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
        parent_id=str(front_matter.get("parent_id") or "").strip(),
        report=report,
    )


def resolve_managed_document_target(
    repo_root: Path,
    target: Mapping[str, Any],
) -> ManagedDocumentTarget:
    normalized = normalize_managed_document_target(target)
    collection = resolve_managed_document_collection(
        repo_root,
        collection=normalized.get("collection"),
        stage=normalized["stage"],
    )
    report_contract = source_model.report_source_contract_for_collection(
        repo_root,
        collection.parent_config,
        collection.document_config,
    )
    if collection.collection:
        path = confined_document_path(collection.source_root, normalized["doc_id"])
        document = source_doc_from_path(
            path=path,
            requested_doc_id=normalized["doc_id"],
            report_contract=report_contract,
        )
        source_model.validate_document_status_front_matter(
            document.front_matter,
            collection_config=collection.document_config,
            source_name=path.name,
        )
    else:
        parent_documents = [
            source_doc_from_path(
                path=confined_source_path(collection.source_root, candidate),
                report_contract=report_contract,
            )
            for candidate in source_model.document_markdown_paths(collection.source_root)
        ]
        for candidate in parent_documents:
            source_model.validate_document_status_front_matter(
                candidate.front_matter,
                collection_config=collection.document_config,
                source_name=candidate.path.name,
            )
        source_model.validate_collection_docs(
            parent_documents,
            allow_unknown_parent_ids=collection.parent_config.allow_unresolved_parent_ids,
        )
        document = next(
            (
                candidate
                for candidate in parent_documents
                if candidate.doc_id == normalized["doc_id"]
            ),
            None,
        )
        if document is None:
            raise FileNotFoundError(
                f"managed source document {normalized['doc_id']!r} was not found"
            )
        path = document.path.resolve()
        try:
            path.relative_to(collection.source_root)
        except ValueError as exc:
            raise ValueError("source path escapes configured document root") from exc
    return ManagedDocumentTarget(
        collection=collection.collection,
        doc_id=document.doc_id,
        parent_config=collection.parent_config,
        document_config=collection.document_config,
        source_root=collection.source_root,
        document=document,
        stage=collection.stage,
    )


def managed_document_metadata(
    repo_root: Path,
    target: Mapping[str, Any],
) -> dict[str, object]:
    resolved = resolve_managed_document_target(repo_root, target)
    document = resolved.document
    front_matter = document.front_matter
    record: dict[str, object] = {
        "doc_id": document.doc_id,
        "title": document.title,
        "summary": " ".join(str(front_matter.get("summary") or "").split()),
        "date": str(front_matter.get("date") or "").strip(),
        "date_display": str(front_matter.get("date_display") or "").strip(),
    }
    payload_revision = source_model.source_revision(document.source_text.encode("utf-8"))
    if source_model.collection_supports_draft(resolved.document_config):
        record["draft"] = front_matter.get("draft", True)
    if not resolved.collection:
        record["ui_status"] = document.ui_status
        record["parent_id"] = document.parent_id

    payload: dict[str, object] = {
        "ok": True,
        **resolved.request_target(),
        "record": record,
        "source_revision": payload_revision,
    }
    if resolved.stage == "working":
        from docs_document_placement import document_location_parent_id

        payload["location_parent_id"] = document_location_parent_id(repo_root, resolved)
    if resolved.collection:
        subject_fields = collection_customisation_authoring_subject_fields(
            resolved.document_config.collection_customisation
        )
        folder_supported = resolved.stage == "working" and FOLDER_PATH_FIELD in subject_fields
        payload["folder_subject_supported"] = folder_supported
        if subject_fields or any(
            field_name in front_matter for field_name in AUTHORING_SUBJECT_FIELDS
        ):
            record["authoring_subject"] = normalize_authoring_subject(
                front_matter,
                folder_supported=folder_supported,
            )
        customisation_record = collection_customisation_metadata_record(
            resolved.document_config.collection_customisation,
            front_matter,
            doc_id=document.doc_id,
        )
        if customisation_record is not None:
            record["customisation"] = customisation_record
        payload["collection"] = resolved.collection
    return payload
