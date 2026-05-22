#!/usr/bin/env python3
"""Catalogue-specific Studio activity profiles and row helpers."""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from catalogue import catalogue_routes as routes
from catalogue.catalogue_source import slug_id
from catalogue.moment_sources import normalize_moment_filename
from catalogue.series_ids import normalize_series_id


LOGS_REL_DIR = Path("var/studio/catalogue/logs")

ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK = "catalogue-work"
ACTIVITY_CONTEXT_ACTION_SAVE_WORK = "save-work"
ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK = "/studio/catalogue-work/"
ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_SAVE = "catalogueWorkSave"
ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL = "catalogue-work-detail"
ACTIVITY_CONTEXT_ACTION_SAVE_WORK_DETAIL = "save-work-detail"
ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL = "/studio/catalogue-work-detail/"
ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_DETAIL_SAVE = "catalogueWorkDetailSave"
ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES = "catalogue-series"
ACTIVITY_CONTEXT_ACTION_SAVE_SERIES = "save-series"
ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES = "/studio/catalogue-series/"
ACTIVITY_CONTEXT_CONTROL_CATALOGUE_SERIES_SAVE = "catalogueSeriesSave"
ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT = "catalogue-moment"
ACTIVITY_CONTEXT_ACTION_SAVE_MOMENT = "save-moment"
ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT = "/studio/catalogue-moment/"
ACTIVITY_CONTEXT_CONTROL_CATALOGUE_MOMENT_SAVE = "catalogueMomentSave"


@dataclass(frozen=True)
class ActivityActionProfile:
    page_id: str
    action_id: str
    route: str
    control_id: str
    control_selector: str
    endpoint: str
    record_family: str
    record_id_field: str
    script_purpose_ids: tuple[str, ...]
    published_step_label: str = ""
    published_script_purpose_id: str = ""
    lookup_script_purpose_id: str = "rebuild-lookups"


