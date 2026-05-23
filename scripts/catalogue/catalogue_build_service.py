"""Scoped catalogue build service routes for Local Studio."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue.catalogue_build_commands import build_search_command
from catalogue.catalogue_build_field_plan import apply_field_build_plan_to_scope, build_field_plan_for_scope
from catalogue.catalogue_build_media import build_local_media_plan
from catalogue.catalogue_build_scopes import build_scope_for_moment, build_scope_for_series, build_scope_for_work
from catalogue.catalogue_json_build import run_scoped_build_scope
from catalogue.catalogue_source import normalize_detail_uid_value, normalize_series_ids_value, slug_id
from catalogue.catalogue_service_context import CatalogueWriteContext, normalize_moment_id_value
from catalogue.series_ids import normalize_series_id
from local_env import runtime_env


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


def run_catalogue_search_rebuild(repo_root: Path, *, write: bool) -> dict[str, Any]:
    proc = subprocess.run(
        build_search_command(repo_root, write=write, force=False, env=runtime_env(repo_root=repo_root)),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-8:]) if proc.stdout else "",
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-8:]) if proc.stderr else "",
    }
    if proc.returncode != 0:
        detail = payload["stderr_tail"] or payload["stdout_tail"] or "catalogue search rebuild failed"
        raise RuntimeError(str(detail))
    return payload


def run_build_targets(context: CatalogueWriteContext, build_targets: list[dict[str, Any]]) -> dict[str, Any]:
    if not build_targets:
        return {
            "ok": True,
            "requested_count": 0,
            "completed_count": 0,
            "targets": [],
            "remaining_targets": [],
        }

    target_results: list[dict[str, Any]] = []
    for index, target in enumerate(build_targets):
        work_id = slug_id(target.get("work_id"))
        extra_series_ids = normalize_series_ids_value(target.get("extra_series_ids"))
        success, payload = run_build_operation(
            context,
            work_id=work_id,
            series_id="",
            moment_id="",
            extra_series_ids=extra_series_ids,
            extra_work_ids=[],
            detail_uid="",
            force=False,
        )
        target_results.append(
            {
                "work_id": work_id,
                "extra_series_ids": extra_series_ids,
                "ok": success,
                "completed_at_utc": payload.get("completed_at_utc"),
                "error": payload.get("error"),
            }
        )
        if not success:
            return {
                "ok": False,
                "requested_count": len(build_targets),
                "completed_count": index,
                "targets": target_results,
                "remaining_targets": build_targets[index:],
                "error": payload.get("error"),
                "failed_step": payload.get("failed_step"),
            }

    return {
        "ok": True,
        "requested_count": len(build_targets),
        "completed_count": len(build_targets),
        "targets": target_results,
        "remaining_targets": [],
        "completed_at_utc": activity.utc_now(),
    }


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
