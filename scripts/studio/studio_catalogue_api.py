"""Local Studio app adapter for narrow Catalogue-owned routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import sys
from typing import Any, Mapping


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
STUDIO_DIR = Path(__file__).resolve().parent
for candidate in (SCRIPTS_DIR, STUDIO_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue import catalogue_activity as activity  # noqa: E402
from catalogue.project_state_report import (  # noqa: E402
    DEFAULT_OUTPUT_REL_PATH,
    PROJECTS_BASE_DIR_ENV_NAME,
    build_project_state_report,
    resolve_projects_base_dir,
)
from local_env import runtime_env  # noqa: E402
from media.build_thumbnail_quality_preview import build_preview as build_thumbnail_quality_preview  # noqa: E402
from script_logging import append_script_log  # noqa: E402
from studio_activity import append_studio_activity  # noqa: E402


LOGS_REL_DIR = Path("var/studio/catalogue/logs")
PROJECT_STATE_REPORT_API_PATH = "/studio/api/catalogue/project-state-report"


def catalogue_get_payload(repo_root: Path, api_path: str) -> dict[str, Any]:
    if api_path == "/health":
        return {"ok": True, "service": "studio_catalogue", "routes": ["project-state-report", "thumbnail-quality-preview"]}
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
    if api_path == "/thumbnail-quality-preview":
        return HTTPStatus.OK, thumbnail_quality_preview_payload(repo_root, dry_run=dry_run)
    raise FileNotFoundError(f"Unknown catalogue API route: {api_path}")


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


def thumbnail_quality_preview_payload(repo_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    payload = build_thumbnail_quality_preview(
        repo_root,
        env=runtime_env(repo_root=repo_root),
        write=not dry_run,
    )
    payload["dry_run"] = dry_run
    log_event(
        repo_root,
        "thumbnail_quality_preview",
        {
            "source_count": payload.get("source_count"),
            "data_path": payload.get("data_path"),
            "dry_run": dry_run,
        },
    )
    return payload


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    append_script_log(
        Path(__file__),
        event=event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )
