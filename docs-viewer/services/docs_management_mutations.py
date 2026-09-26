#!/usr/bin/env python3
"""Planning helpers for Docs Management source mutations."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import docs_source_model as source_model
from docs_document_subjects import subject_key_is_canonical
from docs_index_order import INDEX_ORDER_FILENAME, exclude_nodes, index_order_text, insert_node, move_node, read_index_order, tree_parent_ids
from docs_management_document_target import (
    ManagedDocumentTarget,
    managed_document_target_request,
    resolve_managed_document_collection,
    resolve_managed_document_target,
)
from docs_workspace_config import (
    load_docs_stage,
    require_document_authoring,
    generated_documents_path,
    document_source_path,
    resolve_external_data_root,
    resolve_workspace_path,
)
from docs_collection_customisations import (
    normalize_collection_customisation_metadata_update,
    collection_customisation_assignable_field_groups,
)


COLLECTION_DELETE_PREVIEW_KEYS = frozenset({"stage", "collection", "doc_id"})
COLLECTION_DELETE_APPLY_KEYS = frozenset(
    {"stage", "collection", "doc_id", "source_revision", "confirm"}
)
SOURCE_REVISION_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ASSIGN_FIELD_GROUP_KEYS = frozenset(
    {
        "stage",
        "collection",
        "doc_id",
        "source_revision",
        "field_group",
        "fields",
        "confirm",
    }
)


class ManagedDocumentRevisionConflict(ValueError):
    """The confirmed source bytes no longer match the preview receipt."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(str(payload.get("error") or "managed document source changed after preview"))
        self.payload = payload


