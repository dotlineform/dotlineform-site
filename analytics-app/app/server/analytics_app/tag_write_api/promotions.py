#!/usr/bin/env python3
"""Tag promotion and demotion write handlers for the Analytics app API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tag_services import tag_activity
from tag_services import tag_promotion_mutations as tag_promotions
from tag_services import tag_routes
from tag_services import tag_source_model as tag_source
from tag_services import tag_write_transactions as tag_transactions
from tag_write_api import common


def promote_tag_alias_response(
    repo_root: Path,
    body: dict[str, Any],
    *,
    preview: bool,
    dry_run: bool = False,
) -> dict[str, object]:
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    allowed_write_paths = {registry_path, aliases_path}

    alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)

    now_utc = common.utc_now()
    registry_payload = tag_source.load_registry(registry_path)
    aliases_payload = tag_source.load_aliases(aliases_path)
    allowed_groups = tag_source.extract_allowed_groups(registry_payload)
    group = tag_source.sanitize_group(body.get("group"), allowed_groups, "group")

    registry_updated, aliases_updated, stats, registry_changed, aliases_changed = tag_promotions.promote_alias_to_canonical_tag(
        registry_payload=registry_payload,
        aliases_payload=aliases_payload,
        alias_key=alias_key,
        group=group,
        now_utc=now_utc,
    )
    summary_text = tag_promotions.build_promote_summary_text(stats)

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "preview": preview,
        **stats,
    }

    payloads_to_write: dict[Path, dict[str, Any]] = {}
    if registry_changed:
        payloads_to_write[registry_path] = registry_updated
    if aliases_changed:
        payloads_to_write[aliases_path] = aliases_updated

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
        if payloads_to_write:
            tag_transactions.atomic_write_many(payloads_to_write)

    if not preview:
        common.log_event(
            repo_root,
            "promote_tag_alias",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            common.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.PROMOTE_ALIAS_APPLY_PATH,
                dry_run=dry_run,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Promoted alias {stats.get('alias')} to {stats.get('new_tag_id')}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload


def demote_tag_response(
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

    old_tag_id = tag_source.sanitize_tag_id(body.get("tag_id"), "tag_id")
    alias_targets = tag_source.sanitize_tag_id_list(body.get("alias_targets"), "alias_targets")
    tag_source.enforce_alias_group_constraints(alias_targets, "alias_targets")

    now_utc = common.utc_now()
    registry_payload = tag_source.load_registry(registry_path)
    aliases_payload = tag_source.load_aliases(aliases_path)
    assignments_payload = tag_source.load_assignments(assignments_path)

    registry_updated, aliases_updated, assignments_updated, stats, assignments_changed = tag_promotions.demote_tag_to_alias(
        registry_payload=registry_payload,
        aliases_payload=aliases_payload,
        assignments_payload=assignments_payload,
        old_tag_id=old_tag_id,
        alias_targets=alias_targets,
        now_utc=now_utc,
    )
    summary_text = tag_promotions.build_demote_summary_text(stats)

    response_payload: dict[str, object] = {
        "ok": True,
        "updated_at_utc": now_utc,
        "summary_text": summary_text,
        "preview": preview,
        **stats,
    }

    payloads_to_write: dict[Path, dict[str, Any]] = {
        registry_path: registry_updated,
        aliases_path: aliases_updated,
    }
    if assignments_changed:
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
            "demote_tag",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            common.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.DEMOTE_TAG_APPLY_PATH,
                dry_run=dry_run,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Demoted {stats.get('old_tag_id')} to alias {stats.get('alias_key')}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload
