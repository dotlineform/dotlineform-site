#!/usr/bin/env python3
"""Confined source targets and inventories for managed Docs documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import docs_source_model as source_model
from docs_scope_config import (
    DocsScopeConfig,
    DocsSubScopeConfig,
    SUB_SCOPE_ID_PATTERN,
    document_source_path,
    load_docs_scope_configs,
    resolve_scope_path,
)
from docs_subscope_customisations import (
    sub_scope_customisation_document_groups,
    sub_scope_customisation_metadata_record,
)


PARENT_TARGET_KEYS = frozenset({"scope", "doc_id"})
SUB_SCOPE_TARGET_KEYS = frozenset({"scope", "sub_scope", "doc_id"})
PARENT_COLLECTION_TARGET_KEYS = frozenset({"scope"})
SUB_SCOPE_COLLECTION_TARGET_KEYS = frozenset({"scope", "sub_scope"})


@dataclass(frozen=True)
class ManagedDocumentTarget:
    scope: str
    sub_scope: str
    doc_id: str
    parent_config: DocsScopeConfig
    document_config: DocsScopeConfig | DocsSubScopeConfig
    source_root: Path
    document: source_model.ScopeDoc

    def request_target(self) -> dict[str, str]:
        target = {"scope": self.scope, "doc_id": self.doc_id}
        if self.sub_scope:
            target["sub_scope"] = self.sub_scope
        return target


@dataclass(frozen=True)
class ManagedDocumentCollection:
    scope: str
    sub_scope: str
    parent_config: DocsScopeConfig
    document_config: DocsScopeConfig | DocsSubScopeConfig
    source_root: Path

    def request_target(self) -> dict[str, str]:
        target = {"scope": self.scope}
        if self.sub_scope:
            target["sub_scope"] = self.sub_scope
        return target


def required_target_text(value: Any, *, field: str, lowercase: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a non-blank string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} is required")
    return normalized.lower() if lowercase else normalized


def normalize_managed_document_target(target: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(target, Mapping):
        raise ValueError("managed document target must be an object")
    keys = frozenset(target)
    if keys not in {PARENT_TARGET_KEYS, SUB_SCOPE_TARGET_KEYS}:
        raise ValueError(
            "managed document target must contain exactly scope and doc_id, "
            "with sub_scope only for a sub-scope document"
        )
    normalized = {
        "scope": required_target_text(target.get("scope"), field="scope", lowercase=True),
        "doc_id": required_target_text(target.get("doc_id"), field="doc_id"),
    }
    if "sub_scope" in target:
        normalized["sub_scope"] = required_target_text(
            target.get("sub_scope"),
            field="sub_scope",
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
        SUB_SCOPE_COLLECTION_TARGET_KEYS,
    }:
        raise ValueError(
            "managed document collection target must contain exactly scope, "
            "with sub_scope only for a configured child collection"
        )
    normalized = {
        "scope": required_target_text(
            target.get("scope"),
            field="scope",
            lowercase=True,
        ),
    }
    if "sub_scope" in target:
        normalized["sub_scope"] = required_target_text(
            target.get("sub_scope"),
            field="sub_scope",
            lowercase=True,
        )
    return normalized


def managed_document_target_request(request: Mapping[str, Any]) -> dict[str, Any]:
    target = {
        "scope": request.get("scope"),
        "doc_id": request.get("doc_id"),
    }
    if "sub_scope" in request:
        target["sub_scope"] = request.get("sub_scope")
    return target


def resolve_managed_document_collection(
    repo_root: Path,
    *,
    scope: Any,
    sub_scope: Any | None = None,
) -> ManagedDocumentCollection:
    normalized_scope = required_target_text(scope, field="scope", lowercase=True)
    configs = load_docs_scope_configs(repo_root, scope_ids=[normalized_scope])
    parent_config = configs.get(normalized_scope)
    if parent_config is None:
        raise ValueError(f"unknown Docs Viewer scope: {normalized_scope}")

    normalized_sub_scope = ""
    document_config: DocsScopeConfig | DocsSubScopeConfig = parent_config
    if sub_scope is not None:
        normalized_sub_scope = required_target_text(
            sub_scope,
            field="sub_scope",
            lowercase=True,
        )
        if not SUB_SCOPE_ID_PATTERN.fullmatch(normalized_sub_scope):
            raise ValueError("sub_scope must identify one configured child scope")
        matching = [
            candidate
            for candidate in parent_config.sub_scopes
            if candidate.sub_scope == normalized_sub_scope
        ]
        if not matching:
            raise ValueError(
                f"unknown sub_scope {normalized_sub_scope!r} for scope {normalized_scope!r}"
            )
        document_config = matching[0]

    source_root = resolve_scope_path(repo_root, document_source_path(document_config)).resolve()
    if not source_root.is_dir():
        target_label = (
            f"{normalized_scope}/{normalized_sub_scope}"
            if normalized_sub_scope
            else normalized_scope
        )
        raise FileNotFoundError(f"source root not found for managed document target {target_label}")
    return ManagedDocumentCollection(
        scope=normalized_scope,
        sub_scope=normalized_sub_scope,
        parent_config=parent_config,
        document_config=document_config,
        source_root=source_root,
    )


def resolve_managed_document_collection_target(
    repo_root: Path,
    target: Mapping[str, Any],
) -> ManagedDocumentCollection:
    normalized = normalize_managed_document_collection_target(target)
    return resolve_managed_document_collection(
        repo_root,
        scope=normalized["scope"],
        sub_scope=normalized.get("sub_scope"),
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
    scope: str,
    requested_doc_id: str | None = None,
) -> source_model.ScopeDoc:
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
    return source_model.ScopeDoc(
        scope=scope,
        path=path,
        source_text=source_text,
        front_matter=dict(front_matter),
        body=body,
        doc_id=existing_doc_id,
        title=title or existing_doc_id,
        ui_status=source_model.normalize_ui_status(front_matter.get("ui_status")),
        parent_id=str(front_matter.get("parent_id") or "").strip(),
        viewable=source_model.doc_is_viewable(front_matter),
        group=source_model.normalize_document_group(front_matter.get("group")),
    )


def resolve_managed_document_target(
    repo_root: Path,
    target: Mapping[str, Any],
) -> ManagedDocumentTarget:
    normalized = normalize_managed_document_target(target)
    collection = resolve_managed_document_collection(
        repo_root,
        scope=normalized["scope"],
        sub_scope=normalized.get("sub_scope"),
    )
    if collection.sub_scope:
        path = confined_document_path(collection.source_root, normalized["doc_id"])
        document = source_doc_from_path(
            path=path,
            scope=collection.scope,
            requested_doc_id=normalized["doc_id"],
        )
        source_model.validate_sub_scope_document_metadata(
            document,
            ui_statuses=collection.document_config.ui_statuses,
            document_groups=sub_scope_customisation_document_groups(
                collection.document_config.sub_scope_customisation
            ),
            sub_scope_customisation=collection.document_config.sub_scope_customisation,
        )
    else:
        parent_documents = [
            source_doc_from_path(
                path=confined_source_path(collection.source_root, candidate),
                scope=collection.scope,
            )
            for candidate in source_model.scope_markdown_paths(collection.source_root)
        ]
        source_model.validate_scope_docs(
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
        scope=collection.scope,
        sub_scope=collection.sub_scope,
        doc_id=document.doc_id,
        parent_config=collection.parent_config,
        document_config=collection.document_config,
        source_root=collection.source_root,
        document=document,
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
        "ui_status": document.ui_status,
        "viewable": document.viewable,
    }
    if not resolved.sub_scope:
        record["parent_id"] = document.parent_id

    payload: dict[str, object] = {
        "ok": True,
        "scope": resolved.scope,
        "doc_id": document.doc_id,
        "record": record,
    }
    if resolved.sub_scope:
        record["group"] = document.group
        customisation_record = sub_scope_customisation_metadata_record(
            resolved.document_config.sub_scope_customisation,
            front_matter,
            doc_id=document.doc_id,
        )
        if customisation_record is not None:
            record["customisation"] = customisation_record
        payload["sub_scope"] = resolved.sub_scope
        payload["source_revision"] = source_model.source_revision(
            document.source_text.encode("utf-8")
        )
        payload["choices"] = {
            "ui_status": list(resolved.document_config.ui_statuses),
            "group": list(
                sub_scope_customisation_document_groups(
                    resolved.document_config.sub_scope_customisation
                )
            ),
        }
    return payload