def relative_path(repo_root: Path, path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        pass
    try:
        return resolved_path.relative_to(resolve_external_data_root().resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("source path is outside the repo and external Docs Viewer root") from exc


def normalize_summary(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_metadata_text(value: Any) -> str:
    return str(value or "").strip()


def ordered_doc_ids(doc_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw_doc_id in doc_ids:
        doc_id = str(raw_doc_id or "").strip()
        if not doc_id or doc_id in seen:
            continue
        seen.add(doc_id)
        ordered.append(doc_id)
    return ordered


def require_delete_doc_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("doc_ids is required")
    doc_ids = ordered_doc_ids(value)
    if not doc_ids:
        raise ValueError("doc_ids is required")
    return doc_ids


def delete_selection_docs(
    docs: list[source_model.SourceDoc],
    requested_doc_ids: list[str],
) -> tuple[list[str], list[source_model.SourceDoc]]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    missing_doc_ids = [doc_id for doc_id in requested_doc_ids if doc_id not in docs_by_id]
    if missing_doc_ids:
        raise FileNotFoundError(f"docs not found: {', '.join(missing_doc_ids)}")

    selected = set(requested_doc_ids)
    effective_root_doc_ids: list[str] = []
    for doc_id in requested_doc_ids:
        parent_id = docs_by_id[doc_id].parent_id
        seen = {doc_id}
        covered_by_selected_ancestor = False
        while parent_id:
            if parent_id in selected:
                covered_by_selected_ancestor = True
                break
            if parent_id in seen:
                raise ValueError(f"doc hierarchy contains a cycle at {parent_id!r}")
            seen.add(parent_id)
            parent = docs_by_id.get(parent_id)
            if parent is None:
                break
            parent_id = parent.parent_id
        if not covered_by_selected_ancestor:
            effective_root_doc_ids.append(doc_id)

    delete_docs: list[source_model.SourceDoc] = []
    seen_delete_ids: set[str] = set()
    for root_doc_id in effective_root_doc_ids:
        for doc in source_model.subtree_docs_in_tree_order(docs, root_doc_id):
            if doc.doc_id in seen_delete_ids:
                continue
            seen_delete_ids.add(doc.doc_id)
            delete_docs.append(doc)
    return effective_root_doc_ids, delete_docs


def delete_selection_warning(requested_count: int, additional_descendant_count: int) -> str:
    if requested_count == 1:
        selected_text = "the selected document"
    else:
        selected_text = f"{requested_count} checked documents"
    if additional_descendant_count:
        descendant_text = (
            f"{additional_descendant_count} additional descendant document"
            f"{'s' if additional_descendant_count != 1 else ''}"
        )
        return f"This permanently deletes {selected_text} and {descendant_text}."
    return f"This permanently deletes {selected_text}."


@dataclass(frozen=True)
class SourceWrite:
    """A planned write, optionally identifying a referring document's revision."""

    path: Path
    text: str
    original_bytes: Optional[bytes] = None
    create_only: bool = False
    revision_target: Optional[dict[str, str]] = None


@dataclass(frozen=True)
class SourceDelete:
    path: Path
    original_bytes: Optional[bytes] = None


@dataclass(frozen=True)
class ManagementMutationPlan:
    stage: str
    response: Dict[str, Any]
    collection: str = ""
    source_writes: tuple[SourceWrite, ...] = ()
    source_deletes: tuple[SourceDelete, ...] = ()
    suppression_reason: Optional[str] = None
    build_doc_ids: Optional[list[str]] = None
    log_event_name: Optional[str] = None
    log_details: Dict[str, Any] = field(default_factory=dict)
    include_write_result_keys: bool = False
    restore_deletes_on_rebuild_failure: bool = False
    report_create_commit_on_rebuild_failure: bool = False
    revision_conflict_operation: str = "apply"
    revision_conflict_error: str = (
        "managed document source changed before applying changes"
    )

    @property
    def changed_paths(self) -> list[Path]:
        return [write.path for write in self.source_writes] + [delete.path for delete in self.source_deletes]

    @property
    def has_source_changes(self) -> bool:
        return bool(self.source_writes or self.source_deletes)


def plan_create(
    repo_root: Path, body: Dict[str, Any], *, body_markdown: str | None = None,
) -> ManagementMutationPlan:
    """Plan one create-only write without reading existing named-collection docs.

    Ordinary documents add their ID to the authored tree.
    Catalogue records start ready; other documents start as drafts. Catalogue
    fields are present before the creation build. Internal generators may supply
    body_markdown; the HTTP create request does not expose it.
    """
    if "scope" in body:
        raise ValueError("scope is retired; supply stage")
    if "viewable" in body:
        raise ValueError("legacy viewable is not accepted")
    if "publishable" in body or "draft" in body:
        raise ValueError("publishable is retired and draft is assigned by Create")
    collection_requested = "collection" in body
    resolved_collection = resolve_managed_document_collection(
        repo_root,
        collection=body.get("collection") if collection_requested else None,
        stage=body.get("stage"),
        require_existing_source_root=False,
    )
    require_document_authoring(resolved_collection.parent_config)
    stage = resolved_collection.stage
    collection = resolved_collection.collection
    title = str(body.get("title") or "New Doc").strip() or "New Doc"
    create_fields: Dict[str, Any] = {}
    if collection == "catalogue":
        work_id = body.get("work_id")
        if not isinstance(work_id, str) or not work_id.isascii() or not subject_key_is_canonical("work", work_id):
            raise ValueError("Catalogue New requires work_id as an exact five-digit string")
        if not isinstance(body.get("title"), str) or not body["title"].strip():
            raise ValueError("Catalogue New requires a non-blank title")
        create_fields["work_id"] = work_id
    elif "work_id" in body:
        raise ValueError("work_id is only accepted when creating a Catalogue collection document")
    target_root = resolved_collection.source_root
    if "parent_id" in body:
        raise ValueError("Create uses target_doc_id and placement, not parent_id")
    tree = read_index_order(target_root) if not collection else []

    timestamp = source_model.current_doc_timestamp()
    doc_id = source_model.allocate_doc_id(
        timestamp,
        set(tree_parent_ids(tree)),
    )
    parent_id = ""
    if not collection:
        parent_id = insert_node(
            tree, {"doc_id": doc_id, "children": []},
            str(body.get("target_doc_id") or ""), str(body.get("placement") or "inside"),
        )
    target_path = target_root / f"{doc_id}.md"
    front_matter_seed: Dict[str, Any] = {
        "doc_id": doc_id,
        "title": title,
        "added_date": timestamp,
        **create_fields,
    }
    if source_model.collection_supports_draft(resolved_collection.document_config):
        front_matter_seed["draft"] = collection != "catalogue"
    front_matter = source_model.advance_doc_front_matter(
        front_matter_seed,
        timestamp=timestamp,
    )
    source_text = source_model.format_source(
        front_matter, f"# {title}\n" if body_markdown is None else body_markdown,
        collection=collection,
    )
    path = relative_path(repo_root, target_path)
    target = {**resolved_collection.request_target(), "doc_id": doc_id}
    if collection:
        target["collection"] = collection
    record: Dict[str, Any] = {
        "doc_id": doc_id,
        "title": title,
    }
    if source_model.collection_supports_draft(resolved_collection.document_config):
        record["draft"] = front_matter["draft"]
    if not collection:
        record["parent_id"] = parent_id
    response: Dict[str, Any] = {
        "ok": True,
        "stage": stage,
        "doc_id": doc_id,
        "path": path,
        "target": target,
        "record": record,
        "summary_text": f"Created {doc_id}.",
    }
    if collection:
        response["collection"] = collection
    log_details = {
        "stage": stage,
        "doc_id": doc_id,
        "path": path,
    }
    if collection:
        log_details["collection"] = collection

    return ManagementMutationPlan(
        collection=collection,
        stage=resolved_collection.stage,
        response=response,
        source_writes=(
            SourceWrite(
                target_path,
                source_text,
                create_only=True,
            ),
            *((SourceWrite(target_root / INDEX_ORDER_FILENAME, index_order_text(tree)),) if not collection else ()),
        ),
        suppression_reason="docs-create",
        build_doc_ids=[] if collection else [doc_id],
        log_event_name="docs-create",
        log_details=log_details,
        include_write_result_keys=True,
        report_create_commit_on_rebuild_failure=True,
    )


def _assignable_field_groups(resolved: ManagedDocumentTarget) -> tuple[Any, ...]:
    if not resolved.collection:
        return ()
    return collection_customisation_assignable_field_groups(
        resolved.document_config.collection_customisation
    )


def plan_assign_field_group(
    repo_root: Path,
    body: Dict[str, Any],
) -> ManagementMutationPlan:
    if frozenset(body) != ASSIGN_FIELD_GROUP_KEYS:
        required = ", ".join(sorted(ASSIGN_FIELD_GROUP_KEYS))
        raise ValueError(
            "assign field group must contain exactly " + required
        )
    if body.get("confirm") is not True:
        raise ValueError("assign field group requires confirm=true")

    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    require_document_authoring(resolved.parent_config)
    if not resolved.collection:
        raise ValueError("assign field group requires a collection document")

    requested_revision = str(body.get("source_revision") or "").strip()
    if not SOURCE_REVISION_PATTERN.fullmatch(requested_revision):
        raise ValueError(
            "source_revision is required for assignable field group updates"
        )
    raw_group_id = body.get("field_group")
    if (
        not isinstance(raw_group_id, str)
        or raw_group_id != raw_group_id.strip()
        or raw_group_id != raw_group_id.lower()
        or not raw_group_id
    ):
        raise ValueError("field_group must be one exact configured identity")
    group_id = raw_group_id
    groups = [
        group
        for group in _assignable_field_groups(resolved)
        if group.group_id == group_id
    ]
    if len(groups) != 1:
        raise ValueError(
            f"assignable field group is not configured: {group_id or 'missing identity'}"
        )
    group = groups[0]
    raw_fields = body.get("fields")
    if not isinstance(raw_fields, dict):
        raise ValueError("assign field group fields must be an object")
    if set(raw_fields) != set(group.field_names):
        raise ValueError(
            "assign field group fields must contain exactly "
            + ", ".join(group.field_names)
        )
    if group.group_id == "authoring_subject" and raw_fields.get("folder_path"):
        raise ValueError("Folder subjects are unavailable in this workspace")

    target = resolved.document
    source_bytes = target.source_text.encode("utf-8")
    current_revision = source_revision(source_bytes)
    if requested_revision != current_revision:
        raise ManagedDocumentRevisionConflict(
            revision_conflict_payload(
                target=resolved.request_target(),
                requested_revision=requested_revision,
                current_revision=current_revision,
                operation="assign_field_group",
                error="managed document source changed before field group assignment",
            )
        )

    customisation_update = normalize_collection_customisation_metadata_update(
        resolved.document_config.collection_customisation,
        raw_fields,
        provided=True,
        repo_root=repo_root,
        front_matter=target.front_matter,
        doc_id=target.doc_id,
    )
    if customisation_update is None:
        raise ValueError("assignable field group customisation is unavailable")
    expected_fields = set(group.field_names)
    if (
        set(customisation_update.get("front_matter_updates") or {})
        != expected_fields
        or set(customisation_update.get("record") or {}) != expected_fields
    ):
        raise ValueError(
            "assignable field group normalizer returned fields outside its declaration"
        )

    response: Dict[str, Any] = {
        "ok": True,
        "operation": "assign_field_group",
        "target": resolved.request_target(),
        "stage": resolved.stage,
        "collection": resolved.collection,
        "doc_id": target.doc_id,
        "field_group": group.group_id,
        "fields": customisation_update["record"],
        "changes": customisation_update["changes"],
        "path": relative_path(repo_root, target.path),
        "source_revision": current_revision,
    }
    if not any(customisation_update["changes"].values()):
        response["summary_text"] = f"No {group.group_id} changes for {target.doc_id}."
        return ManagementMutationPlan(
            collection=resolved.collection,
            stage=resolved.stage,
            response=response,
        )

    updated_front_matter = dict(target.front_matter)
    for field_name, field_value in customisation_update[
        "front_matter_updates"
    ].items():
        if field_value is None:
            updated_front_matter.pop(field_name, None)
        else:
            updated_front_matter[field_name] = field_value
    updated_front_matter = source_model.advance_front_matter_for_recent_edit(
        target.front_matter,
        target.body,
        updated_front_matter,
        target.body,
    )
    updated_source_text = source_model.format_source(
        updated_front_matter,
        target.body,
        collection=resolved.collection,
    )
    source_model.parse_collection_document_report(
        repo_root,
        resolved.parent_config,
        resolved.document_config,
        updated_source_text,
        source_name=target.path.as_posix(),
    )
    response["source_revision"] = source_revision(
        updated_source_text.encode("utf-8")
    )
    response["summary_text"] = f"Updated {group.group_id} for {target.doc_id}."
    return ManagementMutationPlan(
        collection=resolved.collection,
        stage=resolved.stage,
        response=response,
        source_writes=(
            SourceWrite(
                target.path,
                updated_source_text,
                original_bytes=source_bytes,
            ),
        ),
        suppression_reason="docs-assign-field-group",
        log_event_name="docs-assign-field-group",
        log_details={
            "stage": resolved.stage,
            "collection": resolved.collection,
            "doc_id": target.doc_id,
            "field_group": group.group_id,
            **customisation_update["changes"],
        },
        include_write_result_keys=True,
        revision_conflict_operation="assign_field_group",
        revision_conflict_error=(
            "managed document source changed before field group assignment"
        ),
    )


def plan_move(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    """Move one ordinary subtree by editing only index-order.json."""
    config = load_docs_stage(repo_root, body.get("stage"))
    require_document_authoring(config)
    if body.get("collection") or "parent_id" in body or "scope" in body:
        raise ValueError("Position requires an ordinary document, target_doc_id and placement")
    doc_id = str(body.get("doc_id") or "")
    root = document_source_path(config)
    tree = read_index_order(root)
    parent_id = move_node(tree, doc_id, str(body.get("target_doc_id") or ""), str(body.get("placement") or ""))
    return ManagementMutationPlan(
        stage=config.stage,
        response={
            "ok": True, "stage": config.stage, "doc_id": doc_id,
            "record": {"doc_id": doc_id, "parent_id": parent_id},
            "summary_text": f"Positioned {doc_id}.",
        },
        source_writes=(SourceWrite(root / INDEX_ORDER_FILENAME, index_order_text(tree)),),
        suppression_reason="docs-position",
        build_doc_ids=[doc_id],
        include_write_result_keys=True,
    )


def plan_delete_preview(repo_root: Path, doc_ids: list[str], *, stage: str) -> Dict[str, Any]:
    config = load_docs_stage(repo_root, stage)
    require_document_authoring(config)
    requested_doc_ids = require_delete_doc_ids(doc_ids)
    docs = source_model.load_stage_docs_for_config(repo_root, config)
    effective_root_doc_ids, delete_docs = delete_selection_docs(docs, requested_doc_ids)
    delete_documents = [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "path": relative_path(repo_root, doc.path),
        }
        for doc in delete_docs
    ]
    delete_doc_ids = [doc.doc_id for doc in delete_docs]
    requested_count = len(requested_doc_ids)
    additional_descendant_count = len(set(delete_doc_ids) - set(requested_doc_ids))
    warnings = [delete_selection_warning(requested_count, additional_descendant_count)]
    configured_default = config.default_doc_id
    default_doc_id_changed = configured_default in set(delete_doc_ids)

    return {
        "ok": True,
        "stage": stage,
        "allowed": True,
        "blockers": [],
        "warnings": warnings,
        "requested_doc_count": requested_count,
        "requested_doc_ids": requested_doc_ids,
        "effective_root_count": len(effective_root_doc_ids),
        "effective_root_doc_ids": effective_root_doc_ids,
        "delete_count": len(delete_docs),
        "additional_descendant_count": additional_descendant_count,
        "delete_doc_ids": delete_doc_ids,
        "delete_documents": delete_documents,
        "default_doc_id_changed": default_doc_id_changed,
        "default_doc_id": "" if default_doc_id_changed else configured_default,
    }


def selected_delete_writes(config: Any, doc_ids: list[str], collection: str = "") -> tuple[SourceWrite, ...]:
    from docs_selected_documents import read_selected, selected_path, selected_text

    path = selected_path(config)
    original = path.read_bytes()
    payload = read_selected(config)
    rows = [row for row in payload["docs"] if not (row.get("collection", "") == collection and row["doc_id"] in doc_ids)]
    if rows == payload["docs"]:
        return ()
    return (SourceWrite(path, selected_text({**payload, "docs": rows}), original_bytes=original),)


def plan_delete_apply(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    if "scope" in body:
        raise ValueError("scope is retired; supply stage")
    config = load_docs_stage(repo_root, body.get("stage"))
    stage = config.stage
    require_document_authoring(config)
    requested_doc_ids = require_delete_doc_ids(body.get("doc_ids"))
    if not body.get("confirm"):
        raise ValueError("delete apply requires confirm=true")

    preview = plan_delete_preview(repo_root, requested_doc_ids, stage=stage)
    if not preview["allowed"]:
        raise ValueError("; ".join(preview["blockers"]))

    docs = source_model.load_stage_docs_for_config(repo_root, config)
    effective_root_doc_ids, delete_docs = delete_selection_docs(docs, requested_doc_ids)
    delete_doc_ids = [doc.doc_id for doc in delete_docs]
    delete_paths = [relative_path(repo_root, doc.path) for doc in delete_docs]
    delete_count = len(delete_docs)
    additional_descendant_count = len(set(delete_doc_ids) - set(requested_doc_ids))
    summary_text = f"Deleted {delete_count} document{'s' if delete_count != 1 else ''}."
    return ManagementMutationPlan(
        stage=config.stage,
        response={
            "ok": True,
            "stage": stage,
            "paths": delete_paths,
            "requested_doc_count": len(requested_doc_ids),
            "requested_doc_ids": requested_doc_ids,
            "effective_root_count": len(effective_root_doc_ids),
            "effective_root_doc_ids": effective_root_doc_ids,
            "delete_count": delete_count,
            "additional_descendant_count": additional_descendant_count,
            "deleted_doc_ids": delete_doc_ids,
            "warnings": preview["warnings"],
            "default_doc_id_changed": preview["default_doc_id_changed"],
            "default_doc_id": preview["default_doc_id"],
            "summary_text": summary_text,
        },
        source_deletes=tuple(SourceDelete(doc.path) for doc in delete_docs),
        source_writes=(SourceWrite(
            document_source_path(config) / INDEX_ORDER_FILENAME,
            index_order_text(exclude_nodes(read_index_order(document_source_path(config)), set(delete_doc_ids))),
        ), *selected_delete_writes(config, delete_doc_ids)),
        suppression_reason="docs-delete",
        build_doc_ids=delete_doc_ids,
        log_event_name="docs-delete",
        log_details={
            "stage": stage,
            "paths": delete_paths,
            "requested_doc_ids": requested_doc_ids,
            "effective_root_doc_ids": effective_root_doc_ids,
            "deleted_doc_ids": delete_doc_ids,
            "delete_count": delete_count,
            "additional_descendant_count": additional_descendant_count,
            "default_doc_id_changed": preview["default_doc_id_changed"],
        },
        include_write_result_keys=True,
    )


def require_exact_collection_delete_request(
    body: Dict[str, Any],
    *,
    apply: bool,
) -> None:
    expected = COLLECTION_DELETE_APPLY_KEYS if apply else COLLECTION_DELETE_PREVIEW_KEYS
    actual = frozenset(body)
    if actual != expected:
        required = ", ".join(sorted(expected))
        raise ValueError(
            "collection document delete "
            f"{'apply' if apply else 'preview'} must contain exactly {required}"
        )


def source_revision(source_bytes: bytes) -> str:
    return f"sha256:{hashlib.sha256(source_bytes).hexdigest()}"


def collection_delete_generated_outputs(
    repo_root: Path,
    resolved: ManagedDocumentTarget,
) -> list[dict[str, str]]:
    output_root = resolve_workspace_path(
        repo_root,
        generated_documents_path(resolved.document_config),
    )
    return [
        {
            "kind": "collection_manifest",
            "action": "rebuild",
            "path": relative_path(repo_root, output_root / "manifest.json"),
        },
        {
            "kind": "collection_document",
            "action": "remove",
            "path": relative_path(
                repo_root,
                output_root / "by-id" / f"{resolved.doc_id}.json",
            ),
        },
    ]


def plan_collection_delete_preview(
    repo_root: Path,
    body: Dict[str, Any],
) -> Dict[str, Any]:
    """Plan a write-free delete of one exact configured child document."""

    require_exact_collection_delete_request(body, apply=False)
    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    require_document_authoring(resolved.parent_config)
    if not resolved.collection:
        raise ValueError("collection is required for collection document delete")

    document = resolved.document
    source_bytes = document.source_text.encode("utf-8")
    target = resolved.request_target()
    path = relative_path(repo_root, document.path)
    return {
        "ok": True,
        "operation": "preview",
        "target": target,
        "stage": resolved.stage,
        "collection": resolved.collection,
        "doc_id": document.doc_id,
        "title": document.title,
        "source_revision": source_revision(source_bytes),
        "allowed": True,
        "blockers": [],
        "warnings": ["This permanently deletes the displayed collection document."],
        "delete_count": 1,
        "delete_documents": [
            {
                "doc_id": document.doc_id,
                "title": document.title,
                "path": path,
            }
        ],
        "generated_outputs": collection_delete_generated_outputs(repo_root, resolved),
    }


def revision_conflict_payload(
    *,
    target: dict[str, str],
    requested_revision: str,
    current_revision: str,
    operation: str = "apply",
    error: str = "collection document source changed after delete preview",
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": False,
        "operation": operation,
        "target": target,
        "stage": target["stage"],
        "doc_id": target["doc_id"],
        "source_revision": requested_revision,
        "current_source_revision": current_revision,
        "error": error,
        "retry_safe": False,
    }
    if target.get("collection"):
        payload["collection"] = target["collection"]
    return payload


def plan_collection_delete_apply(
    repo_root: Path,
    body: Dict[str, Any],
) -> ManagementMutationPlan:
    """Plan one confirmed child-source deletion against its preview revision."""

    require_exact_collection_delete_request(body, apply=True)
    if body.get("confirm") is not True:
        raise ValueError("collection document delete apply requires confirm=true")
    requested_revision = str(body.get("source_revision") or "").strip()
    if not SOURCE_REVISION_PATTERN.fullmatch(requested_revision):
        raise ValueError("source_revision must be a sha256 revision receipt")

    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    require_document_authoring(resolved.parent_config)
    if not resolved.collection:
        raise ValueError("collection is required for collection document delete")

    document = resolved.document
    source_bytes = document.source_text.encode("utf-8")
    current_revision = source_revision(source_bytes)
    target = resolved.request_target()
    if current_revision != requested_revision:
        raise ManagedDocumentRevisionConflict(
            revision_conflict_payload(
                target=target,
                requested_revision=requested_revision,
                current_revision=current_revision,
            )
        )

    path = relative_path(repo_root, document.path)
    return ManagementMutationPlan(
        collection=resolved.collection,
        stage=resolved.stage,
        response={
            "ok": True,
            "operation": "apply",
            "target": target,
            "stage": resolved.stage,
            "collection": resolved.collection,
            "doc_id": document.doc_id,
            "title": document.title,
            "source_revision": requested_revision,
            "path": path,
            "deleted_doc_ids": [document.doc_id],
            "delete_count": 1,
            "generated_outputs": collection_delete_generated_outputs(repo_root, resolved),
            "summary_text": f"Deleted {document.doc_id}.",
        },
        source_deletes=(SourceDelete(document.path, original_bytes=source_bytes),),
        source_writes=selected_delete_writes(resolved.parent_config, [document.doc_id], resolved.collection),
        suppression_reason="docs-collection-document-delete",
        revision_conflict_operation="apply",
        revision_conflict_error="collection document source changed after delete preview",
        log_event_name="docs-delete",
        log_details={
            "stage": resolved.stage,
            "collection": resolved.collection,
            "doc_id": document.doc_id,
            "deleted_doc_ids": [document.doc_id],
            "delete_count": 1,
            "path": path,
        },
        include_write_result_keys=True,
        restore_deletes_on_rebuild_failure=True,
    )
