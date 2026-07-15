#!/usr/bin/env python3
"""Request validation and target-state revalidation for Docs Import collection decisions."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from docs_import_collection_plan import DocumentsCollectionPlan, collection_issue


COLLECTION_APPLY_BODY_FIELDS = {
    "scope",
    "staged_filename",
    "preview_only",
    "confirm",
    "decisions",
    "export_id",
    "source_sha256",
    "planned_identities",
    "activity_context",
}
COLLECTION_DECISION_FIELDS = {"record_index", "action", "target_doc_id", "note"}


@dataclass(frozen=True)
class CollectionDecision:
    record_index: int
    action: str
    target_doc_id: str = ""
    note: str = ""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _validate_apply_body(body: dict[str, Any]) -> None:
    extra_fields = sorted(set(body) - COLLECTION_APPLY_BODY_FIELDS)
    if extra_fields:
        raise ValueError("collection apply does not accept fields: " + ", ".join(extra_fields))
    if body.get("preview_only") is not False:
        raise ValueError("collection apply requires preview_only false")
    if body.get("confirm") is not True:
        raise ValueError("collection apply requires confirm true")


def parse_collection_decisions(body: dict[str, Any]) -> dict[int, CollectionDecision]:
    _validate_apply_body(body)
    raw_decisions = body.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ValueError("collection apply decisions must be an array")
    decisions: dict[int, CollectionDecision] = {}
    for raw in raw_decisions:
        if not isinstance(raw, dict):
            raise ValueError("each collection decision must be an object")
        extra_fields = sorted(set(raw) - COLLECTION_DECISION_FIELDS)
        if extra_fields:
            raise ValueError("collection decisions do not accept fields: " + ", ".join(extra_fields))
        record_index = raw.get("record_index")
        if not isinstance(record_index, int) or isinstance(record_index, bool) or record_index < 0:
            raise ValueError("collection decision record_index must be a non-negative integer")
        if record_index in decisions:
            raise ValueError(f"duplicate collection decision for record_index {record_index}")
        action = _clean_text(raw.get("action")).lower()
        if action not in {"overwrite", "skip"}:
            raise ValueError("collection decision action must be overwrite or skip")
        note = raw.get("note", "")
        if not isinstance(note, str):
            raise ValueError("collection decision note must be a string")
        decisions[record_index] = CollectionDecision(
            record_index=record_index,
            action=action,
            target_doc_id=_clean_text(raw.get("target_doc_id")),
            note=note.strip(),
        )
    return decisions


def refreshed_collection_plan(
    plan: DocumentsCollectionPlan,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = plan.as_dict()
    payload["preview_only"] = True
    payload["reconfirmation_required"] = True
    payload["ready_for_confirmation"] = False
    payload["revalidation_issues"] = copy.deepcopy(issues)
    return payload


def _resolve_actions(
    plan: DocumentsCollectionPlan,
    decisions: dict[int, CollectionDecision],
) -> tuple[dict[int, str], list[dict[str, Any]]]:
    records = plan.response.get("records") if isinstance(plan.response.get("records"), list) else []
    actions: dict[int, str] = {}
    issues: list[dict[str, Any]] = []
    valid_indices = {int(record["record_index"]) for record in records}
    unknown_indices = sorted(set(decisions) - valid_indices)
    if unknown_indices:
        raise ValueError(
            "collection decisions reference unknown record indices: "
            + ", ".join(str(index) for index in unknown_indices)
        )
    for record in records:
        index = int(record["record_index"])
        current_action = _clean_text(record.get("action"))
        decision = decisions.get(index)
        if current_action == "create":
            actions[index] = "create"
            if decision is not None:
                issues.append(collection_issue(
                    "warning",
                    "target_state_changed",
                    "record no longer requires the submitted collision or error decision",
                    record_index=index,
                    doc_id=_clean_text(record.get("doc_id")),
                ))
            continue
        if current_action != "decision-required":
            issues.append(collection_issue(
                "error",
                "record_not_applicable",
                "record is not currently eligible for collection apply",
                record_index=index,
                doc_id=_clean_text(record.get("doc_id")),
            ))
            continue
        if decision is None:
            issues.append(collection_issue(
                "warning",
                "decision_required",
                "record requires a refreshed explicit decision",
                record_index=index,
                doc_id=_clean_text(record.get("doc_id")),
            ))
            continue
        allowed = set(record.get("allowed_actions") or []) - {"cancel"}
        if decision.action not in allowed:
            issues.append(collection_issue(
                "warning",
                "decision_no_longer_allowed",
                f"submitted action {decision.action!r} is not allowed by the refreshed plan",
                record_index=index,
                doc_id=_clean_text(record.get("doc_id")),
            ))
            continue
        decision_kind = _clean_text(record.get("decision_kind"))
        collision = record.get("collision") if isinstance(record.get("collision"), dict) else {}
        if decision_kind == "collision" and decision.target_doc_id != _clean_text(collision.get("doc_id")):
            issues.append(collection_issue(
                "warning",
                "collision_target_changed",
                "collision target identity changed; review the refreshed plan",
                record_index=index,
                doc_id=_clean_text(record.get("doc_id")),
            ))
            continue
        if decision_kind == "invalid-record" and decision.note and decision.action != "skip":
            raise ValueError("invalid-record notes are allowed only with skip")
        if decision_kind != "invalid-record" and decision.note:
            raise ValueError("collection decision notes are allowed only for skipped invalid records")
        actions[index] = decision.action

    for dependency in plan.response.get("new_parent_dependencies") or []:
        if not isinstance(dependency, dict):
            continue
        parent_index = dependency.get("parent_record_index")
        child_index = dependency.get("record_index")
        if actions.get(parent_index) == "skip" and actions.get(child_index) != "skip":
            issues.append(collection_issue(
                "error",
                "skipped_parent",
                f"parent record {dependency.get('parent_id')!r} is skipped but its child is still planned",
                record_index=child_index if isinstance(child_index, int) else None,
                doc_id=_clean_text(dependency.get("doc_id")),
            ))
    return actions, issues


def resolve_collection_apply_request(
    plan: DocumentsCollectionPlan,
    body: dict[str, Any],
) -> tuple[dict[int, CollectionDecision], dict[int, str], dict[str, Any] | None]:
    """Return validated decisions/actions or a write-free refreshed-plan response."""

    decisions = parse_collection_decisions(body)
    confirmed_export_id = _clean_text(body.get("export_id"))
    confirmed_source_sha256 = _clean_text(body.get("source_sha256"))
    if not confirmed_export_id or not confirmed_source_sha256:
        raise ValueError("collection apply requires confirmed export_id and source_sha256")
    current_package = plan.response.get("package") if isinstance(plan.response.get("package"), dict) else {}
    if (
        confirmed_export_id != _clean_text(current_package.get("export_id"))
        or confirmed_source_sha256 != _clean_text(current_package.get("source_sha256"))
    ):
        return decisions, {}, refreshed_collection_plan(plan, [
            collection_issue(
                "warning",
                "package_identity_changed",
                "staged package identity changed; review the refreshed plan",
            )
        ])
    if plan.response.get("blockers"):
        return decisions, {}, refreshed_collection_plan(plan, [
            collection_issue("error", "plan_blocked", "refreshed collection plan is blocked")
        ])
    actions, issues = _resolve_actions(plan, decisions)
    if issues:
        return decisions, actions, refreshed_collection_plan(plan, issues)
    return decisions, actions, None


__all__ = [
    "COLLECTION_APPLY_BODY_FIELDS",
    "COLLECTION_DECISION_FIELDS",
    "CollectionDecision",
    "parse_collection_decisions",
    "refreshed_collection_plan",
    "resolve_collection_apply_request",
]