ACTIVITY_PROFILE_SAVE_WORK = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
    action_id=ACTIVITY_CONTEXT_ACTION_SAVE_WORK,
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_SAVE,
    control_selector="#catalogueWorkSave",
    endpoint=routes.WORK_SAVE_PATH,
    record_family="work",
    record_id_field="work_id",
    script_purpose_ids=("save-canonical-data", "rebuild-published-work-data", "rebuild-lookups", "update-search"),
    published_step_label="Generate Work Pages",
    published_script_purpose_id="rebuild-published-work-data",
)
ACTIVITY_PROFILE_SAVE_WORK_DETAIL = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
    action_id=ACTIVITY_CONTEXT_ACTION_SAVE_WORK_DETAIL,
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_DETAIL_SAVE,
    control_selector="#catalogueWorkDetailSave",
    endpoint=routes.DETAIL_SAVE_PATH,
    record_family="work_detail",
    record_id_field="detail_uid",
    script_purpose_ids=("save-canonical-data", "rebuild-published-work-data", "rebuild-lookups", "update-search"),
    published_step_label="Generate Work Pages",
    published_script_purpose_id="rebuild-published-work-data",
)
ACTIVITY_PROFILE_SAVE_SERIES = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
    action_id=ACTIVITY_CONTEXT_ACTION_SAVE_SERIES,
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_SERIES_SAVE,
    control_selector="#catalogueSeriesSave",
    endpoint=routes.SERIES_SAVE_PATH,
    record_family="series",
    record_id_field="series_id",
    script_purpose_ids=("save-canonical-data", "rebuild-published-series-data", "rebuild-lookups", "update-search"),
    published_step_label="Generate Work Pages",
    published_script_purpose_id="rebuild-published-series-data",
)
ACTIVITY_PROFILE_SAVE_MOMENT = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
    action_id=ACTIVITY_CONTEXT_ACTION_SAVE_MOMENT,
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_MOMENT_SAVE,
    control_selector="#catalogueMomentSave",
    endpoint=routes.MOMENT_SAVE_PATH,
    record_family="moment",
    record_id_field="moment_id",
    script_purpose_ids=("save-canonical-data", "rebuild-published-moment-data", "update-search"),
    published_step_label="Generate Moment Pages",
    published_script_purpose_id="rebuild-published-moment-data",
    lookup_script_purpose_id="",
)
ACTIVITY_PROFILE_CREATE_WORK = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
    action_id="create-work",
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_SAVE,
    control_selector="#catalogueWorkSave",
    endpoint=routes.WORK_CREATE_PATH,
    record_family="work",
    record_id_field="work_id",
    script_purpose_ids=("save-canonical-data", "rebuild-lookups"),
)
ACTIVITY_PROFILE_CREATE_WORK_DETAIL = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
    action_id="create-work-detail",
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_WORK_DETAIL_SAVE,
    control_selector="#catalogueWorkDetailSave",
    endpoint=routes.DETAIL_CREATE_PATH,
    record_family="work_detail",
    record_id_field="detail_uid",
    script_purpose_ids=("save-canonical-data", "rebuild-lookups"),
)
ACTIVITY_PROFILE_CREATE_SERIES = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
    action_id="create-series",
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
    control_id=ACTIVITY_CONTEXT_CONTROL_CATALOGUE_SERIES_SAVE,
    control_selector="#catalogueSeriesSave",
    endpoint=routes.SERIES_CREATE_PATH,
    record_family="series",
    record_id_field="series_id",
    script_purpose_ids=("save-canonical-data", "rebuild-lookups"),
)
ACTIVITY_PUBLICATION_PROFILES: dict[tuple[str, str], ActivityActionProfile] = {
    ("work", "publish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
        action_id="publish-work",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
        control_id="catalogueWorkPublication",
        control_selector="#catalogueWorkPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="work",
        record_id_field="work_id",
        script_purpose_ids=("save-canonical-data", "rebuild-published-work-data", "rebuild-lookups", "update-search"),
        published_step_label="Generate Work Pages",
        published_script_purpose_id="rebuild-published-work-data",
    ),
    ("work", "unpublish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
        action_id="unpublish-work",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
        control_id="catalogueWorkPublication",
        control_selector="#catalogueWorkPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="work",
        record_id_field="work_id",
        script_purpose_ids=("save-canonical-data", "rebuild-lookups", "clean-generated-artifacts", "update-search"),
    ),
    ("work_detail", "publish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
        action_id="publish-work-detail",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
        control_id="catalogueWorkDetailPublication",
        control_selector="#catalogueWorkDetailPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="work_detail",
        record_id_field="detail_uid",
        script_purpose_ids=("save-canonical-data", "rebuild-published-work-data", "rebuild-lookups", "update-search"),
        published_step_label="Generate Work Pages",
        published_script_purpose_id="rebuild-published-work-data",
    ),
    ("work_detail", "unpublish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
        action_id="unpublish-work-detail",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
        control_id="catalogueWorkDetailPublication",
        control_selector="#catalogueWorkDetailPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="work_detail",
        record_id_field="detail_uid",
        script_purpose_ids=("save-canonical-data", "rebuild-lookups", "clean-generated-artifacts", "update-search"),
    ),
    ("series", "publish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
        action_id="publish-series",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
        control_id="catalogueSeriesPublication",
        control_selector="#catalogueSeriesPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="series",
        record_id_field="series_id",
        script_purpose_ids=("save-canonical-data", "rebuild-published-series-data", "rebuild-lookups", "update-search"),
        published_step_label="Generate Work Pages",
        published_script_purpose_id="rebuild-published-series-data",
    ),
    ("series", "unpublish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
        action_id="unpublish-series",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
        control_id="catalogueSeriesPublication",
        control_selector="#catalogueSeriesPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="series",
        record_id_field="series_id",
        script_purpose_ids=("save-canonical-data", "rebuild-lookups", "clean-generated-artifacts", "update-search"),
    ),
    ("moment", "publish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
        action_id="publish-moment",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
        control_id="catalogueMomentPublication",
        control_selector="#catalogueMomentPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="moment",
        record_id_field="moment_id",
        script_purpose_ids=("save-canonical-data", "rebuild-published-moment-data", "update-search"),
        published_step_label="Generate Moment Pages",
        published_script_purpose_id="rebuild-published-moment-data",
        lookup_script_purpose_id="",
    ),
    ("moment", "unpublish"): ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
        action_id="unpublish-moment",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
        control_id="catalogueMomentPublication",
        control_selector="#catalogueMomentPublication",
        endpoint=routes.PUBLICATION_APPLY_PATH,
        record_family="moment",
        record_id_field="moment_id",
        script_purpose_ids=("save-canonical-data", "clean-generated-artifacts", "update-search"),
        lookup_script_purpose_id="",
    ),
}
ACTIVITY_DELETE_PROFILES: dict[str, ActivityActionProfile] = {
    "work": ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK,
        action_id="delete-work",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK,
        control_id="catalogueWorkDelete",
        control_selector="#catalogueWorkDelete",
        endpoint=routes.DELETE_APPLY_PATH,
        record_family="work",
        record_id_field="work_id",
        script_purpose_ids=("delete-canonical-data", "clean-generated-artifacts", "rebuild-lookups", "update-search"),
    ),
    "work_detail": ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_WORK_DETAIL,
        action_id="delete-work-detail",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_WORK_DETAIL,
        control_id="catalogueWorkDetailDelete",
        control_selector="#catalogueWorkDetailDelete",
        endpoint=routes.DELETE_APPLY_PATH,
        record_family="work_detail",
        record_id_field="detail_uid",
        script_purpose_ids=("delete-canonical-data", "clean-generated-artifacts", "rebuild-lookups", "update-search"),
    ),
    "series": ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_SERIES,
        action_id="delete-series",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_SERIES,
        control_id="catalogueSeriesDelete",
        control_selector="#catalogueSeriesDelete",
        endpoint=routes.DELETE_APPLY_PATH,
        record_family="series",
        record_id_field="series_id",
        script_purpose_ids=("delete-canonical-data", "clean-generated-artifacts", "rebuild-lookups", "update-search"),
    ),
    "moment": ActivityActionProfile(
        page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
        action_id="delete-moment",
        route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
        control_id="catalogueMomentDelete",
        control_selector="#catalogueMomentDelete",
        endpoint=routes.DELETE_APPLY_PATH,
        record_family="moment",
        record_id_field="moment_id",
        script_purpose_ids=("delete-canonical-data", "clean-generated-artifacts", "update-search"),
        lookup_script_purpose_id="",
    ),
}
ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS = ActivityActionProfile(
    page_id="bulk-add-work",
    action_id="import-workbook-records",
    route="/studio/bulk-add-work/",
    control_id="bulkAddWorkApply",
    control_selector="#bulkAddWorkApply",
    endpoint=routes.IMPORT_APPLY_PATH,
    record_family="workbook_import",
    record_id_field="import_mode",
    script_purpose_ids=("import-source-data", "rebuild-lookups"),
)
ACTIVITY_PROFILE_IMPORT_MOMENT = ActivityActionProfile(
    page_id=ACTIVITY_CONTEXT_PAGE_CATALOGUE_MOMENT,
    action_id="import-moment",
    route=ACTIVITY_CONTEXT_ROUTE_CATALOGUE_MOMENT,
    control_id="catalogueMomentImportApply",
    control_selector="#catalogueMomentImportApply",
    endpoint=routes.MOMENT_IMPORT_APPLY_PATH,
    record_family="moment",
    record_id_field="moment_id",
    script_purpose_ids=("import-source-data",),
)
ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT = ActivityActionProfile(
    page_id="project-state",
    action_id="run-project-state-report",
    route="/studio/project-state/?mode=manage",
    control_id="projectStateRunButton",
    control_selector="#projectStateRunButton",
    endpoint="/studio/api/catalogue/project-state-report",
    record_family="report",
    record_id_field="activity_target",
    script_purpose_ids=("generate-report",),
)
ACTIVITY_ACTION_PROFILES: tuple[ActivityActionProfile, ...] = (
    ACTIVITY_PROFILE_SAVE_WORK,
    ACTIVITY_PROFILE_SAVE_WORK_DETAIL,
    ACTIVITY_PROFILE_SAVE_SERIES,
    ACTIVITY_PROFILE_SAVE_MOMENT,
    ACTIVITY_PROFILE_CREATE_WORK,
    ACTIVITY_PROFILE_CREATE_WORK_DETAIL,
    ACTIVITY_PROFILE_CREATE_SERIES,
    *ACTIVITY_PUBLICATION_PROFILES.values(),
    *ACTIVITY_DELETE_PROFILES.values(),
    ACTIVITY_PROFILE_IMPORT_WORKBOOK_RECORDS,
    ACTIVITY_PROFILE_IMPORT_MOMENT,
    ACTIVITY_PROFILE_RUN_PROJECT_STATE_REPORT,
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def activity_id_component(value: Any) -> str:
    text = activity_context_value(value)
    safe_value = "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")
    return safe_value or "activity"


