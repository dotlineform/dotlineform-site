#!/usr/bin/env python3
"""Docs Viewer service config and capability tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from docs_viewer_service_test_support import REPO_ROOT, docs_viewer_service, write_json

def test_load_service_config_reads_env_local() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        write_json(
            repo_root / "site-tools/config/site-tools.json",
            {"schema_version": "site_tools_config_v1"},
        )
        write_json(
            repo_root / "docs-viewer/config/defaults/docs-viewer-service.json",
            {
                "capabilities": {
                    "management_enabled_default": False,
                    "generated_reads_enabled_default": True,
                    "watch_enabled_default": True,
                },
            },
        )
        site_env = repo_root / ".env.local"
        site_env.write_text(
            "\n".join(
                [
                    'export DOCS_VIEWER_HOST="127.0.0.1"',
                    'export DOCS_VIEWER_PORT="8899"',
                    'export DOCS_VIEWER_BASE_URL="http://127.0.0.1:8899"',
                    'export DOCS_VIEWER_MANAGEMENT_ENABLED="1"',
                    'export DOCS_VIEWER_GENERATED_READS_ENABLED="0"',
                    'export DOCS_VIEWER_WATCH_ENABLED="0"',
                ]
            ),
            encoding="utf-8",
        )

        config = docs_viewer_service.load_service_config(repo_root, environ={})

    assert config.host == "127.0.0.1"
    assert config.port == 8899
    assert config.base_url == "http://127.0.0.1:8899"
    assert config.management_enabled is True
    assert config.generated_reads_enabled is False
    assert config.watch_enabled is False

@pytest.mark.parametrize(
    ("host", "base_url", "message"),
    [
        ("0.0.0.0", "http://0.0.0.0:8776", "loopback"),
        ("127.0.0.1", "http://127.0.0.1:8777", "DOCS_VIEWER_PORT"),
        ("127.0.0.1", "https://127.0.0.1:8776", "http loopback"),
    ],
)
def test_load_service_config_rejects_non_local_or_mismatched_service_location(
    host: str,
    base_url: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        docs_viewer_service.load_service_config(
            REPO_ROOT,
            environ={
                "DOCS_VIEWER_HOST": host,
                "DOCS_VIEWER_PORT": "8776",
                "DOCS_VIEWER_BASE_URL": base_url,
            },
        )

def test_management_service_api_base_lives_in_route_config() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    manage_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-manage")

    assert manage_route["viewer_base_url"] == "/docs/"
    assert manage_route["app_kind"] == "manage"
    assert manage_route["include_scope_param"] is True
    assert manage_route["access"]["allow_scope_query"] is True
    assert manage_route["access"]["management_ui"] is True
    assert manage_route["services"]["generated_data"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["services"]["source"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["services"]["management"]["base_url"] == "http://127.0.0.1:8776"

def test_manage_route_config_separates_generated_reads_from_management_services() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    manage_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-manage")

    assert manage_route["viewer_base_url"] == "/docs/"
    assert manage_route["app_kind"] == "manage"
    assert manage_route["access"]["management_ui"] is False
    assert manage_route["services"]["generated_data"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["services"]["source"]["base_url"] == ""
    assert manage_route["services"]["management"]["base_url"] == ""

def test_apply_capability_flags_respects_local_service_flags() -> None:
    payload = {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_settings_writes": True,
            "html_import": True,
            "docs_export": True,
            "library_import": True,
            "scope_lifecycle": {"create_apply": True, "delete_apply": True},
            "scopes": {
                "studio": {
                    "generated_data_reads": True,
                    "generated_search_reads": True,
                },
            },
        },
    }
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=False,
        watch_enabled=True,
    )

    result = docs_viewer_service.apply_capability_flags(payload, config)
    capabilities = result["capabilities"]

    assert capabilities["docs_management"] is False
    assert capabilities["generated_data_reads"] is False
    assert capabilities["source_config_settings_writes"] is False
    assert capabilities["html_import"] is False
    assert capabilities["scope_lifecycle"]["create_apply"] is False
    assert capabilities["scopes"]["studio"]["generated_data_reads"] is False
    assert capabilities["scopes"]["studio"]["generated_search_reads"] is False

def test_capabilities_endpoint_returns_json_error_for_source_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = object.__new__(docs_viewer_service.DocsViewerRequestHandler)
    handler.server = type(
        "Server",
        (),
        {
            "repo_root": REPO_ROOT,
            "docs_viewer_config": docs_viewer_service.DocsViewerServiceConfig(
                host="127.0.0.1",
                port=8776,
                base_url="http://127.0.0.1:8776",
                management_enabled=True,
                generated_reads_enabled=True,
                watch_enabled=True,
            ),
        },
    )()
    sent: dict[str, object] = {}

    def fake_send_json(payload: object, status: object = docs_viewer_service.HTTPStatus.OK) -> None:
        sent["payload"] = payload
        sent["status"] = status

    def fail_capabilities(_repo_root: Path) -> dict[str, object]:
        raise ValueError("Unknown parent_id 'missing-parent' for doc 'broken-parent-doc'")

    monkeypatch.setattr(handler, "send_json", fake_send_json)
    monkeypatch.setattr(docs_viewer_service.docs_service, "capabilities_payload", fail_capabilities)

    handler.send_capabilities_json()

    assert sent["status"] == docs_viewer_service.HTTPStatus.BAD_REQUEST
    assert sent["payload"] == {
        "ok": False,
        "error": "Unknown parent_id 'missing-parent' for doc 'broken-parent-doc'",
    }
