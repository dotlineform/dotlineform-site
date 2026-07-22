#!/usr/bin/env python3
"""Direct Docs Viewer document-package application service."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

import docs_activity
import docs_document_package_routes as routes
from docs_document_packages.apply_hierarchy import apply_hierarchy_updates
from docs_document_packages.apply_summaries import apply_summary_updates
from docs_document_packages.export_config import (
    default_content_format,
    load_config_file,
    supported_content_formats,
    supported_target_formats,
    supports_return_import,
    validate_config_payload,
)
from docs_document_packages.package import (
    build_document_package,
    list_returned_document_packages,
    selectable_document_records,
    update_document_prepare_context,
)
from docs_document_packages.review import (
    parse_returned_document_records,
    review_returned_document_package,
)
from docs_document_packages.review_sources import create_review_source_folder
from docs_document_packages.workspace import configured_workspace_paths, workspace_status
from docs_document_packages.write import DocumentPackageWriteDependencies
from docs_import_document_package_content import normalize_documents_import_content
from docs_management_context import log_event
from docs_scope_config import load_docs_scope_configs
import docs_source_model as source_model
import docs_write_rebuild


DOCUMENTS_DATA_DOMAIN = "documents"
FORBIDDEN_REQUEST_FIELDS = {
    "app",
    "adapter_id",
    "data_domain",
    "operation",
    "record_indices",
    "selection",
}
REVIEW_ACTIONS = (
    {"id": "content", "label": "Review content"},
    {"id": "summaries", "label": "Review summaries"},
    {"id": "hierarchy", "label": "Review hierarchy"},
)
APPLY_ACTIONS = (
    {"id": "summary_apply", "label": "Update summaries"},
    {"id": "hierarchy_apply", "label": "Apply hierarchy"},
)


def refresh_source_model_scope_configs(repo_root: Path) -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root)
    source_model.DOCS_SCOPE_CONFIGS.clear()
    source_model.DOCS_SCOPE_CONFIGS.update(configs)
    source_model.DOCUMENT_SOURCE_ROOTS.clear()
    source_model.DOCUMENT_SOURCE_ROOTS.update(
        {scope: source_model.document_source_path(config) for scope, config in configs.items()}
    )
    return configs


def query_value(params: dict[str, list[str]], key: str) -> str:
    return str((params.get(key) or [""])[0] or "").strip()


def require_scope(repo_root: Path, value: Any) -> str:
    scope = str(value or "").strip().lower()
    try:
        configs = refresh_source_model_scope_configs(repo_root)
    except FileNotFoundError:
        configs = {
            configured_scope: source_model.DOCS_SCOPE_CONFIGS.get(configured_scope)
            for configured_scope in source_model.DOCUMENT_SOURCE_ROOTS
        }
    if scope not in configs:
        raise ValueError(f"scope must be one of: {', '.join(sorted(configs))}")
    return scope


def require_direct_request(body: dict[str, Any]) -> None:
    if "record_indices" in body:
        raise ValueError("record_indices is not supported; returned document packages are atomic")
    forbidden = sorted(field for field in FORBIDDEN_REQUEST_FIELDS if field in body)
    if forbidden:
        raise ValueError(
            "document package requests do not accept generic adapter fields: "
            + ", ".join(forbidden)
        )


def dry_run_value(body: dict[str, Any]) -> bool:
    value = body.get("dry_run", False)
    if not isinstance(value, bool):
        raise ValueError("dry_run must be true or false")
    return value


def optional_boolean_value(body: dict[str, Any], key: str) -> bool | None:
    if key not in body:
        return None
    value = body.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be true or false")
    return value


def profile_contract(config: dict[str, Any]) -> dict[str, Any]:
    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    content = config.get("content_format") if isinstance(config.get("content_format"), dict) else {}
    selection = config.get("selection") if isinstance(config.get("selection"), dict) else {}
    limits = config.get("limits") if isinstance(config.get("limits"), dict) else {}
    external_context = (
        config.get("external_context")
        if isinstance(config.get("external_context"), dict)
        else {}
    )
    document_fields = [
        {
            "output_path": str(field.get("output_path") or "").strip(),
            "required": field.get("required") is True,
        }
        for field in config.get("document_fields", [])
        if isinstance(field, dict) and str(field.get("output_path") or "").strip()
    ]
    return {
        "profile_id": str(config.get("id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "description": str(config.get("description") or "").strip(),
        "target_format": str(target.get("format") or "").strip(),
        "supported_target_formats": supported_target_formats(config),
        "record_shape": str(target.get("record_shape") or "").strip(),
        "content_format": default_content_format(config),
        "supported_content_formats": supported_content_formats(config),
        "supports_return_import": supports_return_import(config),
        "selection": {
            "mode": str(selection.get("mode") or "").strip(),
            "include_descendants": selection.get("include_descendants") is not False,
            "include_non_viewable": selection.get("include_non_viewable") is not False,
            "supports_include_non_viewable": selection.get("supports_include_non_viewable") is True,
            "supports_missing_summary_only": selection.get("supports_missing_summary_only") is True,
            "default_missing_summary_only": selection.get("default_missing_summary_only") is True,
        },
        "limits": {
            "max_documents": limits.get("max_documents") if isinstance(limits.get("max_documents"), int) else None,
        },
        "external_context": external_context,
        "document_fields": document_fields,
    }


def config_payload(repo_root: Path) -> dict[str, Any]:
    configs = refresh_source_model_scope_configs(repo_root)
    profile_payload = load_config_file(repo_root)
    errors, warnings = validate_config_payload(profile_payload)
    if errors:
        raise ValueError("document package profiles are invalid: " + "; ".join(errors))
    status = workspace_status(repo_root)
    return {
        "ok": True,
        "profiles": [
            profile_contract(config)
            for config in profile_payload.get("configs", [])
            if isinstance(config, dict) and config.get("enabled") is not False
        ],
        "scopes": [
            {"scope": scope, "label": source_model.humanize(scope)}
            for scope in sorted(configs)
        ],
        "review_actions": list(REVIEW_ACTIONS),
        "apply_actions": list(APPLY_ACTIONS),
        "workspace": {
            "available": bool(status.get("available")),
            "message": str(status.get("message") or ""),
        },
        "warnings": warnings,
    }


def documents_payload(repo_root: Path, params: dict[str, list[str]]) -> dict[str, Any]:
    scope = require_scope(repo_root, query_value(params, "scope"))
    return selectable_document_records(repo_root, scope=scope, selection_model="documents")


def returned_payload(repo_root: Path, params: dict[str, list[str]]) -> dict[str, Any]:
    scope = require_scope(repo_root, query_value(params, "scope"))
    roots = configured_workspace_paths(repo_root)
    report = list_returned_document_packages(
        repo_root,
        scope=scope,
        staging_root=roots.import_staging,
        metadata_root=roots.meta,
    )
    for collection_name in ("files", "blocked_files", "unassigned_files"):
        report[collection_name] = [
            {
                key: value
                for key, value in item.items()
                if key not in {"app", "adapter_id", "config_id", "data_domain"}
            }
            for item in report.get(collection_name, [])
            if isinstance(item, dict)
        ]
    return report


def get_payload(
    repo_root: Path,
    path: str,
    params: dict[str, list[str]],
) -> dict[str, Any]:
    if path == routes.CONFIG_PATH:
        return config_payload(repo_root)
    if path == routes.DOCUMENTS_PATH:
        return documents_payload(repo_root, params)
    if path == routes.RETURNED_PATH:
        return returned_payload(repo_root, params)
    raise FileNotFoundError("Not found")


def prepare_package(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope = require_scope(repo_root, body.get("scope"))
    profile_id = str(body.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("profile_id is required")
    doc_ids = body.get("doc_ids", [])
    if not isinstance(doc_ids, list):
        raise ValueError("doc_ids must be a list")
    select_all = body.get("select_all", False)
    if not isinstance(select_all, bool):
        raise ValueError("select_all must be true or false")
    dry_run = dry_run_value(body)
    missing_summary_only = optional_boolean_value(body, "missing_summary_only")
    include_non_viewable = optional_boolean_value(body, "include_non_viewable")
    roots = configured_workspace_paths(repo_root)
    payload = build_document_package(
        repo_root,
        scope=scope,
        data_domain=DOCUMENTS_DATA_DOMAIN,
        config_id=profile_id,
        raw_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
        include_non_viewable=include_non_viewable,
        dry_run=dry_run,
        config_path="",
        target_format=str(body.get("target_format") or "").strip(),
        content_format=str(body.get("content_format") or "").strip(),
        output_root=roots.exports,
        metadata_root=roots.meta,
    )
    payload["profile_id"] = profile_id
    payload.pop("config_id", None)
    if payload.get("ok"):
        action = "Validated package" if dry_run else "Prepared package"
        count = int(payload.get("counts", {}).get("exported") or 0)
        payload["summary_text"] = f"{action} with {count} document(s)."
    log_event(
        repo_root,
        "document-package-prepare",
        {
            "scope": scope,
            "profile_id": profile_id,
            "dry_run": dry_run,
            "output_written": bool(payload.get("output_written")),
            "exported": int(payload.get("counts", {}).get("exported") or 0),
        },
    )
    docs_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
    return payload


def update_context(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    refresh_source_model_scope_configs(repo_root)
    profile_id = str(body.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("profile_id is required")
    dry_run = dry_run_value(body)
    payload = update_document_prepare_context(
        repo_root,
        config_id=profile_id,
        external_context=body.get("external_context"),
        config_path="",
        dry_run=dry_run,
    )
    payload["profile_id"] = profile_id
    payload.pop("config_id", None)
    log_event(
        repo_root,
        "document-package-context",
        {"profile_id": profile_id, "dry_run": dry_run, "output_written": bool(payload.get("output_written"))},
    )
    return payload


def inspect_returned(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope = require_scope(repo_root, body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    roots = configured_workspace_paths(repo_root)
    return parse_returned_document_records(
        repo_root,
        scope=scope,
        staged_filename=staged_filename,
        staging_root=roots.import_staging,
        metadata_root=roots.meta,
    )


def content_review_response(payload: dict[str, Any]) -> dict[str, Any]:
    ok = payload.get("ok") is True
    existing = ok and payload.get("review_existing") is True
    written = ok and payload.get("review_source_folder_written") is True
    ready = existing or written
    package_id = str(payload.get("folder_id") or "").strip() if ready else ""
    if ready and not package_id:
        response = dict(payload)
        response.update({
            "ok": False,
            "review_action": "content",
            "review_package_id": "",
            "review_url": "",
            "review_existing": False,
            "issues": list(payload.get("issues") or []) + [
                {
                    "level": "error",
                    "code": "missing_review_package_id",
                    "message": "Docs Review package identity is unavailable.",
                }
            ],
            "summary_text": "Docs Review package was not prepared.",
        })
        return response
    if existing:
        summary_text = f"Docs Review package {package_id} already exists."
    elif written:
        summary_text = f"Prepared Docs Review package {package_id}."
    else:
        summary_text = str(payload.get("summary_text") or "Docs Review package was not prepared.").strip()
    response = dict(payload)
    response.update({
        "review_action": "content",
        "review_package_id": package_id,
        "review_url": f"/docs-review/?package={package_id}" if package_id else "",
        "review_existing": existing,
        "summary_text": summary_text,
    })
    return response


def review_returned(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope = require_scope(repo_root, body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    review_action = str(body.get("review_action") or "").strip()
    if review_action not in {item["id"] for item in REVIEW_ACTIONS}:
        raise ValueError("review_action must be content, summaries, or hierarchy")
    dry_run = dry_run_value(body)
    roots = configured_workspace_paths(repo_root)
    if review_action == "content":
        payload = content_review_response(
            create_review_source_folder(
                repo_root,
                scope=scope,
                staged_filename=staged_filename,
                dry_run=dry_run,
                staging_root=roots.import_staging,
                metadata_root=roots.meta,
                preview_root=roots.import_preview,
                normalize_import_content=normalize_documents_import_content,
            )
        )
    else:
        payload = review_returned_document_package(
            repo_root,
            scope=scope,
            staged_filename=staged_filename,
            dry_run=dry_run,
            staging_root=roots.import_staging,
            metadata_root=roots.meta,
            preview_root=roots.import_preview,
            data_domain=DOCUMENTS_DATA_DOMAIN,
        )
        if payload.get("ok"):
            count = len(payload.get("review_records", []))
            label = "hierarchy" if review_action == "hierarchy" else "summaries"
            payload["summary_text"] = f"Reviewed {label} for {count} document(s)."
    log_event(
        repo_root,
        "document-package-review",
        {
            "scope": scope,
            "staged_filename": staged_filename,
            "review_action": review_action,
            "dry_run": dry_run,
            "ok": bool(payload.get("ok")),
        },
    )
    return payload


def apply_returned(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    scope = require_scope(repo_root, body.get("scope"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    apply_action = str(body.get("apply_action") or "").strip()
    if apply_action not in {item["id"] for item in APPLY_ACTIONS}:
        raise ValueError("apply_action must be summary_apply or hierarchy_apply")
    confirmed = body.get("confirm", False)
    if not isinstance(confirmed, bool):
        raise ValueError("confirm must be true or false")
    dry_run = dry_run_value(body)
    roots = configured_workspace_paths(repo_root)
    common = {
        "scope": scope,
        "staged_filename": staged_filename,
        "confirmed": confirmed,
        "dry_run": dry_run,
        "staging_root": roots.import_staging,
        "metadata_root": roots.meta,
        "subject_label": "Documents",
        "dependencies": DocumentPackageWriteDependencies(
            perform_source_write_and_rebuild=docs_write_rebuild.perform_source_write_and_rebuild,
        ),
    }
    payload = (
        apply_summary_updates(repo_root, **common)
        if apply_action == "summary_apply"
        else apply_hierarchy_updates(repo_root, **common)
    )
    payload.pop("operation", None)
    payload["apply_action"] = apply_action
    log_event(
        repo_root,
        "document-package-apply",
        {
            "scope": scope,
            "staged_filename": staged_filename,
            "apply_action": apply_action,
            "dry_run": dry_run,
            "confirmed": confirmed,
            "ok": bool(payload.get("ok")),
        },
    )
    docs_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
    return payload


def post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    require_direct_request(body)
    if path == routes.PREPARE_PATH:
        payload = prepare_package(repo_root, body)
    elif path == routes.CONTEXT_PATH:
        payload = update_context(repo_root, body)
    elif path == routes.RETURNED_INSPECT_PATH:
        payload = inspect_returned(repo_root, body)
    elif path == routes.RETURNED_REVIEW_PATH:
        payload = review_returned(repo_root, body)
    elif path == routes.RETURNED_APPLY_PATH:
        payload = apply_returned(repo_root, body)
    else:
        raise FileNotFoundError("Not found")
    return (
        HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST,
        payload,
    )


__all__ = ["config_payload", "get_payload", "post_response"]