def studio_activity_id(now_utc: str, correlation_id: str, script_purpose_id: str) -> str:
    return f"{now_utc}-{activity_id_component(correlation_id)}-{activity_id_component(script_purpose_id)}"


def activity_context_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def activity_correlation_id(value: Any) -> str:
    requested = activity_context_value(value)
    if not requested:
        return uuid.uuid4().hex
    safe_value = "".join(ch for ch in requested if ch.isalnum() or ch in "._:-")
    return safe_value[:120] or uuid.uuid4().hex


def normalize_detail_uid_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("detail_uid is required")
    if "-" in text:
        raw_work_id, raw_detail_id = text.split("-", 1)
    else:
        digits = "".join(ch for ch in text if ch.isdigit())
        if len(digits) != 8:
            raise ValueError(f"invalid detail_uid: {value!r}")
        raw_work_id, raw_detail_id = digits[:5], digits[5:]
    work_id = slug_id(raw_work_id)
    detail_id = slug_id(raw_detail_id, width=3)
    return f"{work_id}-{detail_id}"


def normalize_moment_id_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("moment_id is required")
    return normalize_moment_filename(text if text.endswith(".md") else f"{text}.md")[:-3]


def normalize_activity_record_id(record_id_field: str, value: Any) -> str:
    if record_id_field == "work_id":
        return slug_id(value)
    if record_id_field == "detail_uid":
        return normalize_detail_uid_value(value)
    if record_id_field == "series_id":
        return normalize_series_id(value)
    if record_id_field == "moment_id":
        return normalize_moment_id_value(value)
    return activity_context_value(value)


