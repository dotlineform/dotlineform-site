"""Analytics API adapters for the local Studio app server."""

from __future__ import annotations

import datetime as dt
import json
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import script_logging  # noqa: E402
import studio_activity  # noqa: E402
from analytics import tag_activity  # noqa: E402
from analytics import tag_alias_mutations as tag_aliases  # noqa: E402
from analytics import tag_assignment_service as tag_assignments  # noqa: E402
from analytics import tag_registry_mutations as tag_registry  # noqa: E402
from analytics import tag_routes  # noqa: E402
from analytics import tag_source_model as tag_source  # noqa: E402
from analytics import tag_write_transactions as tag_transactions  # noqa: E402


DATA_DIR = Path("assets/studio/data")
BACKUPS_REL_DIR = Path("var/studio/backups")
LOGS_REL_DIR = Path("var/studio/logs")
READ_ENDPOINTS = {
    "/tag-aliases": {
        "path": DATA_DIR / "tag_aliases.json",
        "label": "Tag Aliases",
        "required_key": "aliases",
        "required_type": dict,
    },
    "/tag-assignments": {
        "path": DATA_DIR / "tag_assignments.json",
        "label": "Tag Assignments",
        "required_key": "series",
        "required_type": dict,
    },
    "/tag-groups": {
        "path": DATA_DIR / "tag_groups.json",
        "label": "Tag Groups",
        "required_key": "groups",
        "required_type": list,
    },
    "/tag-registry": {
        "path": DATA_DIR / "tag_registry.json",
        "label": "Tag Registry",
        "required_key": "tags",
        "required_type": list,
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def analytics_health_payload() -> dict[str, object]:
    return {
        "ok": True,
        "service": "studio_analytics",
        "writes": {
            "import_tag_assignments": True,
            "import_tag_assignments_preview": True,
            "import_tag_aliases": True,
            "import_tag_registry": True,
            "delete_tag_alias": True,
            "mutate_tag_alias": True,
            "mutate_tag_alias_preview": True,
            "mutate_tag": True,
            "mutate_tag_preview": True,
            "save_tags": True,
        },
    }


def data_payload(repo_root: Path, endpoint: str) -> dict[str, object]:
    spec = READ_ENDPOINTS.get(endpoint)
    if spec is None:
        raise FileNotFoundError("Not found")
    path = repo_root / spec["path"]
    label = str(spec["label"])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read {label} data: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} data must be a JSON object: {path}")
    required_value = payload.get(str(spec["required_key"]))
    required_type = spec["required_type"]
    if not isinstance(required_value, required_type):
        raise RuntimeError(f"{label} data must include {spec['required_key']} {required_type.__name__}: {path}")

    return {
        "ok": True,
        **payload,
    }


def analytics_get_payload(repo_root: Path, path: str) -> dict[str, object]:
    if path == "/health":
        return analytics_health_payload()
    return data_payload(repo_root, path)


def analytics_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    if path == tag_routes.SAVE_TAGS_PATH:
        return HTTPStatus.OK, save_tags_response(repo_root, body, dry_run=dry_run)
    if path == tag_routes.IMPORT_ASSIGNMENTS_PREVIEW_PATH:
        return HTTPStatus.OK, import_tag_assignments_response(repo_root, body, preview=True, dry_run=dry_run)
    if path == tag_routes.IMPORT_ASSIGNMENTS_APPLY_PATH:
        return HTTPStatus.OK, import_tag_assignments_response(repo_root, body, preview=False, dry_run=dry_run)
    if path == tag_routes.IMPORT_REGISTRY_PATH:
        return HTTPStatus.OK, import_tag_registry_response(repo_root, body, dry_run=dry_run)
    if path == tag_routes.IMPORT_ALIASES_PATH:
        return HTTPStatus.OK, import_tag_aliases_response(repo_root, body, dry_run=dry_run)
    if path == tag_routes.DELETE_ALIAS_PATH:
        return HTTPStatus.OK, delete_tag_alias_response(repo_root, body, dry_run=dry_run)
    if path == tag_routes.MUTATE_ALIAS_PREVIEW_PATH:
        return HTTPStatus.OK, mutate_tag_alias_response(repo_root, body, preview=True, dry_run=dry_run)
    if path == tag_routes.MUTATE_ALIAS_APPLY_PATH:
        return HTTPStatus.OK, mutate_tag_alias_response(repo_root, body, preview=False, dry_run=dry_run)
    if path == tag_routes.MUTATE_TAG_PREVIEW_PATH:
        return HTTPStatus.OK, mutate_tag_response(repo_root, body, preview=True, dry_run=dry_run)
    if path == tag_routes.MUTATE_TAG_APPLY_PATH:
        return HTTPStatus.OK, mutate_tag_response(repo_root, body, preview=False, dry_run=dry_run)
    raise FileNotFoundError("Not found")


def save_tags_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {assignments_path}

    series_id = body.get("series_id")
    work_id = body.get("work_id")
    keep_work = body.get("keep_work")
    tags = body.get("tags")

    now_utc = utc_now()
    payload = tag_source.load_assignments(assignments_path)
    updated_payload, response_payload, would_write = tag_assignments.plan_assignment_save(
        payload,
        series_id,
        work_id,
        keep_work,
        tags,
        now_utc,
    )
    deleted = bool(response_payload.get("deleted"))
    normalized_series_id = str(response_payload.get("series_id") or "")
    normalized_work_id = response_payload.get("work_id")
    normalized_keep_work = response_payload.get("keep_work")

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = would_write
    else:
        if assignments_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(assignments_path, updated_payload, backups_dir)

    log_event(
        repo_root,
        "save_tags",
        {
            "series_id": normalized_series_id,
            "work_id": normalized_work_id,
            "keep_work": normalized_keep_work,
            "tag_count": response_payload["tag_count"],
            "deleted": deleted,
            "dry_run": dry_run,
        },
    )
    tag_activity.attach_tag_activity(
        repo_root=repo_root,
        endpoint=tag_routes.SAVE_TAGS_PATH,
        dry_run=dry_run,
        append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
        body=body,
        response_payload=response_payload,
        record_id=normalized_series_id,
        record_groups={
            "series": [normalized_series_id],
            "works": [normalized_work_id] if normalized_work_id else [],
        },
        detail_items=[
            f"Saved tag assignments for series {normalized_series_id}.",
            f"Updated work {normalized_work_id}." if normalized_work_id else "",
            f"Tag count: {response_payload['tag_count']}.",
        ],
        activity_id_suffix=f"work:{normalized_work_id}" if normalized_work_id else f"series:{normalized_series_id}",
    )
    return response_payload


def import_tag_assignments_response(
    repo_root: Path,
    body: dict[str, Any],
    *,
    preview: bool,
    dry_run: bool = False,
) -> dict[str, object]:
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    series_index_path = (repo_root / tag_source.SERIES_INDEX_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {assignments_path}

    import_assignments = tag_source.sanitize_import_assignments_session(body.get("import_assignments"))
    import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))
    resolutions = sanitize_import_resolutions(body.get("resolutions"))

    now_utc = utc_now()
    existing_payload = tag_source.load_assignments(assignments_path)
    series_index_payload = tag_source.load_series_index(series_index_path)
    preview_payload = tag_assignments.preview_assignment_import(
        existing_payload,
        import_assignments,
        series_index_payload,
    )
    response_payload = tag_assignments.build_assignment_import_preview_response(
        preview_payload,
        import_filename,
        now_utc,
    )

    if preview:
        log_event(
            repo_root,
            "import_tag_assignments_preview",
            {
                "staged_series_count": preview_payload["staged_series_count"],
                "applicable_count": preview_payload["applicable_count"],
                "conflict_count": preview_payload["conflict_count"],
                "invalid_count": preview_payload["invalid_count"],
                "missing_count": preview_payload["missing_count"],
                "dry_run": dry_run,
            },
        )
        return response_payload

    updated_payload, apply_stats = tag_assignments.apply_assignment_import(
        existing_payload,
        import_assignments,
        preview_payload,
        resolutions,
        now_utc,
    )
    response_payload = tag_assignments.build_assignment_import_apply_response(response_payload, apply_stats)
    apply_summary_text = str(response_payload.get("summary_text") or "")

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **apply_stats,
        }
    else:
        if assignments_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(assignments_path, updated_payload, backups_dir)

    log_event(
        repo_root,
        "import_tag_assignments",
        {
            **apply_stats,
            "dry_run": dry_run,
        },
    )
    if tag_activity.tag_activity_changed(apply_stats):
        tag_activity.attach_tag_activity(
            repo_root=repo_root,
            endpoint=tag_routes.IMPORT_ASSIGNMENTS_APPLY_PATH,
            dry_run=dry_run,
            append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
            body=body,
            response_payload=response_payload,
            detail_items=[
                apply_summary_text,
                f"Applied series: {apply_stats.get('applied_series')}; skipped: {apply_stats.get('skipped_series')}.",
            ],
            status=tag_activity.tag_activity_status(apply_stats),
        )
    return response_payload


