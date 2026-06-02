"""Catalogue work create/save service routes for Local Studio."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_lookup_refresh as lookup_refresh
from catalogue import catalogue_save_build as save_build
from catalogue import catalogue_source_mutation as source_mutation
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_build_operation
from catalogue.catalogue_field_registry import field_aware_build_plan, load_catalogue_field_registry
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    append_activity_rows,
    extract_apply_build,
    focused_lookup_refresh_response,
    load_works_payload,
    log_event,
    lookup_refresh_response_for_plan,
    refresh_lookup_payloads,
    refresh_lookup_payloads_for_work_change,
)
from catalogue.catalogue_source import WORK_FIELDS, normalize_series_ids_value, normalize_status, records_from_json_source, slug_id


def work_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_work_id = body.get("work_id")
    work_update = extract_work_update(body)
    if requested_work_id is None:
        requested_work_id = work_update.get("work_id")
    work_id = slug_id(requested_work_id)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_CREATE_WORK,
        record_id=work_id,
    )

    works_payload = load_works_payload(context.works_path)
    works = works_payload["works"]
    if isinstance(works.get(work_id), dict):
        raise ValueError(f"work_id already exists: {work_id}")

    mutation_plan = source_mutation.plan_work_create(
        records_from_json_source(context.source_dir),
        works,
        work_id,
        work_update,
    )
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    target_path = context.works_path.resolve()
    if target_path not in context.allowed_write_paths:
        raise ValueError("write target not allowlisted")
    write_result = transactions.execute_source_json_write(
        {target_path: mutation_plan.payload},
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "work_id": work_id,
        "created": True,
        "changed": True,
        "changed_fields": mutation_plan.changed_fields,
        "record": mutation_plan.updated_record,
    }
    if activity_context:
        payload["activity_context"] = activity_context
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = True
    else:
        payload["saved_at_utc"] = activity.utc_now()

    log_event(
        context.repo_root,
        "catalogue_work_create",
        {
            "work_id": work_id,
            "changed_fields": payload["changed_fields"],
            "dry_run": context.dry_run,
        },
    )
    if not context.dry_run:
        refresh_result = refresh_lookup_payloads(context)
        payload["lookup_refresh"] = refresh_result
        if activity_context:
            now_utc = activity.utc_now()
            record_groups = activity.activity_record_groups(works=[work_id])
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    *activity.catalogue_source_write_activity_rows(
                        activity.ACTIVITY_PROFILE_CREATE_WORK,
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        record_groups=record_groups,
                        detail_items=[
                            f"Created canonical draft work record {work_id}",
                            f"Changed fields: {', '.join(payload['changed_fields'])}",
                        ],
                    ),
                    activity.catalogue_lookup_activity_row(
                        activity_context,
                        now_utc=now_utc,
                        record_groups=record_groups,
                        detail_items=[
                            f"Refreshed catalogue lookup data after creating work {work_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                    ),
                ],
            )
    return payload


def work_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_apply_build = extract_apply_build(body)
    requested_work_id = body.get("work_id")
    work_update = extract_work_update(body)
    if requested_work_id is None:
        requested_work_id = work_update.get("work_id")
    work_id = slug_id(requested_work_id)
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_SAVE_WORK,
        record_id=work_id,
    )

    works_payload = load_works_payload(context.works_path)
    works = works_payload["works"]
    current_record = works.get(work_id)
    if not isinstance(current_record, dict):
        raise ValueError(f"work_id not found: {work_id}")

    source_records = records_from_json_source(context.source_dir)
    mutation_plan = source_mutation.plan_work_save(
        source_records,
        works,
        work_id,
        current_record,
        work_update,
    )
    updated_record = mutation_plan.updated_record
    apply_build = requested_apply_build and normalize_status(updated_record.get("status")) == "published"
    fields_changed = mutation_plan.changed_fields
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    changed = mutation_plan.changed
    if changed:
        target_path = context.works_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            {target_path: mutation_plan.payload},
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload: dict[str, Any] = {
        "ok": True,
        "work_id": work_id,
        "changed": changed,
        "changed_fields": fields_changed,
        "record": updated_record,
    }
    if activity_context:
        payload["activity_context"] = activity_context
    build_plan: dict[str, Any] = {}
    lookup_refresh_payload: dict[str, Any] = {}
    if changed:
        build_plan = field_aware_build_plan(
            load_catalogue_field_registry(context.repo_root),
            record_family="work",
            operation="metadata_update",
            changed_field_names=fields_changed,
            context={
                "source_records": source_records,
                "current_record": current_record,
                "updated_record": updated_record,
            },
        )
        payload["build_plan"] = build_plan
        lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
            record_family="work",
            changed_field_names=fields_changed,
            build_plan=build_plan,
        )
        lookup_refresh_payload = lookup_refresh_response_for_plan(lookup_plan)
        payload["lookup_refresh"] = lookup_refresh_payload
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = changed
    elif changed:
        payload["saved_at_utc"] = activity.utc_now()

    log_event(
        context.repo_root,
        "catalogue_work_save",
        {
            "work_id": work_id,
            "changed": changed,
            "changed_fields": fields_changed,
            "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
            "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
            "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
            "activity_page_id": activity_context.get("page_id") if activity_context else "",
            "activity_action_id": activity_context.get("action_id") if activity_context else "",
            "dry_run": context.dry_run,
        },
    )
    if changed and not context.dry_run:
        refresh_result = refresh_lookup_payloads_for_work_change(
            context,
            work_id,
            current_record,
            updated_record,
            build_plan,
        )
        payload["lookup_refresh"] = focused_lookup_refresh_response(refresh_result)
        if activity_context:
            now_utc = activity.utc_now()
            related_series_ids = sorted(
                {
                    *normalize_series_ids_value(current_record.get("series_ids")),
                    *normalize_series_ids_value(updated_record.get("series_ids")),
                }
            )
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        status="completed",
                        record_groups={"works": [work_id], "series": [], "work_details": [], "moments": []},
                        detail_items=[
                            f"Saved canonical work record {work_id}",
                            f"Changed fields: {', '.join(fields_changed)}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": [work_id], "series": related_series_ids, "work_details": [], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for work {work_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ],
            )
    previous_series_ids = normalize_series_ids_value(current_record.get("series_ids"))
    next_series_ids = normalize_series_ids_value(updated_record.get("series_ids"))
    removed_series_ids = [series_id for series_id in previous_series_ids if series_id not in next_series_ids]
    build_payload = save_build.apply_save_build_follow_through(
        payload,
        requested_apply_build=requested_apply_build,
        apply_build=apply_build,
        changed=changed,
        build_plan=build_plan,
        unpublished_reason="work_not_published",
        unpublished_message="Work must be published before a public update can run.",
        run_build=lambda: run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            extra_series_ids=normalize_series_ids_value([*extra_series_ids, *removed_series_ids]),
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
                activity.ACTIVITY_PROFILE_SAVE_WORK,
                activity_context,
                build_payload,
                published_detail=f"Updated published work JSON for {work_id}",
                search_detail=f"Rebuilt catalogue search for work {work_id}",
                fallback_record_groups={"works": [work_id], "series": [], "work_details": [], "moments": []},
            ),
        )
    return payload


def extract_work_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("work"))
    if raw_record is None:
        raw_record = {field: body[field] for field in WORK_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in WORK_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work field")
    return dict(raw_record)
