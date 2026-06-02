"""Catalogue series create/save service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_lookup_refresh as lookup_refresh
from catalogue import catalogue_save_build as save_build
from catalogue import catalogue_source_mutation as source_mutation
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_service import run_build_operation
from catalogue.catalogue_field_registry import field_aware_build_plan, full_fallback_build_plan, load_catalogue_field_registry
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    append_activity_rows,
    extract_apply_build,
    focused_lookup_refresh_response,
    load_series_payload,
    load_works_payload,
    log_event,
    lookup_refresh_response_for_plan,
    refresh_lookup_payloads,
    refresh_lookup_payloads_for_series_change,
)
from catalogue.catalogue_source import SERIES_FIELDS, normalize_series_ids_value, normalize_status, records_from_json_source, slug_id
from catalogue.series_ids import normalize_series_id


def series_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_series_id = body.get("series_id")
    series_update = extract_series_update(body)
    if requested_series_id is None:
        requested_series_id = series_update.get("series_id")
    series_id = normalize_series_id(requested_series_id)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_CREATE_SERIES,
        record_id=series_id,
    )
    work_updates_request = extract_series_work_updates(body)

    series_payload = load_series_payload(context.series_path)
    series_map = series_payload["series"]
    if isinstance(series_map.get(series_id), dict):
        raise ValueError(f"series_id already exists: {series_id}")

    works_payload = load_works_payload(context.works_path)
    works_map = works_payload["works"]
    mutation_plan = source_mutation.plan_series_create(
        records_from_json_source(context.source_dir),
        series_map,
        works_map,
        series_id,
        series_update,
        work_updates_request,
    )
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    changed_work_ids = mutation_plan.changed_work_ids
    target_payloads: dict[Path, dict[str, Any]] = {
        context.series_path.resolve(): mutation_plan.payload,
    }
    if changed_work_ids and mutation_plan.works_payload is not None:
        target_payloads[context.works_path.resolve()] = mutation_plan.works_payload
    for target_path in target_payloads:
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
    write_result = transactions.execute_source_json_write(
        target_payloads,
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "series_id": series_id,
        "created": True,
        "changed": True,
        "changed_fields": mutation_plan.changed_fields,
        "changed_work_ids": changed_work_ids,
        "record": mutation_plan.updated_record,
        "work_records": mutation_plan.work_records,
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
        "catalogue_series_create",
        {
            "series_id": series_id,
            "changed_fields": payload["changed_fields"],
            "changed_work_ids": changed_work_ids,
            "dry_run": context.dry_run,
        },
    )
    if not context.dry_run:
        refresh_result = refresh_lookup_payloads(context)
        payload["lookup_refresh"] = refresh_result
        if activity_context:
            now_utc = activity.utc_now()
            record_groups = activity.activity_record_groups(works=changed_work_ids, series=[series_id])
            detail_items = [
                f"Created canonical draft series record {series_id}",
                f"Changed fields: {', '.join(payload['changed_fields'])}",
            ]
            if changed_work_ids:
                detail_items.append(f"Saved {len(changed_work_ids)} member work record(s)")
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    *activity.catalogue_source_write_activity_rows(
                        activity.ACTIVITY_PROFILE_CREATE_SERIES,
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        record_groups=record_groups,
                        detail_items=detail_items,
                    ),
                    activity.catalogue_lookup_activity_row(
                        activity_context,
                        now_utc=now_utc,
                        record_groups=record_groups,
                        detail_items=[
                            f"Refreshed catalogue lookup data after creating series {series_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                    ),
                ],
            )
    return payload


def series_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_apply_build = extract_apply_build(body)
    requested_series_id = body.get("series_id")
    series_update = extract_series_update(body)
    if requested_series_id is None:
        requested_series_id = series_update.get("series_id")
    series_id = normalize_series_id(requested_series_id)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_SAVE_SERIES,
        record_id=series_id,
    )
    work_updates_request = extract_series_work_updates(body)
    extra_work_ids = [slug_id(raw) for raw in body.get("extra_work_ids") or []]

    series_payload = load_series_payload(context.series_path)
    series_map = series_payload["series"]
    current_series_record = series_map.get(series_id)
    if not isinstance(current_series_record, dict):
        raise ValueError(f"series_id not found: {series_id}")

    works_payload = load_works_payload(context.works_path)
    works_map = works_payload["works"]
    source_records = records_from_json_source(context.source_dir)
    mutation_plan = source_mutation.plan_series_save(
        source_records,
        series_map,
        works_map,
        series_id,
        current_series_record,
        series_update,
        work_updates_request,
    )
    updated_series_record = mutation_plan.updated_record
    apply_build = requested_apply_build and normalize_status(updated_series_record.get("status")) == "published"
    changed_work_ids = mutation_plan.changed_work_ids
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    series_changed_fields = mutation_plan.changed_fields
    changed = mutation_plan.changed
    if changed:
        target_payloads: dict[Path, dict[str, Any]] = {}
        if series_changed_fields:
            target_payloads[context.series_path.resolve()] = mutation_plan.payload
        if changed_work_ids and mutation_plan.works_payload is not None:
            target_payloads[context.works_path.resolve()] = mutation_plan.works_payload
        for target_path in target_payloads:
            if target_path not in context.allowed_write_paths:
                raise ValueError("write target not allowlisted")
        transactions.execute_source_json_write(
            target_payloads,
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload: dict[str, Any] = {
        "ok": True,
        "series_id": series_id,
        "changed": changed,
        "changed_fields": series_changed_fields,
        "changed_work_ids": changed_work_ids,
        "record": updated_series_record,
        "work_records": mutation_plan.work_records,
    }
    if activity_context:
        payload["activity_context"] = activity_context
    build_plan: dict[str, Any] = {}
    lookup_refresh_payload: dict[str, Any] = {}
    if changed:
        field_registry = load_catalogue_field_registry(context.repo_root)
        if changed_work_ids:
            build_plan = full_fallback_build_plan(
                field_registry,
                fields=[*series_changed_fields, "work.series_ids"],
                fallback_reason="series_save_changed_member_works",
                reason="Series save also changed member work records; use conservative fallback until cross-family saves are scoped explicitly.",
                record_family="series",
            )
        else:
            build_plan = field_aware_build_plan(
                field_registry,
                record_family="series",
                operation="metadata_update",
                changed_field_names=series_changed_fields,
                context={
                    "source_records": source_records,
                    "current_record": current_series_record,
                    "updated_record": updated_series_record,
                },
            )
        payload["build_plan"] = build_plan
        lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
            record_family="series",
            changed_field_names=series_changed_fields,
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
        "catalogue_series_save",
        {
            "series_id": series_id,
            "changed": changed,
            "changed_fields": series_changed_fields,
            "changed_work_ids": changed_work_ids,
            "lookup_refresh_mode": lookup_refresh_payload.get("mode") if changed else "none",
            "lookup_refresh_artifacts": lookup_refresh_payload.get("artifacts") if changed else [],
            "activity_correlation_id": activity_context.get("correlation_id") if activity_context else "",
            "activity_page_id": activity_context.get("page_id") if activity_context else "",
            "activity_action_id": activity_context.get("action_id") if activity_context else "",
            "dry_run": context.dry_run,
        },
    )
    if changed and not context.dry_run:
        refresh_result = refresh_lookup_payloads_for_series_change(
            context,
            series_id,
            series_changed_fields,
            build_plan,
        )
        payload["lookup_refresh"] = focused_lookup_refresh_response(refresh_result)
        if activity_context:
            now_utc = activity.utc_now()
            canonical_detail_items = [f"Saved canonical series record {series_id}"]
            if series_changed_fields:
                canonical_detail_items.append(f"Changed series fields: {', '.join(series_changed_fields)}")
            if changed_work_ids:
                canonical_detail_items.append(f"Saved {len(changed_work_ids)} member work record(s)")
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        status="completed",
                        record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
                        detail_items=canonical_detail_items,
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for series {series_id}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ],
            )
    build_payload = save_build.apply_save_build_follow_through(
        payload,
        requested_apply_build=requested_apply_build,
        apply_build=apply_build,
        changed=changed,
        build_plan=build_plan,
        unpublished_reason="series_not_published",
        unpublished_message="Series must be published before a public update can run.",
        run_build=lambda: run_build_operation(
            context,
            work_id="",
            series_id=series_id,
            extra_series_ids=[],
            extra_work_ids=extra_work_ids,
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
                activity.ACTIVITY_PROFILE_SAVE_SERIES,
                activity_context,
                build_payload,
                published_detail=f"Updated published series/work JSON for series {series_id}",
                search_detail=f"Rebuilt catalogue search for series {series_id}",
                fallback_record_groups={"works": changed_work_ids, "series": [series_id], "work_details": [], "moments": []},
            ),
        )
    return payload


def extract_series_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("series"))
    if raw_record is None:
        raw_record = {field: body[field] for field in SERIES_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in SERIES_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one series field")
    return dict(raw_record)


def extract_series_work_updates(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_updates = body.get("work_updates") or []
    if raw_updates == []:
        return []
    if not isinstance(raw_updates, list):
        raise ValueError("work_updates must be an array")
    updates: list[dict[str, Any]] = []
    for raw in raw_updates:
        if not isinstance(raw, dict):
            raise ValueError("work_updates entries must be objects")
        unknown = sorted(str(key) for key in raw.keys() if str(key) not in {"work_id", "series_ids"})
        if unknown:
            raise ValueError(f"work_updates entry contains unsupported fields: {', '.join(unknown)}")
        updates.append(
            {
                "work_id": slug_id(raw.get("work_id")),
                "series_ids": normalize_series_ids_value(raw.get("series_ids")),
            }
        )
    return updates