def import_tag_registry_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {registry_path}

    mode = str(body.get("mode") or "").strip().lower()
    import_registry = body.get("import_registry")
    import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))

    now_utc = utc_now()
    existing_payload = tag_source.load_registry(registry_path)
    updated_payload, stats = tag_registry.apply_registry_import(existing_payload, import_registry, mode, now_utc)
    summary_text = tag_registry.build_import_summary_text(stats)

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "import_filename": import_filename,
        **stats,
    }

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    else:
        if registry_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(registry_path, updated_payload, backups_dir)

    log_event(
        repo_root,
        "import_tag_registry",
        {
            "summary_text": summary_text,
            "import_filename": import_filename,
            "mode": mode,
            "dry_run": dry_run,
            **stats,
        },
    )
    if tag_activity.tag_activity_changed(stats):
        tag_activity.attach_tag_activity(
            repo_root=repo_root,
            endpoint=tag_routes.IMPORT_REGISTRY_PATH,
            dry_run=dry_run,
            append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
            body=body,
            response_payload=response_payload,
            detail_items=[
                summary_text,
                f"Mode: {mode}; imported: {stats.get('imported_total')}; final tags: {stats.get('final_total')}.",
            ],
            status=tag_activity.tag_activity_status(stats),
        )
    return response_payload


