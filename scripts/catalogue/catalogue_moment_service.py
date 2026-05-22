"""Catalogue moment preview service routes for Local Studio."""

from __future__ import annotations

from typing import Any, Mapping

from catalogue.catalogue_build_media import build_local_media_plan, build_moment_readiness
from catalogue.catalogue_build_scopes import build_scope_for_moment, preview_moment_source
from catalogue.catalogue_service_context import CatalogueWriteContext, load_moments_payload, normalize_moment_id_value
from catalogue.moment_sources import normalize_moment_metadata_record


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
