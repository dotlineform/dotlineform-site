"""Callable catalogue write/read service helpers for Local Studio."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue import catalogue_delete_plans
from catalogue import catalogue_prose_import as prose_import
from catalogue.catalogue_build_field_plan import apply_field_build_plan_to_scope, build_field_plan_for_scope
from catalogue.catalogue_build_media import build_local_media_plan, build_moment_readiness
from catalogue.catalogue_build_scopes import build_scope_for_moment, build_scope_for_series, build_scope_for_work, preview_moment_source
from catalogue.catalogue_json_build import run_scoped_build_scope
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, load_json_file, normalize_detail_uid_value, normalize_series_ids_value, slug_id
from catalogue.moment_sources import CATALOGUE_MOMENT_PROSE_REL_DIR, MOMENT_METADATA_FILENAME, normalize_moment_filename, normalize_moment_metadata_record
from catalogue.series_ids import normalize_series_id
from script_logging import append_script_log
from studio_activity import append_studio_activity


BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
LOGS_REL_DIR = Path("var/studio/catalogue/logs")

SERVICE_POST_PATHS = {
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
    moments_path: Path
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
        moments_path=(source_dir / MOMENT_METADATA_FILENAME).resolve(),
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
