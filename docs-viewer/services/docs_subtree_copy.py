#!/usr/bin/env python3
"""Write-free planning for copying one canonical Docs Viewer subtree."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, unquote_plus

import docs_source_model as source_model
from docs_scope_config import (
    DocsScopeConfig,
    PUBLIC_SCOPE_TYPE,
    document_source_path,
    load_docs_scope_configs,
    resolve_scope_path,
)


COPY_SUBTREE_PREVIEW_SCHEMA_VERSION = "docs_copy_subtree_preview_v1"
COPY_SUBTREE_APPLY_PLAN_SCHEMA_VERSION = "docs_copy_subtree_apply_plan_v1"
IdentityTokenFactory = Callable[[int], str]
ROOT_RELATIVE_VIEWER_URL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9:/])/(?:[A-Za-z0-9._~-]+/)+\?[^\s)>'\"<]+"
)


@dataclass(frozen=True)
class CopySubtreeDocumentPlan:
    source_doc: source_model.ScopeDoc
    target_doc_id: str
    target_parent_id: str
    target_path: Path


@dataclass(frozen=True)
class CopySubtreePlan:
    source_scope: str
    target_scope: str
    source_config: DocsScopeConfig
    target_config: DocsScopeConfig
    copy_timestamp: str
    documents: tuple[CopySubtreeDocumentPlan, ...]

    @property
    def root(self) -> CopySubtreeDocumentPlan:
        return self.documents[0]

    @property
    def id_map(self) -> dict[str, str]:
        return {
            document.source_doc.doc_id: document.target_doc_id
            for document in self.documents
        }

    def preview_payload(self) -> dict[str, Any]:
        return {
            "schema_version": COPY_SUBTREE_PREVIEW_SCHEMA_VERSION,
            "ok": True,
            "source": {
                "scope": self.source_scope,
                "doc_id": self.root.source_doc.doc_id,
                "title": self.root.source_doc.title,
            },
            "target": {
                "scope": self.target_scope,
                "placement": "scope_root",
            },
            "document_count": len(self.documents),
            "descendant_count": len(self.documents) - 1,
            "apply_plan": self.apply_plan_payload(),
        }

    def apply_plan_payload(self) -> dict[str, Any]:
        return {
            "schema_version": COPY_SUBTREE_APPLY_PLAN_SCHEMA_VERSION,
            "source_scope": self.source_scope,
            "source_doc_id": self.root.source_doc.doc_id,
            "target_scope": self.target_scope,
            "copy_timestamp": self.copy_timestamp,
            "source_config_sha256": _scope_config_sha256(self.source_config),
            "target_config_sha256": _scope_config_sha256(self.target_config),
            "documents": [
                {
                    "source_doc_id": document.source_doc.doc_id,
                    "source_sha256": _source_sha256(document.source_doc.source_text),
                    "target_doc_id": document.target_doc_id,
                }
                for document in self.documents
            ],
        }


@dataclass(frozen=True)
class CopySubtreeSourceTransform:
    planned_document: CopySubtreeDocumentPlan
    source_text: str
    viewer_link_rewrites: int

    @property
    def target_path(self) -> Path:
        return self.planned_document.target_path


@dataclass(frozen=True)
class CopySubtreeTransformation:
    plan: CopySubtreePlan
    documents: tuple[CopySubtreeSourceTransform, ...]

    @property
    def viewer_link_rewrites(self) -> int:
        return sum(document.viewer_link_rewrites for document in self.documents)


def _jsonable_receipt_value(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable_receipt_value(asdict(value))
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {
            str(key): _jsonable_receipt_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_jsonable_receipt_value(item) for item in value]
    return value


def _scope_config_sha256(config: DocsScopeConfig) -> str:
    serialized = json.dumps(
        _jsonable_receipt_value(config),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _source_sha256(source_text: str) -> str:
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def _receipt_text(payload: dict[str, Any], key: str) -> str:
    return str(payload.get(key) or "").strip()


def _stale_receipt(message: str) -> ValueError:
    return ValueError(f"copy subtree preview is stale: {message}")


def _normalize_configured_scope(
    value: Any,
    *,
    field: str,
    configs: dict[str, DocsScopeConfig],
) -> str:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError(f"{field} is required")
    if scope not in configs:
        raise ValueError(f"{field} {scope!r} is not a configured Docs Viewer scope")
    return scope


def require_copy_source_root(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    require_writable: bool,
) -> Path:
    if require_writable and config.scope_type == PUBLIC_SCOPE_TYPE:
        raise ValueError(
            f"public target scope {config.scope_id!r} is not available for subtree copy"
        )
    root = resolve_scope_path(repo_root, document_source_path(config))
    if not root.exists() or not root.is_dir():
        raise ValueError(f"source root for scope {config.scope_id!r} is unavailable")
    if not os.access(root, os.R_OK | os.X_OK):
        raise ValueError(f"source root for scope {config.scope_id!r} is unavailable")
    if require_writable and not os.access(root, os.W_OK | os.X_OK):
        raise ValueError(f"target scope {config.scope_id!r} cannot accept managed canonical writes")
    return root


def _allocate_target_identities(
    source_docs: list[source_model.ScopeDoc],
    target_docs: list[source_model.ScopeDoc],
    *,
    copy_timestamp: str,
    target_root: Path,
    token_factory: IdentityTokenFactory | None,
) -> dict[str, str]:
    unavailable = {
        identity.lower()
        for doc in [*source_docs, *target_docs]
        for identity in (doc.doc_id, doc.path.stem)
        if identity
    }
    id_map: dict[str, str] = {}
    for source_doc in source_docs:
        allocation_kwargs = {"token_factory": token_factory} if token_factory is not None else {}
        target_doc_id = source_model.allocate_doc_id(
            copy_timestamp,
            unavailable,
            **allocation_kwargs,
        )
        target_path = target_root / f"{target_doc_id}.md"
        if target_path.exists():
            raise ValueError(f"planned target path already exists for {target_doc_id!r}")
        unavailable.add(target_doc_id)
        id_map[source_doc.doc_id] = target_doc_id
    return id_map


def _planned_documents(
    source_docs: list[source_model.ScopeDoc],
    *,
    id_map: dict[str, str],
    target_root: Path,
) -> tuple[CopySubtreeDocumentPlan, ...]:
    planned: list[CopySubtreeDocumentPlan] = []
    planned_ids: set[str] = set()
    for index, source_doc in enumerate(source_docs):
        target_doc_id = id_map[source_doc.doc_id]
        if index == 0:
            target_parent_id = ""
        else:
            target_parent_id = id_map.get(source_doc.parent_id, "")
            if not target_parent_id or target_parent_id not in planned_ids:
                raise RuntimeError(
                    f"copy plan parent for source doc {source_doc.doc_id!r} was not planned before its child"
                )
        planned.append(
            CopySubtreeDocumentPlan(
                source_doc=source_doc,
                target_doc_id=target_doc_id,
                target_parent_id=target_parent_id,
                target_path=target_root / f"{target_doc_id}.md",
            )
        )
        planned_ids.add(target_doc_id)
    return tuple(planned)


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
    plan: CopySubtreePlan,
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
    plan: CopySubtreePlan,
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
    return f"{plan.target_config.viewer_base_url}?{'&'.join(updated_parts)}{fragment_suffix}"


def rewrite_copied_viewer_links(
    body: str,
    plan: CopySubtreePlan,
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

    return ROOT_RELATIVE_VIEWER_URL_PATTERN.sub(replace_url, body), changed


def transform_copy_subtree(plan: CopySubtreePlan) -> CopySubtreeTransformation:
    """Render candidate canonical target sources without writing them."""

    transformed: list[CopySubtreeSourceTransform] = []
    for planned_document in plan.documents:
        front_matter = dict(planned_document.source_doc.front_matter)
        front_matter["doc_id"] = planned_document.target_doc_id
        front_matter["added_date"] = plan.copy_timestamp
        front_matter["last_updated"] = plan.copy_timestamp
        front_matter["parent_id"] = planned_document.target_parent_id
        front_matter.pop("viewable", None)
        body, viewer_link_rewrites = rewrite_copied_viewer_links(
            planned_document.source_doc.body,
            plan,
        )
        transformed.append(
            CopySubtreeSourceTransform(
                planned_document=planned_document,
                source_text=source_model.format_source(front_matter, body),
                viewer_link_rewrites=viewer_link_rewrites,
            )
        )
    return CopySubtreeTransformation(plan=plan, documents=tuple(transformed))


def plan_copy_subtree(
    repo_root: Path,
    *,
    source_scope: Any,
    source_doc_id: Any,
    target_scope: Any,
    copy_timestamp: str | None = None,
    token_factory: IdentityTokenFactory | None = None,
) -> CopySubtreePlan:
    """Return one complete copy plan without writing source or generated data."""

    configs = load_docs_scope_configs(repo_root)
    normalized_source_scope = _normalize_configured_scope(
        source_scope,
        field="source_scope",
        configs=configs,
    )
    normalized_target_scope = _normalize_configured_scope(
        target_scope,
        field="target_scope",
        configs=configs,
    )
    if normalized_target_scope == normalized_source_scope:
        raise ValueError("target_scope must differ from source_scope")

    normalized_source_doc_id = str(source_doc_id or "").strip()
    if not normalized_source_doc_id:
        raise ValueError("source_doc_id is required")

    source_config = configs[normalized_source_scope]
    target_config = configs[normalized_target_scope]
    require_copy_source_root(repo_root, source_config, require_writable=False)
    target_root = require_copy_source_root(repo_root, target_config, require_writable=True)

    source_docs = source_model.load_scope_docs_for_config(repo_root, source_config)
    try:
        ordered_source_docs = source_model.subtree_docs_in_tree_order(
            source_docs,
            normalized_source_doc_id,
        )
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"doc {normalized_source_doc_id!r} not found in scope {normalized_source_scope}"
        ) from exc
    target_docs = source_model.load_scope_docs_for_config(repo_root, target_config)

    timestamp = str(copy_timestamp or source_model.current_doc_timestamp()).strip()
    if not source_model.is_doc_timestamp(timestamp):
        raise ValueError("copy_timestamp must use YYYY-MM-DD HH:MM:SS")
    id_map = _allocate_target_identities(
        ordered_source_docs,
        target_docs,
        copy_timestamp=timestamp,
        target_root=target_root,
        token_factory=token_factory,
    )
    documents = _planned_documents(
        ordered_source_docs,
        id_map=id_map,
        target_root=target_root,
    )
    return CopySubtreePlan(
        source_scope=normalized_source_scope,
        target_scope=normalized_target_scope,
        source_config=source_config,
        target_config=target_config,
        copy_timestamp=timestamp,
        documents=documents,
    )


def restore_copy_subtree_apply_plan(
    repo_root: Path,
    payload: Any,
) -> CopySubtreePlan:
    """Restore one previewed plan from its bounded apply receipt."""

    if not isinstance(payload, dict):
        raise ValueError("copy subtree apply_plan is required")
    if _receipt_text(payload, "schema_version") != COPY_SUBTREE_APPLY_PLAN_SCHEMA_VERSION:
        raise ValueError("copy subtree apply_plan schema_version is invalid")

    configs = load_docs_scope_configs(repo_root)
    source_scope = _normalize_configured_scope(
        payload.get("source_scope"),
        field="source_scope",
        configs=configs,
    )
    target_scope = _normalize_configured_scope(
        payload.get("target_scope"),
        field="target_scope",
        configs=configs,
    )
    if source_scope == target_scope:
        raise _stale_receipt("target scope matches source scope")
    source_doc_id = _receipt_text(payload, "source_doc_id")
    if not source_doc_id:
        raise ValueError("copy subtree apply_plan source_doc_id is required")
    copy_timestamp = _receipt_text(payload, "copy_timestamp")
    if not source_model.is_doc_timestamp(copy_timestamp):
        raise ValueError("copy subtree apply_plan copy_timestamp is invalid")

    source_config = configs[source_scope]
    target_config = configs[target_scope]
    if _receipt_text(payload, "source_config_sha256") != _scope_config_sha256(source_config):
        raise _stale_receipt(f"source scope {source_scope!r} configuration changed")
    if _receipt_text(payload, "target_config_sha256") != _scope_config_sha256(target_config):
        raise _stale_receipt(f"target scope {target_scope!r} configuration changed")

    require_copy_source_root(repo_root, source_config, require_writable=False)
    target_root = require_copy_source_root(repo_root, target_config, require_writable=True)
    source_docs = source_model.load_scope_docs_for_config(repo_root, source_config)
    try:
        ordered_source_docs = source_model.subtree_docs_in_tree_order(
            source_docs,
            source_doc_id,
        )
    except FileNotFoundError as exc:
        raise _stale_receipt(f"source document {source_doc_id!r} is unavailable") from exc
    target_docs = source_model.load_scope_docs_for_config(repo_root, target_config)

    receipt_documents = payload.get("documents")
    if not isinstance(receipt_documents, list) or not receipt_documents:
        raise ValueError("copy subtree apply_plan documents are required")
    if len(receipt_documents) != len(ordered_source_docs):
        raise _stale_receipt("source subtree membership or order changed")

    unavailable = {
        identity.lower()
        for doc in [*source_docs, *target_docs]
        for identity in (doc.doc_id, doc.path.stem)
        if identity
    }
    id_map: dict[str, str] = {}
    planned_target_ids: set[str] = set()
    for receipt_document, source_doc in zip(receipt_documents, ordered_source_docs):
        if not isinstance(receipt_document, dict):
            raise ValueError("copy subtree apply_plan document records must be objects")
        receipt_source_doc_id = _receipt_text(receipt_document, "source_doc_id")
        if receipt_source_doc_id != source_doc.doc_id:
            raise _stale_receipt("source subtree membership or order changed")
        if _receipt_text(receipt_document, "source_sha256") != _source_sha256(source_doc.source_text):
            raise _stale_receipt(f"source content changed for {source_doc.doc_id!r}")
        target_doc_id = _receipt_text(receipt_document, "target_doc_id")
        if not source_model.is_immutable_doc_id(target_doc_id):
            raise ValueError(f"copy subtree apply_plan target identity {target_doc_id!r} is invalid")
        if not source_model.doc_id_matches_added_date(target_doc_id, copy_timestamp):
            raise ValueError(
                f"copy subtree apply_plan target identity {target_doc_id!r} does not match the copy timestamp"
            )
        normalized_target_doc_id = target_doc_id.lower()
        if normalized_target_doc_id in unavailable or normalized_target_doc_id in planned_target_ids:
            raise _stale_receipt(f"target identity {target_doc_id!r} is no longer available")
        target_path = target_root / f"{target_doc_id}.md"
        if target_path.exists():
            raise _stale_receipt(f"target path for {target_doc_id!r} is no longer available")
        id_map[source_doc.doc_id] = target_doc_id
        planned_target_ids.add(normalized_target_doc_id)

    return CopySubtreePlan(
        source_scope=source_scope,
        target_scope=target_scope,
        source_config=source_config,
        target_config=target_config,
        copy_timestamp=copy_timestamp,
        documents=_planned_documents(
            ordered_source_docs,
            id_map=id_map,
            target_root=target_root,
        ),
    )


__all__ = [
    "COPY_SUBTREE_APPLY_PLAN_SCHEMA_VERSION",
    "COPY_SUBTREE_PREVIEW_SCHEMA_VERSION",
    "CopySubtreeDocumentPlan",
    "CopySubtreePlan",
    "CopySubtreeSourceTransform",
    "CopySubtreeTransformation",
    "plan_copy_subtree",
    "require_copy_source_root",
    "restore_copy_subtree_apply_plan",
    "rewrite_copied_viewer_links",
    "transform_copy_subtree",
]
