"""Pure publication preview planners for catalogue write paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import catalogue_cleanup
import catalogue_source_mutation as source_mutation
from catalogue_json_build import (
    build_local_media_plan,
    build_scope_for_moment,
    build_scope_for_series,
    build_scope_for_work,
    preview_moment_source,
)
from catalogue_source import (
    DEFAULT_SOURCE_DIR,
    SOURCE_FILES,
    normalize_status,
    normalize_series_ids_value,
    records_from_json_source,
    slug_id,
)
from moment_sources import MOMENT_METADATA_FILENAME, load_moment_metadata_records, normalize_moment_metadata_record


def publication_source_path_key(kind: str) -> str:
    if kind == "work":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["works"])
    if kind == "work_detail":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["work_details"])
    if kind == "series":
        return str(DEFAULT_SOURCE_DIR / SOURCE_FILES["series"])
    return str(DEFAULT_SOURCE_DIR / MOMENT_METADATA_FILENAME)


def publication_affected_for_record(source_dir: Path, kind: str, record_id: str) -> Dict[str, list[str]]:
    source_records = records_from_json_source(source_dir)
    affected: Dict[str, list[str]] = {
        "works": [],
        "series": [],
        "work_details": [],
        "moments": [],
    }
    if kind == "work":
        work_record = source_records.works.get(record_id)
        if not isinstance(work_record, dict):
            raise ValueError(f"work_id not found: {record_id}")
        affected["works"] = [record_id]
        affected["series"] = normalize_series_ids_value(work_record.get("series_ids"))
        affected["work_details"] = sorted(
            detail_uid
            for detail_uid, detail_record in source_records.work_details.items()
            if str(detail_record.get("work_id") or "") == record_id
        )
    elif kind == "work_detail":
        detail_record = source_records.work_details.get(record_id)
        if not isinstance(detail_record, dict):
            raise ValueError(f"detail_uid not found: {record_id}")
        work_id = str(detail_record.get("work_id") or "")
        affected["works"] = [work_id] if work_id else []
        affected["work_details"] = [record_id]
    elif kind == "series":
        series_record = source_records.series.get(record_id)
        if not isinstance(series_record, dict):
            raise ValueError(f"series_id not found: {record_id}")
        affected["series"] = [record_id]
        affected["works"] = sorted(
            work_id
            for work_id, work_record in source_records.works.items()
            if record_id in normalize_series_ids_value(work_record.get("series_ids"))
        )
    else:
        moment_records = load_moment_metadata_records(source_dir)
        if record_id not in moment_records:
            raise ValueError(f"moment_id not found: {record_id}")
        affected["moments"] = [record_id]
    return affected


def series_publish_bootstrap_work_records(source_dir: Path, series_id: str) -> Dict[str, Dict[str, Any]]:
    records = records_from_json_source(source_dir)
    promoted: Dict[str, Dict[str, Any]] = {}
    for work_id, work_record in records.works.items():
        if series_id not in normalize_series_ids_value(work_record.get("series_ids")):
            continue
        if normalize_status(work_record.get("status")) != "draft":
            continue
        promoted[work_id] = source_mutation.normalize_work_update(work_id, work_record, {"status": "published"})
    return promoted


def publication_bootstrap_work_records(
    source_dir: Path,
    kind: str,
    action: str,
    record_id: str,
    target_record: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    if kind != "series" or action != "publish":
        return {}
    if normalize_status(target_record.get("status")) != "published":
        return {}
    return series_publish_bootstrap_work_records(source_dir, record_id)


def current_publication_record(source_dir: Path, kind: str, record_id: str) -> Dict[str, Any]:
    if kind == "work":
        record = records_from_json_source(source_dir).works.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"work_id not found: {record_id}")
        return dict(record)
    if kind == "work_detail":
        record = records_from_json_source(source_dir).work_details.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"detail_uid not found: {record_id}")
        return dict(record)
    if kind == "series":
        record = records_from_json_source(source_dir).series.get(record_id)
        if not isinstance(record, dict):
            raise ValueError(f"series_id not found: {record_id}")
        return dict(record)
    record = load_moment_metadata_records(source_dir).get(record_id)
    if not isinstance(record, dict):
        raise ValueError(f"moment_id not found: {record_id}")
    return normalize_moment_metadata_record(record_id, record)


def normalize_publication_record(
    kind: str,
    record_id: str,
    current_record: Mapping[str, Any],
    action: str,
    record_update: Mapping[str, Any],
) -> Dict[str, Any]:
    if action == "publish":
        update = {"status": "published"}
    elif action == "unpublish":
        update = {"status": "draft"}
    else:
        update = dict(record_update)
        requested_status = normalize_status(update.get("status")) if "status" in update else normalize_status(current_record.get("status"))
        current_status = normalize_status(current_record.get("status"))
        if requested_status != current_status:
            raise ValueError("save_published must not change publication status")

    if kind == "work":
        return source_mutation.normalize_work_update(record_id, current_record, update)
    if kind == "work_detail":
        return source_mutation.normalize_work_detail_update(record_id, current_record, update)
    if kind == "series":
        return source_mutation.normalize_series_update(record_id, current_record, update)
    return source_mutation.normalize_moment_update(record_id, current_record, update)


def validate_publication_target(
    source_dir: Path,
    kind: str,
    record_id: str,
    target_record: Dict[str, Any],
    *,
    work_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> list[str]:
    source_records = records_from_json_source(source_dir)
    if kind == "work":
        return source_mutation.validate_work_records(source_records, record_id, target_record)
    if kind == "work_detail":
        return source_mutation.validate_detail_records(source_records, record_id, target_record)
    if kind == "series":
        errors = source_mutation.validate_series_save_record(target_record)
        errors.extend(source_mutation.validate_series_records(source_records, record_id, target_record, work_updates or {}))
        return errors
    return source_mutation.validate_moment_record(record_id, target_record)


def publication_specific_blockers(
    source_dir: Path,
    repo_root: Path,
    kind: str,
    record_id: str,
    target_record: Mapping[str, Any],
    *,
    work_updates: Optional[Mapping[str, Dict[str, Any]]] = None,
) -> list[str]:
    if normalize_status(target_record.get("status")) != "published":
        return []

    records = records_from_json_source(source_dir)
    effective_works = dict(records.works)
    if work_updates:
        effective_works.update({work_id: dict(record) for work_id, record in work_updates.items()})
    if kind == "work":
        published_series_ids = [
            series_id
            for series_id in normalize_series_ids_value(target_record.get("series_ids"))
            if isinstance(records.series.get(series_id), dict)
            and normalize_status(records.series[series_id].get("status")) == "published"
        ]
        if not published_series_ids:
            return [f"work {record_id} must belong to a published series before publishing"]
        return []

    if kind == "work_detail":
        work_id = slug_id(target_record.get("work_id"))
        parent = effective_works.get(work_id)
        if not isinstance(parent, dict):
            return [f"parent work_id not found: {work_id}"]
        if normalize_status(parent.get("status")) != "published":
            return [f"parent work {work_id} must be published before publishing detail {record_id}"]
        return []

    if kind == "series":
        primary_work_id = str(target_record.get("primary_work_id") or "").strip()
        blockers: list[str] = []
        if not primary_work_id:
            blockers.append("series primary_work_id is required before publishing")
        primary = effective_works.get(primary_work_id)
        if primary_work_id and not isinstance(primary, dict):
            blockers.append(f"primary work_id not found: {primary_work_id}")
        elif isinstance(primary, dict):
            if normalize_status(primary.get("status")) != "published":
                blockers.append(f"primary work {primary_work_id} must be published before publishing series {record_id}")
            if record_id not in normalize_series_ids_value(primary.get("series_ids")):
                blockers.append(f"primary work {primary_work_id} must belong to series {record_id}")
        member_work_ids = [
            work_id
            for work_id, work_record in effective_works.items()
            if record_id in normalize_series_ids_value(work_record.get("series_ids"))
            and normalize_status(work_record.get("status")) == "published"
        ]
        if not member_work_ids:
            blockers.append("series must have at least one published member work before publishing")
        return blockers

    if kind == "moment":
        preview = preview_moment_source(repo_root, f"{record_id}.md", metadata=dict(target_record))
        if not preview.get("valid"):
            return [str(error) for error in preview.get("errors") or []] or ["moment source preview failed"]
    return []


def build_publication_build_impact(
    source_dir: Path,
    repo_root: Path,
    kind: str,
    record_id: str,
    target_record: Mapping[str, Any],
    *,
    action: str,
    extra_series_ids: list[str],
    extra_work_ids: list[str],
    force: bool,
) -> Dict[str, Any]:
    try:
        if kind == "work":
            build = build_scope_for_work(source_dir, record_id, extra_series_ids=extra_series_ids)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        elif kind == "work_detail":
            work_id = slug_id(target_record.get("work_id"))
            build = build_scope_for_work(source_dir, work_id, extra_series_ids=extra_series_ids, detail_uid=record_id)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        elif kind == "series":
            build = build_scope_for_series(source_dir, record_id, extra_work_ids=extra_work_ids)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        else:
            build = build_scope_for_moment(repo_root, f"{record_id}.md", metadata=dict(target_record), force=force)
            build["local_media"] = build_local_media_plan(repo_root, scope=build, force=force)
        return {
            "type": "scoped_public_update",
            "available": True,
            "build": build,
        }
    except Exception as exc:  # noqa: BLE001
        payload = {
            "type": "scoped_public_update",
            "available": action == "publish",
            "build": {
                "work_ids": [record_id] if kind == "work" else [slug_id(target_record.get("work_id"))] if kind == "work_detail" else [],
                "series_ids": [record_id] if kind == "series" else [],
                "moment_ids": [record_id] if kind == "moment" else [],
                "rebuild_search": True,
                "search_scope": "catalogue",
                "refresh_published": True,
            },
        }
        if action == "publish":
            payload["pending_source_write"] = True
            payload["summary"] = "Scoped public update will be resolved after the source status is written."
        else:
            payload["error"] = str(exc)
        return payload


def build_publication_preview(source_dir: Path, repo_root: Path, request: Mapping[str, Any]) -> Dict[str, Any]:
    kind = str(request.get("kind") or "")
    action = str(request.get("action") or "")
    record_id = str(request.get("id") or "")
    current_record = current_publication_record(source_dir, kind, record_id)
    current_status = normalize_status(current_record.get("status")) or "draft"
    record_update = request.get("record_update") if isinstance(request.get("record_update"), Mapping) else {}
    blockers: list[str] = []

    if action == "publish" and current_status == "published":
        blockers.append("record is already published")
    elif action == "unpublish" and current_status != "published":
        blockers.append("record is not published")
    elif action == "save_published" and current_status != "published":
        blockers.append("save_published requires a published record")

    target_record = normalize_publication_record(kind, record_id, current_record, action, record_update)
    target_status = normalize_status(target_record.get("status")) or "draft"
    changed = current_record != target_record
    changed_field_names = source_mutation.changed_fields(current_record, target_record)
    bootstrap_work_records = publication_bootstrap_work_records(source_dir, kind, action, record_id, target_record)
    bootstrap_work_ids = sorted(bootstrap_work_records)
    source_changed = changed or bool(bootstrap_work_records)
    validation_errors = validate_publication_target(source_dir, kind, record_id, target_record, work_updates=bootstrap_work_records)
    blockers.extend(validation_errors)
    blockers.extend(publication_specific_blockers(source_dir, repo_root, kind, record_id, target_record, work_updates=bootstrap_work_records))
    affected = publication_affected_for_record(source_dir, kind, record_id)
    impact: Dict[str, Any] = {
        "source": {
            "path": publication_source_path_key(kind),
            "will_write": source_changed,
            "changed_fields": changed_field_names,
            "bootstrap_publish_work_ids": bootstrap_work_ids,
        },
        "public": {},
    }
    if bootstrap_work_records:
        impact["source"]["additional_paths"] = [
            {
                "path": str(DEFAULT_SOURCE_DIR / SOURCE_FILES["works"]),
                "will_write": True,
                "changed_record_ids": bootstrap_work_ids,
            }
        ]

    if action == "unpublish":
        if kind == "moment":
            cleanup = catalogue_cleanup.moment_delete_preview_cleanup(repo_root, record_id)
        else:
            cleanup = catalogue_cleanup.catalogue_delete_preview_cleanup(repo_root, kind, record_id, affected)
        impact["public"] = {
            "type": "public_cleanup",
            "cleanup": cleanup,
        }
    else:
        impact["public"] = build_publication_build_impact(
            source_dir,
            repo_root,
            kind,
            record_id,
            target_record,
            action=action,
            extra_series_ids=list(request.get("extra_series_ids") or []),
            extra_work_ids=list(request.get("extra_work_ids") or []),
            force=bool(request.get("force")),
        )

    if action in {"publish", "save_published"} and not impact["public"].get("available", True):
        blockers.append(str(impact["public"].get("error") or "public update preview failed"))

    blocked = bool(blockers)
    return {
        "ok": True,
        "kind": kind,
        "id": record_id,
        "action": action,
        "allowed": not blocked,
        "blocked": blocked,
        "blockers": blockers,
        "validation_errors": validation_errors,
        "current_status": current_status,
        "target_status": target_status,
        "record": current_record,
        "target_record": target_record,
        "changed": changed,
        "source_changed": source_changed,
        "changed_fields": changed_field_names,
        "bootstrap_publish_work_ids": bootstrap_work_ids,
        "affected": affected,
        "impact": impact,
        "summary": f"{action.replace('_', ' ')} {kind} {record_id}: {current_status} -> {target_status}.",
    }
