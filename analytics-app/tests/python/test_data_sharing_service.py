#!/usr/bin/env python3
"""Focused checks for the Studio Data Sharing service gateway."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (SCRIPTS_DIR, ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

import data_sharing_adapters  # noqa: E402
import data_sharing_routes  # noqa: E402
import data_sharing_service  # noqa: E402
from data_sharing.services.dispatch import DataSharingAdapterHandlers  # noqa: E402
from data_sharing.workflows.prepare import prepare_package as data_sharing_prepare_package  # noqa: E402


def test_neutral_data_sharing_routes_use_data_sharing_namespace() -> None:
    assert data_sharing_routes.PREPARE_PATH == "/data-sharing/prepare"
    assert data_sharing_routes.RETURNED_PACKAGES_PATH == "/data-sharing/returned-packages"
    assert data_sharing_routes.REVIEW_PATH == "/data-sharing/review"
    assert data_sharing_routes.APPLY_PATH == "/data-sharing/apply"
    assert all("/docs/" not in path for path in (*data_sharing_routes.GET_PATHS, *data_sharing_routes.POST_PATHS))


def test_gateway_dispatches_active_documents_adapter() -> None:
    calls: list[dict[str, object]] = []

    def fake_prepare(repo_root, body, dry_run, adapter):
        calls.append({"repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation}

    handlers = {
        "documents": data_sharing_service.DataSharingAdapterHandlers(
            module="documents",
            prepare=fake_prepare,
        )
    }

    payload = data_sharing_service.prepare_package(
        REPO_ROOT,
        {"data_domain": "library", "config_id": "library-document-summaries"},
        True,
        handlers,
    )

    assert payload == {"ok": True, "adapter_id": "documents", "operation": "prepare"}
    assert calls[0]["adapter_id"] == "documents"
    assert calls[0]["dry_run"] is True


def test_headless_prepare_workflow_uses_injected_resolver_and_handlers() -> None:
    calls: list[dict[str, object]] = []

    def fake_resolver(repo_root, data_domain, operation):
        calls.append({"repo_root": repo_root, "data_domain": data_domain, "operation": operation, "kind": "resolve"})
        return SimpleNamespace(
            adapter={"module": "documents"},
            adapter_id="documents",
            operation=operation,
        )

    def fake_prepare(repo_root, body, dry_run, adapter):
        calls.append({"repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id, "kind": "prepare"})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation}

    payload = data_sharing_prepare_package(
        REPO_ROOT,
        {"data_domain": "library", "config_id": "library-document-summaries"},
        True,
        {"documents": DataSharingAdapterHandlers(module="documents", prepare=fake_prepare)},
        fake_resolver,
    )

    assert payload == {"ok": True, "adapter_id": "documents", "operation": "prepare"}
    assert calls[0]["kind"] == "resolve"
    assert calls[0]["data_domain"] == "library"
    assert calls[0]["operation"] == "prepare"
    assert calls[1]["kind"] == "prepare"
    assert calls[1]["dry_run"] is True


def test_gateway_fails_active_adapter_without_registered_handler() -> None:
    try:
        data_sharing_service.review_returned_package(
            REPO_ROOT,
            {"data_domain": "tags", "operation": "review", "staged_filename": "tags.json"},
            True,
            {},
        )
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected ValueError")

    assert "adapter 'analytics-tags' module 'analytics.tags' has no registered Data Sharing service" in message


def test_gateway_fails_active_unregistered_adapter_module() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        registry_path = repo_root / data_sharing_adapters.REGISTRY_REL_PATH
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "data_sharing_adapters_v2",
                    "dispatch": [
                        {"data_domain": "library", "operation": "prepare", "adapter_id": "documents"},
                    ],
                    "adapters": [
                        {
                            "id": "documents",
                            "module": "documents.future",
                            "label": "Documents",
                            "status": "active",
                            "portability": {"package": "documents-package"},
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
                                    },
                                    "source_write_targets": {},
                                    "sources": {},
                                    "config": {},
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
                                    "activity": {
                                        "script_purpose": "data-sharing-prepare",
                                        "record_groups": ["documents"],
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        try:
            data_sharing_service.prepare_package(repo_root, {"data_domain": "library"}, True, {})
        except ValueError as error:
            message = str(error)
        else:
            raise AssertionError("expected ValueError")

    assert "module 'documents.future' has no registered Data Sharing service" in message


def main() -> None:
    test_neutral_data_sharing_routes_use_data_sharing_namespace()
    test_gateway_dispatches_active_documents_adapter()
    test_gateway_fails_active_adapter_without_registered_handler()
    test_gateway_fails_active_unregistered_adapter_module()


if __name__ == "__main__":
    main()
