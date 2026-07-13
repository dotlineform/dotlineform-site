"""Catalogue work-detail section service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from catalogue import catalogue_activity as activity
from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_media import PIPELINE_CONFIG, detect_projects_base_dir, read_image_dims_px
from catalogue.catalogue_build_service import run_build_operation
from catalogue.catalogue_generation_common import compact_json_object
from catalogue.catalogue_service_context import (
    CatalogueWriteContext,
    log_event,
    refresh_lookup_payloads,
)
from catalogue.catalogue_source import (
    DETAIL_FIELDS,
    DETAIL_SECTION_FIELDS,
    CatalogueSourceRecords,
    normalize_detail_sort_value,
    next_detail_section_id,
    normalize_source_record,
    normalize_status,
    normalize_optional_int,
    normalize_text,
    ordered_work_detail_sections,
    records_from_json_source,
    slug_id,
    sort_record_map,
    validate_source_records,
    work_details_payload_for_maps,
)
from catalogue.project_state_report import IMAGE_EXTENSIONS
from local_env import runtime_env
from pipeline_config import source_works_root_subdir
from studio.services.media.publish_media_to_r2 import run_catalogue_upload_targets


DetailMediaPublisher = Callable[..., Mapping[str, object]]


def _default_detail_media_publisher(**kwargs: Any) -> Mapping[str, object]:
    return run_catalogue_upload_targets(**kwargs)


def _detail_media_target_payload(detail_uid: str) -> dict[str, str]:
    return {"kind": "work_details", "id": detail_uid}


def _detail_media_publish_warning(detail_uids: Sequence[str]) -> dict[str, Any]:
    return {
        "status": "warning",
        "target_count": len(detail_uids),
        "object_count": len(detail_uids) * 3,
        "uploaded": 0,
        "unchanged": 0,
        "failed": len(detail_uids) * 3,
        "failed_targets": [_detail_media_target_payload(detail_uid) for detail_uid in detail_uids],
    }


def _compact_detail_media_publish(
    report: Mapping[str, object],
    detail_uids: Sequence[str],
) -> dict[str, Any]:
    raw_counts = report.get("counts") if isinstance(report.get("counts"), Mapping) else {}
    counts: dict[str, int] = {}
    for key, value in raw_counts.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count:
            counts[str(key)] = count

    successful_object_statuses = {"uploaded", "overwritten", "unchanged"}
    successful_version_statuses = {"promoted", "current"}
    failed_detail_uids = {
        str(item.get("item_id") or "")
        for item in report.get("objects") or []
        if isinstance(item, Mapping)
        and str(item.get("status") or "") not in successful_object_statuses
    }
    finalized_detail_uids = {
        str(item.get("item_id") or "")
        for item in report.get("media_versions") or []
        if isinstance(item, Mapping)
        and str(item.get("status") or "") in successful_version_statuses
    }
    failed_detail_uids.update(
        detail_uid for detail_uid in detail_uids if detail_uid not in finalized_detail_uids
    )
    failed_object_count = sum(
        count for status, count in counts.items() if status not in successful_object_statuses
    )
    return {
        "status": "warning" if failed_detail_uids else "completed",
        "target_count": len(detail_uids),
        "object_count": sum(counts.values()),
        "uploaded": counts.get("uploaded", 0) + counts.get("overwritten", 0),
        "unchanged": counts.get("unchanged", 0),
        "failed": max(failed_object_count, len(failed_detail_uids)),
        "failed_targets": [
            _detail_media_target_payload(detail_uid)
            for detail_uid in sorted(failed_detail_uids)
            if detail_uid
        ],
    }


def publish_created_detail_media(
    context: CatalogueWriteContext,
    detail_uids: Sequence[str],
    remote_publish_runner: DetailMediaPublisher,
) -> dict[str, Any]:
    try:
        report = remote_publish_runner(
            repo_root=context.repo_root,
            targets=[("work_details", detail_uid) for detail_uid in detail_uids],
            write=True,
            force=False,
            changed_only=False,
            allow_partial=False,
        )
    except (Exception, SystemExit):
        return _detail_media_publish_warning(detail_uids)
    return _compact_detail_media_publish(report, detail_uids)


def create_detail_section_payload(
    context: CatalogueWriteContext,
    body: Mapping[str, Any],
    *,
    remote_publish_runner: DetailMediaPublisher = _default_detail_media_publisher,
) -> dict[str, Any]:
    request = extract_create_detail_section_request(body)
    work_id = request["work_id"]
    project_subfolder = request["project_subfolder"]
    filenames = request["filenames"]

    source_records = records_from_json_source(context.source_dir)
    work_record = source_records.works.get(work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {work_id}")
    if normalize_status(work_record.get("status")) != "published":
        raise ValueError(f"parent work {work_id} must be published before adding work details")

    project_folder = normalize_text(work_record.get("project_folder"))
    requested_project_folder = request["project_folder"]
    if requested_project_folder and requested_project_folder != project_folder:
        raise ValueError("project_folder does not match the current work")
    if not project_folder:
        raise ValueError("current work has no project_folder")

    existing_section = find_existing_section_for_subfolder(source_records, work_id, project_subfolder)
    if existing_section:
        section_id = normalize_text(existing_section.get("section_id"))
        log_event(
            context.repo_root,
            "catalogue_detail_section_create",
            {
                "work_id": work_id,
                "section_id": section_id,
                "details_subfolder": project_subfolder,
                "changed": False,
                "reason": "section_exists",
                "dry_run": context.dry_run,
            },
        )
        return {
            "ok": True,
            "changed": False,
            "reason": "section_exists",
            "work_id": work_id,
            "section_id": section_id,
            "section": dict(existing_section),
            "created_detail_uids": [],
            "created_count": 0,
        }

    folder_path = resolve_project_detail_folder(context, project_folder, project_subfolder)
    valid_files = visible_image_filenames(folder_path)
    missing_files = [filename for filename in filenames if filename not in valid_files]
    if missing_files:
        raise ValueError("selected file(s) not found in detail subfolder: " + ", ".join(missing_files[:10]))

    section_id = next_detail_section_id(
        work_id,
        source_records.work_details.values(),
        source_records.work_detail_sections.values(),
    )
    section_record = normalize_source_record(
        {
            "section_id": section_id,
            "work_id": work_id,
            "details_subfolder": project_subfolder,
            "section_title": project_subfolder,
        },
        DETAIL_SECTION_FIELDS,
    )

    next_detail_number = next_detail_id_number(work_id, source_records.work_details.values())
    created_details: dict[str, dict[str, Any]] = {}
    for offset, filename in enumerate(filenames):
        detail_id = str(next_detail_number + offset).zfill(3)
        detail_uid = f"{work_id}-{detail_id}"
        if detail_uid in source_records.work_details:
            raise ValueError(f"detail_uid already exists: {detail_uid}")
        width_px, height_px = read_image_dims_px(folder_path / filename)
        detail_payload = {
            "detail_uid": detail_uid,
            "work_id": work_id,
            "detail_id": detail_id,
            "section_id": section_id,
            "project_filename": filename,
            "media_version": 1,
            "title": filename_stem(filename),
        }
        if width_px is not None and height_px is not None:
            detail_payload["width_px"] = width_px
            detail_payload["height_px"] = height_px
        detail_record = normalize_source_record(
            detail_payload,
            DETAIL_FIELDS,
        )
        created_details[detail_uid] = compact_json_object(detail_record)

    next_sections = dict(source_records.work_detail_sections)
    next_sections[section_id] = section_record
    next_details = dict(source_records.work_details)
    next_details.update(created_details)
    validation_records = CatalogueSourceRecords(
        works=source_records.works,
        work_detail_sections=sort_record_map(next_sections),
        work_details=sort_record_map(next_details),
        series=source_records.series,
    )
    validation_errors = validate_source_records(validation_records, allow_compat_detail_project_subfolder=False)
    if validation_errors:
        raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

    target_path = context.work_details_path.resolve()
    if target_path not in context.allowed_write_paths:
        raise ValueError("write target not allowlisted")
    changed = True
    if changed:
        transactions.execute_source_json_write(
            {
                target_path: work_details_payload_for_maps(
                    next_sections,
                    next_details,
                )
            },
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload: dict[str, Any] = {
        "ok": True,
        "changed": changed,
        "created": True,
        "work_id": work_id,
        "section_id": section_id,
        "section": section_record,
        "created_detail_uids": sorted(created_details),
        "created_count": len(created_details),
        "records": [
            {"detail_uid": detail_uid, "record": record}
            for detail_uid, record in sorted(created_details.items())
        ],
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = changed
    else:
        payload["saved_at_utc"] = activity.utc_now()
        payload["build_requested"] = True
        build_result = build_created_details(context, work_id, sorted(created_details))
        payload["build"] = build_result
        if build_result["ok"]:
            remote_publish = publish_created_detail_media(
                context,
                sorted(created_details),
                remote_publish_runner,
            )
            payload["r2_media"] = remote_publish
            if remote_publish["status"] == "warning":
                payload["warning"] = "Detail section was created, but R2 media publishing did not complete."
            confirmed_details = records_from_json_source(context.source_dir).work_details
            payload["records"] = [
                {"detail_uid": detail_uid, "record": confirmed_details[detail_uid]}
                for detail_uid in sorted(created_details)
                if detail_uid in confirmed_details
            ]
        payload["lookup_refresh"] = refresh_lookup_payloads(context)

    log_event(
        context.repo_root,
        "catalogue_detail_section_create",
        {
            "work_id": work_id,
            "section_id": section_id,
            "details_subfolder": project_subfolder,
            "created_count": len(created_details),
            "changed": changed,
            "dry_run": context.dry_run,
        },
    )
    return payload


def save_detail_section_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
    request = extract_save_detail_section_request(body)
    work_id = request["work_id"]
    section_id = request["section_id"]

    source_records = records_from_json_source(context.source_dir)
    section_record = source_records.work_detail_sections.get(section_id)
    if not isinstance(section_record, dict):
        raise ValueError(f"section_id not found: {section_id}")
    if normalize_text(section_record.get("work_id")) != work_id:
        raise ValueError("section_id does not belong to work_id")

    next_sections = {key: dict(value) for key, value in source_records.work_detail_sections.items()}
    next_record = dict(section_record)
    next_record["section_title"] = request["section_title"]
    if request["detail_sort"] == "title":
        next_record["detail_sort"] = "title"
    else:
        next_record.pop("detail_sort", None)
    next_sections[section_id] = normalize_source_record(
        next_record,
        DETAIL_SECTION_FIELDS,
    )

    current_sections = ordered_work_detail_sections(source_records, work_id)
    requested_position = request["section_position"]
    if requested_position is not None and len(current_sections) > 1:
        ordered_section_ids = [normalize_text(section.get("section_id")) for section in current_sections]
        if section_id not in ordered_section_ids:
            raise ValueError("section_id not found in current work order")
        ordered_section_ids.remove(section_id)
        to_index = max(0, min(requested_position - 1, len(ordered_section_ids)))
        ordered_section_ids.insert(to_index, section_id)
        for index, ordered_section_id in enumerate(ordered_section_ids, start=1):
            section = dict(next_sections[ordered_section_id])
            section["section_order"] = index
            next_sections[ordered_section_id] = normalize_source_record(
                section,
                DETAIL_SECTION_FIELDS,
            )

    validation_records = CatalogueSourceRecords(
        works=source_records.works,
        work_detail_sections=sort_record_map(next_sections),
        work_details=source_records.work_details,
        series=source_records.series,
    )
    validation_errors = validate_source_records(validation_records, allow_compat_detail_project_subfolder=False)
    if validation_errors:
        raise ValueError("source validation failed: " + "; ".join(validation_errors[:20]))

    target_path = context.work_details_path.resolve()
    if target_path not in context.allowed_write_paths:
        raise ValueError("write target not allowlisted")

    changed = sort_record_map(next_sections) != sort_record_map(source_records.work_detail_sections)
    if changed:
        transactions.execute_source_json_write(
            {
                target_path: work_details_payload_for_maps(
                    next_sections,
                    source_records.work_details,
                )
            },
            dry_run=context.dry_run,
            repo_root=context.repo_root,
        )

    payload: dict[str, Any] = {
        "ok": True,
        "changed": changed,
        "work_id": work_id,
        "section_id": section_id,
        "section": next_sections[section_id],
    }
    if context.dry_run:
        payload["dry_run"] = True
        payload["would_write"] = changed
    elif changed:
        payload["saved_at_utc"] = activity.utc_now()
        payload["lookup_refresh"] = refresh_lookup_payloads(context)
        payload["build_requested"] = True
        success, build_payload = run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            extra_series_ids=[],
            extra_work_ids=[],
            detail_uid="",
            force=False,
        )
        payload["build"] = build_payload
        if not success:
            payload["build_failed"] = True
    log_event(
        context.repo_root,
        "catalogue_detail_section_save",
        {
            "work_id": work_id,
            "section_id": section_id,
            "changed": changed,
            "dry_run": context.dry_run,
        },
    )
    return payload


def build_created_details(context: CatalogueWriteContext, work_id: str, detail_uids: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for index, detail_uid in enumerate(detail_uids):
        success, build_payload = run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            extra_series_ids=[],
            extra_work_ids=[],
            detail_uid=detail_uid,
            force=False,
        )
        results.append(
            {
                "detail_uid": detail_uid,
                "ok": success,
                "completed_at_utc": build_payload.get("completed_at_utc"),
                "error": build_payload.get("error"),
                "failed_step": build_payload.get("failed_step"),
                "media": build_payload.get("media"),
            }
        )
        if not success:
            return {
                "ok": False,
                "requested_count": len(detail_uids),
                "completed_count": index,
                "details": results,
                "remaining_detail_uids": detail_uids[index:],
                "error": build_payload.get("error"),
                "failed_step": build_payload.get("failed_step"),
            }
    return {
        "ok": True,
        "requested_count": len(detail_uids),
        "completed_count": len(detail_uids),
        "details": results,
        "remaining_detail_uids": [],
        "completed_at_utc": activity.utc_now(),
    }


def extract_create_detail_section_request(body: Mapping[str, Any]) -> dict[str, Any]:
    work_id = slug_id(body.get("work_id"))
    project_folder = normalize_optional_segment(body.get("project_folder"), "project_folder")
    project_subfolder = normalize_required_segment(body.get("project_subfolder"), "project_subfolder")
    raw_filenames = body.get("filenames")
    if not isinstance(raw_filenames, list) or not raw_filenames:
        raise ValueError("filenames must be a non-empty array")
    filenames: list[str] = []
    seen: set[str] = set()
    for raw_filename in raw_filenames:
        filename = normalize_image_filename(raw_filename)
        key = filename.lower()
        if key in seen:
            continue
        seen.add(key)
        filenames.append(filename)
    if not filenames:
        raise ValueError("filenames must include at least one image filename")
    return {
        "work_id": work_id,
        "project_folder": project_folder,
        "project_subfolder": project_subfolder,
        "filenames": filenames,
    }


def extract_save_detail_section_request(body: Mapping[str, Any]) -> dict[str, Any]:
    work_id = slug_id(body.get("work_id"))
    section_id = normalize_text(body.get("section_id"))
    if not section_id:
        raise ValueError("section_id is required")
    section_title = normalize_text(body.get("section_title"))
    if not section_title:
        raise ValueError("section_title is required")
    raw_position = body.get("section_position")
    section_position = normalize_optional_int(raw_position)
    if raw_position is not None and normalize_text(raw_position) and section_position is None:
        raise ValueError("section_position must be a whole number")
    if section_position is not None and section_position < 1:
        raise ValueError("section_position must be one or greater")
    raw_detail_sort = normalize_text(body.get("detail_sort"))
    detail_sort_input = "detail_id" if raw_detail_sort == "id" else raw_detail_sort
    detail_sort = normalize_detail_sort_value(detail_sort_input) or ""
    if raw_detail_sort and not detail_sort:
        raise ValueError("detail_sort must be id, detail_id, or title")
    return {
        "work_id": work_id,
        "section_id": section_id,
        "section_title": section_title,
        "section_position": section_position,
        "detail_sort": detail_sort or "detail_id",
    }


def normalize_required_segment(value: Any, field: str) -> str:
    text = normalize_text(value)
    if not text:
        raise ValueError(f"{field} is required")
    path = Path(text)
    if path.is_absolute() or len(path.parts) != 1:
        raise ValueError(f"{field} must be a single path segment")
    part = path.parts[0]
    if part in {"", ".", ".."} or part.startswith("."):
        raise ValueError(f"{field} must be a visible folder name")
    return part


def normalize_optional_segment(value: Any, field: str) -> str:
    text = normalize_text(value)
    return normalize_required_segment(text, field) if text else ""


def normalize_image_filename(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        raise ValueError("filename is required")
    path = Path(text)
    if path.is_absolute() or len(path.parts) != 1:
        raise ValueError("filename must be a single path segment")
    filename = path.parts[0]
    if filename in {"", ".", ".."} or filename.startswith("."):
        raise ValueError("filename must be visible")
    if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"unsupported image filename: {filename}")
    return filename


def resolve_project_detail_folder(context: CatalogueWriteContext, project_folder: str, project_subfolder: str) -> Path:
    projects_base_dir = detect_projects_base_dir(runtime_env(repo_root=context.repo_root))
    projects_root = (projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)).resolve()
    folder_path = (projects_root / project_folder / project_subfolder).resolve()
    try:
        folder_path.relative_to(projects_root)
    except ValueError as error:
        raise ValueError("detail media path must stay inside the projects root") from error
    if not folder_path.is_dir():
        raise ValueError("detail media folder does not exist")
    return folder_path


def visible_image_filenames(folder_path: Path) -> set[str]:
    return {
        child.name
        for child in folder_path.iterdir()
        if child.is_file() and not child.name.startswith(".") and child.suffix.lower() in IMAGE_EXTENSIONS
    }


def find_existing_section_for_subfolder(
    source_records: CatalogueSourceRecords,
    work_id: str,
    project_subfolder: str,
) -> dict[str, Any] | None:
    target = project_subfolder.lower()
    for section in source_records.work_detail_sections.values():
        if normalize_text(section.get("work_id")) != work_id:
            continue
        if normalize_text(section.get("details_subfolder")).lower() == target:
            return dict(section)
    return None


def next_detail_id_number(work_id: str, detail_records: Iterable[Mapping[str, Any]]) -> int:
    max_number = 0
    for record in detail_records:
        if normalize_text(record.get("work_id")) != work_id:
            continue
        detail_id = normalize_text(record.get("detail_id"))
        if not detail_id.isdigit():
            continue
        max_number = max(max_number, int(detail_id))
    return max_number + 1


def filename_stem(filename: str) -> str:
    path = Path(filename)
    return path.stem or filename
