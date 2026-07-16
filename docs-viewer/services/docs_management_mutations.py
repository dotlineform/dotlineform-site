#!/usr/bin/env python3
"""Planning helpers for Docs Management source mutations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import docs_source_model as source_model
from docs_scope_config import load_docs_scope_configs, resolve_external_data_root


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


@dataclass(frozen=True)
class SourceDelete:
    path: Path


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
    source_writes: tuple[SourceWrite, ...] = ()
    source_deletes: tuple[SourceDelete, ...] = ()
    suppression_reason: Optional[str] = None
    build_doc_ids: Optional[list[str]] = None
    search_doc_ids: Optional[list[str]] = None
    rebuilds: tuple[ScopeRebuild, ...] = ()
    log_event_name: Optional[str] = None
    log_details: Dict[str, Any] = field(default_factory=dict)
    include_write_result_keys: bool = False

    @property
    def changed_paths(self) -> list[Path]:
        return [write.path for write in self.source_writes] + [delete.path for delete in self.source_deletes]

    @property
    def has_source_changes(self) -> bool:
        return bool(self.source_writes or self.source_deletes)


def plan_create(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    docs = source_model.load_scope_docs(repo_root, scope)
    title = str(body.get("title") or "New Doc").strip() or "New Doc"
    docs_by_id = {doc.doc_id: doc for doc in docs}
    parent_id = str(body.get("parent_id") or "").strip()

    if parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")

    timestamp = source_model.current_doc_timestamp()
    doc_id = source_model.allocate_doc_id(
        timestamp,
        {identity for doc in docs for identity in (doc.doc_id, doc.path.stem)},
    )
    target_root = source_model.scope_root(repo_root, scope)
    target_path = target_root / f"{doc_id}.md"
    front_matter = source_model.advance_doc_front_matter({
        "doc_id": doc_id,
        "title": title,
        "added_date": timestamp,
        "parent_id": parent_id,
    }, timestamp=timestamp)
    if not source_model.default_viewable_for_scope(scope):
        front_matter["viewable"] = False
    viewable = source_model.default_viewable_for_scope(scope)
    source_text = source_model.format_source(front_matter, f"# {title}\n")
    path = relative_path(repo_root, target_path)

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": doc_id,
            "path": path,
            "record": {
                "doc_id": doc_id,
                "title": title,
                "parent_id": parent_id,
                "viewable": viewable,
            },
            "summary_text": f"Created {doc_id}.",
        },
        source_writes=(SourceWrite(target_path, source_text),),
        suppression_reason="docs-create",
        build_doc_ids=[doc_id],
        search_doc_ids=[doc_id],
        log_event_name="docs-create",
        log_details={"scope": scope, "doc_id": doc_id, "path": path},
        include_write_result_keys=True,
    )


def plan_update_metadata(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")

    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    title = str(body.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")

    parent_id = str(body.get("parent_id") or "").strip()
    if parent_id == target.doc_id:
        raise ValueError("parent_id cannot be the current doc")
    if parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
    if parent_id and parent_id in source_model.descendant_doc_ids(docs, target.doc_id):
        raise ValueError("parent_id cannot be a child or descendant of the current doc")

    title_changed = title != target.title
    parent_changed = parent_id != target.parent_id
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
    ui_status = source_model.normalize_ui_status(body.get("ui_status")) if status_was_provided else current_ui_status
    status_changed = status_was_provided and ui_status != current_ui_status
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
    if not any(changes.values()):
        return ManagementMutationPlan(
            scope=scope,
            response={
                "ok": True,
                "scope": scope,
                "doc_id": target.doc_id,
                "path": relative_path(repo_root, target.path),
                "record": {
                    "doc_id": target.doc_id,
                    "title": target.title,
                    "parent_id": target.parent_id,
                    "summary": current_summary,
                    "date": current_date,
                    "date_display": current_date_display,
                    "ui_status": current_ui_status,
                    "viewable": current_viewable,
                },
                "changes": dict.fromkeys(changes.keys(), False),
                "summary_text": f"No metadata changes for {target.doc_id}.",
            },
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
    updated_front_matter["parent_id"] = parent_id
    updated_front_matter.pop("sort_order", None)
    updated_front_matter = source_model.advance_front_matter_for_recent_edit(
        target.front_matter,
        target.body,
        updated_front_matter,
        target.body,
    )

    search_doc_ids = metadata_search_doc_ids(docs, target.doc_id, title_changed=title_changed)
    if status_changed and not (title_changed or parent_changed or summary_changed or viewable_changed):
        search_doc_ids = []

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "record": {
                "doc_id": target.doc_id,
                "title": title,
                "parent_id": parent_id,
                "summary": summary,
                "date": date,
                "date_display": date_display,
                "ui_status": ui_status,
                "viewable": viewable,
            },
            "changes": changes,
            "summary_text": f"Updated metadata for {target.doc_id}.",
        },
        source_writes=(SourceWrite(target.path, source_model.format_source(updated_front_matter, target.body)),),
        suppression_reason="docs-update-metadata",
        build_doc_ids=[target.doc_id],
        search_doc_ids=search_doc_ids,
        log_event_name="docs-update-metadata",
        log_details={
            "scope": scope,
            "doc_id": target.doc_id,
            "title_changed": title_changed,
            "parent_changed": parent_changed,
            "summary_changed": summary_changed,
            "date_changed": date_changed,
            "date_display_changed": date_display_changed,
            "status_changed": status_changed,
            "viewable_changed": viewable_changed,
        },
        include_write_result_keys=True,
    )


def ordered_unique_doc_ids(raw_doc_ids: Any) -> list[str]:
    if not isinstance(raw_doc_ids, list):
        raise ValueError("doc_ids must be a list")
    doc_ids = ordered_doc_ids([str(raw_doc_id or "").strip() for raw_doc_id in raw_doc_ids])
    if not doc_ids:
        raise ValueError("doc_ids is required")
    return doc_ids


def next_viewable_from_body(body: Dict[str, Any]) -> bool:
    if "viewable" in body:
        return source_model.front_matter_boolean(body, "viewable", True)
    raise ValueError("viewable is required")


def expand_viewability_targets(
    docs: list[source_model.ScopeDoc],
    doc_ids: list[str],
    include_descendants: bool,
) -> list[source_model.ScopeDoc]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target_ids: list[str] = []
    seen: set[str] = set()

    def add_doc_id(doc_id: str) -> None:
        if doc_id not in docs_by_id:
            raise FileNotFoundError(f"doc {doc_id!r} not found")
        if doc_id in seen:
            return
        seen.add(doc_id)
        target_ids.append(doc_id)

    for doc_id in doc_ids:
        add_doc_id(doc_id)
        if include_descendants:
            for descendant_id in sorted(source_model.descendant_doc_ids(docs, doc_id)):
                add_doc_id(descendant_id)

    return [docs_by_id[doc_id] for doc_id in target_ids]


def plan_viewability_update(
    repo_root: Path,
    scope: str,
    targets: list[source_model.ScopeDoc],
    next_viewable: bool,
    *,
    operation: str,
    suppression_reason: str,
    requested_doc_ids: list[str],
    include_descendants: bool,
) -> ManagementMutationPlan:
    changed_targets = [target for target in targets if target.viewable != next_viewable]
    skipped_targets = [target for target in targets if target.viewable == next_viewable]
    changed_doc_ids = {target.doc_id for target in changed_targets}

    response = {
        "ok": True,
        "scope": scope,
        "doc_ids": [target.doc_id for target in targets],
        "changed_doc_ids": [target.doc_id for target in changed_targets],
        "skipped_doc_ids": [target.doc_id for target in skipped_targets],
        "records": [
            {
                "doc_id": target.doc_id,
                "viewable": next_viewable if target.doc_id in changed_doc_ids else target.viewable,
                "path": relative_path(repo_root, target.path),
            }
            for target in targets
        ],
        "summary_text": (
            f"Updated viewability for {len(changed_targets)} doc{'s' if len(changed_targets) != 1 else ''}."
            if changed_targets
            else f"No viewability changes for {len(targets)} doc{'s' if len(targets) != 1 else ''}."
        ),
    }

    if not changed_targets:
        return ManagementMutationPlan(scope=scope, response=response)

    return ManagementMutationPlan(
        scope=scope,
        response=response,
        source_writes=tuple(
            SourceWrite(
                target.path,
                source_model.rewrite_doc_source(
                    target,
                    {
                        "viewable": False if not next_viewable else None,
                    },
                ),
            )
            for target in changed_targets
        ),
        suppression_reason=suppression_reason,
        build_doc_ids=[target.doc_id for target in changed_targets],
        search_doc_ids=[target.doc_id for target in changed_targets],
        log_event_name=operation,
        log_details={
            "scope": scope,
            "requested_count": len(requested_doc_ids),
            "target_count": len(targets),
            "changed_count": len(changed_targets),
            "to_viewable": next_viewable,
        },
        include_write_result_keys=True,
    )


def plan_update_viewability_bulk(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_ids = ordered_unique_doc_ids(body.get("doc_ids"))
    next_viewable = next_viewable_from_body(body)
    include_descendants = bool(body.get("include_descendants"))
    docs = source_model.load_scope_docs(repo_root, scope)
    targets = expand_viewability_targets(docs, doc_ids, include_descendants)
    return plan_viewability_update(
        repo_root,
        scope,
        targets,
        next_viewable,
        operation="update-viewability-bulk",
        suppression_reason="docs-update-viewability-bulk",
        requested_doc_ids=doc_ids,
        include_descendants=include_descendants,
    )


def plan_update_viewability(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    next_viewable = next_viewable_from_body(body)
    docs = source_model.load_scope_docs(repo_root, scope)
    targets = expand_viewability_targets(docs, [doc_id], False)
    plan = plan_viewability_update(
        repo_root,
        scope,
        targets,
        next_viewable,
        operation="update-viewability",
        suppression_reason="docs-update-viewability",
        requested_doc_ids=[doc_id],
        include_descendants=False,
    )
    target = targets[0]
    response = dict(plan.response)
    response["doc_id"] = target.doc_id
    response["path"] = relative_path(repo_root, target.path)
    response["record"] = {
        "doc_id": target.doc_id,
        "viewable": next_viewable if target.viewable != next_viewable else target.viewable,
    }
    response["summary_text"] = (
        f"No viewability changes for {target.doc_id}."
        if target.viewable == next_viewable
        else f"Updated viewability for {target.doc_id}."
    )
    return ManagementMutationPlan(
        scope=plan.scope,
        response=response,
        source_writes=plan.source_writes,
        source_deletes=plan.source_deletes,
        suppression_reason=plan.suppression_reason,
        build_doc_ids=plan.build_doc_ids,
        search_doc_ids=plan.search_doc_ids,
        log_event_name=plan.log_event_name,
        log_details=plan.log_details,
        include_write_result_keys=plan.include_write_result_keys,
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


def plan_delete_preview(repo_root: Path, scope: str, doc_id: str) -> Dict[str, Any]:
    scope = source_model.normalize_scope(scope)
    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")

    children = [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "path": relative_path(repo_root, doc.path),
        }
        for doc in docs
        if doc.parent_id == target.doc_id
    ]
    blockers = []
    warnings = []
    if children:
        blockers.append(f"{len(children)} child docs still depend on this parent")
    configured_default = configured_default_doc_id(repo_root, scope)
    default_doc_id_changed = configured_default == target.doc_id

    return {
        "ok": True,
        "scope": scope,
        "doc_id": target.doc_id,
        "title": target.title,
        "path": relative_path(repo_root, target.path),
        "allowed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "children": children,
        "default_doc_id_changed": default_doc_id_changed,
        "default_doc_id": "" if default_doc_id_changed else configured_default,
    }


def plan_delete_apply(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not body.get("confirm"):
        raise ValueError("delete apply requires confirm=true")

    preview = plan_delete_preview(repo_root, scope, doc_id)
    if not preview["allowed"]:
        raise ValueError("; ".join(preview["blockers"]))

    docs = source_model.load_scope_docs(repo_root, scope)
    target = next(doc for doc in docs if doc.doc_id == doc_id)
    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "warnings": preview["warnings"],
            "default_doc_id_changed": preview["default_doc_id_changed"],
            "default_doc_id": preview["default_doc_id"],
            "summary_text": f"Deleted {target.doc_id}.",
        },
        source_deletes=(SourceDelete(target.path),),
        suppression_reason="docs-delete",
        build_doc_ids=[target.doc_id],
        search_doc_ids=[target.doc_id],
        log_event_name="docs-delete",
        log_details={
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "default_doc_id_changed": preview["default_doc_id_changed"],
        },
        include_write_result_keys=True,
    )
