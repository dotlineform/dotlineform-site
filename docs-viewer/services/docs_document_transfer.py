#!/usr/bin/env python3
"""Write-free planning for multi-document Copy and Move transfers."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qs, urlsplit

import docs_source_model as source_model
import docs_document_publication_lineage as publication_lineage
import docs_media_source_evidence as media_source_evidence
from docs_artifact_locations import (
    DELETE_CAPABILITY,
    READ_CAPABILITY,
    STAT_CAPABILITY,
    VERIFY_BYTES_CAPABILITY,
    WRITE_CAPABILITY,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
)
from docs_media_inventory import (
    MEDIA_REFERENCE_PATTERN,
    DocsMediaReference,
    document_media_references,
    source_media_references,
)
from docs_scope_config import (
    PUBLIC_SCOPE_TYPE,
    DocsScopeConfig,
)
from docs_management_document_target import (
    ManagedDocumentCollection,
    resolve_managed_document_collection,
)
from docs_subscope_customisations import (
    LINEAGE_EDITORIAL_ROLE,
    LINEAGE_SOURCE_ROLE,
    sub_scope_customisation_document_lineage_contract,
    sub_scope_customisation_transfer_contract,
)


TRANSFER_PREVIEW_SCHEMA_VERSION = "docs_document_transfer_preview_v4"
TRANSFER_APPLY_PLAN_SCHEMA_VERSION = "docs_document_transfer_apply_plan_v4"
COPY_MODE = "copy"
MOVE_MODE = "move"
SUPPORTED_TRANSFER_MODES = frozenset({COPY_MODE, MOVE_MODE})
COPY_ACTION_NEW = "new"
COPY_ACTION_REPLACE = "replace"
SUPPORTED_COPY_ACTIONS = frozenset({COPY_ACTION_NEW, COPY_ACTION_REPLACE})
MEDIA_SOURCE_EVIDENCE_COPY = "copy"
MEDIA_SOURCE_EVIDENCE_RETAIN = "retain"
MEDIA_SOURCE_EVIDENCE_UNRECORDED = "unrecorded"
IdentityTokenFactory = Callable[[int], str]
BuildSourceIdentityResolver = Callable[[str], str]

ROOT_RELATIVE_VIEWER_URL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9:/])/(?:[A-Za-z0-9._~%-]+/)*\?[^\s)>'\"<]+"
)
MARKDOWN_EXTERNAL_MEDIA_PATTERN = re.compile(
    r"!\[[^\]]*\]\(\s*(?P<url>https?://[^\s)]+)",
    re.IGNORECASE,
)
HTML_EXTERNAL_MEDIA_PATTERN = re.compile(
    r"<(?:img|source|video|audio)\b[^>]*\b(?:src|poster)\s*=\s*[\"']"
    r"(?P<url>https?://[^\"']+)",
    re.IGNORECASE,
)


def _mermaid_source_identity(published_identity: str) -> str:
    if Path(published_identity).suffix.lower() != ".svg":
        raise ValueError(
            f"Mermaid build output {published_identity!r} must use the .svg suffix"
        )
    return Path(published_identity).with_suffix(".mmd").as_posix()


REGISTERED_BUILD_SOURCE_IDENTITY_RESOLVERS: dict[
    str,
    BuildSourceIdentityResolver,
] = {
    "mermaid": _mermaid_source_identity,
}


@dataclass(frozen=True)
class TransferBlocker:
    code: str
    message: str
    media_type: str = ""
    identity: str = ""
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransferWarning:
    code: str
    message: str
    document_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransferCustomMetadataDecision:
    source_doc_id: str
    field_name: str
    source_customisation: str
    target_customisation: str
    contract_id: str
    status: str
    reason: str


@dataclass(frozen=True)
class TransferLinkDecision:
    source_doc_id: str
    referenced_doc_id: str
    target_doc_id: str
    status: str
    occurrence_count: int


@dataclass(frozen=True)
class RetainedExternalDependency:
    kind: str
    reference: str
    document_ids: tuple[str, ...]


@dataclass(frozen=True)
class TransferBuildSourcePlan:
    build_type: str
    producer: str
    publishes_to: str
    source_identity: str
    source_provider: str
    target_provider: str
    source_size: int
    source_sha256: str
    target_status: str


@dataclass(frozen=True)
class TransferMediaSourceEvidencePlan:
    status: str
    source_root: str = ""
    source_path: str = ""


@dataclass(frozen=True)
class TransferMediaPlan:
    media_type: str
    identity: str
    source_provider: str
    target_provider: str
    source_reference: str
    target_reference: str
    source_size: int
    source_sha256: str
    target_status: str
    document_ids: tuple[str, ...]
    shared_outside_document_ids: tuple[str, ...]
    build_sources: tuple[TransferBuildSourcePlan, ...]
    source_evidence: TransferMediaSourceEvidencePlan | None


@dataclass(frozen=True)
class TransferLineageEditorialChoice:
    editorial_doc_id: str
    title: str
    available: bool


@dataclass(frozen=True)
class TransferLineageDecision:
    source_doc_id: str
    source_title: str
    action: str
    replace_target_doc_id: str
    existing_editorials: tuple[TransferLineageEditorialChoice, ...]


@dataclass(frozen=True)
class DocumentLineageTransferPlan:
    contract_id: str
    decisions: tuple[TransferLineageDecision, ...]


@dataclass(frozen=True)
class TransferDocumentPlan:
    source_doc: source_model.ScopeDoc
    target_doc_id: str
    target_parent_id: str
    target_path: Path
    requested: bool
    effective_root: bool
    copy_action: str
    replacement_doc: source_model.ScopeDoc | None


@dataclass(frozen=True)
class DocumentTransferPlan:
    mode: str
    source_collection: ManagedDocumentCollection
    target_collection: ManagedDocumentCollection
    operation_timestamp: str
    include_descendants: bool
    descendants_forced: bool
    requested_doc_ids: tuple[str, ...]
    documents: tuple[TransferDocumentPlan, ...]
    media: tuple[TransferMediaPlan, ...]
    custom_metadata: tuple[TransferCustomMetadataDecision, ...]
    link_decisions: tuple[TransferLinkDecision, ...]
    retained_external_dependencies: tuple[RetainedExternalDependency, ...]
    lineage: DocumentLineageTransferPlan | None
    blockers: tuple[TransferBlocker, ...]
    warnings: tuple[TransferWarning, ...]

    @property
    def source_scope(self) -> str:
        return self.source_collection.scope

    @property
    def source_sub_scope(self) -> str:
        return self.source_collection.sub_scope

    @property
    def target_scope(self) -> str:
        return self.target_collection.scope

    @property
    def target_sub_scope(self) -> str:
        return self.target_collection.sub_scope

    @property
    def source_config(self) -> DocsScopeConfig:
        return self.source_collection.parent_config

    @property
    def target_config(self) -> DocsScopeConfig:
        return self.target_collection.parent_config

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def descendant_count(self) -> int:
        return len(self.documents) - len(self.requested_doc_ids)

    @property
    def effective_root_count(self) -> int:
        return sum(document.effective_root for document in self.documents)

    @property
    def id_map(self) -> dict[str, str]:
        return {
            document.source_doc.doc_id: document.target_doc_id
            for document in self.documents
        }

    def preview_payload(self) -> dict[str, Any]:
        source = self.source_collection.request_target()
        target = {
            **self.target_collection.request_target(),
            "placement": (
                "sub_scope_root" if self.target_sub_scope else "scope_root"
            ),
        }
        payload = {
            "schema_version": TRANSFER_PREVIEW_SCHEMA_VERSION,
            "ok": self.ok,
            "mode": self.mode,
            "include_descendants": self.include_descendants,
            "descendants_forced": self.descendants_forced,
            "source": source,
            "target": target,
            "requested_count": len(self.requested_doc_ids),
            "effective_root_count": self.effective_root_count,
            "descendant_count": self.descendant_count,
            "document_count": len(self.documents),
            "unique_media_count": len(self.media),
            "retained_external_count": len(self.retained_external_dependencies),
            "documents": [
                {
                    "source_doc_id": document.source_doc.doc_id,
                    "title": document.source_doc.title,
                    "target_doc_id": document.target_doc_id,
                    "target_parent_id": document.target_parent_id,
                    "requested": document.requested,
                    "effective_root": document.effective_root,
                    "copy_action": document.copy_action,
                }
                for document in self.documents
            ],
            "media": [_media_payload(item) for item in self.media],
            "custom_metadata": {
                status: [
                    asdict(item)
                    for item in self.custom_metadata
                    if item.status == status
                ]
                for status in ("retained", "omitted", "rejected")
            },
            "link_decisions": [asdict(item) for item in self.link_decisions],
            "retained_external_dependencies": [
                asdict(dependency)
                for dependency in self.retained_external_dependencies
            ],
            "lineage": _lineage_preview_payload(self.lineage),
            "blockers": [asdict(blocker) for blocker in self.blockers],
            "warnings": [asdict(warning) for warning in self.warnings],
            "apply_plan": self.apply_plan_payload() if self.ok else None,
        }
        if source_model.collection_supports_publishable(
            self.target_collection.document_config
        ):
            payload["target_default_publishable"] = True
        return payload

    def apply_plan_payload(self) -> dict[str, Any]:
        if not self.ok:
            raise ValueError("blocked document transfer has no apply plan")
        payload = {
            "schema_version": TRANSFER_APPLY_PLAN_SCHEMA_VERSION,
            "mode": self.mode,
            "source": self.source_collection.request_target(),
            "target": self.target_collection.request_target(),
            "operation_timestamp": self.operation_timestamp,
            "include_descendants": self.include_descendants,
            "requested_doc_ids": list(self.requested_doc_ids),
            "source_parent_config_sha256": _config_sha256(self.source_config),
            "source_collection_config_sha256": _config_sha256(
                self.source_collection.document_config
            ),
            "target_parent_config_sha256": _config_sha256(self.target_config),
            "target_collection_config_sha256": _config_sha256(
                self.target_collection.document_config
            ),
            "media_owners": {
                "source": {"scope": self.source_scope},
                "target": {"scope": self.target_scope},
            },
            "target_rebuild_owner": self.target_collection.request_target(),
            "documents": [
                {
                    "source_doc_id": document.source_doc.doc_id,
                    "source_sha256": _source_sha256(document.source_doc.source_text),
                    "target_doc_id": document.target_doc_id,
                    "target_parent_id": document.target_parent_id,
                    "copy_action": document.copy_action,
                }
                for document in self.documents
            ],
            "media": [
                {
                    "media_type": item.media_type,
                    "identity": item.identity,
                    "source_sha256": item.source_sha256,
                    "target_status": item.target_status,
                    "shared_outside_document_ids": list(item.shared_outside_document_ids),
                    "source_evidence": (
                        asdict(item.source_evidence)
                        if item.source_evidence is not None
                        else None
                    ),
                    "build_sources": [
                        {
                            "build_type": build.build_type,
                            "source_identity": build.source_identity,
                            "source_sha256": build.source_sha256,
                            "target_status": build.target_status,
                        }
                        for build in item.build_sources
                    ],
                }
                for item in self.media
            ],
            "custom_metadata": [
                asdict(item)
                for item in self.custom_metadata
            ],
            "link_decisions": [
                asdict(item)
                for item in self.link_decisions
            ],
            "lineage": _lineage_apply_payload(self.lineage),
        }
        if source_model.collection_supports_publishable(
            self.target_collection.document_config
        ):
            payload["target_default_publishable"] = True
        return payload


def _lineage_preview_payload(
    lineage: DocumentLineageTransferPlan | None,
) -> dict[str, Any] | None:
    if lineage is None:
        return None
    return {
        "contract_id": lineage.contract_id,
        "choice_required": any(not decision.action for decision in lineage.decisions),
        "sources": [
            {
                "source_doc_id": decision.source_doc_id,
                "title": decision.source_title,
                "action": decision.action,
                "replace_target_doc_id": decision.replace_target_doc_id,
                "existing_editorials": [asdict(choice) for choice in decision.existing_editorials],
            }
            for decision in lineage.decisions
        ],
    }


def _lineage_apply_payload(
    lineage: DocumentLineageTransferPlan | None,
) -> dict[str, Any] | None:
    if lineage is None:
        return None
    return {
        "contract_id": lineage.contract_id,
        "decisions": [
            {
                "source_doc_id": decision.source_doc_id,
                "action": decision.action,
                "replace_target_doc_id": decision.replace_target_doc_id,
            }
            for decision in lineage.decisions
        ],
    }


def _media_payload(item: TransferMediaPlan) -> dict[str, Any]:
    payload = asdict(item)
    payload["build_sources"] = [asdict(build) for build in item.build_sources]
    return payload


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


def _config_sha256(config: Any) -> str:
    serialized = json.dumps(
        _jsonable_receipt_value(config),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _source_sha256(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_scope(value: Any, *, field: str) -> str:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError(f"{field} is required")
    return scope


def _normalize_mode(value: Any) -> str:
    mode = str(value or "").strip().lower()
    if mode not in SUPPORTED_TRANSFER_MODES:
        raise ValueError("transfer_mode must be copy or move")
    return mode


def _normalize_requested_doc_ids(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("requested_doc_ids must be an array")
    requested: list[str] = []
    seen: set[str] = set()
    for item in value:
        doc_id = str(item or "").strip()
        if not doc_id:
            raise ValueError("requested_doc_ids must not contain empty values")
        if doc_id in seen:
            continue
        seen.add(doc_id)
        requested.append(doc_id)
    if not requested:
        raise ValueError("requested_doc_ids must contain at least one document")
    return tuple(requested)


def _receipt_text(payload: Mapping[str, Any], key: str) -> str:
    return str(payload.get(key) or "").strip()


def _stale_receipt(message: str) -> ValueError:
    return ValueError(f"document transfer preview is stale: {message}")


def _require_collection_root(
    collection: ManagedDocumentCollection,
    *,
    role: str,
    writable: bool,
    mode: str,
) -> Path:
    if (
        writable
        and collection.parent_config.scope_type == PUBLIC_SCOPE_TYPE
        and mode != COPY_MODE
    ):
        raise ValueError(f"public {role} scope {collection.scope!r} is not writable")
    root = collection.source_root
    label = (
        f"{collection.scope}/{collection.sub_scope}"
        if collection.sub_scope
        else collection.scope
    )
    if not root.exists() or not root.is_dir():
        raise ValueError(f"{role} document root for collection {label!r} is unavailable")
    if not os.access(root, os.R_OK | os.X_OK):
        raise ValueError(f"{role} document root for collection {label!r} is unavailable")
    if writable and not os.access(root, os.W_OK | os.X_OK):
        raise ValueError(f"{role} collection {label!r} cannot accept canonical writes")
    return root


def document_transfer_collection_capabilities(
    collection: ManagedDocumentCollection,
) -> dict[str, bool]:
    """Report operation eligibility for one exact configured collection."""

    def available(*, role: str, writable: bool, mode: str) -> bool:
        try:
            _require_collection_root(
                collection,
                role=role,
                writable=writable,
                mode=mode,
            )
        except (OSError, ValueError):
            return False
        return True

    return {
        "copy_source": available(
            role="source",
            writable=False,
            mode=COPY_MODE,
        ),
        "move_source": (
            not collection.sub_scope
            and available(role="source", writable=True, mode=MOVE_MODE)
        ),
        "copy_target": available(
            role="target",
            writable=True,
            mode=COPY_MODE,
        ),
        "move_target": (
            not collection.sub_scope
            and available(role="target", writable=True, mode=MOVE_MODE)
        ),
    }


def document_transfer_scope_capabilities(
    repo_root: Path,
    config: DocsScopeConfig,
) -> dict[str, bool]:
    """Report mode-aware source and target eligibility through planner rules."""
    try:
        collection = resolve_managed_document_collection(
            repo_root,
            scope=config.scope_id,
        )
    except (OSError, ValueError):
        return {
            "copy_source": False,
            "move_source": False,
            "target": False,
        }
    capabilities = document_transfer_collection_capabilities(collection)
    return {
        "copy_source": capabilities["copy_source"],
        "move_source": capabilities["move_source"],
        "target": capabilities["copy_target"] or capabilities["move_target"],
    }


def document_transfer_collection_capability_records(
    repo_root: Path,
    config: DocsScopeConfig,
) -> list[dict[str, Any]]:
    """Project server-owned eligibility for every configured exact collection."""

    records: list[dict[str, Any]] = []
    configured = [("", config.scope_id)] + [
        (sub_scope.sub_scope, f"{config.scope_id} / {sub_scope.title}")
        for sub_scope in config.sub_scopes
    ]
    for sub_scope, label in configured:
        target = {"scope": config.scope_id}
        if sub_scope:
            target["sub_scope"] = sub_scope
        try:
            collection = resolve_managed_document_collection(
                repo_root,
                scope=config.scope_id,
                sub_scope=sub_scope or None,
            )
            capabilities = document_transfer_collection_capabilities(collection)
        except (OSError, ValueError):
            capabilities = {
                "copy_source": False,
                "move_source": False,
                "copy_target": False,
                "move_target": False,
            }
        records.append(
            {
                "target": target,
                "label": label,
                **capabilities,
            }
        )
    return records


def _effective_documents(
    docs: list[source_model.ScopeDoc],
    requested_doc_ids: tuple[str, ...],
    *,
    include_descendants: bool,
) -> tuple[list[source_model.ScopeDoc], tuple[str, ...]]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    missing = sorted(set(requested_doc_ids) - set(docs_by_id))
    if missing:
        raise FileNotFoundError(f"documents not found in source scope: {', '.join(missing)}")

    effective_ids = set(requested_doc_ids)
    if include_descendants:
        for doc_id in requested_doc_ids:
            effective_ids.update(source_model.descendant_doc_ids(docs, doc_id))

    children_by_parent: dict[str, list[source_model.ScopeDoc]] = {}
    for doc in docs:
        children_by_parent.setdefault(doc.parent_id, []).append(doc)
    for children in children_by_parent.values():
        children.sort(key=source_model.scope_doc_sort_key)

    roots = sorted(
        (
            docs_by_id[doc_id]
            for doc_id in effective_ids
            if docs_by_id[doc_id].parent_id not in effective_ids
        ),
        key=source_model.scope_doc_sort_key,
    )
    ordered: list[source_model.ScopeDoc] = []

    def append_selected(doc: source_model.ScopeDoc) -> None:
        ordered.append(doc)
        for child in children_by_parent.get(doc.doc_id, ()):
            if child.doc_id in effective_ids:
                append_selected(child)

    for root in roots:
        append_selected(root)

    requested_ids = set(requested_doc_ids)
    ordered_requested = tuple(doc.doc_id for doc in ordered if doc.doc_id in requested_ids)
    return ordered, ordered_requested


def _allocate_copy_ids(
    source_docs: list[source_model.ScopeDoc],
    target_docs: list[source_model.ScopeDoc],
    *,
    timestamp: str,
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
            timestamp,
            unavailable,
            **allocation_kwargs,
        )
        if (target_root / f"{target_doc_id}.md").exists():
            raise ValueError(f"planned target path already exists for {target_doc_id!r}")
        unavailable.add(target_doc_id.lower())
        id_map[source_doc.doc_id] = target_doc_id
    return id_map


def _planned_documents(
    source_docs: list[source_model.ScopeDoc],
    requested_doc_ids: tuple[str, ...],
    target_docs: list[source_model.ScopeDoc],
    *,
    mode: str,
    timestamp: str,
    target_root: Path,
    token_factory: IdentityTokenFactory | None,
    lineage: DocumentLineageTransferPlan | None,
    blockers: list[TransferBlocker],
) -> tuple[TransferDocumentPlan, ...]:
    source_ids = {doc.doc_id for doc in source_docs}
    requested_ids = set(requested_doc_ids)
    if mode == COPY_MODE:
        decisions = {
            decision.source_doc_id: decision
            for decision in lineage.decisions
        } if lineage is not None else {}
        new_docs = [
            source_doc
            for source_doc in source_docs
            if lineage is None
            or decisions[source_doc.doc_id].action == COPY_ACTION_NEW
        ]
        id_map = _allocate_copy_ids(
            new_docs,
            target_docs,
            timestamp=timestamp,
            target_root=target_root,
            token_factory=token_factory,
        )
        replacement_docs: dict[str, source_model.ScopeDoc] = {}
        target_docs_by_id = {document.doc_id: document for document in target_docs}
        if lineage is not None:
            for source_doc in source_docs:
                decision = decisions[source_doc.doc_id]
                if decision.action == COPY_ACTION_REPLACE:
                    replacement = target_docs_by_id[decision.replace_target_doc_id]
                    id_map[source_doc.doc_id] = replacement.doc_id
                    replacement_docs[source_doc.doc_id] = replacement
                elif not decision.action:
                    id_map[source_doc.doc_id] = ""
    else:
        id_map = {doc.doc_id: doc.doc_id for doc in source_docs}
        replacement_docs = {}
        target_ids = {doc.doc_id for doc in target_docs}
        for source_doc in source_docs:
            if source_doc.doc_id in target_ids or (target_root / f"{source_doc.doc_id}.md").exists():
                blockers.append(
                    TransferBlocker(
                        code="target_document_collision",
                        message=(
                            f"target scope already contains document identity "
                            f"{source_doc.doc_id!r}"
                        ),
                        document_ids=(source_doc.doc_id,),
                    )
                )

    return tuple(
        TransferDocumentPlan(
            source_doc=source_doc,
            target_doc_id=id_map[source_doc.doc_id],
            target_parent_id=(
                replacement_docs[source_doc.doc_id].parent_id
                if source_doc.doc_id in replacement_docs
                else (
                    id_map[source_doc.parent_id]
                    if source_doc.parent_id in source_ids
                    else ""
                )
            ),
            target_path=(
                replacement_docs[source_doc.doc_id].path
                if source_doc.doc_id in replacement_docs
                else target_root / f"{id_map[source_doc.doc_id]}.md"
            ),
            requested=source_doc.doc_id in requested_ids,
            effective_root=source_doc.parent_id not in source_ids,
            copy_action=(
                decisions[source_doc.doc_id].action
                if lineage is not None
                else COPY_ACTION_NEW if mode == COPY_MODE else ""
            ),
            replacement_doc=replacement_docs.get(source_doc.doc_id),
        )
        for source_doc in source_docs
    )


def published_transfer_adapters(
    repo_root: Path,
    config: DocsScopeConfig,
    media_types: Iterable[str],
    *,
    client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, ArtifactLocationAdapter]:
    selected = {
        media_type: config.media.types[media_type]
        for media_type in sorted(set(media_types))
        if media_type in config.media.types
    }
    remote_client = authenticated_remote_client_for_locations(
        repo_root,
        [media.location for media in selected.values()],
        client=client,  # type: ignore[arg-type]
        env_files=env_files,
        environ=environ,
    )
    return {
        media_type: artifact_location_adapter(
            repo_root,
            media.location,
            served_path_prefix=media.served_path_prefix,
            remote_client=remote_client,
        )
        for media_type, media in selected.items()
    }


def transfer_build_source_adapter(
    repo_root: Path,
    config: DocsScopeConfig,
    build_type: str,
) -> ArtifactLocationAdapter:
    build = config.media.build_sources[build_type]
    return artifact_location_adapter(
        repo_root,
        build.location,
    )


def _build_source_identity(
    *,
    build_type: str,
    producer: str,
    published_identity: str,
) -> str:
    resolver = REGISTERED_BUILD_SOURCE_IDENTITY_RESOLVERS.get(producer)
    if resolver is None:
        raise ValueError(
            f"build media {build_type!r} uses unsupported producer {producer!r}"
        )
    return resolver(published_identity)


def _target_artifact_status(
    adapter: ArtifactLocationAdapter,
    identity: str,
    source_bytes: bytes,
) -> str:
    if adapter.stat(identity) is None:
        return "create"
    return "reuse" if adapter.read(identity) == source_bytes else "collision"


def _retained_dependencies(
    config: DocsScopeConfig,
    documents: Iterable[source_model.ScopeDoc],
    blockers: list[TransferBlocker],
) -> tuple[RetainedExternalDependency, ...]:
    references: dict[tuple[str, str], set[str]] = {}
    for doc in documents:
        for match in MEDIA_REFERENCE_PATTERN.finditer(doc.source_text):
            reference = match.group("path").lstrip("/")
            if reference.lower().startswith(("http://", "https://")):
                references.setdefault(("external_url", reference), set()).add(doc.doc_id)
                continue
            parts = Path(reference).parts
            if len(parts) < 4 or parts[0] != "docs":
                continue
            if parts[1] != config.scope_id:
                references.setdefault(("other_scope_media", reference), set()).add(doc.doc_id)
                continue
            if parts[2] not in config.media.types:
                blockers.append(
                    TransferBlocker(
                        code="unsupported_source_media_role",
                        message=(
                            f"source media role {parts[2]!r} is not configured "
                            f"for scope {config.scope_id!r}"
                        ),
                        media_type=parts[2],
                        identity=Path(*parts[3:]).as_posix(),
                        document_ids=(doc.doc_id,),
                    )
                )
        for pattern in (MARKDOWN_EXTERNAL_MEDIA_PATTERN, HTML_EXTERNAL_MEDIA_PATTERN):
            for match in pattern.finditer(doc.source_text):
                reference = match.group("url").rstrip(".,;:")
                references.setdefault(("external_url", reference), set()).add(doc.doc_id)
    return tuple(
        RetainedExternalDependency(
            kind=kind,
            reference=reference,
            document_ids=tuple(sorted(doc_ids)),
        )
        for (kind, reference), doc_ids in sorted(references.items())
    )


def _build_source_plan(
    repo_root: Path,
    source_config: DocsScopeConfig,
    target_config: DocsScopeConfig,
    *,
    media_type: str,
    published_identity: str,
    build_type: str,
    mode: str,
    blockers: list[TransferBlocker],
) -> TransferBuildSourcePlan | None:
    source_build = source_config.media.build_sources[build_type]
    target_build = target_config.media.build_sources.get(build_type)
    source_identity = ""
    try:
        source_identity = _build_source_identity(
            build_type=build_type,
            producer=source_build.producer,
            published_identity=published_identity,
        )
    except ValueError as exc:
        blockers.append(
            TransferBlocker(
                code="unsupported_source_media_build",
                message=str(exc),
                media_type=media_type,
                identity=published_identity,
            )
        )
        return None

    if (
        target_build is None
        or target_build.producer != source_build.producer
        or target_build.publishes_to != media_type
    ):
        blockers.append(
            TransferBlocker(
                code="unsupported_target_media_build",
                message=(
                    f"target scope does not support {build_type!r} "
                    f"{source_build.producer!r} sources for {media_type!r}"
                ),
                media_type=media_type,
                identity=published_identity,
            )
        )
        return None

    source_adapter = transfer_build_source_adapter(
        repo_root,
        source_config,
        build_type,
    )
    target_adapter = transfer_build_source_adapter(
        repo_root,
        target_config,
        build_type,
    )
    try:
        source_adapter.require(
            READ_CAPABILITY,
            STAT_CAPABILITY,
            *([DELETE_CAPABILITY] if mode == MOVE_MODE else []),
            role=f"{source_config.scope_id}/{build_type} build source",
        )
        target_adapter.require(
            READ_CAPABILITY,
            STAT_CAPABILITY,
            WRITE_CAPABILITY,
            VERIFY_BYTES_CAPABILITY,
            role=f"{target_config.scope_id}/{build_type} build source",
        )
        if source_adapter.stat(source_identity) is None:
            raise FileNotFoundError(f"build source does not exist: {source_identity}")
        source_bytes = source_adapter.read(source_identity)
        target_status = _target_artifact_status(
            target_adapter,
            source_identity,
            source_bytes,
        )
    except Exception as exc:
        blockers.append(
            TransferBlocker(
                code="build_source_unavailable",
                message=(
                    f"build source {build_type}/{source_identity or published_identity} "
                    f"could not be planned: {exc}"
                ),
                media_type=media_type,
                identity=published_identity,
            )
        )
        return None

    if target_status == "collision":
        blockers.append(
            TransferBlocker(
                code="target_build_source_collision",
                message=(
                    f"target build source {build_type}/{source_identity} "
                    "has different bytes"
                ),
                media_type=media_type,
                identity=published_identity,
            )
        )
    return TransferBuildSourcePlan(
        build_type=build_type,
        producer=source_build.producer,
        publishes_to=source_build.publishes_to,
        source_identity=source_identity,
        source_provider=source_adapter.location.provider,
        target_provider=target_adapter.location.provider,
        source_size=len(source_bytes),
        source_sha256=_bytes_sha256(source_bytes),
        target_status=target_status,
    )


def _media_source_evidence_plans(
    repo_root: Path,
    source_config: DocsScopeConfig,
    target_config: DocsScopeConfig,
    identities: Iterable[tuple[str, str]],
    *,
    mode: str,
) -> dict[tuple[str, str], TransferMediaSourceEvidencePlan]:
    if mode != COPY_MODE:
        return {}
    source_records = {
        (record.media_type, record.identity): record
        for record in media_source_evidence.load_media_source_evidence(
            repo_root,
            source_config.scope_id,
        )
    }
    target_records = {
        (record.media_type, record.identity): record
        for record in media_source_evidence.load_media_source_evidence(
            repo_root,
            target_config.scope_id,
        )
    }
    plans: dict[tuple[str, str], TransferMediaSourceEvidencePlan] = {}
    for key in sorted(set(identities)):
        record = target_records.get(key)
        if record is not None:
            plans[key] = TransferMediaSourceEvidencePlan(
                status=MEDIA_SOURCE_EVIDENCE_RETAIN,
                source_root=record.source_root,
                source_path=record.source_path,
            )
            continue
        record = source_records.get(key)
        if record is not None:
            plans[key] = TransferMediaSourceEvidencePlan(
                status=MEDIA_SOURCE_EVIDENCE_COPY,
                source_root=record.source_root,
                source_path=record.source_path,
            )
            continue
        plans[key] = TransferMediaSourceEvidencePlan(
            status=MEDIA_SOURCE_EVIDENCE_UNRECORDED,
        )
    return plans


def _media_plans(
    repo_root: Path,
    source_config: DocsScopeConfig,
    target_config: DocsScopeConfig,
    documents: list[source_model.ScopeDoc],
    *,
    mode: str,
    blockers: list[TransferBlocker],
    source_media_client: object | None,
    target_media_client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> tuple[TransferMediaPlan, ...]:
    references_by_identity: dict[tuple[str, str], list[DocsMediaReference]] = {}
    for doc in documents:
        for reference in source_media_references(
            source_config,
            doc.source_text,
            doc_id=doc.doc_id,
        ):
            references_by_identity.setdefault(
                (reference.media_type, reference.identity),
                [],
            ).append(reference)
    if not references_by_identity:
        return ()

    source_evidence_plans = _media_source_evidence_plans(
        repo_root,
        source_config,
        target_config,
        references_by_identity,
        mode=mode,
    )

    media_types = {media_type for media_type, _identity in references_by_identity}
    try:
        source_adapters = published_transfer_adapters(
            repo_root,
            source_config,
            media_types,
            client=source_media_client,
            env_files=env_files,
            environ=environ,
        )
    except Exception as exc:
        blockers.append(
            TransferBlocker(
                code="source_media_provider_unavailable",
                message=f"source media provider could not be opened: {exc}",
            )
        )
        source_adapters = {}
    try:
        target_adapters = published_transfer_adapters(
            repo_root,
            target_config,
            media_types,
            client=target_media_client,
            env_files=env_files,
            environ=environ,
        )
    except Exception as exc:
        blockers.append(
            TransferBlocker(
                code="target_media_provider_unavailable",
                message=f"target media provider could not be opened: {exc}",
            )
        )
        target_adapters = {}

    outside_references: dict[tuple[str, str], set[str]] = {}
    if mode == MOVE_MODE:
        effective_ids = {doc.doc_id for doc in documents}
        for reference in document_media_references(repo_root, source_config):
            if reference.doc_id not in effective_ids:
                outside_references.setdefault(
                    (reference.media_type, reference.identity),
                    set(),
                ).add(reference.doc_id)

    plans: list[TransferMediaPlan] = []
    for (media_type, identity), references in sorted(references_by_identity.items()):
        document_ids = tuple(sorted({reference.doc_id for reference in references}))
        source_media = source_config.media.types[media_type]
        target_media = target_config.media.types.get(media_type)
        source_adapter = source_adapters.get(media_type)
        target_adapter = target_adapters.get(media_type)
        source_bytes = b""
        source_available = False
        target_status = "blocked"

        if target_media is None:
            blockers.append(
                TransferBlocker(
                    code="unsupported_target_media_role",
                    message=f"target scope has no {media_type!r} media role",
                    media_type=media_type,
                    identity=identity,
                    document_ids=document_ids,
                )
            )
        if source_adapter is None:
            blockers.append(
                TransferBlocker(
                    code="source_media_unavailable",
                    message=f"source media adapter is unavailable for {media_type}/{identity}",
                    media_type=media_type,
                    identity=identity,
                    document_ids=document_ids,
                )
            )
        else:
            try:
                source_adapter.require(
                    READ_CAPABILITY,
                    STAT_CAPABILITY,
                    *([DELETE_CAPABILITY] if mode == MOVE_MODE else []),
                    role=f"{source_config.scope_id}/{media_type} published media",
                )
                if source_adapter.stat(identity) is None:
                    raise FileNotFoundError(f"media does not exist: {identity}")
                source_bytes = source_adapter.read(identity)
                source_available = True
            except Exception as exc:
                blockers.append(
                    TransferBlocker(
                        code="source_media_unavailable",
                        message=f"source media {media_type}/{identity} could not be read: {exc}",
                        media_type=media_type,
                        identity=identity,
                        document_ids=document_ids,
                    )
                )

        if source_available and target_media is not None and target_adapter is not None:
            try:
                target_adapter.require(
                    READ_CAPABILITY,
                    STAT_CAPABILITY,
                    WRITE_CAPABILITY,
                    VERIFY_BYTES_CAPABILITY,
                    role=f"{target_config.scope_id}/{media_type} published media",
                )
                target_status = _target_artifact_status(
                    target_adapter,
                    identity,
                    source_bytes,
                )
            except Exception as exc:
                blockers.append(
                    TransferBlocker(
                        code="target_media_unavailable",
                        message=f"target media {media_type}/{identity} could not be planned: {exc}",
                        media_type=media_type,
                        identity=identity,
                        document_ids=document_ids,
                    )
                )
            if target_status == "collision":
                blockers.append(
                    TransferBlocker(
                        code="target_media_collision",
                        message=f"target media {media_type}/{identity} has different bytes",
                        media_type=media_type,
                        identity=identity,
                        document_ids=document_ids,
                    )
                )

        build_sources: list[TransferBuildSourcePlan] = []
        for build_type in source_media.build_inputs:
            build_plan = _build_source_plan(
                repo_root,
                source_config,
                target_config,
                media_type=media_type,
                published_identity=identity,
                build_type=build_type,
                mode=mode,
                blockers=blockers,
            )
            if build_plan is not None:
                build_sources.append(build_plan)

        if build_sources and target_status == "create":
            target_status = "produce"

        plans.append(
            TransferMediaPlan(
                media_type=media_type,
                identity=identity,
                source_provider=source_media.location.provider,
                target_provider=target_media.location.provider if target_media else "",
                source_reference=f"{source_media.reference_prefix.as_posix()}/{identity}",
                target_reference=(
                    f"{target_media.reference_prefix.as_posix()}/{identity}"
                    if target_media
                    else ""
                ),
                source_size=len(source_bytes),
                source_sha256=_bytes_sha256(source_bytes) if source_available else "",
                target_status=target_status,
                document_ids=document_ids,
                shared_outside_document_ids=tuple(
                    sorted(outside_references.get((media_type, identity), set()))
                ),
                build_sources=tuple(build_sources),
                source_evidence=source_evidence_plans.get((media_type, identity)),
            )
        )
    return tuple(plans)


def _viewer_link_target(source: str, config: DocsScopeConfig) -> set[str]:
    targets: set[str] = set()
    for match in ROOT_RELATIVE_VIEWER_URL_PATTERN.finditer(source):
        parsed = urlsplit(match.group(0))
        if parsed.path != config.viewer_base_url:
            continue
        query = parse_qs(parsed.query, keep_blank_values=True)
        doc_values = query.get("doc", ())
        scope_values = query.get("scope", ())
        if len(doc_values) != 1 or len(scope_values) > 1:
            continue
        scope = scope_values[0] if scope_values else (
            config.scope_id if not config.include_scope_param else ""
        )
        if scope == config.scope_id:
            targets.add(doc_values[0])
    return targets


def _move_inbound_link_warnings(
    source_config: DocsScopeConfig,
    target_config: DocsScopeConfig,
    all_source_docs: list[source_model.ScopeDoc],
    effective_docs: list[source_model.ScopeDoc],
) -> list[TransferWarning]:
    effective_ids = {doc.doc_id for doc in effective_docs}
    effective_by_id = {doc.doc_id: doc for doc in effective_docs}
    warnings: list[TransferWarning] = []
    for outside_doc in all_source_docs:
        if outside_doc.doc_id in effective_ids:
            continue
        inbound_targets = sorted(
            _viewer_link_target(outside_doc.source_text, source_config) & effective_ids
        )
        for target_doc_id in inbound_targets:
            target_doc = effective_by_id[target_doc_id]
            warnings.append(
                TransferWarning(
                    code="inbound_viewer_link",
                    message=(
                        f"“{outside_doc.title}” links to “{target_doc.title}”. "
                        f"That link will remain pointed at the "
                        f"“{source_config.scope_id}” scope after the move; "
                        f"change it to “{target_config.scope_id}” if it should "
                        f"follow the document."
                    ),
                    document_ids=(outside_doc.doc_id, target_doc_id),
                )
            )
    return warnings


def _collection_customisation(
    collection: ManagedDocumentCollection,
) -> Any:
    return getattr(collection.document_config, "sub_scope_customisation", None)


def _normalize_copy_lineage_actions(
    raw: Any,
) -> dict[str, tuple[str, str]]:
    if raw is None:
        return {}
    if not isinstance(raw, (list, tuple)):
        raise ValueError("copy_lineage_actions must be an array")
    if not raw:
        raise ValueError("copy_lineage_actions must not be empty")
    actions: dict[str, tuple[str, str]] = {}
    expected_fields = frozenset(
        {"source_doc_id", "action", "replace_target_doc_id"}
    )
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"copy_lineage_actions[{index}] must be an object")
        if frozenset(item) != expected_fields:
            raise ValueError(
                f"copy_lineage_actions[{index}] fields must be "
                "source_doc_id, action, replace_target_doc_id"
            )
        source_doc_id = str(item.get("source_doc_id") or "").strip()
        action = str(item.get("action") or "").strip().lower()
        replace_target_doc_id = str(
            item.get("replace_target_doc_id") or ""
        ).strip()
        if not source_doc_id:
            raise ValueError(
                f"copy_lineage_actions[{index}].source_doc_id is required"
            )
        if source_doc_id in actions:
            raise ValueError("copy_lineage_actions contains a duplicate source")
        if action not in SUPPORTED_COPY_ACTIONS:
            raise ValueError(f"copy_lineage_actions[{index}].action is invalid")
        if action == COPY_ACTION_NEW and replace_target_doc_id:
            raise ValueError(
                f"copy_lineage_actions[{index}] New must not select a target"
            )
        if action == COPY_ACTION_REPLACE and not replace_target_doc_id:
            raise ValueError(
                f"copy_lineage_actions[{index}] Replace requires an exact target"
            )
        actions[source_doc_id] = (action, replace_target_doc_id)
    return actions


def _document_lineage_plan(
    repo_root: Path,
    source_collection: ManagedDocumentCollection,
    target_collection: ManagedDocumentCollection,
    source_docs: Iterable[source_model.ScopeDoc],
    target_docs: Iterable[source_model.ScopeDoc],
    *,
    mode: str,
    raw_actions: Any,
    blockers: list[TransferBlocker],
) -> DocumentLineageTransferPlan | None:
    source_aspect = sub_scope_customisation_document_lineage_contract(
        _collection_customisation(source_collection)
    )
    target_aspect = sub_scope_customisation_document_lineage_contract(
        _collection_customisation(target_collection)
    )
    enabled = (
        mode == COPY_MODE
        and source_aspect is not None
        and target_aspect is not None
        and source_aspect.role == LINEAGE_SOURCE_ROLE
        and target_aspect.role == LINEAGE_EDITORIAL_ROLE
        and source_aspect.contract_id == target_aspect.contract_id
    )
    if not enabled:
        if raw_actions is not None:
            raise ValueError(
                "copy_lineage_actions are not supported for this exact transfer"
            )
        return None
    if not source_collection.sub_scope or not target_collection.sub_scope:
        raise ValueError("document lineage requires exact sub-scope collections")

    normalized_actions = _normalize_copy_lineage_actions(raw_actions)
    source_documents = tuple(source_docs)
    source_ids = {document.doc_id for document in source_documents}
    unknown_sources = sorted(set(normalized_actions) - source_ids)
    if unknown_sources:
        raise ValueError(
            "copy_lineage_actions contains documents outside the exact selection: "
            + ", ".join(unknown_sources)
        )
    if raw_actions is not None:
        missing_sources = sorted(source_ids - set(normalized_actions))
        if missing_sources:
            raise ValueError(
                "copy_lineage_actions is missing exact selected documents: "
                + ", ".join(missing_sources)
            )

    lineage_table = publication_lineage.load_table(repo_root)
    target_by_id = {document.doc_id: document for document in target_docs}
    decisions: list[TransferLineageDecision] = []
    selected_replace_targets: set[str] = set()
    for document in source_documents:
        editorials = publication_lineage.editorials_for_working(
            lineage_table,
            working_scope=source_collection.scope,
            working_sub_scope=source_collection.sub_scope,
            editorial_scope=target_collection.scope,
            editorial_sub_scope=target_collection.sub_scope,
            working_doc_id=document.doc_id,
        )
        choices = tuple(
            TransferLineageEditorialChoice(
                editorial_doc_id=editorial.doc_id,
                title=(
                    target_by_id[editorial.doc_id].title
                    if editorial.doc_id in target_by_id
                    else ""
                ),
                available=editorial.doc_id in target_by_id,
            )
            for editorial in editorials
        )
        available_ids = {
            choice.editorial_doc_id
            for choice in choices
            if choice.available
        }
        selected = normalized_actions.get(document.doc_id)
        if selected is None:
            action = COPY_ACTION_NEW if not available_ids else ""
            replace_target_doc_id = ""
            if available_ids:
                blockers.append(
                    TransferBlocker(
                        code="lineage_copy_action_required",
                        message=(
                            f"choose New or one exact Replace target for "
                            f"{document.doc_id!r}"
                        ),
                        document_ids=(document.doc_id,),
                    )
                )
        else:
            action, replace_target_doc_id = selected
            if (
                action == COPY_ACTION_REPLACE
                and replace_target_doc_id not in available_ids
            ):
                raise ValueError(
                    f"Replace target {replace_target_doc_id!r} is not an available "
                    f"Editorial child for {document.doc_id!r}"
                )
            if action == COPY_ACTION_REPLACE:
                if replace_target_doc_id in selected_replace_targets:
                    raise ValueError(
                        f"Replace target {replace_target_doc_id!r} was selected "
                        "for more than one source"
                    )
                selected_replace_targets.add(replace_target_doc_id)
        decisions.append(
            TransferLineageDecision(
                source_doc_id=document.doc_id,
                source_title=document.title,
                action=action,
                replace_target_doc_id=replace_target_doc_id,
                existing_editorials=choices,
            )
        )
    return DocumentLineageTransferPlan(
        contract_id=source_aspect.contract_id,
        decisions=tuple(decisions),
    )


def _custom_metadata_decisions(
    source_collection: ManagedDocumentCollection,
    target_collection: ManagedDocumentCollection,
    documents: Iterable[source_model.ScopeDoc],
    blockers: list[TransferBlocker],
) -> tuple[TransferCustomMetadataDecision, ...]:
    source_customisation = _collection_customisation(source_collection)
    source_contract = sub_scope_customisation_transfer_contract(
        source_customisation
    )
    if source_contract is None:
        return ()
    target_customisation = _collection_customisation(target_collection)
    target_contract = sub_scope_customisation_transfer_contract(
        target_customisation
    )
    source_customisation_id = str(
        getattr(source_customisation, "customisation_id", "") or ""
    )
    target_customisation_id = str(
        getattr(target_customisation, "customisation_id", "") or ""
    )
    decisions: list[TransferCustomMetadataDecision] = []
    for document in documents:
        for field_name in source_contract.owned_field_names:
            if field_name not in document.front_matter:
                continue
            status = "retained"
            reason = "target advertises the same transfer contract"
            if (
                target_contract is None
                or target_contract.contract_id != source_contract.contract_id
            ):
                status = "omitted"
                reason = "target does not advertise the source transfer contract"
            elif field_name not in target_contract.owned_field_names:
                status = "rejected"
                reason = "target transfer contract does not declare this field"
            else:
                try:
                    target_contract.validate_field(
                        target_customisation.settings,
                        field_name,
                        document.front_matter[field_name],
                    )
                except ValueError as exc:
                    status = "rejected"
                    reason = str(exc)
            decision = TransferCustomMetadataDecision(
                source_doc_id=document.doc_id,
                field_name=field_name,
                source_customisation=source_customisation_id,
                target_customisation=target_customisation_id,
                contract_id=source_contract.contract_id,
                status=status,
                reason=reason,
            )
            decisions.append(decision)
            if status == "rejected":
                blockers.append(
                    TransferBlocker(
                        code="target_custom_metadata_rejected",
                        message=(
                            f"target rejected custom field {field_name!r} from "
                            f"{source_customisation_id!r} for document "
                            f"{document.doc_id!r}: {reason}"
                        ),
                        identity=field_name,
                        document_ids=(document.doc_id,),
                    )
                )
    return tuple(
        sorted(
            decisions,
            key=lambda item: (
                item.source_doc_id,
                item.field_name,
                item.status,
            ),
        )
    )


def collection_report_host_doc_id(
    repo_root: Path,
    collection: ManagedDocumentCollection,
) -> str:
    if not collection.sub_scope:
        return ""
    lifecycle = getattr(collection.document_config, "lifecycle", None)
    if lifecycle is not None:
        return lifecycle.report_host_doc_id
    parent_documents = source_model.load_scope_docs_for_config(
        repo_root,
        collection.parent_config,
    )
    matching = [
        document.doc_id
        for document in parent_documents
        if (
            document.report is not None
            and document.report.id == "docs_subscope"
            and document.report.sub_scope == collection.sub_scope
        )
    ]
    if len(matching) != 1:
        raise ValueError(
            "source sub-scope report must resolve exactly once for "
            f"{collection.scope}/{collection.sub_scope}"
        )
    return matching[0]


def viewer_link_collection_doc_id(
    raw_url: str,
    collection: ManagedDocumentCollection,
    *,
    report_host_doc_id: str,
) -> str:
    parsed = urlsplit(raw_url)
    config = collection.parent_config
    if parsed.path != config.viewer_base_url:
        return ""
    query = parse_qs(parsed.query, keep_blank_values=True)
    scope_values = query.get("scope", ())
    if len(scope_values) > 1:
        return ""
    scope = (
        scope_values[0]
        if scope_values
        else config.scope_id if not config.include_scope_param else ""
    )
    if scope != collection.scope:
        return ""
    doc_values = query.get("doc", ())
    subdoc_values = query.get("subdoc", ())
    if collection.sub_scope:
        if (
            len(doc_values) != 1
            or doc_values[0] != report_host_doc_id
            or len(subdoc_values) != 1
        ):
            return ""
        return subdoc_values[0]
    if len(doc_values) != 1 or subdoc_values:
        return ""
    return doc_values[0]


def _link_decisions(
    repo_root: Path,
    source_collection: ManagedDocumentCollection,
    documents: Iterable[source_model.ScopeDoc],
    id_map: Mapping[str, str],
) -> tuple[TransferLinkDecision, ...]:
    report_host_doc_id = collection_report_host_doc_id(
        repo_root,
        source_collection,
    )
    occurrences: dict[tuple[str, str, str, str], int] = {}
    for document in documents:
        for match in ROOT_RELATIVE_VIEWER_URL_PATTERN.finditer(document.body):
            referenced_doc_id = viewer_link_collection_doc_id(
                match.group(0),
                source_collection,
                report_host_doc_id=report_host_doc_id,
            )
            if not referenced_doc_id:
                continue
            target_doc_id = id_map.get(referenced_doc_id, "")
            status = "remap" if target_doc_id else "retain"
            key = (
                document.doc_id,
                referenced_doc_id,
                target_doc_id,
                status,
            )
            occurrences[key] = occurrences.get(key, 0) + 1
    return tuple(
        TransferLinkDecision(
            source_doc_id=source_doc_id,
            referenced_doc_id=referenced_doc_id,
            target_doc_id=target_doc_id,
            status=status,
            occurrence_count=count,
        )
        for (
            source_doc_id,
            referenced_doc_id,
            target_doc_id,
            status,
        ), count in sorted(occurrences.items())
    )


def _internal_parent_relationships(
    documents: Iterable[source_model.ScopeDoc],
) -> tuple[tuple[str, str], ...]:
    documents_by_id = {document.doc_id: document for document in documents}
    return tuple(
        sorted(
            (document.parent_id, document.doc_id)
            for document in documents_by_id.values()
            if document.parent_id in documents_by_id
        )
    )


def plan_document_transfer(
    repo_root: Path,
    *,
    source_scope: Any,
    source_sub_scope: Any | None = None,
    requested_doc_ids: Any,
    target_scope: Any,
    target_sub_scope: Any | None = None,
    transfer_mode: Any,
    include_descendants: Any = False,
    copy_lineage_actions: Any = None,
    operation_timestamp: str | None = None,
    token_factory: IdentityTokenFactory | None = None,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocumentTransferPlan:
    """Return a deterministic document/media transfer preview without writes."""

    mode = _normalize_mode(transfer_mode)
    normalized_source_scope = _normalize_scope(source_scope, field="source_scope")
    normalized_target_scope = _normalize_scope(target_scope, field="target_scope")
    source_collection = resolve_managed_document_collection(
        repo_root,
        scope=normalized_source_scope,
        sub_scope=source_sub_scope,
    )
    target_collection = resolve_managed_document_collection(
        repo_root,
        scope=normalized_target_scope,
        sub_scope=target_sub_scope,
    )
    if source_collection.request_target() == target_collection.request_target():
        raise ValueError("target collection must differ from source collection")
    normalized_requested_ids = _normalize_requested_doc_ids(requested_doc_ids)
    if not isinstance(include_descendants, bool):
        raise ValueError("include_descendants must be a boolean")
    descendants_forced = mode == MOVE_MODE
    effective_include_descendants = include_descendants or descendants_forced
    if mode == MOVE_MODE and (
        source_collection.sub_scope or target_collection.sub_scope
    ):
        raise ValueError("Move supports parent-scope collections only")
    source_config = source_collection.parent_config
    target_config = target_collection.parent_config
    if mode == MOVE_MODE and source_config.scope_type == PUBLIC_SCOPE_TYPE:
        raise ValueError("public source scopes cannot be moved")
    if source_collection.sub_scope and include_descendants:
        raise ValueError("sub-scope Copy does not support descendant inclusion")

    _require_collection_root(
        source_collection,
        role="source",
        writable=mode == MOVE_MODE,
        mode=mode,
    )
    target_root = _require_collection_root(
        target_collection,
        role="target",
        writable=True,
        mode=mode,
    )
    source_docs = source_model.load_document_collection_docs_for_config(
        repo_root,
        source_collection.parent_config,
        source_collection.document_config,
    )
    target_docs = source_model.load_document_collection_docs_for_config(
        repo_root,
        target_collection.parent_config,
        target_collection.document_config,
    )
    effective_docs, ordered_requested_ids = _effective_documents(
        source_docs,
        normalized_requested_ids,
        include_descendants=effective_include_descendants,
    )
    blockers: list[TransferBlocker] = []
    warnings: list[TransferWarning] = []
    relationships = _internal_parent_relationships(effective_docs)
    if source_collection.sub_scope and relationships:
        raise ValueError(
            "sub-scope Copy selection contains a parent/child relationship"
        )

    timestamp = str(operation_timestamp or source_model.current_doc_timestamp()).strip()
    if not source_model.is_doc_timestamp(timestamp):
        raise ValueError("operation_timestamp must use YYYY-MM-DD HH:MM:SS")

    if target_collection.sub_scope and relationships:
        blockers.append(
            TransferBlocker(
                code="flat_target_hierarchy",
                message=(
                    "sub-scope target cannot accept an internal parent/child "
                    "selection"
                ),
                document_ids=tuple(
                    sorted(
                        {
                            doc_id
                            for relationship in relationships
                            for doc_id in relationship
                        }
                    )
                ),
            )
        )
    lineage = _document_lineage_plan(
        repo_root,
        source_collection,
        target_collection,
        effective_docs,
        target_docs,
        mode=mode,
        raw_actions=copy_lineage_actions,
        blockers=blockers,
    )
    documents = _planned_documents(
        effective_docs,
        ordered_requested_ids,
        target_docs,
        mode=mode,
        timestamp=timestamp,
        target_root=target_root,
        token_factory=token_factory,
        lineage=lineage,
        blockers=blockers,
    )
    if mode == MOVE_MODE:
        warnings.extend(
            _move_inbound_link_warnings(
                source_config,
                target_config,
                source_docs,
                effective_docs,
            )
        )
    retained_dependencies = _retained_dependencies(
        source_config,
        effective_docs,
        blockers,
    )
    custom_metadata = (
        _custom_metadata_decisions(
            source_collection,
            target_collection,
            effective_docs,
            blockers,
        )
        if mode == COPY_MODE
        else ()
    )
    media = _media_plans(
        repo_root,
        source_config,
        target_config,
        effective_docs,
        mode=mode,
        blockers=blockers,
        source_media_client=source_media_client,
        target_media_client=target_media_client,
        env_files=env_files,
        environ=environ,
    )
    unique_blockers = tuple(
        sorted(
            set(blockers),
            key=lambda blocker: (
                blocker.code,
                blocker.media_type,
                blocker.identity,
                blocker.document_ids,
                blocker.message,
            ),
        )
    )
    unique_warnings = tuple(
        sorted(
            set(warnings),
            key=lambda warning: (
                warning.code,
                warning.document_ids,
                warning.message,
            ),
        )
    )
    link_decisions = _link_decisions(
        repo_root,
        source_collection,
        effective_docs,
        {
            document.source_doc.doc_id: document.target_doc_id
            for document in documents
        },
    )
    return DocumentTransferPlan(
        mode=mode,
        source_collection=source_collection,
        target_collection=target_collection,
        operation_timestamp=timestamp,
        include_descendants=effective_include_descendants,
        descendants_forced=descendants_forced,
        requested_doc_ids=ordered_requested_ids,
        documents=documents,
        media=media,
        custom_metadata=custom_metadata,
        link_decisions=link_decisions,
        retained_external_dependencies=retained_dependencies,
        lineage=lineage,
        blockers=unique_blockers,
        warnings=unique_warnings,
    )


def restore_document_transfer_apply_plan(
    repo_root: Path,
    payload: Any,
    *,
    source_media_client: object | None = None,
    target_media_client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> DocumentTransferPlan:
    """Restore and revalidate one bounded transfer apply receipt."""

    if not isinstance(payload, dict):
        raise ValueError("document transfer apply_plan is required")
    if _receipt_text(payload, "schema_version") != TRANSFER_APPLY_PLAN_SCHEMA_VERSION:
        raise ValueError("document transfer apply_plan schema_version is invalid")

    mode = _normalize_mode(payload.get("mode"))
    source_target = payload.get("source")
    target_target = payload.get("target")
    if not isinstance(source_target, Mapping) or not isinstance(
        target_target,
        Mapping,
    ):
        raise ValueError(
            "document transfer apply_plan source and target collections are required"
        )
    source_collection = resolve_managed_document_collection(
        repo_root,
        scope=source_target.get("scope"),
        sub_scope=(
            source_target.get("sub_scope")
            if "sub_scope" in source_target
            else None
        ),
    )
    target_collection = resolve_managed_document_collection(
        repo_root,
        scope=target_target.get("scope"),
        sub_scope=(
            target_target.get("sub_scope")
            if "sub_scope" in target_target
            else None
        ),
    )
    if frozenset(source_target) != frozenset(
        source_collection.request_target()
    ) or frozenset(target_target) != frozenset(target_collection.request_target()):
        raise ValueError(
            "document transfer apply_plan collection targets contain unknown fields"
        )
    if source_collection.request_target() == target_collection.request_target():
        raise _stale_receipt("target collection matches source collection")
    operation_timestamp = _receipt_text(payload, "operation_timestamp")
    if not source_model.is_doc_timestamp(operation_timestamp):
        raise ValueError("document transfer apply_plan operation_timestamp is invalid")
    include_descendants = payload.get("include_descendants")
    if not isinstance(include_descendants, bool):
        raise ValueError("document transfer apply_plan include_descendants must be a boolean")
    requested_doc_ids = payload.get("requested_doc_ids")
    if not isinstance(requested_doc_ids, list):
        raise ValueError("document transfer apply_plan requested_doc_ids must be an array")

    receipt_documents = payload.get("documents")
    if not isinstance(receipt_documents, list) or not receipt_documents:
        raise ValueError("document transfer apply_plan documents are required")

    lineage_payload = payload.get("lineage")
    copy_lineage_actions: Any = None
    if lineage_payload is not None:
        if not isinstance(lineage_payload, Mapping):
            raise ValueError("document transfer apply_plan lineage is invalid")
        decisions = lineage_payload.get("decisions")
        if not isinstance(decisions, list):
            raise ValueError(
                "document transfer apply_plan lineage decisions are required"
            )
        copy_lineage_actions = decisions

    token_factory: IdentityTokenFactory | None = None
    if mode == COPY_MODE:
        tokens: list[str] = []
        planned_target_ids: set[str] = set()
        for record in receipt_documents:
            if not isinstance(record, dict):
                raise ValueError(
                    "document transfer apply_plan document records must be objects"
                )
            target_doc_id = _receipt_text(record, "target_doc_id")
            if not source_model.is_immutable_doc_id(target_doc_id):
                raise ValueError(
                    f"document transfer apply_plan target identity "
                    f"{target_doc_id!r} is invalid"
                )
            copy_action = _receipt_text(record, "copy_action")
            if copy_action not in SUPPORTED_COPY_ACTIONS:
                raise ValueError(
                    "document transfer apply_plan copy action is invalid"
                )
            if copy_action == COPY_ACTION_NEW:
                if not source_model.doc_id_matches_added_date(
                    target_doc_id,
                    operation_timestamp,
                ):
                    raise ValueError(
                        f"document transfer apply_plan target identity "
                        f"{target_doc_id!r} does not match the operation timestamp"
                    )
                tokens.append(target_doc_id.rsplit("-", 1)[-1])
            if target_doc_id in planned_target_ids:
                raise ValueError(
                    f"document transfer apply_plan target identity "
                    f"{target_doc_id!r} is duplicated"
                )
            planned_target_ids.add(target_doc_id)

        token_index = 0

        def receipt_token_factory(_size: int) -> str:
            nonlocal token_index
            if token_index >= len(tokens):
                return tokens[-1]
            token = tokens[token_index]
            token_index += 1
            return token

        if tokens:
            token_factory = receipt_token_factory

    try:
        restored = plan_document_transfer(
            repo_root,
            source_scope=source_collection.scope,
            source_sub_scope=source_collection.sub_scope or None,
            requested_doc_ids=requested_doc_ids,
            target_scope=target_collection.scope,
            target_sub_scope=target_collection.sub_scope or None,
            transfer_mode=mode,
            include_descendants=include_descendants,
            copy_lineage_actions=copy_lineage_actions,
            operation_timestamp=operation_timestamp,
            token_factory=token_factory,
            source_media_client=source_media_client,
            target_media_client=target_media_client,
            env_files=env_files,
            environ=environ,
        )
        restored_payload = restored.apply_plan_payload()
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        raise _stale_receipt(str(exc)) from exc
    if restored_payload != payload:
        raise _stale_receipt("source, target, configuration, or transfer plan changed")
    return restored


__all__ = [
    "COPY_ACTION_NEW",
    "COPY_ACTION_REPLACE",
    "COPY_MODE",
    "MEDIA_SOURCE_EVIDENCE_COPY",
    "MEDIA_SOURCE_EVIDENCE_RETAIN",
    "MEDIA_SOURCE_EVIDENCE_UNRECORDED",
    "MOVE_MODE",
    "REGISTERED_BUILD_SOURCE_IDENTITY_RESOLVERS",
    "SUPPORTED_TRANSFER_MODES",
    "TRANSFER_APPLY_PLAN_SCHEMA_VERSION",
    "TRANSFER_PREVIEW_SCHEMA_VERSION",
    "TransferMediaSourceEvidencePlan",
    "DocumentTransferPlan",
    "DocumentLineageTransferPlan",
    "BuildSourceIdentityResolver",
    "IdentityTokenFactory",
    "RetainedExternalDependency",
    "TransferBlocker",
    "TransferBuildSourcePlan",
    "TransferCustomMetadataDecision",
    "TransferDocumentPlan",
    "TransferLinkDecision",
    "TransferLineageDecision",
    "TransferLineageEditorialChoice",
    "TransferMediaPlan",
    "TransferWarning",
    "collection_report_host_doc_id",
    "document_transfer_collection_capability_records",
    "document_transfer_collection_capabilities",
    "document_transfer_scope_capabilities",
    "plan_document_transfer",
    "published_transfer_adapters",
    "restore_document_transfer_apply_plan",
    "transfer_build_source_adapter",
    "viewer_link_collection_doc_id",
]
