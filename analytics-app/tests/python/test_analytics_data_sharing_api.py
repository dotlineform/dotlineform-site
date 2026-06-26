#!/usr/bin/env python3
"""Focused checks for Analytics-owned Data Sharing API dispatch."""

from __future__ import annotations

from http import HTTPStatus
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "analytics-app" / "tests" / "fixtures"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (FIXTURES_DIR, REPO_ROOT, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

import analytics_data_sharing_api  # noqa: E402
from analytics_app_config import runtime_config  # noqa: E402
from data_sharing_factory import make_documents_data_sharing_repo as make_repo  # noqa: E402


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
        "context": "/analytics/api/data-sharing/context",
        "review": "/analytics/api/data-sharing/review",
        "apply": "/analytics/api/data-sharing/apply",
    }


def test_health_payload_identifies_analytics_data_sharing_service() -> None:
    payload = analytics_data_sharing_api.data_sharing_get_payload(REPO_ROOT, "/health", {})

    assert payload["ok"] is True
    assert payload["service"] == "analytics_data_sharing"
    assert payload["endpoints"]["prepare"] == "/analytics/api/data-sharing/prepare"
    assert payload["endpoints"]["context"] == "/analytics/api/data-sharing/context"
    assert payload["endpoints"]["config"] == "/analytics/api/data-sharing/config"


def test_config_payload_publishes_public_workflow_metadata_without_static_paths() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        payload = analytics_data_sharing_api.data_sharing_get_payload(root, "/config", {})

    assert payload["ok"] is True
    assert payload["schema_version"] == "data_sharing_adapters_v2"
    adapter = payload["adapters"][0]
    assert adapter["id"] == "documents"
    assert payload["docs_scopes"] == [
        {
            "id": "library",
            "label": "Library",
            "source": "docs-viewer/source/library",
        }
    ]
    assert adapter["data_domains"]["documents"] == {
        "app": "docs-viewer",
        "label": "Documents",
        "status": "active",
        "selection_model": "documents",
        "record_selectors": {
            "docs_scope": {
                "source": "docs_scope_config",
                "required": True,
            },
        },
    }
    prepare = next(item for item in adapter["capabilities"] if item["operation"] == "prepare")
    profile = prepare["sharing_profiles"][0]
    assert profile["id"] == "library-smoke"
    assert profile["label"] == "Library smoke"
    assert profile["data_domains"] == ["documents"]
    assert profile["target"] == {"format": "json", "supported_formats": ["json"]}
    assert profile["selection"] == {
        "mode": "explicit_doc_ids",
        "include_descendants": True,
        "supports_missing_summary_only": True,
        "default_missing_summary_only": False,
    }
    assert profile["external_context"] == {
        "task": "review_documents",
        "response_guidance": "Return proposed changes keyed by doc_id.",
        "field_descriptions": {
            "doc_id": "Stable document identifier.",
        },
    }
    assert profile["document_fields"] == [{"source": "doc_id", "output_path": "doc_id"}]
    assert "output" not in profile
    assert "metadata" not in profile
    assert "path_pattern" not in json.dumps(profile)
    assert "include_non_viewable" not in json.dumps(profile)
    assert "paths" not in adapter["data_domains"]["documents"]
    assert "path_contract" not in prepare
    apply = next(item for item in adapter["capabilities"] if item["operation"] == "apply")
    action = apply["apply_actions"][0]
    assert action["id"] == "summary_apply"
    assert action["label"] == "Update summaries"
    assert "activity" not in action


def test_selectable_records_returns_documents_without_docs_viewer_http() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        payload = analytics_data_sharing_api.data_sharing_get_payload(
            root,
            "/selectable-records",
            {"data_domain": ["documents"], "docs_scope": ["library"]},
        )

    assert payload["ok"] is True
    assert payload["adapter_id"] == "documents"
    assert payload["selection_model"] == "documents"
    assert payload["source"] == {
        "kind": "adapter",
        "module": "documents",
        "source": "docs_source_metadata",
        "scope": "library",
    }
    records_by_id = {record["id"]: record for record in payload["records"]}
    assert records_by_id["library"]["selectable"] is True
    assert records_by_id["library"]["summary"] == "Library root."
    assert records_by_id["hidden-doc"]["selectable"] is False


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
        {"data_domain": "documents", "config_id": "document-summaries"},
        dry_run=True,
    )

    assert status == HTTPStatus.OK
    assert payload == {"ok": True, "adapter_id": "documents", "operation": "prepare"}
    assert calls[0]["dry_run"] is True


def test_context_endpoint_updates_documents_prepare_profile_context() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        status, payload = analytics_data_sharing_api.data_sharing_post_response(
            root,
            "/context",
            {
                "data_domain": "documents",
                "config_id": "library-smoke",
                "external_context": {
                    "task": "suggest_updates",
                    "response_guidance": "Return changed fields keyed by doc_id.",
                    "field_descriptions": {
                        "doc_id": "Document id to preserve exactly.",
                    },
                },
            },
            dry_run=False,
        )
        profile_payload = json.loads(
            (root / "data-sharing/adapters/documents/config/prepare-profiles.json").read_text(encoding="utf-8")
        )

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["external_context"]["task"] == "suggest_updates"
    assert profile_payload["configs"][0]["external_context"] == {
        "task": "suggest_updates",
        "response_guidance": "Return changed fields keyed by doc_id.",
        "field_descriptions": {
            "doc_id": "Document id to preserve exactly.",
        },
    }


def test_context_endpoint_rejects_stale_field_descriptions() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        with pytest.raises(ValueError, match="unknown field"):
            analytics_data_sharing_api.data_sharing_post_response(
                root,
                "/context",
                {
                    "data_domain": "documents",
                    "config_id": "library-smoke",
                    "external_context": {
                        "task": "suggest_updates",
                        "response_guidance": "Return changed fields keyed by doc_id.",
                        "field_descriptions": {
                            "doc_id": "Document id.",
                            "stale": "No longer exported.",
                        },
                    },
                },
            )


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
            {"data_domain": ["documents"]},
    )

    assert payload == {"ok": True, "adapter_id": "documents", "operation": "list_returned", "files": []}
    assert calls[0]["data_domain"] == "documents"


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
        {"data_domain": "documents", "staged_filename": "summaries.jsonl"},
        dry_run=True,
    )
    apply_status, apply_payload = analytics_data_sharing_api.data_sharing_post_response(
        REPO_ROOT,
        "/apply",
        {"data_domain": "documents", "operation": "apply", "apply_action": "summary_apply", "staged_filename": "summaries.jsonl"},
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
