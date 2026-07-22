#!/usr/bin/env python3
"""Wrapper-neutral, write-free planning for Docs Import collections."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from docs_import_content import CONTENT_INTENT_REPLACE, ImportContent
from docs_import_document import (
    IMPORT_DOCUMENT_CREATE,
    IMPORT_DOCUMENT_OVERWRITE,
    ImportDocumentPlan,
    plan_import_document,
)
from docs_import_preview import generate_normalized_import_content_preview
from docs_import_source_helpers import relative_path
from docs_source_model import (
    ScopeDoc,
    allocate_doc_id,
    current_doc_timestamp,
    doc_id_matches_added_date,
    is_immutable_doc_id,
)
from docs_document_packages.workspace import marker_path


MEDIA_PLAN_FIELDS = (
    "source",
    "source_path",
    "staging_path",
    "media_path",
    "media_token",
    "served_reference",
    "location_provider",
    "artifact_identity",
    "media_class",
    "kind",
    "mime_type",
    "size_bytes",
    "title",
)
DECLARED_ASSET_FIELDS = (
    "asset_id",
    "kind",
    "package_path",
    "source_token",
    "sha256",
)


@dataclass
class CollectionRecordState:
    """One wrapper record as it moves through collection planning."""

    record_index: int
    raw: Any
    doc_id: str = ""
    source_doc_id: str = ""
    create_added_date: str = ""
    title: str = ""
    parent_id: str = ""
    normalized: ImportContent | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    blocked: bool = False
    collision: ScopeDoc | None = None
    document_plan: ImportDocumentPlan | None = None
    import_preview: dict[str, Any] = field(default_factory=dict)
    parent_resolution: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentsCollectionPlan:
    """Internal plans plus a safe body-free API projection."""

    normalized_records: tuple[ImportContent | None, ...]
    document_plans: tuple[ImportDocumentPlan | None, ...]
    response: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self.response)


def collection_issue(
    level: str,
    code: str,
    message: str,
    *,
    record_index: int | None = None,
    doc_id: str = "",
) -> dict[str, Any]:
    item: dict[str, Any] = {"level": level, "code": code, "message": message}
    if record_index is not None:
        item["record_index"] = record_index
    if doc_id:
        item["doc_id"] = doc_id
    return item


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _sanitize_issue_paths(items: list[dict[str, Any]], workspace_root: Path) -> list[dict[str, Any]]:
    workspace_path = str(workspace_root.resolve())
    workspace_marker = marker_path(workspace_root, workspace_root=workspace_root)
    sanitized = copy.deepcopy(items)
    for item in sanitized:
        message = item.get("message")
        if isinstance(message, str):
            item["message"] = message.replace(workspace_path, workspace_marker)
    return sanitized


def _collision_for(record: ImportContent, docs: list[ScopeDoc]) -> ScopeDoc | None:
    return next(
        (doc for doc in docs if doc.doc_id == record.doc_id or doc.path.stem == record.doc_id),
        None,
    )


def _prepare_local_create_identities(
    states: list[CollectionRecordState],
    docs: list[ScopeDoc],
    planned_identities: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    supplied: dict[int, dict[str, Any]] = {}
    if planned_identities is not None:
        if not isinstance(planned_identities, list):
            raise ValueError("planned_identities must be an array")
        for item in planned_identities:
            if not isinstance(item, dict):
                raise ValueError("each planned identity must be an object")
            if set(item) != {"record_index", "source_doc_id", "doc_id", "added_date"}:
                raise ValueError(
                    "planned identity fields must be record_index, source_doc_id, doc_id, added_date"
                )
            index = item.get("record_index")
            if not isinstance(index, int) or isinstance(index, bool) or index < 0:
                raise ValueError("planned identity record_index must be a non-negative integer")
            if index in supplied:
                raise ValueError(f"duplicate planned identity for record_index {index}")
            supplied[index] = item

    unavailable = {identity for doc in docs for identity in (doc.doc_id, doc.path.stem)}
    source_to_local: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    planned_create_indices: set[int] = set()
    for state in states:
        record = state.normalized
        state.source_doc_id = state.doc_id
        if record is None or state.blocked or state.errors:
            continue
        state.collision = _collision_for(record, docs)
        if state.collision is not None:
            continue
        planned_create_indices.add(state.record_index)
        supplied_row = supplied.get(state.record_index)
        if supplied_row is None:
            added_date = current_doc_timestamp()
            local_doc_id = allocate_doc_id(added_date, unavailable)
        else:
            if _clean_text(supplied_row.get("source_doc_id")) != state.source_doc_id:
                raise ValueError(
                    f"planned identity source_doc_id changed for record_index {state.record_index}"
                )
            added_date = _clean_text(supplied_row.get("added_date"))
            local_doc_id = _clean_text(supplied_row.get("doc_id"))
            if not is_immutable_doc_id(local_doc_id) or not doc_id_matches_added_date(
                local_doc_id,
                added_date,
            ):
                raise ValueError(
                    f"planned identity is invalid for record_index {state.record_index}"
                )
            if local_doc_id in unavailable:
                raise ValueError(
                    f"planned identity collides for record_index {state.record_index}"
                )
        unavailable.add(local_doc_id)
        source_to_local[state.source_doc_id] = local_doc_id
        state.create_added_date = added_date
        rows.append(
            {
                "record_index": state.record_index,
                "source_doc_id": state.source_doc_id,
                "doc_id": local_doc_id,
                "added_date": added_date,
            }
        )

    unknown_indices = sorted(set(supplied) - planned_create_indices)
    if unknown_indices:
        raise ValueError(
            "planned identities reference records that are no longer creates: "
            + ", ".join(str(index) for index in unknown_indices)
        )

    for state in states:
        record = state.normalized
        local_doc_id = source_to_local.get(state.source_doc_id)
        if record is None:
            continue
        parent_id = source_to_local.get(record.parent_id, record.parent_id)
        front_matter = copy.deepcopy(record.front_matter)
        if "parent_id" in front_matter:
            front_matter["parent_id"] = parent_id
        provenance = copy.deepcopy(record.provenance)
        if local_doc_id is not None:
            provenance["source_doc_id"] = state.source_doc_id
        state.normalized = replace(
            record,
            doc_id=local_doc_id or record.doc_id,
            parent_id=parent_id,
            front_matter=front_matter,
            provenance=provenance,
        )
        if local_doc_id is not None:
            state.doc_id = local_doc_id
        state.parent_id = parent_id
    return rows


def _collision_payload(repo_root: Path, target: ScopeDoc | None) -> dict[str, Any]:
    if target is None:
        return {"exists": False, "doc_id": "", "title": "", "path": "", "stem": ""}
    return {
        "exists": True,
        "doc_id": target.doc_id,
        "title": target.title,
        "path": relative_path(repo_root, target.path),
        "stem": target.path.stem,
    }


def _safe_media_plans(preview: dict[str, Any]) -> list[dict[str, Any]]:
    raw_plans: list[Any] = []
    if isinstance(preview.get("media_plans"), list):
        raw_plans.extend(preview["media_plans"])
    if isinstance(preview.get("media_plan"), dict):
        raw_plans.append(preview["media_plan"])
    return [
        {
            key: copy.deepcopy(plan[key])
            for key in MEDIA_PLAN_FIELDS
            if key in plan
        }
        for plan in raw_plans
        if isinstance(plan, dict)
    ]


def _declared_asset_plans(
    record: ImportContent,
    record_index: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    plans: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for asset in record.assets:
        plan = {
            key: copy.deepcopy(asset[key])
            for key in DECLARED_ASSET_FIELDS
            if key in asset
        }
        plan["status"] = "mapping-required"
        plans.append(plan)
        warnings.append(
            collection_issue(
                "warning",
                "declared_asset_mapping_required",
                "Declared package asset has no authorized materialization mapping; its source reference will be preserved.",
                record_index=record_index,
                doc_id=record.doc_id,
            )
        )
    return plans, warnings


def _plan_document_candidates(
    repo_root: Path,
    scope: str,
    states: list[CollectionRecordState],
    docs: list[ScopeDoc],
    *,
    staging_root: Path,
    workspace_root: Path,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for state in states:
        record = state.normalized
        if record is None:
            continue
        collision = state.collision
        if collision is not None and collision.doc_id != record.doc_id:
            state.blocked = True
            blockers.append(
                collection_issue(
                    "error",
                    "collision_target_identity_mismatch",
                    (
                        f"record {record.doc_id!r} collides with filename {collision.path.name!r} "
                        f"owned by doc_id {collision.doc_id!r}"
                    ),
                    record_index=state.record_index,
                    doc_id=record.doc_id,
                )
            )
            continue
        preview: dict[str, Any] = {}
        if record.content_intent == CONTENT_INTENT_REPLACE:
            try:
                preview = generate_normalized_import_content_preview(
                    record,
                    repo_root=repo_root,
                    scope=scope,
                    staging_root=staging_root,
                    workspace_root=workspace_root,
                )
            except (RuntimeError, ValueError) as exc:
                state.errors.append(
                    collection_issue(
                        "error",
                        "invalid_record_content",
                        str(exc),
                        record_index=state.record_index,
                        doc_id=record.doc_id,
                    )
                )
                continue
            for warning_text in preview.get("warnings") or []:
                state.warnings.append(
                    collection_issue(
                        "warning",
                        "content_warning",
                        _clean_text(warning_text),
                        record_index=state.record_index,
                        doc_id=record.doc_id,
                    )
                )
        state.import_preview = preview
        operation = IMPORT_DOCUMENT_OVERWRITE if collision is not None else IMPORT_DOCUMENT_CREATE
        try:
            state.document_plan = plan_import_document(
                repo_root,
                scope,
                record,
                operation=operation,
                docs=docs,
                target=collision,
                import_preview=preview if record.content_intent == CONTENT_INTENT_REPLACE else None,
                create_doc_id=record.doc_id if collision is None else "",
                create_added_date=state.create_added_date if collision is None else "",
            )
            state.parent_id = state.document_plan.parent_id
        except ValueError as exc:
            state.errors.append(
                collection_issue(
                    "error",
                    "invalid_front_matter",
                    str(exc),
                    record_index=state.record_index,
                    doc_id=record.doc_id,
                )
            )
    return blockers


def _parent_resolution(
    state: CollectionRecordState,
    *,
    existing_docs_by_id: dict[str, ScopeDoc],
    package_states_by_id: dict[str, CollectionRecordState],
) -> dict[str, Any]:
    parent_id = state.parent_id
    if not parent_id:
        return {"parent_id": "", "resolution": "root", "record_index": None}
    if parent_id in existing_docs_by_id:
        return {"parent_id": parent_id, "resolution": "existing", "record_index": None}
    parent_state = package_states_by_id.get(parent_id)
    if parent_state is not None:
        return {
            "parent_id": parent_id,
            "resolution": "package-create",
            "record_index": parent_state.record_index,
        }
    return {"parent_id": parent_id, "resolution": "missing", "record_index": None}


def _validate_hierarchy(
    states: list[CollectionRecordState],
    docs: list[ScopeDoc],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []
    existing_docs_by_id = {doc.doc_id: doc for doc in docs}
    package_states_by_id = {
        state.doc_id: state
        for state in states
        if state.doc_id and isinstance(state.raw, dict)
    }
    valid_states = [
        state
        for state in states
        if not state.blocked and not state.errors and state.doc_id
    ]
    for state in states:
        state.parent_resolution = _parent_resolution(
            state,
            existing_docs_by_id=existing_docs_by_id,
            package_states_by_id=package_states_by_id,
        )
        if state.blocked or state.errors or not state.doc_id:
            continue
        resolution = state.parent_resolution
        if resolution["resolution"] == "missing":
            blockers.append(
                collection_issue(
                    "error",
                    "missing_parent",
                    f"parent_id {state.parent_id!r} is not an existing or package document",
                    record_index=state.record_index,
                    doc_id=state.doc_id,
                )
            )
        elif resolution["resolution"] == "package-create":
            parent_state = package_states_by_id[state.parent_id]
            if parent_state.blocked or parent_state.errors:
                blockers.append(
                    collection_issue(
                        "error",
                        "parent_record_requires_resolution",
                        f"parent record {state.parent_id!r} has a record-level error",
                        record_index=state.record_index,
                        doc_id=state.doc_id,
                    )
                )
            else:
                dependencies.append(
                    {
                        "doc_id": state.doc_id,
                        "record_index": state.record_index,
                        "parent_id": state.parent_id,
                        "parent_record_index": parent_state.record_index,
                    }
                )

    parent_map = {doc.doc_id: doc.parent_id for doc in docs}
    for state in valid_states:
        record = state.normalized
        if record is None:
            continue
        if state.collision is not None and "parent_id" not in record.front_matter:
            parent_map[record.doc_id] = state.collision.parent_id
        else:
            parent_map[record.doc_id] = record.parent_id
    reported_cycles: set[tuple[str, ...]] = set()
    for state in valid_states:
        visited: list[str] = []
        current = state.doc_id
        while current:
            if current in visited:
                cycle = visited[visited.index(current):]
                cycle_key = tuple(sorted(cycle))
                if cycle_key not in reported_cycles:
                    reported_cycles.add(cycle_key)
                    blockers.append(
                        collection_issue(
                            "error",
                            "hierarchy_cycle",
                            "planned hierarchy contains a cycle: " + " -> ".join([*cycle, current]),
                            record_index=state.record_index,
                            doc_id=state.doc_id,
                        )
                    )
                break
            visited.append(current)
            current = parent_map.get(current, "")
    return blockers, dependencies


def _record_response(repo_root: Path, state: CollectionRecordState) -> dict[str, Any]:
    record = state.normalized
    errors = copy.deepcopy(state.errors)
    if state.blocked or record is None or errors:
        action = "blocked"
    elif state.collision is not None:
        action = IMPORT_DOCUMENT_OVERWRITE
    else:
        action = IMPORT_DOCUMENT_CREATE
    media_plans = _safe_media_plans(state.import_preview)
    declared_asset_plans: list[dict[str, Any]] = []
    if record is not None:
        declared_asset_plans, asset_warnings = _declared_asset_plans(record, state.record_index)
        state.warnings.extend(asset_warnings)
    target_path = (
        relative_path(repo_root, state.document_plan.target_path)
        if state.document_plan is not None
        else ""
    )
    return {
        "record_index": state.record_index,
        "record_identity": record.record_identity if record is not None else "",
        "doc_id": state.doc_id,
        "source_doc_id": state.source_doc_id,
        "added_date": state.create_added_date,
        "title": state.title,
        "content_intent": record.content_intent if record is not None else "unknown",
        "action": action,
        "collision": _collision_payload(repo_root, state.collision),
        "target_path": target_path,
        "parent": copy.deepcopy(state.parent_resolution),
        "link_count": len(record.links) if record is not None else 0,
        "media_plans": media_plans,
        "declared_asset_plans": declared_asset_plans,
        "warnings": copy.deepcopy(state.warnings),
        "errors": errors,
    }


def blocked_collection_plan(
    *,
    source_format: str,
    scope: str,
    staged_filename: str,
    blockers: list[dict[str, Any]],
    workspace_root: Path,
) -> DocumentsCollectionPlan:
    safe_blockers = _sanitize_issue_paths(blockers, workspace_root)
    response = {
        "ok": True,
        "plan_valid": False,
        "collection": True,
        "source_format": source_format,
        "scope": scope,
        "staged_filename": staged_filename,
        "preview_only": True,
        "ready_for_confirmation": False,
        "package": {},
        "planned_identities": [],
        "planned_actions": [],
        "records": [],
        "new_parent_dependencies": [],
        "blockers": safe_blockers,
        "warnings": [],
        "counts": {
            "records": 0,
            "creates": 0,
            "collisions": 0,
            "record_errors": 0,
            "media_plans": 0,
            "warnings": 0,
            "blockers": len(safe_blockers),
        },
    }
    return DocumentsCollectionPlan(normalized_records=(), document_plans=(), response=response)


def plan_import_content_collection(
    repo_root: Path,
    *,
    source_format: str,
    scope: str,
    staged_filename: str,
    states: list[CollectionRecordState],
    docs: list[ScopeDoc],
    staging_root: Path,
    workspace_root: Path,
    package_projection: dict[str, Any],
    blockers: list[dict[str, Any]],
    planned_identities: list[dict[str, Any]] | None = None,
) -> DocumentsCollectionPlan:
    """Complete a body-free collection plan from wrapper-normalized states."""

    identity_rows = _prepare_local_create_identities(states, docs, planned_identities)
    blockers.extend(
        _plan_document_candidates(
            repo_root,
            scope,
            states,
            docs,
            staging_root=staging_root,
            workspace_root=workspace_root,
        )
    )
    hierarchy_blockers, dependencies = _validate_hierarchy(states, docs)
    blockers.extend(hierarchy_blockers)
    record_responses = [_record_response(repo_root, state) for state in states]
    for record_response in record_responses:
        blockers.extend(copy.deepcopy(record_response["errors"]))
    blockers = _sanitize_issue_paths(blockers, workspace_root)
    for record_response in record_responses:
        record_response["warnings"] = _sanitize_issue_paths(
            record_response["warnings"],
            workspace_root,
        )
        record_response["errors"] = _sanitize_issue_paths(
            record_response["errors"],
            workspace_root,
        )
    package_warnings: list[dict[str, Any]] = []
    record_error_count = sum(bool(record["errors"]) for record in record_responses)
    collision_count = sum(bool(record["collision"]["exists"]) for record in record_responses)
    create_count = sum(record["action"] == "create" for record in record_responses)
    media_plan_count = sum(len(record["media_plans"]) for record in record_responses)
    warning_count = len(package_warnings) + sum(len(record["warnings"]) for record in record_responses)
    planned_actions = [
        {
            "record_index": record["record_index"],
            "action": record["action"],
            "doc_id": record["doc_id"],
            "target_doc_id": (
                record["collision"]["doc_id"]
                if record["action"] == IMPORT_DOCUMENT_OVERWRITE
                else ""
            ),
        }
        for record in record_responses
        if record["action"] in {IMPORT_DOCUMENT_CREATE, IMPORT_DOCUMENT_OVERWRITE}
    ]
    response = {
        "ok": True,
        "plan_valid": not blockers,
        "collection": True,
        "source_format": source_format,
        "scope": scope,
        "staged_filename": staged_filename,
        "preview_only": True,
        "ready_for_confirmation": not blockers,
        "package": copy.deepcopy(package_projection),
        "planned_identities": identity_rows,
        "planned_actions": planned_actions,
        "records": record_responses,
        "new_parent_dependencies": dependencies,
        "blockers": blockers,
        "warnings": package_warnings,
        "counts": {
            "records": len(record_responses),
            "creates": create_count,
            "collisions": collision_count,
            "record_errors": record_error_count,
            "media_plans": media_plan_count,
            "warnings": warning_count,
            "blockers": len(blockers),
        },
    }
    return DocumentsCollectionPlan(
        normalized_records=tuple(state.normalized for state in states),
        document_plans=tuple(state.document_plan for state in states),
        response=response,
    )


__all__ = [
    "CollectionRecordState",
    "DocumentsCollectionPlan",
    "blocked_collection_plan",
    "collection_issue",
    "plan_import_content_collection",
]
