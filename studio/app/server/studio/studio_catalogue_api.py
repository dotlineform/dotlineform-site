"""Local Studio app adapter for narrow Catalogue-owned routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import sys
from typing import Any, Mapping

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_DIR = Path(__file__).resolve().parent
for candidate in (SCRIPTS_DIR, STUDIO_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue import catalogue_activity as activity  # noqa: E402
from catalogue import catalogue_prose_import as prose_import  # noqa: E402
from catalogue import catalogue_lookup_refresh as lookup_refresh  # noqa: E402
from catalogue import catalogue_write_service  # noqa: E402
from catalogue.catalogue_lookup import (  # noqa: E402
    DEFAULT_LOOKUP_DIR,
    build_series_lookup_payload,
    build_series_search_payload,
    build_work_detail_lookup_payload,
    build_work_detail_search_payload,
    build_work_lookup_payload,
    build_work_search_payload,
)
from catalogue.catalogue_source import (  # noqa: E402
    DEFAULT_SOURCE_DIR,
    SOURCE_FILES,
    load_json_file,
    normalize_detail_uid_value,
    payload_for_map,
    records_from_json_source,
    slug_id,
)
from catalogue.catalogue_transactions import execute_source_json_write  # noqa: E402
from catalogue.catalogue_workbook_import import (  # noqa: E402
    DEFAULT_IMPORT_WORKBOOK_PATH,
    IMPORT_MODE_WORKS,
    apply_workbook_import_plan,
    build_workbook_import_plan,
    normalize_import_mode,
    plan_to_response,
)
from catalogue.moment_sources import CATALOGUE_MOMENT_PROSE_REL_DIR, MOMENT_METADATA_FILENAME  # noqa: E402
from catalogue.project_state_report import (  # noqa: E402
    DEFAULT_OUTPUT_REL_PATH,
    PROJECTS_BASE_DIR_ENV_NAME,
    build_project_state_report,
    open_project_state_report,
    resolve_projects_base_dir,
)
from catalogue.series_ids import normalize_series_id  # noqa: E402
from local_env import runtime_env  # noqa: E402
from script_logging import append_script_log  # noqa: E402
from studio_activity import append_studio_activity  # noqa: E402


LOGS_REL_DIR = Path("var/studio/catalogue/logs")
PROJECT_STATE_REPORT_API_PATH = "/studio/api/catalogue/project-state-report"
CATALOGUE_READ_KEYS = {
    "catalogue_works",
    "catalogue_work_details",
    "catalogue_series",
    "catalogue_moments",
    "catalogue_lookup_work_search",
    "catalogue_lookup_series_search",
    "catalogue_lookup_work_detail_search",
    "catalogue_lookup_work_base",
    "catalogue_lookup_work_detail_base",
    "catalogue_lookup_series_base",
}

def catalogue_get_payload(repo_root: Path, api_path: str, query: Mapping[str, list[str]] | None = None) -> dict[str, Any]:
    if api_path == "/health":
        return {
            "ok": True,
            "service": "studio_catalogue",
            "routes": [
                "read",
                "bulk-save",
                "delete-preview",
                "delete-apply",
                "publication-preview",
                "publication-apply",
                "work/create",
                "work/save",
                "work-detail/create",
                "work-detail/save",
                "series/create",
                "series/save",
                "build-preview",
                "build-apply",
                "prose/import-preview",
                "prose/import-apply",
                "moment/import-preview",
                "moment/import-apply",
                "moment/preview",
                "moment/save",
                "import-preview",
                "import-apply",
                "project-state-report",
                "project-state-open-report",
            ],
        }
    if api_path == "/read":
        return catalogue_read_payload(repo_root, query or {})
    raise FileNotFoundError(f"Unknown catalogue API route: {api_path}")


def catalogue_post_response(
    repo_root: Path,
    api_path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, Any]]:
    if api_path == "/project-state-report":
        return HTTPStatus.OK, project_state_report_payload(repo_root, body, dry_run=dry_run)
    if api_path == "/project-state-open-report":
        return HTTPStatus.OK, open_project_state_report_payload(repo_root, body, dry_run=dry_run)
    if api_path == "/import-preview":
        return HTTPStatus.OK, import_preview_payload(repo_root, body)
    if api_path == "/import-apply":
        return import_apply_response(repo_root, body, dry_run=dry_run)
    if api_path in catalogue_write_service.SERVICE_POST_PATHS:
        return catalogue_write_service.handle_catalogue_post(repo_root, api_path, body, dry_run=dry_run)
    raise FileNotFoundError(f"Unknown catalogue API route: {api_path}")


def catalogue_read_payload(repo_root: Path, query: Mapping[str, list[str]]) -> dict[str, Any]:
    key = str((query.get("key") or [""])[0] or "").strip()
    record_id = str((query.get("record_id") or [""])[0] or "").strip()
    if key not in CATALOGUE_READ_KEYS:
        raise ValueError(f"unsupported catalogue read key: {key}")

    paths = catalogue_paths(repo_root)
    if key == "catalogue_works":
        return load_source_payload(paths["works_path"], "works")
    if key == "catalogue_work_details":
        return load_source_payload(paths["work_details_path"], "work_details")
    if key == "catalogue_series":
        return load_source_payload(paths["series_path"], "series")
    if key == "catalogue_moments":
        return load_source_payload(paths["moments_path"], "moments")

    source_records = records_from_json_source(paths["source_dir"])
    if key == "catalogue_lookup_work_search":
        return build_work_search_payload(source_records)
    if key == "catalogue_lookup_series_search":
        return build_series_search_payload(source_records)
    if key == "catalogue_lookup_work_detail_search":
        return build_work_detail_search_payload(source_records)
    if key == "catalogue_lookup_work_base":
        work_id = slug_id(record_id)
        if not work_id:
            raise ValueError("record_id is required for work lookup reads")
        return build_work_lookup_payload(source_records, work_id)
    if key == "catalogue_lookup_work_detail_base":
        detail_uid = normalize_detail_uid_value(record_id)
        if not detail_uid:
            raise ValueError("record_id is required for work detail lookup reads")
        return build_work_detail_lookup_payload(source_records, detail_uid)
    if key == "catalogue_lookup_series_base":
        series_id = normalize_series_id(record_id)
        if not series_id:
            raise ValueError("record_id is required for series lookup reads")
        return build_series_lookup_payload(source_records, series_id)
    raise ValueError(f"unsupported catalogue read key: {key}")


def import_preview_payload(repo_root: Path, body: Mapping[str, Any]) -> dict[str, Any]:
    mode = normalize_import_mode(body.get("mode"))
    paths = catalogue_paths(repo_root)
    plan = build_workbook_import_plan(paths["source_dir"], (repo_root / DEFAULT_IMPORT_WORKBOOK_PATH).resolve(), mode)
    return {"ok": True, "mode": mode, "preview": plan_to_response(plan, repo_root=repo_root)}


def import_apply_response(repo_root: Path, body: Mapping[str, Any], *, dry_run: bool = False) -> tuple[HTTPStatus, dict[str, Any]]:
    mode = normalize_import_mode(body.get("mode"))
    activity_context = activity.normalize_activity_context_for_profile(
        body.get("activity_context"),
        activity.ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS,
        record_id=mode,
    )
    paths = catalogue_paths(repo_root)
    plan = build_workbook_import_plan(paths["source_dir"], (repo_root / DEFAULT_IMPORT_WORKBOOK_PATH).resolve(), mode)
    preview_payload = plan_to_response(plan, repo_root=repo_root)
    if plan.blocked_count > 0:
        return HTTPStatus.BAD_REQUEST, {
            "ok": False,
            "error": "import preview contains blocked rows",
            "mode": mode,
            "preview": preview_payload,
        }

    changed = plan.importable_count > 0
    target_kind = plan.target_kind
    if changed and not dry_run:
        updated_records = apply_workbook_import_plan(paths["source_dir"], plan)
        target_path = paths["works_path"] if target_kind == "works" else paths["work_details_path"]
        payload_key = "works" if target_kind == "works" else "work_details"
        payload_records = updated_records.works if target_kind == "works" else updated_records.work_details
        if target_path not in paths["allowed_write_paths"]:
            raise ValueError("write target not allowlisted")
        execute_source_json_write(
            {target_path: payload_for_map(payload_key, payload_records)},
            dry_run=dry_run,
            repo_root=repo_root,
        )
        refresh_lookup_payloads(repo_root, paths["source_dir"], paths["lookup_dir"])

    response_payload: dict[str, Any] = {
        "ok": True,
        "mode": mode,
        "changed": changed,
        "imported_count": plan.importable_count,
        "duplicate_count": plan.duplicate_count,
        "target_kind": target_kind,
        "preview": preview_payload,
    }
    if activity_context:
        response_payload["activity_context"] = activity_context
    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = changed
    elif changed:
        response_payload["saved_at_utc"] = activity.utc_now()

    log_event(
        repo_root,
        "catalogue_import_apply",
        {
            "mode": mode,
            "imported_count": plan.importable_count,
            "duplicate_count": plan.duplicate_count,
            "blocked_count": plan.blocked_count,
            "dry_run": dry_run,
        },
    )
    if not dry_run and activity_context:
        imported_ids = sorted(plan.importable_records.keys())
        record_groups = activity.activity_record_groups(
            works=imported_ids if mode == IMPORT_MODE_WORKS else [],
            work_details=imported_ids if mode != IMPORT_MODE_WORKS else [],
        )
        detail_label = "work" if mode == IMPORT_MODE_WORKS else "work detail"
        now_utc = activity.utc_now()
        append_studio_activity(
            repo_root,
            [
                activity.studio_activity_entry(
                    activity_context,
                    now_utc=now_utc,
                    script_purpose_id="import-source-data",
                    status="completed",
                    record_groups=record_groups,
                    detail_items=[
                        f"Imported {plan.importable_count} {detail_label} record(s) from workbook",
                        f"{plan.duplicate_count} duplicate record(s) already existed",
                        f"Candidate rows reviewed: {plan.total_candidate_rows}",
                    ],
                    source_refs=[
                        {"kind": "source", "path": str(DEFAULT_IMPORT_WORKBOOK_PATH)},
                        {"kind": "log", "path": str(LOGS_REL_DIR / "studio_catalogue_api.log")},
                    ],
                ),
                activity.catalogue_lookup_activity_row(
                    activity_context,
                    now_utc=now_utc,
                    record_groups=record_groups,
                    detail_items=[f"Refreshed catalogue lookup data after workbook {detail_label} import"],
                ),
            ],
        )
        activity.increment_studio_activity_count(response_payload, 2)
    return HTTPStatus.OK, response_payload


def project_state_report_payload(
    repo_root: Path,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    include_subfolders = bool(body.get("include_subfolders"))
    activity_context = activity.normalize_activity_context(
        body.get("activity_context"),
        page_id=activity.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT.page_id,
        action_id=activity.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT.action_id,
        route="/studio/project-state/?mode=manage",
        control_id=activity.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT.control_id,
        record_id_field=activity.ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT.record_id_field,
        record_id="project-state",
    )
    projects_base_dir = resolve_projects_base_dir(env=runtime_env(repo_root=repo_root))
    result = build_project_state_report(
        repo_root=repo_root,
        projects_base_dir=projects_base_dir,
        output_path=repo_root / DEFAULT_OUTPUT_REL_PATH,
        write=not dry_run,
        include_subfolders=include_subfolders,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "generated_at_utc": result["generated_at_utc"],
        "output_path": result["output_path"],
        "projects_root": result["projects_root_display"],
        "catalogue_source_path": result["catalogue_source_path"],
        "include_subfolders": result["include_subfolders"],
        "summary": result["summary"],
        "written": result["written"],
        "dry_run": dry_run,
    }
    if activity_context:
        payload["activity_context"] = activity_context

    log_event(
        repo_root,
        "project_state_report",
        {
            "output_path": result["output_path"],
            "written": result["written"],
            "dry_run": dry_run,
            "include_subfolders": result["include_subfolders"],
            "projects_base_env": PROJECTS_BASE_DIR_ENV_NAME,
            "summary": result["summary"],
        },
    )
    if activity_context and not dry_run and result["written"]:
        summary = result["summary"] if isinstance(result.get("summary"), Mapping) else {}
        append_studio_activity(
            repo_root,
            [
                activity.studio_activity_entry(
                    activity_context,
                    now_utc=str(result["generated_at_utc"]),
                    script_purpose_id="generate-report",
                    status="completed",
                    record_groups={
                        "works": [],
                        "series": [],
                        "work_details": [],
                        "moments": [],
                        "files": [str(result["output_path"])],
                    },
                    detail_items=[
                        f"Wrote project-state report to {result['output_path']}",
                        f"Source folders: {int(summary.get('source_folder_count') or 0)}",
                        f"Source images: {int(summary.get('source_image_count') or 0)}",
                        f"Unrepresented folders: {int(summary.get('unrepresented_folder_count') or 0)}",
                        f"Unrepresented images: {int(summary.get('unrepresented_image_count') or 0)}",
                    ],
                    source_refs=[
                        {"kind": "report", "path": str(result["output_path"])},
                        {"kind": "log", "path": str(LOGS_REL_DIR / "studio_catalogue_api.log")},
                    ],
                )
            ],
        )
        activity.increment_studio_activity_count(payload, 1)
    return payload


def open_project_state_report_payload(
    repo_root: Path,
    body: Mapping[str, Any],
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    editor = str(body.get("editor") or "default").strip().lower()
    payload = open_project_state_report(repo_root, editor=editor, dry_run=dry_run)
    log_event(
        repo_root,
        "project_state_open_report",
        {
            "path": payload["path"],
            "editor": payload["editor"],
            "dry_run": dry_run,
        },
    )
    return payload


def catalogue_paths(repo_root: Path) -> dict[str, Any]:
    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    lookup_dir = (repo_root / DEFAULT_LOOKUP_DIR).resolve()
    works_path = (source_dir / SOURCE_FILES["works"]).resolve()
    work_details_path = (source_dir / SOURCE_FILES["work_details"]).resolve()
    series_path = (source_dir / SOURCE_FILES["series"]).resolve()
    moments_path = (source_dir / MOMENT_METADATA_FILENAME).resolve()
    allowed_write_paths = {
        (source_dir / filename).resolve()
        for kind, filename in SOURCE_FILES.items()
        if kind != "meta"
    }
    allowed_write_paths.add(moments_path)
    return {
        "source_dir": source_dir,
        "lookup_dir": lookup_dir,
        "works_path": works_path,
        "work_details_path": work_details_path,
        "series_path": series_path,
        "moments_path": moments_path,
        "allowed_write_paths": allowed_write_paths,
        "allowed_write_roots": {
            (repo_root / prose_import.CATALOGUE_PROSE_SOURCE_REL_DIR / "works").resolve(),
            (repo_root / prose_import.CATALOGUE_PROSE_SOURCE_REL_DIR / "series").resolve(),
            (repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR).resolve(),
        },
    }


def load_source_payload(path: Path, object_key: str) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload.get(object_key), dict):
        raise ValueError(f"{object_key} source file must include a {object_key} object")
    return payload


def refresh_lookup_payloads(repo_root: Path, source_dir: Path, lookup_dir: Path) -> dict[str, Any]:
    result = lookup_refresh.full_lookup_refresh(source_dir, lookup_dir, repo_root)
    log_event(
        repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": rel_path(repo_root, lookup_dir),
            "mode": result["mode"],
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    append_script_log(
        Path(__file__),
        event=event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )
