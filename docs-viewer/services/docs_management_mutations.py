#!/usr/bin/env python3
"""Planning helpers for Docs Management source mutations."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import docs_source_model as source_model
from docs_management_document_target import (
    ManagedDocumentTarget,
    confined_source_path,
    managed_document_target_request,
    resolve_managed_document_collection,
    resolve_managed_document_target,
    source_doc_from_path,
)
from docs_scope_config import (
    load_docs_scope_configs,
    published_documents_path,
    resolve_external_data_root,
    resolve_scope_path,
)


SUB_SCOPE_DELETE_PREVIEW_KEYS = frozenset({"scope", "sub_scope", "doc_id"})
SUB_SCOPE_DELETE_APPLY_KEYS = frozenset(
    {"scope", "sub_scope", "doc_id", "source_revision", "confirm"}
)
SOURCE_REVISION_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def normalize_configured_metadata_choice(
    value: Any,
    *,
    field: str,
    allowed_values: tuple[str, ...],
) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a scalar string")
    normalized = value.strip().lower()
    if normalized and not allowed_values:
        raise ValueError(f"{field} is not configured for this sub-scope")
    if normalized and normalized not in allowed_values:
        raise ValueError(
            f"Unknown {field} {normalized!r}; expected one of: "
            + ", ".join(allowed_values)
        )
    return normalized


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
    docs: list[source_model.ScopeDoc],
    requested_doc_ids: list[str],
) -> tuple[list[str], list[source_model.ScopeDoc]]:
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

    delete_docs: list[source_model.ScopeDoc] = []
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


def metadata_search_doc_ids(
    docs: list[source_model.ScopeDoc],
    doc_id: str,
    *,
    title_changed: bool,
) -> list[str]:
    doc_ids = [doc_id]
    if title_changed:
        doc_ids.extend(source_model.direct_child_doc_ids(docs, doc_id))
    return ordered_doc_ids(doc_ids)


@dataclass(frozen=True)
class SourceWrite:
    path: Path
    text: str
    original_bytes: Optional[bytes] = None
    create_only: bool = False


@dataclass(frozen=True)
class SourceDelete:
    path: Path
    original_bytes: Optional[bytes] = None


@dataclass(frozen=True)
class ScopeRebuild:
    scope: str
    changed_paths: tuple[Path, ...]
    build_doc_ids: Optional[list[str]] = None
    search_doc_ids: Optional[list[str]] = None
    include_search: bool = True


@dataclass(frozen=True)
class ManagementMutationPlan:
    scope: str
    response: Dict[str, Any]
    sub_scope: str = ""
    source_writes: tuple[SourceWrite, ...] = ()
    source_deletes: tuple[SourceDelete, ...] = ()
    suppression_reason: Optional[str] = None
    build_doc_ids: Optional[list[str]] = None
    search_doc_ids: Optional[list[str]] = None
    rebuilds: tuple[ScopeRebuild, ...] = ()
    log_event_name: Optional[str] = None
    log_details: Dict[str, Any] = field(default_factory=dict)
    include_write_result_keys: bool = False
    restore_deletes_on_rebuild_failure: bool = False
    report_create_commit_on_rebuild_failure: bool = False

    @property
    def changed_paths(self) -> list[Path]:
        return [write.path for write in self.source_writes] + [delete.path for delete in self.source_deletes]

    @property
    def has_source_changes(self) -> bool:
        return bool(self.source_writes or self.source_deletes)


def plan_create(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    sub_scope_requested = "sub_scope" in body
    sub_scope = ""
    target_root: Path
    if sub_scope_requested:
        collection = resolve_managed_document_collection(
            repo_root,
            scope=body.get("scope"),
            sub_scope=body.get("sub_scope"),
        )
        scope = collection.scope
        sub_scope = collection.sub_scope
        target_root = collection.source_root
        docs = []
        for candidate in source_model.scope_markdown_paths(target_root):
            confined = confined_source_path(target_root, candidate)
            document = source_doc_from_path(
                path=confined,
                scope=scope,
                requested_doc_id=candidate.stem,
            )
            source_model.validate_sub_scope_document_metadata(
                document,
                ui_statuses=collection.document_config.ui_statuses,
                document_groups=collection.document_config.document_groups,
            )
            docs.append(document)
        if "parent_id" in body:
            raise ValueError("parent_id is not accepted for a sub-scope document")
    else:
        scope = source_model.normalize_scope(body.get("scope"))
        docs = source_model.load_scope_docs(repo_root, scope)
        target_root = source_model.scope_root(repo_root, scope)
    title = str(body.get("title") or "New Doc").strip() or "New Doc"
    docs_by_id = {doc.doc_id: doc for doc in docs}
    parent_id = str(body.get("parent_id") or "").strip()

    if not sub_scope and parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")

    timestamp = source_model.current_doc_timestamp()
    doc_id = source_model.allocate_doc_id(
        timestamp,
        {identity for doc in docs for identity in (doc.doc_id, doc.path.stem)},
    )
    target_path = target_root / f"{doc_id}.md"
    front_matter_seed: Dict[str, Any] = {
        "doc_id": doc_id,
        "title": title,
        "added_date": timestamp,
    }
    if not sub_scope:
        front_matter_seed["parent_id"] = parent_id
    front_matter = source_model.advance_doc_front_matter(
        front_matter_seed,
        timestamp=timestamp,
    )
    viewable = source_model.default_viewable_for_scope(scope)
    if not viewable:
        front_matter["viewable"] = False
    source_text = source_model.format_source(front_matter, f"# {title}\n")
    path = relative_path(repo_root, target_path)
    target = {"scope": scope, "doc_id": doc_id}
    if sub_scope:
        target["sub_scope"] = sub_scope
    record: Dict[str, Any] = {
        "doc_id": doc_id,
        "title": title,
        "viewable": viewable,
    }
    if not sub_scope:
        record["parent_id"] = parent_id
    response: Dict[str, Any] = {
        "ok": True,
        "scope": scope,
        "doc_id": doc_id,
        "path": path,
        "target": target,
        "record": record,
        "summary_text": f"Created {doc_id}.",
    }
    if sub_scope:
        response["sub_scope"] = sub_scope
    log_details = {
        "scope": scope,
        "doc_id": doc_id,
        "path": path,
    }
    if sub_scope:
        log_details["sub_scope"] = sub_scope

    return ManagementMutationPlan(
        scope=scope,
        sub_scope=sub_scope,
        response=response,
        source_writes=(
            SourceWrite(
                target_path,
                source_text,
                create_only=True,
            ),
        ),
        suppression_reason="docs-create",
        build_doc_ids=[] if sub_scope else [doc_id],
        search_doc_ids=[] if sub_scope else [doc_id],
        log_event_name="docs-create",
        log_details=log_details,
        include_write_result_keys=True,
        report_create_commit_on_rebuild_failure=True,
    )


def plan_update_metadata(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    scope = resolved.scope
    target = resolved.document
    if resolved.sub_scope and "parent_id" in body:
        raise ValueError("parent_id is not editable for a sub-scope document")
    requested_revision = str(body.get("source_revision") or "").strip()
    if resolved.sub_scope and not SOURCE_REVISION_PATTERN.fullmatch(
        requested_revision
    ):
        raise ValueError(
            "source_revision is required for sub-scope metadata updates"
        )
    if requested_revision and not SOURCE_REVISION_PATTERN.fullmatch(
        requested_revision
    ):
        raise ValueError("source_revision must be a sha256 revision receipt")
    source_bytes = target.source_text.encode("utf-8")
    current_revision = source_revision(source_bytes)
    if requested_revision and requested_revision != current_revision:
        raise ManagedDocumentRevisionConflict(
            revision_conflict_payload(
                target=resolved.request_target(),
                requested_revision=requested_revision,
                current_revision=current_revision,
                operation="update_metadata",
                error="managed document source changed before metadata save",
            )
        )
    title = str(body.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")

    docs: list[source_model.ScopeDoc] = []
    parent_id = target.parent_id
    if not resolved.sub_scope:
        docs = source_model.load_scope_docs(repo_root, scope)
        docs_by_id = {doc.doc_id: doc for doc in docs}
        parent_id = str(body.get("parent_id") or "").strip()
        if parent_id == target.doc_id:
            raise ValueError("parent_id cannot be the current doc")
        if parent_id and parent_id not in docs_by_id:
            raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
        if parent_id and parent_id in source_model.descendant_doc_ids(docs, target.doc_id):
            raise ValueError("parent_id cannot be a child or descendant of the current doc")

    title_changed = title != target.title
    parent_changed = not resolved.sub_scope and parent_id != target.parent_id
    summary_was_provided = "summary" in body
    current_summary = normalize_summary(target.front_matter.get("summary"))
    summary = normalize_summary(body.get("summary")) if summary_was_provided else current_summary
    summary_changed = summary_was_provided and summary != current_summary
    date_was_provided = "date" in body
    current_date = normalize_metadata_text(target.front_matter.get("date"))
    date = normalize_metadata_text(body.get("date")) if date_was_provided else current_date
    date_changed = date_was_provided and date != current_date
    date_display_was_provided = "date_display" in body
    current_date_display = normalize_metadata_text(target.front_matter.get("date_display"))
    date_display = normalize_metadata_text(body.get("date_display")) if date_display_was_provided else current_date_display
    date_display_changed = date_display_was_provided and date_display != current_date_display
    status_was_provided = "ui_status" in body
    current_ui_status = source_model.normalize_ui_status(target.front_matter.get("ui_status"))
    if resolved.sub_scope and status_was_provided:
        ui_status = normalize_configured_metadata_choice(
            body.get("ui_status"),
            field="ui_status",
            allowed_values=resolved.document_config.ui_statuses,
        )
    else:
        ui_status = source_model.normalize_ui_status(body.get("ui_status")) if status_was_provided else current_ui_status
    status_changed = status_was_provided and ui_status != current_ui_status
    group_was_provided = resolved.sub_scope and "group" in body
    current_group = target.group
    if group_was_provided and not resolved.document_config.document_groups:
        raise ValueError("group is not configured for this sub-scope")
    group = (
        normalize_configured_metadata_choice(
            body.get("group"),
            field="group",
            allowed_values=resolved.document_config.document_groups,
        )
        if group_was_provided
        else current_group
    )
    group_changed = group_was_provided and group != current_group
    viewable_was_provided = "viewable" in body
    current_viewable = target.viewable
    viewable = source_model.front_matter_boolean(body, "viewable", True) if viewable_was_provided else current_viewable
    viewable_changed = viewable_was_provided and viewable != current_viewable
    changes = {
        "title_changed": title_changed,
        "parent_changed": parent_changed,
        "summary_changed": summary_changed,
        "date_changed": date_changed,
        "date_display_changed": date_display_changed,
        "status_changed": status_changed,
        "viewable_changed": viewable_changed,
    }
    if resolved.sub_scope:
        changes["group_changed"] = group_changed
    if not any(changes.values()):
        record: dict[str, object] = {
            "doc_id": target.doc_id,
            "title": target.title,
            "summary": current_summary,
            "date": current_date,
            "date_display": current_date_display,
            "ui_status": current_ui_status,
            "viewable": current_viewable,
        }
        if not resolved.sub_scope:
            record["parent_id"] = target.parent_id
        else:
            record["group"] = current_group
        response: dict[str, Any] = {
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "source_revision": current_revision,
            "record": record,
            "changes": dict.fromkeys(changes.keys(), False),
            "summary_text": f"No metadata changes for {target.doc_id}.",
        }
        if resolved.sub_scope:
            response["sub_scope"] = resolved.sub_scope
        return ManagementMutationPlan(
            scope=scope,
            sub_scope=resolved.sub_scope,
            response=response,
        )

    updated_front_matter = dict(target.front_matter)
    updated_front_matter["title"] = title
    if summary_was_provided:
        if summary:
            updated_front_matter["summary"] = summary
        else:
            updated_front_matter.pop("summary", None)
    if date_was_provided:
        if date:
            updated_front_matter["date"] = date
        else:
            updated_front_matter.pop("date", None)
    if date_display_was_provided:
        if date_display:
            updated_front_matter["date_display"] = date_display
        else:
            updated_front_matter.pop("date_display", None)
    if status_was_provided:
        if ui_status:
            updated_front_matter["ui_status"] = ui_status
        else:
            updated_front_matter.pop("ui_status", None)
    if viewable_was_provided:
        if viewable:
            updated_front_matter.pop("viewable", None)
        else:
            updated_front_matter["viewable"] = False
    if group_was_provided:
        if group:
            updated_front_matter["group"] = group
        else:
            updated_front_matter.pop("group", None)
    if not resolved.sub_scope:
        updated_front_matter["parent_id"] = parent_id
        updated_front_matter.pop("sort_order", None)
    updated_front_matter = source_model.advance_front_matter_for_recent_edit(
        target.front_matter,
        target.body,
        updated_front_matter,
        target.body,
    )

    search_doc_ids: list[str] = []
    if not resolved.sub_scope:
        search_doc_ids = metadata_search_doc_ids(
            docs,
            target.doc_id,
            title_changed=title_changed,
        )
        if status_changed and not (
            title_changed or parent_changed or summary_changed or viewable_changed
        ):
            search_doc_ids = []

    record = {
        "doc_id": target.doc_id,
        "title": title,
        "summary": summary,
        "date": date,
        "date_display": date_display,
        "ui_status": ui_status,
        "viewable": viewable,
    }
    if not resolved.sub_scope:
        record["parent_id"] = parent_id
    else:
        record["group"] = group
    updated_source_text = source_model.format_source(
        updated_front_matter,
        target.body,
    )
    response = {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "path": relative_path(repo_root, target.path),
        "source_revision": source_revision(updated_source_text.encode("utf-8")),
        "record": record,
        "changes": changes,
        "summary_text": f"Updated metadata for {target.doc_id}.",
    }
    if resolved.sub_scope:
        response["sub_scope"] = resolved.sub_scope
    log_details = {
        "scope": scope,
        "doc_id": target.doc_id,
        "title_changed": title_changed,
        "parent_changed": parent_changed,
        "summary_changed": summary_changed,
        "date_changed": date_changed,
        "date_display_changed": date_display_changed,
        "status_changed": status_changed,
        "viewable_changed": viewable_changed,
    }
    if resolved.sub_scope:
        log_details["sub_scope"] = resolved.sub_scope
        log_details["group_changed"] = group_changed

    return ManagementMutationPlan(
        scope=scope,
        sub_scope=resolved.sub_scope,
        response=response,
        source_writes=(
            SourceWrite(
                target.path,
                updated_source_text,
                original_bytes=source_bytes if requested_revision else None,
            ),
        ),
        suppression_reason="docs-update-metadata",
        build_doc_ids=[] if resolved.sub_scope else [target.doc_id],
        search_doc_ids=search_doc_ids,
        log_event_name="docs-update-metadata",
        log_details=log_details,
        include_write_result_keys=True,
    )


def plan_move(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    parent_id = str(body.get("parent_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")

    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    moving_doc = docs_by_id.get(doc_id)
    if moving_doc is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if parent_id == moving_doc.doc_id:
        raise ValueError("parent_id cannot be the current doc")
    if parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
    if parent_id and parent_id in source_model.descendant_doc_ids(docs, moving_doc.doc_id):
        raise ValueError("parent_id cannot be a child or descendant of the current doc")

    changed = moving_doc.parent_id != parent_id
    search_doc_ids = [moving_doc.doc_id]
    if changed:
        search_doc_ids.extend(sorted(source_model.descendant_doc_ids(docs, moving_doc.doc_id)))

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": moving_doc.doc_id,
            "record": {
                "doc_id": moving_doc.doc_id,
                "parent_id": parent_id,
            },
            "changed_doc_ids": [moving_doc.doc_id] if changed else [],
            "summary_text": f"Moved {moving_doc.doc_id}." if changed else f"No move needed for {moving_doc.doc_id}.",
        },
        source_writes=(SourceWrite(moving_doc.path, source_model.rewrite_doc_placement_source(moving_doc, parent_id)),) if changed else (),
        suppression_reason="docs-move",
        build_doc_ids=[moving_doc.doc_id] if changed else [],
        search_doc_ids=search_doc_ids if changed else [],
        log_event_name="docs-move" if changed else None,
        log_details={
            "scope": scope,
            "doc_id": moving_doc.doc_id,
            "from_parent_id": moving_doc.parent_id,
            "to_parent_id": parent_id,
            "changed_count": 1 if changed else 0,
        },
        include_write_result_keys=True,
    )


def configured_default_doc_id(repo_root: Path, scope: str) -> str:
    try:
        config = load_docs_scope_configs(repo_root).get(scope)
    except FileNotFoundError:
        config = source_model.DOCS_SCOPE_CONFIGS.get(scope)
    return str(getattr(config, "default_doc_id", "") or "").strip()


def plan_delete_preview(repo_root: Path, scope: str, doc_ids: list[str]) -> Dict[str, Any]:
    scope = source_model.normalize_scope(scope)
    requested_doc_ids = require_delete_doc_ids(doc_ids)
    docs = source_model.load_scope_docs(repo_root, scope)
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
    configured_default = configured_default_doc_id(repo_root, scope)
    default_doc_id_changed = configured_default in set(delete_doc_ids)

    return {
        "ok": True,
        "scope": scope,
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


def plan_delete_apply(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    requested_doc_ids = require_delete_doc_ids(body.get("doc_ids"))
    if not body.get("confirm"):
        raise ValueError("delete apply requires confirm=true")

    preview = plan_delete_preview(repo_root, scope, requested_doc_ids)
    if not preview["allowed"]:
        raise ValueError("; ".join(preview["blockers"]))

    docs = source_model.load_scope_docs(repo_root, scope)
    effective_root_doc_ids, delete_docs = delete_selection_docs(docs, requested_doc_ids)
    delete_doc_ids = [doc.doc_id for doc in delete_docs]
    delete_paths = [relative_path(repo_root, doc.path) for doc in delete_docs]
    delete_count = len(delete_docs)
    additional_descendant_count = len(set(delete_doc_ids) - set(requested_doc_ids))
    summary_text = f"Deleted {delete_count} document{'s' if delete_count != 1 else ''}."
    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
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
        suppression_reason="docs-delete",
        build_doc_ids=delete_doc_ids,
        search_doc_ids=delete_doc_ids,
        log_event_name="docs-delete",
        log_details={
            "scope": scope,
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


def require_exact_sub_scope_delete_request(
    body: Dict[str, Any],
    *,
    apply: bool,
) -> None:
    expected = SUB_SCOPE_DELETE_APPLY_KEYS if apply else SUB_SCOPE_DELETE_PREVIEW_KEYS
    actual = frozenset(body)
    if actual != expected:
        required = ", ".join(sorted(expected))
        raise ValueError(
            "sub-scope document delete "
            f"{'apply' if apply else 'preview'} must contain exactly {required}"
        )


def source_revision(source_bytes: bytes) -> str:
    return f"sha256:{hashlib.sha256(source_bytes).hexdigest()}"


def sub_scope_delete_generated_outputs(
    repo_root: Path,
    resolved: ManagedDocumentTarget,
) -> list[dict[str, str]]:
    output_root = resolve_scope_path(
        repo_root,
        published_documents_path(resolved.document_config),
    )
    return [
        {
            "kind": "sub_scope_manifest",
            "action": "rebuild",
            "path": relative_path(repo_root, output_root / "manifest.json"),
        },
        {
            "kind": "sub_scope_document",
            "action": "remove",
            "path": relative_path(
                repo_root,
                output_root / "by-id" / f"{resolved.doc_id}.json",
            ),
        },
    ]


def plan_sub_scope_delete_preview(
    repo_root: Path,
    body: Dict[str, Any],
) -> Dict[str, Any]:
    """Plan a write-free delete of one exact configured child document."""

    require_exact_sub_scope_delete_request(body, apply=False)
    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    if not resolved.sub_scope:
        raise ValueError("sub_scope is required for sub-scope document delete")

    document = resolved.document
    source_bytes = document.source_text.encode("utf-8")
    target = resolved.request_target()
    path = relative_path(repo_root, document.path)
    return {
        "ok": True,
        "operation": "preview",
        "target": target,
        "scope": resolved.scope,
        "sub_scope": resolved.sub_scope,
        "doc_id": document.doc_id,
        "title": document.title,
        "source_revision": source_revision(source_bytes),
        "allowed": True,
        "blockers": [],
        "warnings": ["This permanently deletes the displayed sub-scope document."],
        "delete_count": 1,
        "delete_documents": [
            {
                "doc_id": document.doc_id,
                "title": document.title,
                "path": path,
            }
        ],
        "generated_outputs": sub_scope_delete_generated_outputs(repo_root, resolved),
    }


def revision_conflict_payload(
    *,
    target: dict[str, str],
    requested_revision: str,
    current_revision: str,
    operation: str = "apply",
    error: str = "sub-scope document source changed after delete preview",
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": False,
        "operation": operation,
        "target": target,
        "scope": target["scope"],
        "doc_id": target["doc_id"],
        "source_revision": requested_revision,
        "current_source_revision": current_revision,
        "error": error,
        "retry_safe": False,
    }
    if target.get("sub_scope"):
        payload["sub_scope"] = target["sub_scope"]
    return payload


def plan_sub_scope_delete_apply(
    repo_root: Path,
    body: Dict[str, Any],
) -> ManagementMutationPlan:
    """Plan one confirmed child-source deletion against its preview revision."""

    require_exact_sub_scope_delete_request(body, apply=True)
    if body.get("confirm") is not True:
        raise ValueError("sub-scope document delete apply requires confirm=true")
    requested_revision = str(body.get("source_revision") or "").strip()
    if not SOURCE_REVISION_PATTERN.fullmatch(requested_revision):
        raise ValueError("source_revision must be a sha256 revision receipt")

    resolved = resolve_managed_document_target(
        repo_root,
        managed_document_target_request(body),
    )
    if not resolved.sub_scope:
        raise ValueError("sub_scope is required for sub-scope document delete")

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
        scope=resolved.scope,
        sub_scope=resolved.sub_scope,
        response={
            "ok": True,
            "operation": "apply",
            "target": target,
            "scope": resolved.scope,
            "sub_scope": resolved.sub_scope,
            "doc_id": document.doc_id,
            "title": document.title,
            "source_revision": requested_revision,
            "path": path,
            "deleted_doc_ids": [document.doc_id],
            "delete_count": 1,
            "generated_outputs": sub_scope_delete_generated_outputs(repo_root, resolved),
            "summary_text": f"Deleted {document.doc_id}.",
        },
        source_deletes=(SourceDelete(document.path, original_bytes=source_bytes),),
        suppression_reason="docs-sub-scope-document-delete",
        log_event_name="docs-delete",
        log_details={
            "scope": resolved.scope,
            "sub_scope": resolved.sub_scope,
            "doc_id": document.doc_id,
            "deleted_doc_ids": [document.doc_id],
            "delete_count": 1,
            "path": path,
        },
        include_write_result_keys=True,
        restore_deletes_on_rebuild_failure=True,
    )
