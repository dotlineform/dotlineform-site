"""Catalogue work-detail section create service routes for Local Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

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
    next_detail_section_id,
    normalize_source_record,
    normalize_status,
    normalize_text,
    records_from_json_source,
    slug_id,
    sort_record_map,
    validate_source_records,
    work_details_payload_for_maps,
)
from catalogue.project_state_report import IMAGE_EXTENSIONS
from local_env import runtime_env
from pipeline_config import source_works_root_subdir


def create_detail_section_payload(context: CatalogueWriteContext, body: Mapping[str, Any]) -> dict[str, Any]:
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
        payload["lookup_refresh"] = refresh_lookup_payloads(context)
        payload["build_requested"] = True
        payload["build"] = build_created_details(context, work_id, sorted(created_details))

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


def build_created_details(context: CatalogueWriteContext, work_id: str, detail_uids: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for index, detail_uid in enumerate(detail_uids):
        success, build_payload = run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            moment_id="",
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
