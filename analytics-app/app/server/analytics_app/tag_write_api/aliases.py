#!/usr/bin/env python3
"""Tag alias write handlers for the Analytics app API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tag_services import tag_activity
from tag_services import tag_alias_mutations as tag_aliases
from tag_services import tag_registry_mutations as tag_registry
from tag_services import tag_routes
from tag_services import tag_source_model as tag_source
from tag_services import tag_write_transactions as tag_transactions
from tag_write_api import common


def import_tag_aliases_response(repo_root: Path, body: dict[str, Any], *, dry_run: bool = False) -> dict[str, object]:
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    allowed_write_paths = {aliases_path}

    mode = str(body.get("mode") or "").strip().lower()
    import_aliases = body.get("import_aliases")
    import_filename = tag_source.sanitize_import_filename(body.get("import_filename"))

    now_utc = common.utc_now()
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
        tag_transactions.atomic_write(aliases_path, updated_payload)

    common.log_event(
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
        common.attach_tag_activity(
            repo_root=repo_root,
            endpoint=tag_routes.IMPORT_ALIASES_PATH,
            dry_run=dry_run,
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
    allowed_write_paths = {aliases_path}

    alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)

    now_utc = common.utc_now()
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
        tag_transactions.atomic_write(aliases_path, updated_payload)

    common.log_event(
        repo_root,
        "delete_tag_alias",
        {
            "summary_text": summary_text,
            "dry_run": dry_run,
            **stats,
        },
    )
    common.attach_tag_activity(
        repo_root=repo_root,
        endpoint=tag_routes.DELETE_ALIAS_PATH,
        dry_run=dry_run,
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
    allowed_write_paths = {aliases_path}

    alias_key = tag_source.sanitize_alias_key(body.get("alias"), 0)
    new_alias_key = tag_source.sanitize_alias_key(body.get("new_alias", alias_key), 1)
    description = tag_source.sanitize_alias_description(body.get("description", ""), "description")
    tags = tag_source.sanitize_tag_id_list(body.get("tags"), "tags")
    tag_source.enforce_alias_group_constraints(tags, "tags")

    now_utc = common.utc_now()
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
        tag_transactions.atomic_write(aliases_path, aliases_updated)

    if not preview:
        common.log_event(
            repo_root,
            "mutate_tag_alias",
            {
                "summary_text": summary_text,
                "dry_run": dry_run,
                **stats,
            },
        )
        if tag_activity.tag_activity_changed(stats):
            common.attach_tag_activity(
                repo_root=repo_root,
                endpoint=tag_routes.MUTATE_ALIAS_APPLY_PATH,
                dry_run=dry_run,
                body=body,
                response_payload=response_payload,
                detail_items=[
                    summary_text,
                    f"Alias: {stats.get('alias')}; new alias: {stats.get('new_alias')}.",
                ],
                status=tag_activity.tag_activity_status(stats),
            )
    return response_payload
