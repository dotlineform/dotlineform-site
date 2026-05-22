"""Callable catalogue write/read service helpers for Local Studio."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_delete_plans
from catalogue import catalogue_lookup_refresh as lookup_refresh
from catalogue import catalogue_prose_import as prose_import
from catalogue import catalogue_save_build as save_build
from catalogue import catalogue_source_mutation as source_mutation
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_field_plan import apply_field_build_plan_to_scope, build_field_plan_for_scope
from catalogue.catalogue_field_registry import field_aware_build_plan, full_fallback_build_plan, load_catalogue_field_registry
from catalogue.catalogue_build_media import build_local_media_plan, build_moment_readiness
from catalogue.catalogue_build_scopes import build_scope_for_moment, build_scope_for_series, build_scope_for_work, preview_moment_source
from catalogue.catalogue_json_build import run_scoped_build_scope
from catalogue.catalogue_source import (
    DEFAULT_SOURCE_DIR,
    DETAIL_FIELDS,
    SERIES_FIELDS,
    SOURCE_FILES,
    WORK_FIELDS,
    load_json_file,
    normalize_detail_uid_value,
    normalize_series_ids_value,
    normalize_status,
    records_from_json_source,
    slug_id,
)
from catalogue.moment_sources import CATALOGUE_MOMENT_PROSE_REL_DIR, MOMENT_METADATA_FILENAME, normalize_moment_filename, normalize_moment_metadata_record
from catalogue.series_ids import normalize_series_id
from script_logging import append_script_log
from studio_activity import append_studio_activity


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")

SERVICE_POST_PATHS = {
    "/work/create",
    "/work/save",
    "/work-detail/create",
    "/work-detail/save",
    "/series/create",
    "/series/save",
    "/delete-preview",
    "/build-preview",
    "/build-apply",
    "/moment/preview",
    "/prose/import-preview",
    "/prose/import-apply",
    "/moment/import-preview",
    "/moment/import-apply",
}


@dataclass(frozen=True)
class CatalogueWriteContext:
    repo_root: Path
    source_dir: Path
    lookup_dir: Path
    works_path: Path
    work_details_path: Path
    series_path: Path
    moments_path: Path
    allowed_write_paths: set[Path]
    allowed_write_roots: set[Path]
    backups_dir: Path
    dry_run: bool = False

    def rel_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.repo_root.resolve()))
        except ValueError:
            return path.name


def build_catalogue_write_context(repo_root: Path, *, dry_run: bool = False) -> CatalogueWriteContext:
    resolved_root = repo_root.resolve()
    source_dir = (resolved_root / DEFAULT_SOURCE_DIR).resolve()
    return CatalogueWriteContext(
        repo_root=resolved_root,
        source_dir=source_dir,
        lookup_dir=(resolved_root / "assets" / "studio" / "data" / "catalogue_lookup").resolve(),
        works_path=(source_dir / SOURCE_FILES["works"]).resolve(),
        work_details_path=(source_dir / SOURCE_FILES["work_details"]).resolve(),
        series_path=(source_dir / SOURCE_FILES["series"]).resolve(),
        moments_path=(source_dir / MOMENT_METADATA_FILENAME).resolve(),
        allowed_write_paths={
            (source_dir / filename).resolve()
            for kind, filename in SOURCE_FILES.items()
            if kind != "meta"
        } | {(source_dir / MOMENT_METADATA_FILENAME).resolve()},
        allowed_write_roots={
            (resolved_root / prose_import.CATALOGUE_PROSE_SOURCE_REL_DIR / "works").resolve(),
            (resolved_root / prose_import.CATALOGUE_PROSE_SOURCE_REL_DIR / "series").resolve(),
            (resolved_root / CATALOGUE_MOMENT_PROSE_REL_DIR).resolve(),
        },
        backups_dir=(resolved_root / BACKUPS_REL_DIR).resolve(),
        dry_run=dry_run,
    )


def handle_catalogue_post(
    repo_root: Path,
    api_path: str,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, Any]]:
    context = build_catalogue_write_context(repo_root, dry_run=dry_run)
    if api_path == "/work/create":
        return HTTPStatus.OK, work_create_payload(context, body)
    if api_path == "/work/save":
        return HTTPStatus.OK, work_save_payload(context, body)
    if api_path == "/work-detail/create":
        return HTTPStatus.OK, work_detail_create_payload(context, body)
    if api_path == "/work-detail/save":
        return HTTPStatus.OK, work_detail_save_payload(context, body)
    if api_path == "/series/create":
        return HTTPStatus.OK, series_create_payload(context, body)
    if api_path == "/series/save":
        return HTTPStatus.OK, series_save_payload(context, body)
    if api_path == "/delete-preview":
        return HTTPStatus.OK, delete_preview_payload(context, body)
    if api_path == "/build-preview":
        return HTTPStatus.OK, build_preview_payload(context, body)
    if api_path == "/build-apply":
        success, payload = build_apply_payload(context, body)
        return HTTPStatus.OK if success else HTTPStatus.INTERNAL_SERVER_ERROR, payload
    if api_path == "/moment/preview":
        return HTTPStatus.OK, moment_preview_payload(context, body)
    if api_path == "/prose/import-preview":
        return HTTPStatus.OK, prose_import.build_prose_import_preview(context.repo_root, context.source_dir, body)
    if api_path == "/prose/import-apply":
        return prose_import_apply_response(context, body)
    if api_path == "/moment/import-preview":
        return HTTPStatus.OK, prose_import.build_moment_import_preview(context.repo_root, body)
    if api_path == "/moment/import-apply":
        return HTTPStatus.OK, moment_import_apply_payload(context, body)
    raise FileNotFoundError(f"Unknown catalogue service route: {api_path}")


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
        context.backups_dir,
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
        if write_result.backups:
            payload["backups"] = write_result.backups

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
    backup_response_paths: list[str] = []
    if changed:
        target_path = context.works_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        write_result = transactions.execute_source_json_write(
            {target_path: mutation_plan.payload},
            context.backups_dir,
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )
        backup_response_paths = write_result.backups

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
        if backup_response_paths:
            payload["backups"] = backup_response_paths

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


def work_detail_create_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    requested_detail_uid = body.get("detail_uid")
    detail_update = extract_work_detail_update(body)
    requested_work_id = body.get("work_id", detail_update.get("work_id"))
    requested_detail_id = body.get("detail_id", detail_update.get("detail_id"))
    work_id = slug_id(requested_work_id)
    detail_id = slug_id(requested_detail_id, width=3)
    detail_uid = normalize_detail_uid_value(requested_detail_uid or f"{work_id}-{detail_id}")
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_CREATE_WORK_DETAIL,
        record_id=detail_uid,
    )

    details_payload = load_work_details_payload(context.work_details_path)
    work_details = details_payload["work_details"]
    if isinstance(work_details.get(detail_uid), dict):
        raise ValueError(f"detail_uid already exists: {detail_uid}")

    source_records = records_from_json_source(context.source_dir)
    mutation_plan = source_mutation.plan_work_detail_create(
        source_records,
        work_details,
        detail_uid,
        work_id,
        detail_id,
        detail_update,
    )
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    target_path = context.work_details_path.resolve()
    if target_path not in context.allowed_write_paths:
        raise ValueError("write target not allowlisted")
    write_result = transactions.execute_source_json_write(
        {target_path: mutation_plan.payload},
        context.backups_dir,
        dry_run=context.dry_run,
        repo_root=context.repo_root,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "detail_uid": detail_uid,
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
        if write_result.backups:
            payload["backups"] = write_result.backups

    log_event(
        context.repo_root,
        "catalogue_work_detail_create",
        {
            "detail_uid": detail_uid,
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
            record_groups = activity.activity_record_groups(works=[work_id], work_details=[detail_uid])
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    *activity.catalogue_source_write_activity_rows(
                        activity.ACTIVITY_PROFILE_CREATE_WORK_DETAIL,
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="save-canonical-data",
                        record_groups=record_groups,
                        detail_items=[
                            f"Created canonical draft work detail record {detail_uid}",
                            f"Changed fields: {', '.join(payload['changed_fields'])}",
                        ],
                    ),
                    activity.catalogue_lookup_activity_row(
                        activity_context,
                        now_utc=now_utc,
                        record_groups=record_groups,
                        detail_items=[
                            f"Refreshed catalogue lookup data after creating work detail {detail_uid}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                    ),
                ],
            )
    return payload


def work_detail_save_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    apply_build = extract_apply_build(body)
    requested_detail_uid = body.get("detail_uid")
    detail_update = extract_work_detail_update(body)
    if not requested_detail_uid:
        requested_detail_uid = detail_update.get("detail_uid")
    detail_uid = normalize_detail_uid_value(requested_detail_uid)
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_SAVE_WORK_DETAIL,
        record_id=detail_uid,
    )

    details_payload = load_work_details_payload(context.work_details_path)
    work_details = details_payload["work_details"]
    current_record = work_details.get(detail_uid)
    if not isinstance(current_record, dict):
        raise ValueError(f"detail_uid not found: {detail_uid}")

    source_records = records_from_json_source(context.source_dir)
    mutation_plan = source_mutation.plan_work_detail_save(
        source_records,
        work_details,
        detail_uid,
        current_record,
        detail_update,
    )
    updated_record = mutation_plan.updated_record
    work_id = mutation_plan.work_id
    fields_changed = mutation_plan.changed_fields
    if mutation_plan.validation_errors:
        raise ValueError("source validation failed: " + "; ".join(mutation_plan.validation_errors[:20]))

    changed = mutation_plan.changed
    backup_response_paths: list[str] = []
    if changed:
        target_path = context.work_details_path.resolve()
        if target_path not in context.allowed_write_paths:
            raise ValueError("write target not allowlisted")
        write_result = transactions.execute_source_json_write(
            {target_path: mutation_plan.payload},
            context.backups_dir,
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )
        backup_response_paths = write_result.backups

    payload: dict[str, Any] = {
        "ok": True,
        "detail_uid": detail_uid,
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
            record_family="work_detail",
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
            record_family="work_detail",
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
        if backup_response_paths:
            payload["backups"] = backup_response_paths

    log_event(
        context.repo_root,
        "catalogue_work_detail_save",
        {
            "detail_uid": detail_uid,
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
        refresh_result = refresh_lookup_payloads_for_detail_change(
            context,
            detail_uid,
            current_record,
            updated_record,
            build_plan,
        )
        payload["lookup_refresh"] = focused_lookup_refresh_response(refresh_result)
        if activity_context:
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
                        record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
                        detail_items=[
                            f"Saved canonical work detail record {detail_uid}",
                            f"Changed fields: {', '.join(fields_changed)}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=now_utc,
                        script_purpose_id="rebuild-lookups",
                        status="completed",
                        record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
                        detail_items=[
                            f"Refreshed catalogue lookup data for work detail {detail_uid}",
                            f"Wrote {refresh_result['written_count']} lookup file(s)",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    ),
                ],
            )
    build_payload = save_build.apply_save_build_follow_through(
        payload,
        requested_apply_build=apply_build,
        apply_build=apply_build,
        changed=changed,
        build_plan=build_plan,
        run_build=lambda: run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            extra_series_ids=[],
            extra_work_ids=[],
            detail_uid=detail_uid,
            force=False,
            build_plan=build_plan,
        ),
    )
    if build_payload is not None and activity_context:
        append_activity_rows(
            context.repo_root,
            payload,
            activity.catalogue_build_studio_activity_rows(
                activity.ACTIVITY_PROFILE_SAVE_WORK_DETAIL,
                activity_context,
                build_payload,
                published_detail=f"Updated published parent work JSON for detail {detail_uid}",
                search_detail=f"Rebuilt catalogue search for work detail {detail_uid}",
                fallback_record_groups={"works": [work_id], "series": [], "work_details": [detail_uid], "moments": []},
            ),
        )
    return payload


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
        context.backups_dir,
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
        if write_result.backups:
            payload["backups"] = write_result.backups

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
    backup_response_paths: list[str] = []
    if changed:
        target_payloads: dict[Path, dict[str, Any]] = {}
        if series_changed_fields:
            target_payloads[context.series_path.resolve()] = mutation_plan.payload
        if changed_work_ids and mutation_plan.works_payload is not None:
            target_payloads[context.works_path.resolve()] = mutation_plan.works_payload
        for target_path in target_payloads:
            if target_path not in context.allowed_write_paths:
                raise ValueError("write target not allowlisted")
        write_result = transactions.execute_source_json_write(
            target_payloads,
            context.backups_dir,
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )
        backup_response_paths = write_result.backups

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
        if backup_response_paths:
            payload["backups"] = backup_response_paths

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


def delete_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_delete_request(body)
    preview = catalogue_delete_plans.build_delete_preview(context.source_dir, request["kind"], request["id"], repo_root=context.repo_root)
    return {
        "ok": True,
        "kind": request["kind"],
        "id": request["id"],
        "preview": preview,
    }


def build_preview_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    work_id, series_id, moment_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
    detail_uid = normalize_detail_uid_value(body.get("detail_uid")) if body.get("detail_uid") else ""
    media_only = bool(body.get("media_only"))
    changed_fields = extract_changed_field_names(body)
    record_family = str(body.get("record_family") or body.get("family") or "").strip()
    if work_id:
        scope = build_scope_for_work(
            context.source_dir,
            work_id,
            extra_series_ids=extra_series_ids,
            detail_uid=detail_uid,
        )
    elif series_id:
        scope = build_scope_for_series(context.source_dir, series_id, extra_work_ids=extra_work_ids)
    else:
        scope = build_scope_for_moment(context.repo_root, f"{moment_id}.md", force=force)
    if changed_fields:
        build_plan = build_field_plan_for_scope(
            context.repo_root,
            context.source_dir,
            scope,
            changed_fields=changed_fields,
            record_family=record_family,
        )
        apply_field_build_plan_to_scope(scope, build_plan)
    scope["media_only"] = media_only
    scope["local_media"] = (
        build_local_media_plan(context.repo_root, scope=scope, force=force)
        if bool(scope.get("generate_local_media", True))
        else {"tasks": [], "counts": {"pending": 0, "current": 0, "blocked": 0, "unavailable": 0}}
    )
    return {
        "ok": True,
        "work_id": work_id,
        "series_id": series_id,
        "moment_id": moment_id,
        "detail_uid": detail_uid,
        "force": force,
        "media_only": media_only,
        "build": scope,
    }


def build_apply_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[bool, dict[str, Any]]:
    work_id, series_id, moment_id, extra_series_ids, extra_work_ids, force = extract_generic_build_request(body)
    detail_uid = normalize_detail_uid_value(body.get("detail_uid")) if body.get("detail_uid") else ""
    media_only = bool(body.get("media_only"))
    return run_build_operation(
        context,
        work_id=work_id,
        series_id=series_id,
        moment_id=moment_id,
        extra_series_ids=extra_series_ids,
        extra_work_ids=extra_work_ids,
        detail_uid=detail_uid,
        force=force,
        media_only=media_only,
    )


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


def prose_import_apply_response(context: CatalogueWriteContext, body: Mapping[str, Any]) -> tuple[HTTPStatus, dict[str, Any]]:
    preview = prose_import.build_prose_import_preview(context.repo_root, context.source_dir, body)
    if not preview.get("valid"):
        errors = preview.get("errors") if isinstance(preview.get("errors"), list) else []
        raise ValueError("; ".join(str(error) for error in errors) or "prose import preview failed")
    if preview.get("overwrite_required") and not bool(body.get("confirm_overwrite")):
        return HTTPStatus.CONFLICT, {"ok": False, "error": "overwrite confirmation required", "preview": preview}

    result = prose_import.apply_prose_import(
        context.repo_root,
        context.source_dir,
        body,
        allowed_write_roots=context.allowed_write_roots,
        dry_run=context.dry_run,
        preview=preview,
    )
    target = result.target
    payload: dict[str, Any] = {
        "ok": True,
        "target_kind": target.target_kind,
        "target_id": target.target_id,
        "changed": result.changed,
        "staging_path": result.preview.get("staging_path"),
        "target_path": result.preview.get("target_path"),
        "target_exists": result.preview.get("target_exists"),
        "content_sha256": result.preview.get("content_sha256"),
        "warnings": result.preview.get("warnings", []),
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = result.changed
    elif result.changed:
        payload["imported_at_utc"] = activity.utc_now()
    log_event(
        context.repo_root,
        "catalogue_prose_import_apply",
        {
            "target_kind": target.target_kind,
            "target_id": target.target_id,
            "changed": result.changed,
            "dry_run": context.dry_run,
        },
    )
    return HTTPStatus.OK, payload


def moment_import_apply_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    result = prose_import.apply_moment_import(
        context.repo_root,
        context.source_dir,
        body,
        allowed_write_roots=context.allowed_write_roots,
        backups_dir=context.backups_dir,
        dry_run=context.dry_run,
    )
    moment_id = result.moment_id
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_IMPORT_MOMENT,
        record_id=moment_id,
    )

    payload: dict[str, Any] = {
        "ok": True,
        "moment_file": result.moment_file,
        "moment_id": moment_id,
        "status": "draft",
        "published": False,
        "preview": result.preview,
        "build": {},
        "steps": [],
        "public_url": "",
        "metadata_path": str(result.preview.get("metadata_path") or ""),
        "target_path": str(result.preview.get("target_path") or ""),
    }
    if activity_context:
        payload["activity_context"] = activity_context
    if context.dry_run:
        payload["dry_run"] = True
    if result.backup_paths:
        payload["backups"] = [context.rel_path(path) for path in result.backup_paths]
    if not context.dry_run:
        payload["completed_at_utc"] = activity.utc_now()
        if activity_context:
            append_activity_rows(
                context.repo_root,
                payload,
                [
                    activity.studio_activity_entry(
                        activity_context,
                        now_utc=payload["completed_at_utc"],
                        script_purpose_id="import-source-data",
                        status="completed",
                        record_groups=activity.activity_record_groups(moments=[moment_id]),
                        detail_items=[
                            f"Imported draft moment source {moment_id}",
                            f"Wrote body-only moment prose to {context.rel_path(result.target_path)}",
                            f"Saved canonical moment metadata for {moment_id}",
                        ],
                        source_refs=activity.catalogue_log_source_ref(),
                    )
                ],
            )
    return payload


def run_build_operation(
    context: CatalogueWriteContext,
    *,
    work_id: str,
    series_id: str,
    moment_id: str = "",
    extra_series_ids: list[str],
    extra_work_ids: list[str],
    detail_uid: str,
    force: bool,
    media_only: bool = False,
    build_plan: Mapping[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    if work_id:
        scope = build_scope_for_work(
            context.source_dir,
            work_id,
            extra_series_ids=extra_series_ids,
            detail_uid=detail_uid,
        )
    elif series_id:
        scope = build_scope_for_series(context.source_dir, series_id, extra_work_ids=extra_work_ids)
    else:
        scope = build_scope_for_moment(context.repo_root, f"{moment_id}.md", force=force)
    if build_plan:
        apply_field_build_plan_to_scope(scope, build_plan)
    result = run_scoped_build_scope(
        context.repo_root,
        scope=scope,
        write=not context.dry_run,
        force=force,
        media_only=media_only,
    )

    payload: dict[str, Any] = {
        "ok": result.get("status") == "completed",
        "work_id": work_id,
        "series_id": series_id,
        "moment_id": moment_id,
        "detail_uid": detail_uid,
        "force": force,
        "media_only": media_only,
        "build": result.get("scope"),
        "field_plan": dict(build_plan) if build_plan else None,
        "media": result.get("media"),
        "steps": result.get("steps", []),
    }
    if context.dry_run:
        payload["dry_run"] = True
    if result.get("status") != "completed":
        payload["error"] = str(result.get("error") or "Scoped JSON build failed.")
        payload["failed_step"] = result.get("failed_step")
        return False, payload
    if not context.dry_run:
        payload["completed_at_utc"] = activity.utc_now()
    return True, payload


def load_moments_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    moments = payload.get("moments")
    if not isinstance(moments, dict):
        raise ValueError("moments source file must include a moments object")
    return payload


def load_works_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("works source file must include a works object")
    return payload


def load_work_details_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    work_details = payload.get("work_details")
    if not isinstance(work_details, dict):
        raise ValueError("work details source file must include a work_details object")
    return payload


def load_series_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    series = payload.get("series")
    if not isinstance(series, dict):
        raise ValueError("series source file must include a series object")
    return payload


def refresh_lookup_payloads(context: CatalogueWriteContext) -> dict[str, Any]:
    result = lookup_refresh.full_lookup_refresh(context.source_dir, context.lookup_dir, context.repo_root)
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_work_change(
    context: CatalogueWriteContext,
    work_id: str,
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="work",
        changed_field_names=list(build_plan.get("fields") or []),
        build_plan=build_plan,
    )
    result = lookup_refresh.work_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        work_id=work_id,
        current_record=current_record,
        updated_record=updated_record,
        lookup_plan=lookup_plan,
    )
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "work_id": work_id,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_detail_change(
    context: CatalogueWriteContext,
    detail_uid: str,
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="work_detail",
        changed_field_names=list(build_plan.get("fields") or []),
        build_plan=build_plan,
    )
    result = lookup_refresh.detail_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        detail_uid=detail_uid,
        updated_record=updated_record,
        lookup_plan=lookup_plan,
    )
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "detail_uid": detail_uid,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_series_change(
    context: CatalogueWriteContext,
    series_id: str,
    fields_changed: list[str],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="series",
        changed_field_names=list(build_plan.get("fields") or fields_changed),
        build_plan=build_plan,
    )
    result = lookup_refresh.series_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        series_id=series_id,
        lookup_plan=lookup_plan,
    )
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "series_id": series_id,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def lookup_refresh_response_for_plan(lookup_plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "mode": lookup_plan["mode"],
        "invalidation_class": lookup_plan["class"],
        "artifacts": lookup_plan["artifacts"],
        "unknown_fields": lookup_plan["unknown_fields"],
    }


def focused_lookup_refresh_response(refresh_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "mode": refresh_result["mode"],
        "invalidation_class": refresh_result["invalidation_class"],
        "artifacts": refresh_result["artifacts"],
        "unknown_fields": refresh_result["unknown_fields"],
        "written_count": refresh_result["written_count"],
    }


def normalize_moment_id_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("moment_id is required")
    return normalize_moment_filename(text if text.endswith(".md") else f"{text}.md")[:-3]


def extract_generic_build_request(body: Mapping[str, Any]) -> tuple[str, str, str, list[str], list[str], bool]:
    work_id = str(body.get("work_id") or "").strip()
    series_id = str(body.get("series_id") or "").strip()
    moment_value = str(body.get("moment_id") or body.get("moment_file") or "").strip()
    if sum(1 for value in (work_id, series_id, moment_value) if value) != 1:
        raise ValueError("build request must include exactly one of work_id, series_id, or moment_id")
    normalized_work_id = slug_id(work_id) if work_id else ""
    normalized_series_id = normalize_series_id(series_id) if series_id else ""
    normalized_moment_id = normalize_moment_id_value(moment_value) if moment_value else ""
    extra_series_ids = normalize_series_ids_value(body.get("extra_series_ids"))
    extra_work_ids = [slug_id(raw) for raw in body.get("extra_work_ids") or []]
    return normalized_work_id, normalized_series_id, normalized_moment_id, extra_series_ids, extra_work_ids, bool(body.get("force"))


def extract_changed_field_names(body: Mapping[str, Any]) -> list[str]:
    raw = body.get("changed_fields")
    if raw is None:
        raw = body.get("fields")
    if raw is None:
        return []
    raw_values = raw if isinstance(raw, list) else [raw]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        for part in str(value or "").split(","):
            field = part.strip()
            if not field or field in seen:
                continue
            seen.add(field)
            out.append(field)
    return out


def extract_apply_build(body: Mapping[str, Any]) -> bool:
    return bool(body.get("apply_build"))


def extract_delete_request(body: Mapping[str, Any]) -> dict[str, str]:
    kind = str(body.get("kind") or "").strip().lower()
    if kind not in {"work", "work_detail", "series", "moment"}:
        raise ValueError("delete kind must be work, work_detail, series, or moment")
    if kind == "work":
        record_id = slug_id(body.get("work_id") or body.get("id"))
    elif kind == "work_detail":
        record_id = normalize_detail_uid_value(body.get("detail_uid") or body.get("id"))
    elif kind == "series":
        record_id = normalize_series_id(body.get("series_id") or body.get("id"))
    else:
        record_id = normalize_moment_id_value(body.get("moment_id") or body.get("id"))
    return {
        "kind": kind,
        "id": record_id,
    }


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


def extract_work_detail_update(body: Mapping[str, Any]) -> dict[str, Any]:
    raw_record = body.get("record", body.get("work_detail"))
    if raw_record is None:
        raw_record = {field: body[field] for field in DETAIL_FIELDS if field in body}
    if not isinstance(raw_record, dict):
        raise ValueError("record must be an object")
    unknown = sorted(str(key) for key in raw_record.keys() if str(key) not in DETAIL_FIELDS)
    if unknown:
        raise ValueError(f"record contains unsupported fields: {', '.join(unknown)}")
    if not raw_record:
        raise ValueError("record must include at least one work detail field")
    return dict(raw_record)


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


def log_event(repo_root: Path, event: str, details: Mapping[str, Any] | None = None) -> None:
    try:
        append_script_log(
            Path(__file__),
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        pass


def append_activity_rows(repo_root: Path, response_payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    try:
        append_studio_activity(repo_root, rows)
    except Exception:
        pass
    activity.increment_studio_activity_count(response_payload, len(rows))
