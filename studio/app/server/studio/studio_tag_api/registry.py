#!/usr/bin/env python3
"""Tag registry write handlers for the Studio tag API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tags import tag_activity
from tags import tag_alias_mutations as tag_aliases
from tags import tag_registry_mutations as tag_registry
from tags import tag_routes
from tags import tag_source_model as tag_source
from tags import tag_write_transactions as tag_transactions
from studio_tag_api import common


def create_tag_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    """Validate and atomically create one canonical tag."""
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    allowed_write_paths = {registry_path}

    now_utc = common.utc_now()
    existing_payload = tag_source.load_registry(registry_path)
    updated_payload, stats = tag_registry.create_registry_tag(
        existing_payload,
        group=body.get("group"),
        slug=body.get("slug"),
        description=body.get("description"),
        now_utc=now_utc,
    )
    summary_text = tag_registry.build_create_summary_text(stats)

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
            "tag_id": stats["tag_id"],
            "added": stats["added"],
            "final_total": stats["final_total"],
        }
    else:
        if registry_path not in allowed_write_paths:
            raise ValueError("write target not allowlisted")
        tag_transactions.atomic_write(registry_path, updated_payload)

    common.log_event(
        repo_root,
        "create_tag",
        {
            "summary_text": summary_text,
            "dry_run": dry_run,
            **stats,
        },
    )
    common.attach_tag_activity(
        repo_root=repo_root,
        endpoint=tag_routes.CREATE_TAG_PATH,
        dry_run=dry_run,
        body=body,
        response_payload=response_payload,
        record_id=str(stats["tag_id"]),
        detail_items=[
            summary_text,
            f"Created canonical tag: {stats['tag_id']}.",
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

    now_utc = common.utc_now()
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
        tag_transactions.atomic_write_many(payloads_to_write)

    if not preview:
        common.log_event(
            repo_root,
            "mutate_tag",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            common.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.MUTATE_TAG_APPLY_PATH,
                dry_run=dry_run,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Action: {action}; tag: {old_tag_id}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload
