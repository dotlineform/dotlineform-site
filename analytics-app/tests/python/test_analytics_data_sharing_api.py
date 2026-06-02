#!/usr/bin/env python3
"""Focused checks for Analytics-owned Data Sharing API dispatch."""

from __future__ import annotations

from http import HTTPStatus
import json
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (REPO_ROOT, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

import analytics_data_sharing_api  # noqa: E402
from analytics_app_config import runtime_config  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_docs_scope_config(root: Path) -> None:
    write_json(
        root / "docs-viewer/config/scopes/docs_scopes.json",
        {
            "schema_version": "docs_scopes_v1",
            "scopes": [
                {
                    "scope_id": "library",
                    "source": "docs-viewer/source/library",
                    "media_path_prefix": "docs/library",
                    "output": "assets/data/docs/scopes/library",
                    "search_output": "assets/data/search/library/index.json",
                    "viewer_base_url": "/library/",
                    "include_scope_param": False,
                    "default_doc_id": "library",
                    "allow_nested_source": False,
                    "non_loadable_doc_ids": [],
                    "manage_only_tree_root_ids": [],
                    "show_updated_date": True,
                    "allow_unresolved_parent_ids": False,
                }
            ],
            "docs_viewer": {
                "recently_added_limit": 10,
            },
        },
    )


def write_adapter_registry(root: Path) -> None:
    write_json(
        root / "data-sharing/config/adapters.json",
        {
            "schema_version": "data_sharing_adapters_v2",
            "dispatch": [
                {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "list_returned", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "review", "adapter_id": "documents"},
                {"data_domain": "library", "operation": "apply", "adapter_id": "documents"},
            ],
            "adapters": [
                {
                    "id": "documents",
                    "module": "documents",
                    "label": "Documents",
                    "status": "active",
                    "portability": {"package": "docs-viewer-documents-data-sharing"},
                    "data_domains": {
                        "library": {
                            "label": "Library",
                            "scope": "library",
                            "status": "active",
                            "selection_model": "documents",
                            "paths": {
                                "outbound_package_root": "var/analytics/data-sharing/library/exports",
                                "returned_package_staging_root": "var/analytics/data-sharing/library/import-staging",
                                "review_output_root": "var/analytics/data-sharing/library/import-preview",
                                "source_root": "docs-viewer/source/library",
                                "backup_root": "var/docs/backups",
                            },
                            "source_write_targets": {
                                "documents": "docs-viewer/source/library",
                            },
                            "sources": {
                                "docs_index": "assets/data/docs/scopes/library/index.json",
                                "docs_payload_root": "assets/data/docs/scopes/library/by-id",
                                "source_root": "docs-viewer/source/library",
                            },
                            "config": {
                                "sharing_profiles_path": "data-sharing/config/library-export-configs.json",
                            },
                        }
                    },
                    "capabilities": [
                        {
                            "operation": "prepare",
                            "status": "active",
                            "selection_model": "documents",
                            "input_formats": [],
                            "output_formats": ["json"],
                            "path_contract": {"output_root": "outbound_package_root"},
                            "activity": {"script_purpose": "data-sharing-prepare", "record_groups": ["documents"]},
                        },
                        {
                            "operation": "list_returned",
                            "status": "active",
                            "selection_model": "none",
                            "input_formats": ["json"],
                            "output_formats": [],
                            "path_contract": {"staging_root": "returned_package_staging_root"},
                            "activity": {"script_purpose": "data-sharing-list-returned", "record_groups": ["files"]},
                        },
                        {
                            "operation": "review",
                            "status": "active",
                            "selection_model": "file_only",
                            "input_formats": ["json"],
                            "output_formats": ["markdown"],
                            "path_contract": {"staging_root": "returned_package_staging_root"},
                            "review_rows": {"fields": ["id"]},
                            "activity": {"script_purpose": "data-sharing-review", "record_groups": ["documents"]},
                        },
                        {
                            "operation": "apply",
                            "status": "active",
                            "selection_model": "records",
                            "input_formats": ["json"],
                            "output_formats": [],
                            "path_contract": {"staging_root": "returned_package_staging_root"},
                            "requires_confirmation": True,
                            "apply_actions": [
                                {
                                    "id": "summary_apply",
                                    "label": "Update summaries",
                                    "status": "active",
                                    "confirmation": {"title": "Update?", "body": "Update selected rows."},
                                    "activity": {"script_purpose": "data-sharing-apply", "record_groups": ["documents"]},
                                }
                            ],
                        },
                    ],
                }
            ],
        },
    )


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    (root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
    write_docs_scope_config(root)
    write_adapter_registry(root)
    write_json(
        root / "data-sharing/config/library-export-configs.json",
        {
            "schema_version": "library_export_configs_v1",
            "configs": [
                {
                    "id": "library-smoke",
                    "label": "Library smoke",
                    "enabled": True,
                    "scopes": ["library"],
                    "target": {"format": "json", "supported_formats": ["json"]},
                    "selection": {"mode": "explicit_doc_ids"},
                }
            ],
        },
    )
    write_json(
        root / "assets/data/docs/scopes/library/index.json",
        {
            "docs": [
                {
                    "doc_id": "library",
                    "title": "Library",
                    "viewable": True,
                    "content_text_length": 100,
                    "summary": "Library root.",
                },
                {
                    "doc_id": "hidden-doc",
                    "title": "Hidden",
                    "viewable": False,
                    "hidden": True,
                },
            ]
        },
    )
    return temp_dir


def test_runtime_config_publishes_analytics_owned_data_sharing_endpoints() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    endpoints = payload["app"]["runtime"]["services"]["data_sharing"]

    assert endpoints == {
        "base": "/analytics/api/data-sharing",
        "health": "/analytics/api/data-sharing/health",
        "config": "/analytics/api/data-sharing/config",
        "selectable_records": "/analytics/api/data-sharing/selectable-records",
        "returned_packages": "/analytics/api/data-sharing/returned-packages",
        "prepare": "/analytics/api/data-sharing/prepare",
        "review": "/analytics/api/data-sharing/review",
        "apply": "/analytics/api/data-sharing/apply",
    }


def test_health_payload_identifies_analytics_data_sharing_service() -> None:
    payload = analytics_data_sharing_api.data_sharing_get_payload(REPO_ROOT, "/health", {})

    assert payload["ok"] is True
    assert payload["service"] == "analytics_data_sharing"
    assert payload["endpoints"]["prepare"] == "/analytics/api/data-sharing/prepare"
    assert payload["endpoints"]["config"] == "/analytics/api/data-sharing/config"


def test_config_payload_publishes_public_workflow_metadata_without_static_paths() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        payload = analytics_data_sharing_api.data_sharing_get_payload(root, "/config", {})

    assert payload["ok"] is True
    assert payload["schema_version"] == "data_sharing_adapters_v2"
    adapter = payload["adapters"][0]
    assert adapter["id"] == "documents"
    assert adapter["data_domains"]["library"] == {
        "label": "Library",
        "scope": "library",
        "status": "active",
        "selection_model": "documents",
    }
    prepare = next(item for item in adapter["capabilities"] if item["operation"] == "prepare")
    profile = prepare["sharing_profiles"][0]
    assert profile["id"] == "library-smoke"
    assert profile["label"] == "Library smoke"
    assert profile["target"] == {"format": "json", "supported_formats": ["json"]}
    assert profile["selection"] == {"mode": "explicit_doc_ids"}
    assert "output" not in profile
    assert "metadata" not in profile
    assert "document_fields" not in profile
    assert "paths" not in adapter["data_domains"]["library"]
    assert "path_contract" not in prepare


def test_selectable_records_returns_documents_without_docs_viewer_http() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        payload = analytics_data_sharing_api.data_sharing_get_payload(
            root,
            "/selectable-records",
            {"data_domain": ["library"]},
        )

    assert payload["ok"] is True
    assert payload["adapter_id"] == "documents"
    assert payload["selection_model"] == "documents"
    assert payload["source"] == {
        "kind": "adapter",
        "module": "documents",
        "source": "generated_docs_index",
        "scope": "library",
    }
    assert payload["records"][0]["id"] == "library"
    assert payload["records"][0]["selectable"] is True
    assert payload["records"][1]["id"] == "hidden-doc"
    assert payload["records"][1]["selectable"] is False


def test_analytics_data_sharing_api_avoids_docs_management_context_imports() -> None:
    source = (ANALYTICS_PACKAGE_DIR / "analytics_data_sharing_api.py").read_text(encoding="utf-8")

    assert "docs_management_context" not in source
    assert "docs_management_service" not in source
    assert "docs_management_routes" not in source


def test_prepare_endpoint_dispatches_through_registered_handlers(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_prepare(repo_root, body, dry_run, adapter):
        calls.append({"repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation}

    handlers = {
        "documents": analytics_data_sharing_api.data_sharing_service.DataSharingAdapterHandlers(
            module="documents",
            prepare=fake_prepare,
        )
    }
    monkeypatch.setattr(analytics_data_sharing_api, "DATA_SHARING_HANDLERS", handlers)

    status, payload = analytics_data_sharing_api.data_sharing_post_response(
        REPO_ROOT,
        "/prepare",
        {"data_domain": "library", "config_id": "library-document-summaries"},
        dry_run=True,
    )

    assert status == HTTPStatus.OK
    assert payload == {"ok": True, "adapter_id": "documents", "operation": "prepare"}
    assert calls[0]["dry_run"] is True


def test_returned_packages_endpoint_dispatches_through_registered_handlers(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_list_returned(repo_root, data_domain, adapter):
        calls.append({"repo_root": repo_root, "data_domain": data_domain, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation, "files": []}

    handlers = {
        "documents": analytics_data_sharing_api.data_sharing_service.DataSharingAdapterHandlers(
            module="documents",
            list_returned=fake_list_returned,
        )
    }
    monkeypatch.setattr(analytics_data_sharing_api, "DATA_SHARING_HANDLERS", handlers)

    payload = analytics_data_sharing_api.data_sharing_get_payload(
        REPO_ROOT,
        "/returned-packages",
        {"data_domain": ["library"]},
    )

    assert payload == {"ok": True, "adapter_id": "documents", "operation": "list_returned", "files": []}
    assert calls[0]["data_domain"] == "library"


def test_review_and_apply_endpoints_dispatch_through_registered_handlers(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_review(repo_root, body, dry_run, adapter):
        calls.append({"kind": "review", "repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation, "review_rows": []}

    def fake_apply(repo_root, body, dry_run, adapter):
        calls.append({"kind": "apply", "repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation, "applied_count": 0}

    handlers = {
        "documents": analytics_data_sharing_api.data_sharing_service.DataSharingAdapterHandlers(
            module="documents",
            review=fake_review,
            apply=fake_apply,
        )
    }
    monkeypatch.setattr(analytics_data_sharing_api, "DATA_SHARING_HANDLERS", handlers)

    review_status, review_payload = analytics_data_sharing_api.data_sharing_post_response(
        REPO_ROOT,
        "/review",
        {"data_domain": "library", "staged_filename": "summaries.jsonl"},
        dry_run=True,
    )
    apply_status, apply_payload = analytics_data_sharing_api.data_sharing_post_response(
        REPO_ROOT,
        "/apply",
        {"data_domain": "library", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl"},
        dry_run=True,
    )

    assert review_status == HTTPStatus.OK
    assert review_payload == {"ok": True, "adapter_id": "documents", "operation": "review", "review_rows": []}
    assert apply_status == HTTPStatus.OK
    assert apply_payload == {"ok": True, "adapter_id": "documents", "operation": "apply", "applied_count": 0}
    assert [(call["kind"], call["dry_run"]) for call in calls] == [("review", True), ("apply", True)]


def test_unknown_endpoint_fails_closed() -> None:
    with pytest.raises(FileNotFoundError):
        analytics_data_sharing_api.data_sharing_get_payload(REPO_ROOT, "/missing", {})