def normalize_activity_context(
    raw_context: Any,
    *,
    page_id: str,
    action_id: str,
    route: str,
    control_id: str,
    record_id_field: str,
    record_id: str,
) -> Dict[str, str]:
    if raw_context is None:
        return {}
    if not isinstance(raw_context, Mapping):
        raise ValueError("activity_context must be an object")

    expected_values = {
        "page_id": page_id,
        "action_id": action_id,
        "route": route,
        "control_id": control_id,
    }
    for key, expected in expected_values.items():
        value = activity_context_value(raw_context.get(key))
        if value != expected:
            raise ValueError(f"activity_context.{key} must be {expected!r}")

    requested_record_id = normalize_activity_record_id(record_id_field, raw_context.get(record_id_field))
    if requested_record_id and requested_record_id != record_id:
        raise ValueError(f"activity_context.{record_id_field} must match request {record_id_field}")

    context: Dict[str, str] = {
        "correlation_id": activity_correlation_id(raw_context.get("correlation_id")),
        "page_id": page_id,
        "action_id": action_id,
        "route": route,
        "control_id": control_id,
        "record_id_field": record_id_field,
        record_id_field: record_id,
    }
    control_selector = activity_context_value(raw_context.get("control_selector"))
    if control_selector:
        context["control_selector"] = control_selector
    return context


def normalize_activity_context_for_profile(
    raw_context: Any,
    profile: ActivityActionProfile,
    *,
    record_id: str,
) -> Dict[str, str]:
    return normalize_activity_context(
        raw_context,
        page_id=profile.page_id,
        action_id=profile.action_id,
        route=profile.route,
        control_id=profile.control_id,
        record_id_field=profile.record_id_field,
        record_id=record_id,
    )


def activity_profile_for_publication(kind: str, action: str) -> ActivityActionProfile:
    profile = ACTIVITY_PUBLICATION_PROFILES.get((kind, action))
    if profile is None:
        raise ValueError(f"unsupported publication activity profile: {kind}.{action}")
    return profile


def activity_profile_for_delete(kind: str) -> ActivityActionProfile:
    profile = ACTIVITY_DELETE_PROFILES.get(kind)
    if profile is None:
        raise ValueError(f"unsupported delete activity profile: {kind}")
    return profile