def import_tag_aliases_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {aliases_path}

    mode = str(body.get("mode") or "").strip().lower()
    import_aliases = body.get("import_aliases")
    import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))

    now_utc = utc_now()
    existing_payload = tag_source.load_aliases(aliases_path)
    updated_payload, stats = tag_aliases.apply_aliases_import(existing_payload, import_aliases, mode, now_utc)
    summary_text = tag_registry.build_import_summary_text(stats, noun="aliases")

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "import_filename": import_filename,
        **stats,
    }

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    else:
        if aliases_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(aliases_path, updated_payload, backups_dir)

    log_event(
        repo_root,
        "import_tag_aliases",
        {
            "summary_text": summary_text,
            "import_filename": import_filename,
            "mode": mode,
            "dry_run": dry_run,
            **stats,
        },
    )
    if tag_activity.tag_activity_changed(stats):
        tag_activity.attach_tag_activity(
            repo_root=repo_root,
            endpoint=tag_routes.IMPORT_ALIASES_PATH,
            dry_run=dry_run,
            append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
            body=body,
            response_payload=response_payload,
            detail_items=[
                summary_text,
                f"Mode: {mode}; imported: {stats.get('imported_total')}; final aliases: {stats.get('final_total')}.",
            ],
            status=tag_activity.tag_activity_status(stats),
        )
    return response_payload


