"""Catalogue moment preview service routes for Local Studio."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_invalidation as invalidation
from catalogue import catalogue_save_build as save_build
from catalogue import catalogue_source_mutation as source_mutation
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_build_operation
from catalogue.catalogue_build_media import build_local_media_plan, build_moment_readiness
from catalogue.catalogue_build_scopes import build_scope_for_moment, preview_moment_source
from catalogue.catalogue_field_registry import field_aware_build_plan, load_catalogue_field_registry
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    append_activity_rows,
    extract_apply_build,
    load_moments_payload,
    log_event,
    normalize_moment_id_value,
)
from catalogue.catalogue_source import normalize_status
from catalogue.moment_sources import normalize_moment_metadata_record

MOMENT_FIELDS = [
    "moment_id",
    "title",
    "status",
    "published_date",
    "date",
    "date_display",
    "source_image_file",
    "image_alt",
]


def moment_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    moment_id = normalize_moment_id_value(body.get("moment_id") or body.get("moment_file"))
    moments_payload = load_moments_payload(context.moments_path)
    current_record = moments_payload["moments"].get(moment_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"moment_id not found: {moment_id}")
    normalized_record = normalize_moment_metadata_record(moment_id, current_record)
    preview = preview_moment_source(context.repo_root, f"{moment_id}.md", metadata=normalized_record)
    payload: dict[str, Any] = {
        "ok": True,
        "moment_id": moment_id,
        "record": normalized_record,
        "preview": preview,
        "readiness": build_moment_readiness(context.repo_root, f"{moment_id}.md", metadata=normalized_record),
    }
    if preview.get("valid"):
        scope = build_scope_for_moment(context.repo_root, f"{moment_id}.md", metadata=normalized_record)
        scope["local_media"] = build_local_media_plan(context.repo_root, scope=scope)
        payload["build"] = scope
    return payload


def moment_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_apply_build = extract_apply_build(body)
    requested_moment_id = body.get("moment_id")
    moment_update = extract_moment_update(body)
    if requested_moment_id is None:
        requested_moment_id = moment_update.get("moment_id")
    moment_id = normalize_moment_id_value(requested_moment_id)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_SAVE_MOMENT,
        record_id=moment_id,
    )

    moments_payload = load_moments_payload(context.moments_path)
    moments = moments_payload["moments"]
    current_record = moments.get(moment_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"moment_id not found: {moment_id}")

    mutation_plan = source_mutation.plan_moment_save(moments, moment_id, current_record, moment_update)
    if mutation_plan.validation_errors:
        raise ValueError("moment source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    changed = mutation_plan.changed
    fields_changed = mutation_plan.changed_fields
    normalized_current = mutation_plan.baseline_record
    updated_record = mutation_plan.updated_record
    apply_build = requested_apply_build and normalize_status(updated_record.get("status")) == "published"
    if changed:
        target_path = context.moments_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            {target_path: mutation_plan.payload},
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload: dict[str, Any] = {
        "ok": True,
        "moment_id": moment_id,
        "changed": changed,
        "changed_fields": fields_changed,
        "record": updated_record,
    }
    if activity_context:
        payload["activity_context"] = activity_context
    build_plan: dict[str, Any] = {}
    if changed:
        invalidation_result = invalidation.moment_build_invalidation_for_fields(fields_changed)
        payload["moment_build_invalidation"] = {
            "mode": "moment-scoped-build",
            "invalidation_class": invalidation_result["class"],
            "artifacts": invalidation_result["artifacts"],
            "unknown_fields": invalidation_result["unknown_fields"],
        }
        build_plan = field_aware_build_plan(
            load_catalogue_field_registry(context.repo_root),
            record_family="moment",
            operation="metadata_update",
            changed_field_names=fields_changed,
            context={
                "current_record": normalized_current,
                "updated_record": updated_record,
            },
        )
        payload["build_plan"] = build_plan
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = changed
    elif changed:
        payload["saved_at_utc"] = activity.utc_now()

    log_event(
        context.repo_root,
        "catalogue_moment_save",
        {
            "moment_id": moment_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
            "activity_page_id": activity_context.get("page_id") if activity_context else "",
            "activity_action_id": activity_context.get("action_id") if activity_context else "",
            "dry_run": context.dry_run,
        },
    )
    if changed and not context.dry_run and activity_context:
        now_utc = activity.utc_now()
        append_activity_rows(
            context.repo_root,
            payload,
            [
                activity.studio_activity_entry(
                    activity_context,
                    now_utc=now_utc,
                    script_purpose_id="save-canonical-data",
                    status="completed",
                    record_groups={"works": [], "series": [], "work_details": [], "moments": [moment_id]},
                    detail_items=[
                        f"Saved canonical moment record {moment_id}",
                        f"Changed fields: {', '.join(fields_changed)}",
                    ],
                    source_refs=activity.catalogue_log_source_ref(),
                )
            ],
        )
    build_payload = save_build.apply_save_build_follow_through(
        payload,
        requested_apply_build=requested_apply_build,
        apply_build=apply_build,
        changed=changed,
        build_plan=build_plan,
        unpublished_reason="moment_not_published",
        unpublished_message="Public moment update skipped because the saved moment is not published.",
        unpublished_message_key="message",
        no_artifacts_message_key="message",
        run_build=lambda: run_build_operation(
            context,
            work_id="",
            series_id="",
            moment_id=moment_id,
            extra_series_ids=[],
            extra_work_ids=[],
            detail_uid="",
            force=False,
            build_plan=build_plan,
        ),
    )
    if build_payload is not None and activity_context:
        append_activity_rows(
            context.repo_root,
            payload,
            activity.catalogue_build_studio_activity_rows(
                activity.ACTIVITY_PROFILE_SAVE_MOMENT,
                activity_context,
                build_payload,
                published_detail=f"Updated published moment JSON for {moment_id}",
                search_detail=f"Rebuilt catalogue search for moment {moment_id}",
                fallback_record_groups={"works": [], "series": [], "work_details": [], "moments": [moment_id]},
            ),
        )
    return payload


def extract_moment_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("moment"))
    if raw_record is None:
        raw_record = {field: body[field] for field in MOMENT_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in MOMENT_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one moment field")
    return dict(raw_record)