def activity_record_groups(
    *,
    works: Iterable[str] = (),
    series: Iterable[str] = (),
    work_details: Iterable[str] = (),
    moments: Iterable[str] = (),
    search: Iterable[str] = (),
) -> Dict[str, list[str]]:
    return {
        "works": sorted({str(value) for value in works if str(value).strip()}),
        "series": sorted({str(value) for value in series if str(value).strip()}),
        "work_details": sorted({str(value) for value in work_details if str(value).strip()}),
        "moments": sorted({str(value) for value in moments if str(value).strip()}),
        "search": sorted({str(value) for value in search if str(value).strip()}),
    }


def activity_record_groups_from_affected(affected: Any) -> Dict[str, list[str]]:
    data = affected if isinstance(affected, Mapping) else {}
    return activity_record_groups(
        works=data.get("works") or [],
        series=data.get("series") or [],
        work_details=data.get("work_details") or [],
        moments=data.get("moments") or [],
    )


def studio_activity_entry(
    activity_context: Mapping[str, str],
    *,
    now_utc: str,
    script_purpose_id: str,
    status: str,
    record_groups: Mapping[str, list[str]],
    detail_items: list[str],
    source_refs: list[Mapping[str, str]],
) -> Dict[str, Any]:
    correlation_id = activity_context_value(activity_context.get("correlation_id"))
    activity_id = studio_activity_id(now_utc, correlation_id, script_purpose_id)
    return {
        "id": activity_id,
        "activity_id": activity_id,
        "correlation_id": correlation_id,
        "timestamp": now_utc,
        "time_utc": now_utc,
        "status": status,
        "page_id": activity_context_value(activity_context.get("page_id")),
        "user_action_id": activity_context_value(activity_context.get("action_id")),
        "script_purpose_id": script_purpose_id,
        "record_groups": dict(record_groups),
        "detail_items": list(detail_items),
        "source_refs": [dict(ref) for ref in source_refs],
    }


def catalogue_log_source_ref() -> list[Mapping[str, str]]:
    return [{"kind": "log", "path": str(LOGS_REL_DIR / "catalogue_write_server.log")}]


def build_step_status(build_payload: Mapping[str, Any], label: str) -> str:
    steps = build_payload.get("steps") if isinstance(build_payload.get("steps"), list) else []
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        if str(step.get("label") or "").strip() != label:
            continue
        return "completed" if int(step.get("exit_code") or 0) == 0 else "warning"
    return "completed" if build_payload.get("ok") else "warning"


def build_step_attempted(build_payload: Mapping[str, Any], label: str) -> bool:
    steps = build_payload.get("steps") if isinstance(build_payload.get("steps"), list) else []
    return any(isinstance(step, Mapping) and str(step.get("label") or "").strip() == label for step in steps)


def increment_studio_activity_count(response_payload: Dict[str, Any], count: int) -> None:
    if count <= 0:
        return
    activity_log_payload = response_payload.setdefault("activity_log", {"written_count": 0})
    activity_log_payload["written_count"] = int(activity_log_payload.get("written_count") or 0) + count


def append_studio_activity_rows(server: Any, response_payload: Dict[str, Any], rows: list[Dict[str, Any]]) -> None:
    if not rows:
        return
    server.append_studio_activity(rows)
    increment_studio_activity_count(response_payload, len(rows))


def catalogue_build_record_groups(build_payload: Mapping[str, Any], fallback: Mapping[str, list[str]]) -> Dict[str, list[str]]:
    build_scope = build_payload.get("build") if isinstance(build_payload.get("build"), Mapping) else {}
    return {
        "works": list(build_scope.get("work_ids") or fallback.get("works") or []),
        "series": list(build_scope.get("series_ids") or fallback.get("series") or []),
        "work_details": list(build_scope.get("work_detail_uids") or fallback.get("work_details") or []),
        "moments": list(build_scope.get("moment_ids") or fallback.get("moments") or []),
        "search": ["catalogue"] if build_step_attempted(build_payload, "Build Catalogue Search Index") else [],
    }


