"""Delete selected Work identities or one empty Series through Local Studio."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Mapping

from catalogue.catalogue_delete_plans import build_delete_apply_plan
from catalogue.catalogue_output_service import complete_saved_catalogue_edit
from catalogue.catalogue_source import work_resource_entries
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_service_context import CatalogueWriteContext, utc_now


def delete_apply_response(
    context: CatalogueWriteContext, body: Mapping[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    """Delete one or many Works by exact ID; complete the saved result without rereads.

    The UI offers Series deletion only when its saved Work map has no members.
    The server removes the exact definition and its current relevance pairs.
    Required local completion can fail after canonical deletion; report that
    saved outcome through the shared completion owner without restoring records.
    """
    kind, record_ids = extract_delete_request(body)
    plan = build_delete_apply_plan(context.source_dir, kind, record_ids)
    if not set(plan.payloads).issubset(context.allowed_write_paths):
        raise ValueError("write target not allowlisted")
    deleted_media = {
        wid: {"image": bool(plan.previous.works[wid].get("project_filename")),
              "file_names": sorted(item["filename"] for item in work_resource_entries(plan.previous.works[wid], "downloads"))}
        for wid in record_ids if kind == "works"
    }
    transactions.execute_source_json_write(plan.payloads, dry_run=context.dry_run, repo_root=context.repo_root)
    identity = {"ids": record_ids} if kind == "works" else {"id": record_ids[0]}
    payload: dict[str, Any] = {
        "ok": True, "kind": kind, **identity, "deleted": True, "affected": plan.affected,
        "_shared_changes": plan.shared,
    }
    if context.dry_run:
        payload.update(dry_run=True, would_write=True)
    else:
        payload["saved_at_utc"] = utc_now()
    complete_saved_catalogue_edit(context, payload, plan.previous, current_records=plan.current, deleted_media=deleted_media)
    return HTTPStatus.OK, payload


def extract_delete_request(body: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Validate deletion envelopes; the UI owns saved-identity authoring choices.

    Work spelling/distinctness are not revalidated or normalized here. The
    planner requires exact existing targets; media/queue owners retain their
    identity and confinement checks. Series emptiness belongs to the UI's saved
    membership map; deletion accepts its exact string ID without a revision.
    """
    kind = body.get("kind")
    if kind == "works":
        allowed = {"kind", "ids"}
        raw_ids = body.get("ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError("delete ids must be a non-empty array of exact Work IDs")
        if any(not isinstance(wid, str) for wid in raw_ids):
            raise ValueError("delete ids must contain exact Work ID strings")
        record_ids = raw_ids
    elif kind == "series":
        allowed = {"kind", "series_id"}
        series_id = body.get("series_id")
        if not isinstance(series_id, str):
            raise ValueError("delete series_id must be an exact Series ID string")
        record_ids = [series_id]
    else:
        raise ValueError("delete kind must be works or series")
    unknown = sorted(str(key) for key in body if key not in allowed)
    if unknown:
        raise ValueError("delete contains unsupported fields: " + ", ".join(unknown))
    return kind, record_ids
