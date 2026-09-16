#!/usr/bin/env python3
"""Direct Docs Viewer document-package application service."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
from typing import Any

import docs_document_package_routes as routes
from docs_document_packages.export_config import (
    default_content_format,
    load_config_file,
    supported_content_formats,
    supported_target_formats,
    supports_docs_review,
    supports_return_import,
    validate_full_config_payload,
)
from docs_document_packages.returned_common import (
    DOCS_REVIEW_CAPABILITY,
    RETURN_IMPORT_CAPABILITY,
)
from docs_document_packages.package import (
    build_document_package,
    list_returned_document_packages,
    selectable_document_records,
)
from docs_document_packages.review_sources import create_review_source_folder
from docs_document_packages.workspace import configured_workspace_paths, workspace_status
from docs_import_document_package_content import normalize_documents_import_content
from docs_management_context import log_event
from docs_management_document_target import resolve_managed_document_collection
from docs_document_packages.provenance import require_package_stage


DOCUMENTS_DATA_DOMAIN = "documents"
FORBIDDEN_REQUEST_FIELDS = {
    "app",
    "adapter_id",
    "data_domain",
    "operation",
    "record_indices",
    "selection",
    "scope",
    "sub_scope",
}
PACKAGE_COLLECTION_ALIAS_FIELDS = {"scope", "sub_scope", "parent_scope"}


def query_value(params: dict[str, list[str]], key: str) -> str:
    return str((params.get(key) or [""])[0] or "").strip()


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


def profile_contract(
    config: dict[str, Any],
    *,
    return_import_enabled: bool,
    flat_collection: bool = False,
) -> dict[str, Any]:
    target = config.get("target") if isinstance(config.get("target"), dict) else {}
    selection = config.get("selection") if isinstance(config.get("selection"), dict) else {}
    limits = config.get("limits") if isinstance(config.get("limits"), dict) else {}
    contract = {
        "profile_id": str(config.get("id") or "").strip(),
        "label": str(config.get("label") or "").strip(),
        "description": str(config.get("description") or "").strip(),
        "target_format": str(target.get("format") or "").strip(),
        "supported_target_formats": supported_target_formats(config),
        "record_shape": str(target.get("record_shape") or "").strip(),
        "content_format": default_content_format(config),
        "supported_content_formats": supported_content_formats(config),
        "supports_docs_review": supports_docs_review(config),
        "supports_return_import": (
            return_import_enabled and supports_return_import(config)
        ),
        "selection": {
            "mode": str(selection.get("mode") or "").strip(),
            "include_descendants": selection.get("include_descendants") is not False,
            "supports_missing_summary_only": selection.get("supports_missing_summary_only") is True,
            "default_missing_summary_only": selection.get("default_missing_summary_only") is True,
        },
        "limits": {
            "max_documents": limits.get("max_documents") if isinstance(limits.get("max_documents"), int) else None,
        },
    }
    if flat_collection:
        contract["selection"]["include_descendants"] = False
    return contract


def config_payload(
    repo_root: Path,
    params: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    collection = None
    request_params = params or {}
    stage = require_package_stage(query_value(request_params, "stage"))
    if "collection" in request_params:
        collection = resolve_managed_document_collection(
            repo_root,
            stage=query_value(request_params, "stage"),
            collection=query_value(request_params, "collection"),
        )
    profile_payload = load_config_file(repo_root)
    errors, warnings = validate_full_config_payload(profile_payload)
    if errors:
        raise ValueError("document package profiles are invalid: " + "; ".join(errors))
    status = workspace_status(repo_root)
    payload = {
        "ok": True,
        "profiles": [
            profile_contract(
                config,
                return_import_enabled=(
                    collection is None
                    or collection.document_config.supports_return_import
                ),
                flat_collection=collection is not None,
            )
            for config in profile_payload.get("configs", [])
            if isinstance(config, dict) and config.get("enabled") is not False
        ],
        "stage": stage,
        "workspace": {
            "available": bool(status.get("available")),
            "message": str(status.get("message") or ""),
        },
        "warnings": warnings,
    }
    if collection is not None:
        payload.update({
            "stage": collection.stage,
            "collection": collection.collection,
            "flat_collection": True,
        })
    return payload


def documents_payload(repo_root: Path, params: dict[str, list[str]]) -> dict[str, Any]:
    stage = require_package_stage(query_value(params, "stage"))
    collection = ""
    if "collection" in params:
        resolved_collection = resolve_managed_document_collection(
            repo_root,
            stage=stage,
            collection=query_value(params, "collection"),
        )
        collection = resolved_collection.collection
    return selectable_document_records(
        repo_root,
        stage=stage,
        collection=collection,
        selection_model="collection_documents" if collection else "documents",
    )


def returned_payload(repo_root: Path, params: dict[str, list[str]]) -> dict[str, Any]:
    stage = require_package_stage(query_value(params, "stage"))
    collection = None
    if "collection" in params:
        resolved_collection = resolve_managed_document_collection(
            repo_root,
            stage=stage,
            collection=query_value(params, "collection"),
        )
        if not resolved_collection.document_config.supports_return_import:
            raise ValueError(
                "returned-package import is not enabled for configured "
                f"collection {resolved_collection.stage}/{resolved_collection.collection}"
            )
        collection = resolved_collection.collection
    roots = configured_workspace_paths(repo_root)
    report = list_returned_document_packages(
        repo_root,
        stage=stage,
        collection=collection,
        required_capability=(
            RETURN_IMPORT_CAPABILITY
            if collection is not None
            else DOCS_REVIEW_CAPABILITY
        ),
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
    require_package_stage(query_value(params, "stage"))
    if "scope" in params:
        raise ValueError("scope is retired; use stage and optional collection")
    if "sub_scope" in params:
        raise ValueError("sub_scope is retired; use collection")
    if path == routes.CONFIG_PATH:
        return config_payload(repo_root, params)
    if path == routes.DOCUMENTS_PATH:
        return documents_payload(repo_root, params)
    if path == routes.RETURNED_PATH:
        return returned_payload(repo_root, params)
    raise FileNotFoundError("Not found")


def prepare_package(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if "include_non_viewable" in body or "include_non_publishable" in body:
        raise ValueError(
            "publication eligibility filters are not accepted for package preparation"
        )
    collection_aliases = sorted(
        field for field in PACKAGE_COLLECTION_ALIAS_FIELDS if field in body
    )
    if collection_aliases:
        raise ValueError(
            "document package prepare accepts only stage and optional collection "
            "for collection identity: "
            + ", ".join(collection_aliases)
        )
    stage = require_package_stage(body.get("stage"))
    collection = ""
    if "collection" in body:
        resolved_collection = resolve_managed_document_collection(
            repo_root,
            stage=stage,
            collection=body.get("collection"),
        )
        collection = resolved_collection.collection
    profile_id = str(body.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("profile_id is required")
    doc_ids = body.get("doc_ids", [])
    if not isinstance(doc_ids, list):
        raise ValueError("doc_ids must be a list")
    select_all = body.get("select_all", False)
    if not isinstance(select_all, bool):
        raise ValueError("select_all must be true or false")
    if collection and select_all:
        raise ValueError("collection package preparation requires select_all false")
    dry_run = dry_run_value(body)
    missing_summary_only = optional_boolean_value(body, "missing_summary_only")
    roots = configured_workspace_paths(repo_root)
    payload = build_document_package(
        repo_root,
        stage=stage,
        collection=collection,
        data_domain=DOCUMENTS_DATA_DOMAIN,
        config_id=profile_id,
        raw_doc_ids=doc_ids,
        select_all=select_all,
        missing_summary_only=missing_summary_only,
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
            "stage": stage,
            "profile_id": profile_id,
            "dry_run": dry_run,
            "output_written": bool(payload.get("output_written")),
            "exported": int(payload.get("counts", {}).get("exported") or 0),
            **(
                {
                    "collection": collection,
                    "doc_ids": list(payload.get("selected_doc_ids") or []),
                }
                if collection
                else {}
            ),
        },
    )
    return payload


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
        "review_package_id": package_id,
        "review_url": f"/docs-review/?package={package_id}" if package_id else "",
        "review_existing": existing,
        "summary_text": summary_text,
    })
    return response


def review_returned(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    stage = require_package_stage(body.get("stage"))
    staged_filename = str(body.get("staged_filename") or "").strip()
    if "collection" in body:
        raise ValueError(
            "returned-package review derives collection from trusted export metadata"
        )
    if "review_action" in body:
        raise ValueError("review_action is not supported; returned-package review always prepares full content")
    dry_run = dry_run_value(body)
    roots = configured_workspace_paths(repo_root)
    payload = content_review_response(
        create_review_source_folder(
            repo_root,
            stage=stage,
            staged_filename=staged_filename,
            dry_run=dry_run,
            staging_root=roots.import_staging,
            metadata_root=roots.meta,
            preview_root=roots.import_preview,
            normalize_import_content=normalize_documents_import_content,
        )
    )
    log_event(
        repo_root,
        "document-package-review",
        {
            "stage": stage,
            "staged_filename": staged_filename,
            "dry_run": dry_run,
            "ok": bool(payload.get("ok")),
        },
    )
    return payload
def post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
) -> tuple[HTTPStatus, dict[str, Any]]:
    require_direct_request(body)
    require_package_stage(body.get("stage"))
    if path == routes.PREPARE_PATH:
        payload = prepare_package(repo_root, body)
    elif path == routes.RETURNED_REVIEW_PATH:
        payload = review_returned(repo_root, body)
    else:
        raise FileNotFoundError("Not found")
    return (
        HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST,
        payload,
    )


__all__ = ["config_payload", "get_payload", "post_response"]