def catalogue_build_studio_activity_rows(
    profile: ActivityActionProfile,
    activity_context: Mapping[str, str],
    build_payload: Mapping[str, Any],
    *,
    published_detail: str,
    search_detail: str,
    fallback_record_groups: Mapping[str, list[str]],
) -> list[Dict[str, Any]]:
    now_utc = activity_context_value(build_payload.get("completed_at_utc")) or utc_now()
    record_groups = catalogue_build_record_groups(build_payload, fallback_record_groups)
    rows: list[Dict[str, Any]] = []
    if profile.published_step_label and profile.published_script_purpose_id and build_step_attempted(build_payload, profile.published_step_label):
        rows.append(
            studio_activity_entry(
                activity_context,
                now_utc=now_utc,
                script_purpose_id=profile.published_script_purpose_id,
                status=build_step_status(build_payload, profile.published_step_label),
                record_groups=record_groups,
                detail_items=[published_detail],
                source_refs=catalogue_log_source_ref(),
            )
        )
    if build_step_attempted(build_payload, "Build Catalogue Search Index"):
        rows.append(
            studio_activity_entry(
                activity_context,
                now_utc=now_utc,
                script_purpose_id="update-search",
                status=build_step_status(build_payload, "Build Catalogue Search Index"),
                record_groups=record_groups,
                detail_items=[search_detail],
                source_refs=catalogue_log_source_ref(),
            )
        )
    return rows


def catalogue_source_write_activity_rows(
    profile: ActivityActionProfile,
    activity_context: Mapping[str, str],
    *,
    now_utc: str,
    script_purpose_id: str,
    record_groups: Mapping[str, list[str]],
    detail_items: list[str],
) -> list[Dict[str, Any]]:
    return [
        studio_activity_entry(
            activity_context,
            now_utc=now_utc,
            script_purpose_id=script_purpose_id,
            status="completed",
            record_groups=record_groups,
            detail_items=detail_items,
            source_refs=catalogue_log_source_ref(),
        )
    ]


def catalogue_lookup_activity_row(
    activity_context: Mapping[str, str],
    *,
    now_utc: str,
    record_groups: Mapping[str, list[str]],
    detail_items: list[str],
) -> Dict[str, Any]:
    return studio_activity_entry(
        activity_context,
        now_utc=now_utc,
        script_purpose_id="rebuild-lookups",
        status="completed",
        record_groups=record_groups,
        detail_items=detail_items,
        source_refs=catalogue_log_source_ref(),
    )


def catalogue_cleanup_activity_rows(
    activity_context: Mapping[str, str],
    cleanup_result: Mapping[str, Any],
    *,
    now_utc: str,
    record_groups: Mapping[str, list[str]],
    detail_items: list[str],
) -> list[Dict[str, Any]]:
    rows = [
        studio_activity_entry(
            activity_context,
            now_utc=now_utc,
            script_purpose_id="clean-generated-artifacts",
            status="completed",
            record_groups=record_groups,
            detail_items=detail_items,
            source_refs=catalogue_log_source_ref(),
        )
    ]
    if cleanup_result.get("catalogue_search_rebuilt") or cleanup_result.get("would_rebuild_catalogue_search"):
        rows.append(
            studio_activity_entry(
                activity_context,
                now_utc=now_utc,
                script_purpose_id="update-search",
                status="completed" if int(cleanup_result.get("search_exit_code") or 0) == 0 else "warning",
                record_groups={**dict(record_groups), "search": ["catalogue"]},
                detail_items=["Rebuilt catalogue search after generated artifact cleanup"],
                source_refs=catalogue_log_source_ref(),
            )
        )
    return rows


def catalogue_delete_activity_rows(
    profile: ActivityActionProfile,
    activity_context: Mapping[str, str],
    cleanup_result: Mapping[str, Any],
    *,
    now_utc: str,
    record_groups: Mapping[str, list[str]],
    source_detail_items: list[str],
    cleanup_detail_items: list[str],
) -> list[Dict[str, Any]]:
    rows = catalogue_source_write_activity_rows(
        profile,
        activity_context,
        now_utc=now_utc,
        script_purpose_id="delete-canonical-data",
        record_groups=record_groups,
        detail_items=source_detail_items,
    )
    cleanup_rows = catalogue_cleanup_activity_rows(
        activity_context,
        cleanup_result,
        now_utc=now_utc,
        record_groups=record_groups,
        detail_items=cleanup_detail_items,
    )
    rows.append(cleanup_rows[0])
    if profile.lookup_script_purpose_id:
        rows.append(
            catalogue_lookup_activity_row(
                activity_context,
                now_utc=now_utc,
                record_groups=record_groups,
                detail_items=[f"Refreshed catalogue lookup data after deleting {profile.record_family.replace('_', ' ')}"],
            )
        )
    rows.extend(cleanup_rows[1:])
    return rows
