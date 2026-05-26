#!/usr/bin/env python3
"""Studio-owned Data Sharing API dispatch."""

from __future__ import annotations

import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

import docs_activity  # noqa: E402
import docs_generated_reads  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
import documents_data_sharing_adapter  # noqa: E402
from analytics import tags_data_sharing_adapter  # noqa: E402
from docs_management_context import log_event, make_backup_bundle  # noqa: E402
from studio import data_sharing_adapters, data_sharing_service  # noqa: E402


API_BASE = "/studio/api/data-sharing"
HEALTH_PATH = "/health"
SELECTABLE_RECORDS_PATH = "/selectable-records"
RETURNED_PACKAGES_PATH = "/returned-packages"
PREPARE_PATH = "/prepare"
REVIEW_PATH = "/review"
APPLY_PATH = "/apply"


def documents_data_sharing_dependencies() -> documents_data_sharing_adapter.DocumentsDataSharingDependencies:
    return documents_data_sharing_adapter.DocumentsDataSharingDependencies(
        log_event=log_event,
        make_backup_bundle=make_backup_bundle,
        perform_source_write_and_rebuild=write_rebuild.perform_source_write_and_rebuild,
    )


def tags_data_sharing_dependencies() -> tags_data_sharing_adapter.TagsDataSharingDependencies:
    return tags_data_sharing_adapter.TagsDataSharingDependencies(log_event=log_event)


DATA_SHARING_HANDLERS = {
    "documents": documents_data_sharing_adapter.handlers_for(documents_data_sharing_dependencies),
    "analytics.tags": tags_data_sharing_adapter.handlers_for(tags_data_sharing_dependencies),
}


def service_endpoints() -> dict[str, str]:
    return {
        "base": API_BASE,
        "health": f"{API_BASE}{HEALTH_PATH}",
        "selectable_records": f"{API_BASE}{SELECTABLE_RECORDS_PATH}",
        "returned_packages": f"{API_BASE}{RETURNED_PACKAGES_PATH}",
        "prepare": f"{API_BASE}{PREPARE_PATH}",
        "review": f"{API_BASE}{REVIEW_PATH}",
        "apply": f"{API_BASE}{APPLY_PATH}",
    }


def query_value(params: dict[str, list[str]], key: str) -> str:
    return (params.get(key) or [""])[0]


def data_sharing_get_payload(
    repo_root: Path,
    api_path: str,
    query: dict[str, list[str]],
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    if api_path == HEALTH_PATH:
        return {
            "ok": True,
            "service": "studio_data_sharing",
            "dry_run": dry_run,
            "endpoints": service_endpoints(),
        }
    if api_path == SELECTABLE_RECORDS_PATH:
        return selectable_records_payload(repo_root, query_value(query, "data_domain"))
    if api_path == RETURNED_PACKAGES_PATH:
        return data_sharing_service.list_returned_packages(
            repo_root,
            query_value(query, "data_domain"),
            DATA_SHARING_HANDLERS,
        )
    raise FileNotFoundError("Not found")


def data_sharing_post_response(
    repo_root: Path,
    api_path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    if api_path == PREPARE_PATH:
        payload = data_sharing_service.prepare_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        docs_activity.maybe_attach_docs_export_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == REVIEW_PATH:
        payload = data_sharing_service.review_returned_package(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    if api_path == APPLY_PATH:
        payload = data_sharing_service.apply_returned_changes(repo_root, body, dry_run, DATA_SHARING_HANDLERS)
        docs_activity.maybe_attach_documents_import_apply_activity(repo_root, body, payload, dry_run)
        return HTTPStatus.OK if payload.get("ok") else HTTPStatus.BAD_REQUEST, payload
    raise FileNotFoundError("Not found")


def selectable_records_payload(repo_root: Path, data_domain: Any) -> dict[str, object]:
    adapter = data_sharing_adapters.resolve_adapter(repo_root, data_domain=data_domain, operation="prepare")
    selection_model = str(adapter.capability.get("selection_model") or adapter.domain.get("selection_model") or "").strip()
    records: list[dict[str, object]] = []
    source: dict[str, object] = {"kind": "adapter", "scope": adapter.scope}
    if selection_model == "documents":
        index_payload = docs_generated_reads.read_generated_docs_index(repo_root, adapter.scope)
        docs = index_payload.get("docs")
        if not isinstance(docs, list):
            raise RuntimeError(f"generated docs index for {adapter.scope} is missing docs")
        records = [document_selectable_record(item) for item in docs if isinstance(item, dict)]
        source = {"kind": "generated_docs_index", "scope": adapter.scope}

    return {
        "ok": True,
        "data_domain": adapter.data_domain,
        "adapter_id": adapter.adapter_id,
        "scope": adapter.scope,
        "selection_model": selection_model,
        "records": records,
        "docs": records,
        "source": source,
    }


def document_selectable_record(doc: dict[str, Any]) -> dict[str, object]:
    doc_id = str(doc.get("doc_id") or "").strip()
    title = str(doc.get("title") or doc_id).strip()
    viewable = bool(doc.get("viewable", True))
    hidden = bool(doc.get("hidden", False))
    selectable = bool(doc_id and viewable and not hidden)
    issues: list[dict[str, str]] = []
    if not viewable:
        issues.append({"level": "warning", "message": "Document is not viewable."})
    if hidden:
        issues.append({"level": "warning", "message": "Document is hidden."})
    return {
        "id": doc_id,
        "doc_id": doc_id,
        "title": title,
        "type": "document",
        "meta": doc_id,
        "parent_id": str(doc.get("parent_id") or "").strip(),
        "viewable": viewable,
        "hidden": hidden,
        "selectable": selectable,
        "children": [],
        "issues": issues,
        "content_text_length": int(doc.get("content_text_length") or 0),
        "summary": str(doc.get("summary") or ""),
    }
