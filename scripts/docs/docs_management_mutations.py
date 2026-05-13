#!/usr/bin/env python3
"""Planning helpers for Docs Management source mutations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import docs_source_model as source_model


def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def normalize_summary(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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
class ManagementMutationPlan:
    scope: str
    response: Dict[str, Any]
    backup_operation: Optional[str] = None
    backup_docs: tuple[source_model.ScopeDoc, ...] = ()
    backup_metadata: Optional[Dict[str, Any]] = None
    source_writes: tuple[SourceWrite, ...] = ()
    source_deletes: tuple[SourceDelete, ...] = ()
    suppression_reason: Optional[str] = None
    search_doc_ids: Optional[list[str]] = None
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
    raw_sort_order = body.get("sort_order")
    after_doc_id = str(body.get("after_doc_id") or "").strip()
    parent_id = str(body.get("parent_id") or "").strip()

    if after_doc_id:
        after_doc = docs_by_id.get(after_doc_id)
        if after_doc is None:
            raise ValueError(f"Unknown after_doc_id {after_doc_id!r} for scope {scope}")
        parent_id = after_doc.parent_id
        sort_order = source_model.create_sort_order_after(docs, after_doc)
    elif parent_id and parent_id not in docs_by_id:
        raise ValueError(f"Unknown parent_id {parent_id!r} for scope {scope}")
    elif raw_sort_order in {None, ""}:
        sort_order = source_model.next_sort_order(docs, parent_id)
    else:
        try:
            sort_order = int(raw_sort_order)
        except (TypeError, ValueError) as exc:
            raise ValueError("sort_order must be an integer") from exc

    doc_id = source_model.ensure_unique_stem(docs, title)
    target_root = source_model.scope_root(repo_root, scope)
    target_path = target_root / f"{doc_id}.md"
    timestamp = source_model.current_doc_timestamp()
    front_matter = {
        "doc_id": doc_id,
        "title": title,
        "added_date": timestamp,
        "last_updated": timestamp,
        "parent_id": parent_id,
        "sort_order": sort_order,
        "published": True,
        "hidden": source_model.default_hidden_for_scope(scope),
    }
    hidden = source_model.default_hidden_for_scope(scope)
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
                "sort_order": sort_order,
                "published": True,
                "hidden": hidden,
                "viewable": not hidden,
            },
            "summary_text": f"Created {doc_id}.",
        },
        backup_operation="create",
        backup_metadata={
            "doc_id": doc_id,
            "title": title,
            "path": path,
            "parent_id": parent_id,
            "sort_order": sort_order,
            "after_doc_id": after_doc_id,
        },
        source_writes=(SourceWrite(target_path, source_text),),
        suppression_reason="docs-create",
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

    raw_sort_order = body.get("sort_order")
    raw_sort_order_text = "" if raw_sort_order is None else str(raw_sort_order).strip()
    if raw_sort_order_text.lower() == "append":
        remaining_docs = [doc for doc in docs if doc.doc_id != target.doc_id]
        sort_order = source_model.next_sort_order(remaining_docs, parent_id)
    elif raw_sort_order_text == "":
        sort_order = None
    else:
        try:
            sort_order = int(raw_sort_order_text)
        except (TypeError, ValueError) as exc:
            raise ValueError("sort_order must be an integer, blank, or append") from exc
        if sort_order < 0:
            raise ValueError("sort_order must be zero or greater")

    title_changed = title != target.title
    parent_changed = parent_id != target.parent_id
    sort_changed = sort_order != target.sort_order
    summary_was_provided = "summary" in body
    current_summary = normalize_summary(target.front_matter.get("summary"))
    summary = normalize_summary(body.get("summary")) if summary_was_provided else current_summary
    summary_changed = summary_was_provided and summary != current_summary
    status_was_provided = "ui_status" in body
    current_ui_status = source_model.normalize_ui_status(target.front_matter.get("ui_status"))
    ui_status = source_model.normalize_ui_status(body.get("ui_status")) if status_was_provided else current_ui_status
    status_changed = status_was_provided and ui_status != current_ui_status
    hidden_was_provided = "hidden" in body
    viewable_was_provided = "viewable" in body
    hidden_or_viewable_was_provided = hidden_was_provided or viewable_was_provided
    current_hidden = target.hidden
    current_viewable = target.viewable
    if hidden_was_provided:
        hidden = source_model.front_matter_boolean(body, "hidden", False)
    elif viewable_was_provided:
        hidden = not source_model.front_matter_boolean(body, "viewable", True)
    else:
        hidden = current_hidden
    viewable = not hidden
    hidden_changed = hidden_or_viewable_was_provided and hidden != current_hidden
    viewable_changed = hidden_changed
    changes = {
        "title_changed": title_changed,
        "parent_changed": parent_changed,
        "sort_changed": sort_changed,
        "summary_changed": summary_changed,
        "status_changed": status_changed,
        "hidden_changed": hidden_changed,
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
                    "sort_order": target.sort_order,
                    "summary": current_summary,
                    "ui_status": current_ui_status,
                    "hidden": current_hidden,
                    "viewable": current_viewable,
                },
                "changes": dict.fromkeys(changes.keys(), False),
                "summary_text": f"No metadata changes for {target.doc_id}.",
            },
        )

    timestamp = source_model.current_doc_timestamp()
    updated_front_matter = dict(target.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
    ).strip()
    updated_front_matter["title"] = title
    if summary_was_provided:
        if summary:
            updated_front_matter["summary"] = summary
        else:
            updated_front_matter.pop("summary", None)
    if status_was_provided:
        if ui_status:
            updated_front_matter["ui_status"] = ui_status
        else:
            updated_front_matter.pop("ui_status", None)
    if hidden_or_viewable_was_provided:
        updated_front_matter["hidden"] = hidden
        updated_front_matter.pop("viewable", None)
    updated_front_matter["parent_id"] = parent_id
    if sort_order is None:
        updated_front_matter.pop("sort_order", None)
    else:
        updated_front_matter["sort_order"] = sort_order

    search_doc_ids = metadata_search_doc_ids(docs, target.doc_id, title_changed=title_changed)
    if status_changed and not (title_changed or parent_changed or sort_changed or summary_changed or viewable_changed):
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
                "sort_order": sort_order,
                "summary": summary,
                "ui_status": ui_status,
                "hidden": hidden,
                "viewable": viewable,
            },
            "changes": changes,
            "summary_text": f"Updated metadata for {target.doc_id}.",
        },
        backup_operation="update-metadata",
        backup_docs=(target,),
        backup_metadata={
            "doc_id": target.doc_id,
            "from_title": target.title,
            "to_title": title,
            "from_parent_id": target.parent_id,
            "to_parent_id": parent_id,
            "from_sort_order": target.sort_order,
            "to_sort_order": sort_order,
            "summary_changed": summary_changed,
            "status_changed": status_changed,
            "hidden_changed": hidden_changed,
            "viewable_changed": viewable_changed,
        },
        source_writes=(SourceWrite(target.path, source_model.format_source(updated_front_matter, target.body)),),
        suppression_reason="docs-update-metadata",
        search_doc_ids=search_doc_ids,
        log_event_name="docs-update-metadata",
        log_details={
            "scope": scope,
            "doc_id": target.doc_id,
            "title_changed": title_changed,
            "parent_changed": parent_changed,
            "sort_changed": sort_changed,
            "summary_changed": summary_changed,
            "status_changed": status_changed,
            "hidden_changed": hidden_changed,
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
    if "hidden" in body:
        return not source_model.front_matter_boolean(body, "hidden", False)
    if "viewable" in body:
        return source_model.front_matter_boolean(body, "viewable", True)
    raise ValueError("hidden or viewable is required")


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
    next_hidden = not next_viewable
    changed_targets = [target for target in targets if target.hidden != next_hidden]
    skipped_targets = [target for target in targets if target.hidden == next_hidden]
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
                "hidden": next_hidden if target.doc_id in changed_doc_ids else target.hidden,
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
        backup_operation=operation,
        backup_docs=tuple(changed_targets),
        backup_metadata={
            "requested_doc_ids": requested_doc_ids,
            "include_descendants": include_descendants,
            "target_doc_ids": [target.doc_id for target in targets],
            "changed_doc_ids": [target.doc_id for target in changed_targets],
            "skipped_doc_ids": [target.doc_id for target in skipped_targets],
            "to_hidden": next_hidden,
            "to_viewable": next_viewable,
        },
        source_writes=tuple(
            SourceWrite(
                target.path,
                source_model.rewrite_doc_source(target, {"published": True, "hidden": next_hidden, "viewable": None}),
            )
            for target in changed_targets
        ),
        suppression_reason=suppression_reason,
        search_doc_ids=[target.doc_id for target in changed_targets],
        log_event_name=operation,
        log_details={
            "scope": scope,
            "requested_count": len(requested_doc_ids),
            "target_count": len(targets),
            "changed_count": len(changed_targets),
            "to_hidden": next_hidden,
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
        "hidden": not next_viewable if target.viewable != next_viewable else target.hidden,
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
        backup_operation=plan.backup_operation,
        backup_docs=plan.backup_docs,
        backup_metadata=plan.backup_metadata,
        source_writes=plan.source_writes,
        source_deletes=plan.source_deletes,
        suppression_reason=plan.suppression_reason,
        search_doc_ids=plan.search_doc_ids,
        log_event_name=plan.log_event_name,
        log_details=plan.log_details,
        include_write_result_keys=plan.include_write_result_keys,
    )


def plan_move(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    target_doc_id = str(body.get("target_doc_id") or "").strip()
    position = str(body.get("position") or "after").strip().lower()
    if not doc_id:
        raise ValueError("doc_id is required")
    if not target_doc_id:
        raise ValueError("target_doc_id is required")
    if position not in {"after", "inside"}:
        raise ValueError("position must be `after` or `inside`")

    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    moving_doc = docs_by_id.get(doc_id)
    target_doc = docs_by_id.get(target_doc_id)
    if moving_doc is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if target_doc is None:
        raise FileNotFoundError(f"target_doc_id {target_doc_id!r} not found in scope {scope}")
    if moving_doc.doc_id == target_doc.doc_id:
        raise ValueError("doc cannot be moved onto itself")
    if any(doc.parent_id == moving_doc.doc_id for doc in docs):
        raise ValueError(f"{moving_doc.doc_id} has child docs and cannot be moved")

    planned_placements = source_model.normalized_move_placements(docs, moving_doc, target_doc, position)
    changed_placements = [
        (doc, parent_id, sort_order)
        for doc, parent_id, sort_order in planned_placements
        if doc.parent_id != parent_id or doc.sort_order != sort_order
    ]
    undo_records = [source_model.placement_record(doc) for doc, _parent_id, _sort_order in changed_placements]
    touched_docs = [doc for doc, _parent_id, _sort_order in changed_placements]
    moved_parent_id = next(parent_id for doc, parent_id, _sort_order in planned_placements if doc.doc_id == moving_doc.doc_id)
    moved_sort_order = next(sort_order for doc, _parent_id, sort_order in planned_placements if doc.doc_id == moving_doc.doc_id)

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": moving_doc.doc_id,
            "record": {
                "doc_id": moving_doc.doc_id,
                "parent_id": moved_parent_id,
                "sort_order": moved_sort_order,
            },
            "undo_records": undo_records,
            "changed_doc_ids": [doc.doc_id for doc in touched_docs],
            "summary_text": f"Moved {moving_doc.doc_id}.",
        },
        backup_operation="move" if touched_docs else None,
        backup_docs=tuple(touched_docs),
        backup_metadata={
            "doc_id": moving_doc.doc_id,
            "target_doc_id": target_doc.doc_id,
            "position": position,
            "parent_id": moved_parent_id,
            "sort_order": moved_sort_order,
            "changed_doc_ids": [doc.doc_id for doc in touched_docs],
            "undo_records": undo_records,
        }
        if touched_docs
        else None,
        source_writes=tuple(
            SourceWrite(doc.path, source_model.rewrite_doc_placement_source(doc, parent_id, sort_order))
            for doc, parent_id, sort_order in changed_placements
        ),
        suppression_reason="docs-move",
        search_doc_ids=[moving_doc.doc_id],
        log_event_name="docs-move" if touched_docs else None,
        log_details={
            "scope": scope,
            "doc_id": moving_doc.doc_id,
            "target_doc_id": target_doc.doc_id,
            "position": position,
            "parent_id": moved_parent_id,
            "sort_order": moved_sort_order,
            "changed_count": len(touched_docs),
        },
        include_write_result_keys=True,
    )


def parse_restore_sort_order(raw_sort_order: Any) -> Optional[int]:
    if raw_sort_order is None or raw_sort_order == "":
        return None
    try:
        sort_order = int(str(raw_sort_order).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("restore sort_order must be an integer or blank") from exc
    if sort_order < 0:
        raise ValueError("restore sort_order must be zero or greater")
    return sort_order


def plan_restore_move(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    raw_records = body.get("records")
    if not isinstance(raw_records, list) or not raw_records:
        raise ValueError("records must be a non-empty list")

    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    restore_records: list[tuple[source_model.ScopeDoc, str, Optional[int]]] = []
    seen_doc_ids: set[str] = set()
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise ValueError("each restore record must be an object")
        doc_id = str(raw_record.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError("restore record doc_id is required")
        if doc_id in seen_doc_ids:
            continue
        seen_doc_ids.add(doc_id)
        doc = docs_by_id.get(doc_id)
        if doc is None:
            raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")

        parent_id = str(raw_record.get("parent_id") or "").strip()
        if parent_id == doc.doc_id:
            raise ValueError("restore parent_id cannot be the current doc")
        if parent_id and parent_id not in docs_by_id:
            raise ValueError(f"Unknown restore parent_id {parent_id!r} for scope {scope}")
        if parent_id and parent_id in source_model.descendant_doc_ids(docs, doc.doc_id):
            raise ValueError("restore parent_id cannot be a child or descendant of the current doc")
        sort_order = parse_restore_sort_order(raw_record.get("sort_order"))
        restore_records.append((doc, parent_id, sort_order))

    changed_records = [
        (doc, parent_id, sort_order)
        for doc, parent_id, sort_order in restore_records
        if doc.parent_id != parent_id or doc.sort_order != sort_order
    ]
    touched_docs = [doc for doc, _parent_id, _sort_order in changed_records]
    focus_doc_id = str(body.get("focus_doc_id") or "").strip()
    if focus_doc_id and focus_doc_id not in docs_by_id:
        focus_doc_id = ""

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": focus_doc_id or (restore_records[0][0].doc_id if restore_records else ""),
            "changed_doc_ids": [doc.doc_id for doc in touched_docs],
            "records": [
                {"doc_id": doc.doc_id, "parent_id": parent_id, "sort_order": sort_order}
                for doc, parent_id, sort_order in restore_records
            ],
            "summary_text": (
                f"Restored move for {len(touched_docs)} doc{'s' if len(touched_docs) != 1 else ''}."
                if touched_docs
                else "Move already restored."
            ),
        },
        backup_operation="restore-move" if touched_docs else None,
        backup_docs=tuple(touched_docs),
        backup_metadata={
            "changed_doc_ids": [doc.doc_id for doc in touched_docs],
            "restore_records": [
                {"doc_id": doc.doc_id, "parent_id": parent_id, "sort_order": sort_order}
                for doc, parent_id, sort_order in changed_records
            ],
        }
        if touched_docs
        else None,
        source_writes=tuple(
            SourceWrite(doc.path, source_model.rewrite_doc_placement_source(doc, parent_id, sort_order))
            for doc, parent_id, sort_order in changed_records
        ),
        suppression_reason="docs-restore-move",
        search_doc_ids=[doc.doc_id for doc in touched_docs],
        log_event_name="docs-restore-move" if touched_docs else None,
        log_details={
            "scope": scope,
            "changed_count": len(touched_docs),
            "changed_doc_ids": [doc.doc_id for doc in touched_docs],
        },
        include_write_result_keys=True,
    )


def plan_archive(repo_root: Path, body: Dict[str, Any]) -> ManagementMutationPlan:
    scope = source_model.normalize_scope(body.get("scope"))
    doc_id = str(body.get("doc_id") or "").strip()
    if not doc_id:
        raise ValueError("doc_id is required")

    docs = source_model.load_scope_docs(repo_root, scope)
    docs_by_id = {doc.doc_id: doc for doc in docs}
    target = docs_by_id.get(doc_id)
    if target is None:
        raise FileNotFoundError(f"doc {doc_id!r} not found in scope {scope}")
    if "archive" not in docs_by_id:
        raise ValueError(f"scope {scope} does not define archive doc")
    if target.doc_id == "archive":
        return ManagementMutationPlan(
            scope=scope,
            response={
                "ok": True,
                "scope": scope,
                "doc_id": target.doc_id,
                "path": relative_path(repo_root, target.path),
                "summary_text": "archive is the archive parent and was not changed.",
            },
        )
    if target.parent_id == "archive":
        return ManagementMutationPlan(
            scope=scope,
            response={
                "ok": True,
                "scope": scope,
                "doc_id": target.doc_id,
                "path": relative_path(repo_root, target.path),
                "summary_text": f"{target.doc_id} is already archived.",
            },
        )

    next_order = source_model.next_sort_order(docs, "archive")
    timestamp = source_model.current_doc_timestamp()
    updated_front_matter = dict(target.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
    ).strip()
    updated_front_matter["parent_id"] = "archive"
    updated_front_matter["sort_order"] = next_order

    return ManagementMutationPlan(
        scope=scope,
        response={
            "ok": True,
            "scope": scope,
            "doc_id": target.doc_id,
            "path": relative_path(repo_root, target.path),
            "record": {
                "parent_id": "archive",
                "sort_order": next_order,
            },
            "summary_text": f"Archived {target.doc_id}.",
        },
        backup_operation="archive",
        backup_docs=(target,),
        backup_metadata={
            "doc_id": target.doc_id,
            "from_parent_id": target.parent_id,
            "to_parent_id": "archive",
            "from_sort_order": target.sort_order,
            "to_sort_order": next_order,
        },
        source_writes=(SourceWrite(target.path, source_model.format_source(updated_front_matter, target.body)),),
        suppression_reason="docs-archive",
        search_doc_ids=[target.doc_id],
        log_event_name="docs-archive",
        log_details={"scope": scope, "doc_id": target.doc_id, "path": relative_path(repo_root, target.path)},
        include_write_result_keys=True,
    )


def find_inbound_refs(
    repo_root: Path,
    target: source_model.ScopeDoc,
    docs: list[source_model.ScopeDoc],
) -> list[Dict[str, str]]:
    target_filename = target.path.name
    doc_link_fragment = f"doc={target.doc_id}"
    refs: list[Dict[str, str]] = []
    for doc in docs:
        if doc.doc_id == target.doc_id:
            continue
        source = doc.source_text
        if doc_link_fragment not in source and target_filename not in source:
            continue
        refs.append(
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "path": relative_path(repo_root, doc.path),
            }
        )
    refs.sort(key=lambda item: (item["title"].lower(), item["doc_id"]))
    return refs


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
    inbound_refs = find_inbound_refs(repo_root, target, docs)
    blockers = []
    warnings = []
    if children:
        blockers.append(f"{len(children)} child docs still depend on this parent")
    if inbound_refs:
        warnings.append(f"{len(inbound_refs)} inbound markdown references will become broken")

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
        "inbound_refs": inbound_refs,
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
            "inbound_refs": preview["inbound_refs"],
            "summary_text": f"Deleted {target.doc_id}.",
        },
        backup_operation="delete",
        backup_docs=(target,),
        backup_metadata={
            "doc_id": target.doc_id,
            "warnings": preview["warnings"],
            "inbound_ref_count": len(preview["inbound_refs"]),
        },
        source_deletes=(SourceDelete(target.path),),
        suppression_reason="docs-delete",
        search_doc_ids=[target.doc_id],
        log_event_name="docs-delete",
        log_details={"scope": scope, "doc_id": target.doc_id, "path": relative_path(repo_root, target.path)},
        include_write_result_keys=True,
    )