def delete_tag_alias_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {aliases_path}

    alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)

    now_utc = utc_now()
    existing_payload = tag_source.load_aliases(aliases_path)
    updated_payload, stats = tag_aliases.delete_alias_key(existing_payload, alias_key, now_utc)
    summary_text = f"deleted alias {alias_key}; final {int(stats.get('final_total') or 0)}"

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        **stats,
    }

    if dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    else:
        if aliases_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(aliases_path, updated_payload, backups_dir)

    log_event(
        repo_root,
        "delete_tag_alias",
        {
            "summary_text": summary_text,
            "dry_run": dry_run,
            **stats,
        },
    )
    tag_activity.attach_tag_activity(
        repo_root=repo_root,
        endpoint=tag_routes.DELETE_ALIAS_PATH,
        dry_run=dry_run,
        append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
        body=body,
        response_payload=response_payload,
        detail_items=[summary_text],
        status=tag_activity.tag_activity_status(stats),
    )
    return response_payload


def mutate_tag_alias_response(
    repo_root: Path,
    body: dict[str, Any],
    *,
    preview: bool,
    dry_run: bool = False,
) -> dict[str, object]:
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {aliases_path}

    alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)
    new_alias_key = tag_source.sanitize_alias_key(body.get("new_alias", alias_key), 1)
    description = tag_source.sanitize_alias_description(body.get("description", ""), "description")
    tags = tag_source.sanitize_tag_id_list(body.get("tags"), "tags")
    tag_source.enforce_alias_group_constraints(tags, "tags")

    now_utc = utc_now()
    aliases_payload = tag_source.load_aliases(aliases_path)
    registry_payload = tag_source.load_registry(registry_path)
    aliases_updated, stats = tag_aliases.mutate_alias_entry(
        aliases_payload=aliases_payload,
        registry_payload=registry_payload,
        alias_key=alias_key,
        new_alias_key=new_alias_key,
        description=description,
        tags=tags,
        now_utc=now_utc,
    )
    summary_text = tag_aliases.build_alias_mutation_summary_text(stats)

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "preview": preview,
        **stats,
    }

    should_write = bool(stats.get("changed"))
    if preview:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    elif dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    elif should_write:
        if aliases_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(aliases_path, aliases_updated, backups_dir)

    if not preview:
        log_event(
            repo_root,
            "mutate_tag_alias",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            tag_activity.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.MUTATE_ALIAS_APPLY_PATH,
                dry_run=dry_run,
                append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Alias: {stats.get('alias')}; new alias: {stats.get('new_alias')}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload


def mutate_tag_response(
    repo_root: Path,
    body: dict[str, Any],
    *,
    preview: bool,
    dry_run: bool = False,
) -> dict[str, object]:
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    backups_dir = (repo_root / BACKUPS_REL_DIR).resolve()
    allowed_write_paths = {registry_path, aliases_path, assignments_path}

    action = str(body.get("action") or "").strip().lower()
    old_tag_id = tag_source.sanitize_tag_id(body.get("tag_id"), "tag_id")
    raw_allow_canonical_rename = body.get("allow_canonical_rename", False)
    if not isinstance(raw_allow_canonical_rename, bool):
        raise ValueError("allow_canonical_rename must be a boolean")
    allow_canonical_rename = raw_allow_canonical_rename

    if action not in tag_registry.MUTATE_ACTIONS:
        raise ValueError(f"action must be one of: {sorted(tag_registry.MUTATE_ACTIONS)}")

    new_slug = None
    new_description = None
    if action == "edit":
        raw_new_slug = body.get("new_slug")
        if raw_new_slug is not None and str(raw_new_slug).strip():
            new_slug = tag_source.sanitize_slug(raw_new_slug, "new_slug")
        if "description" in body:
            new_description = tag_source.sanitize_alias_description(body.get("description"), "description")

    now_utc = utc_now()
    registry_payload = tag_source.load_registry(registry_path)
    aliases_payload = tag_source.load_aliases(aliases_path)
    assignments_payload = tag_source.load_assignments(assignments_path)

    registry_updated, mutate_meta = tag_registry.mutate_registry_tag(
        registry_payload,
        action=action,
        old_tag_id=old_tag_id,
        now_utc=now_utc,
        new_slug=new_slug,
        new_description=new_description,
        allow_canonical_rename=allow_canonical_rename,
    )
    new_tag_id = mutate_meta.get("new_tag_id")
    rewrite_to = str(new_tag_id) if new_tag_id else None
    should_rewrite_refs = (action == "delete") or (rewrite_to is not None and rewrite_to != old_tag_id)
    if should_rewrite_refs:
        aliases_updated, alias_stats = tag_aliases.rewrite_aliases_for_tag(
            aliases_payload,
            old_tag_id=old_tag_id,
            new_tag_id=rewrite_to,
            now_utc=now_utc,
        )
        assignments_updated, assignment_stats = tag_registry.rewrite_assignments_for_tag(
            assignments_payload,
            old_tag_id=old_tag_id,
            new_tag_id=rewrite_to,
            now_utc=now_utc,
        )
    else:
        aliases_updated = aliases_payload
        assignments_updated = assignments_payload
        alias_stats = {
            "aliases_rewritten": 0,
            "aliases_removed_empty": 0,
            "aliases_removed_redundant": 0,
            "aliases_final_total": len(aliases_payload.get("aliases", {})) if isinstance(aliases_payload.get("aliases"), dict) else 0,
        }
        assignment_stats = {
            "series_rows_touched": 0,
            "series_tag_refs_rewritten": 0,
            "work_rows_touched": 0,
            "work_tag_refs_rewritten": 0,
        }

    stats: dict[str, Any] = {
        "action": action,
        "old_tag_id": old_tag_id,
        "new_tag_id": rewrite_to,
        "canonical_changed": bool(mutate_meta.get("canonical_changed")),
        "description_changed": bool(mutate_meta.get("description_changed")),
        **alias_stats,
        **assignment_stats,
    }
    summary_text = tag_registry.build_mutation_summary_text(stats)

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "preview": preview,
        **stats,
    }

    payloads_to_write: dict[Path, dict[str, Any]] = {
        registry_path: registry_updated,
    }
    if should_rewrite_refs:
        payloads_to_write[aliases_path] = aliases_updated
        payloads_to_write[assignments_path] = assignments_updated

    if preview:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    elif dry_run:
        response_payload["dry_run"] = True
        response_payload["would_write"] = {
            "updated_at_utc": now_utc,
            **stats,
        }
    else:
        for target in payloads_to_write:
            if target not in allowed_write_paths:
                raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write_many(payloads_to_write, backups_dir)

    if not preview:
        log_event(
            repo_root,
            "mutate_tag",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            tag_activity.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.MUTATE_TAG_APPLY_PATH,
                dry_run=dry_run,
                append_activity=lambda entry: studio_activity.append_studio_activity(repo_root, entry),
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Action: {action}; tag: {old_tag_id}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload


def sanitize_import_resolutions(raw_resolutions: object) -> dict[str, str]:
    resolutions: dict[str, str] = {}
    if raw_resolutions is None:
        return resolutions
    if not isinstance(raw_resolutions, dict):
        raise ValueError("resolutions must be an object")
    for raw_series_id, raw_resolution in raw_resolutions.items():
        series_id = str(raw_series_id or "").strip().lower()
        if not series_id:
            continue
        resolution = str(raw_resolution or "").strip().lower()
        if resolution not in {"overwrite", "skip"}:
            raise ValueError(f"resolutions[{series_id}] must be overwrite or skip")
        resolutions[series_id] = resolution
    return resolutions


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    try:
        script_logging.append_script_log(
            SCRIPTS_DIR / "analytics" / "tag_write_server.py",
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        # Logging should not block local API requests.
        pass
