#!/usr/bin/env python3
"""Focused checks for Studio-owned Data Sharing API dispatch."""

from __future__ import annotations

from http import HTTPStatus
import json
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio import studio_data_sharing_api  # noqa: E402
from studio.app.server.studio.studio_app_config import runtime_config  # noqa: E402


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
                                "outbound_package_root": "var/studio/data-sharing/library/exports",
                                "returned_package_staging_root": "var/studio/data-sharing/library/import-staging",
                                "review_output_root": "var/studio/data-sharing/library/import-preview",
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


def test_runtime_config_publishes_studio_owned_data_sharing_endpoints() -> None:
    payload = runtime_config(REPO_ROOT, "test-version")
    endpoints = payload["app"]["runtime"]["services"]["data_sharing"]

    assert endpoints == {
        "base": "/studio/api/data-sharing",
        "health": "/studio/api/data-sharing/health",
        "selectable_records": "/studio/api/data-sharing/selectable-records",
        "returned_packages": "/studio/api/data-sharing/returned-packages",
        "prepare": "/studio/api/data-sharing/prepare",
        "review": "/studio/api/data-sharing/review",
        "apply": "/studio/api/data-sharing/apply",
    }


def test_health_payload_identifies_studio_data_sharing_service() -> None:
    payload = studio_data_sharing_api.data_sharing_get_payload(REPO_ROOT, "/health", {})

    assert payload["ok"] is True
    assert payload["service"] == "studio_data_sharing"
    assert payload["endpoints"]["prepare"] == "/studio/api/data-sharing/prepare"


def test_selectable_records_returns_documents_without_docs_viewer_http() -> None:
    with make_repo() as temp_path:
        root = Path(temp_path)
        payload = studio_data_sharing_api.data_sharing_get_payload(
            root,
            "/selectable-records",
            {"data_domain": ["library"]},
        )

    assert payload["ok"] is True
    assert payload["adapter_id"] == "documents"
    assert payload["selection_model"] == "documents"
    assert payload["source"] == {"kind": "generated_docs_index", "scope": "library"}
    assert payload["records"][0]["id"] == "library"
    assert payload["records"][0]["selectable"] is True
    assert payload["records"][1]["id"] == "hidden-doc"
    assert payload["records"][1]["selectable"] is False


def test_prepare_endpoint_dispatches_through_registered_handlers(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_prepare(repo_root, body, dry_run, adapter):
        calls.append({"repo_root": repo_root, "body": body, "dry_run": dry_run, "adapter_id": adapter.adapter_id})
        return {"ok": True, "adapter_id": adapter.adapter_id, "operation": adapter.operation}

    handlers = {
        "documents": studio_data_sharing_api.data_sharing_service.DataSharingAdapterHandlers(
            module="documents",
            prepare=fake_prepare,
        )
    }
    monkeypatch.setattr(studio_data_sharing_api, "DATA_SHARING_HANDLERS", handlers)

    status, payload = studio_data_sharing_api.data_sharing_post_response(
        REPO_ROOT,
        "/prepare",
        {"data_domain": "library", "config_id": "library-document-summaries"},
        dry_run=True,
    )

    assert status == HTTPStatus.OK
    assert payload == {"ok": True, "adapter_id": "documents", "operation": "prepare"}
    assert calls[0]["dry_run"] is True


def test_unknown_endpoint_fails_closed() -> None:
    with pytest.raises(FileNotFoundError):
        studio_data_sharing_api.data_sharing_get_payload(REPO_ROOT, "/missing", {})
