#!/usr/bin/env python3
"""Docs Viewer service config and capability tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from docs_viewer_service_test_support import REPO_ROOT, docs_viewer_service, write_json


def test_service_startup_materializes_configured_media_directories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Path] = []
    closed: list[bool] = []
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    class FakeServer:
        server_address = ("127.0.0.1", 8776)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(docs_viewer_service, "load_service_config", lambda *_args, **_kwargs: config)
    monkeypatch.setattr(
        docs_viewer_service.media_storage,
        "ensure_configured_scope_owned_media_directories",
        lambda repo_root: calls.append(repo_root),
    )
    monkeypatch.setattr(docs_viewer_service, "DocsViewerServer", lambda *_args, **_kwargs: FakeServer())

    exit_code = docs_viewer_service.main([])

    assert exit_code == 0
    assert calls == [REPO_ROOT]
    assert closed == [True]


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
                    "review_enabled_default": False,
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
                    'export DOCS_VIEWER_REVIEW_ENABLED="1"',
                    'export DOCS_VIEWER_GENERATED_READS_ENABLED="0"',
                    'export DOCS_VIEWER_WATCH_ENABLED="0"',
                    'export SITE_PREVIEW_BASE="http://127.0.0.1:4011"',
                    'export STUDIO_APP_HOST="localhost"',
                    'export STUDIO_APP_PORT="8877"',
                ]
            ),
            encoding="utf-8",
        )

        config = docs_viewer_service.load_service_config(repo_root, environ={})

    assert config.host == "127.0.0.1"
    assert config.port == 8899
    assert config.base_url == "http://127.0.0.1:8899"
    assert config.management_enabled is True
    assert config.review_enabled is True
    assert config.generated_reads_enabled is False
    assert config.watch_enabled is False
    assert config.public_preview_base == "http://127.0.0.1:4011"
    assert config.studio_base_url == "http://localhost:8877"

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
        public_preview_base="http://127.0.0.1:4011",
        studio_base_url="http://localhost:8877",
    )

    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    manage_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-manage")

    assert manage_route["viewer_base_url"] == "/docs/"
    assert manage_route["app_kind"] == "manage"
    assert manage_route["include_scope_param"] is True
    assert "management" in manage_route["features"]
    assert "source-editing" in manage_route["features"]
    assert manage_route["access"]["allow_scope_query"] is True
    assert manage_route["access"]["management_ui"] is True
    assert manage_route["services"]["generated_data"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["services"]["source"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["services"]["management"]["base_url"] == "http://127.0.0.1:8776"
    assert manage_route["sites"]["public_preview"]["base"] == "http://127.0.0.1:4011"
    assert manage_route["sites"]["studio"]["base"] == "http://localhost:8877"


def test_load_service_config_rejects_invalid_public_preview_base() -> None:
    with pytest.raises(ValueError, match="SITE_PREVIEW_BASE"):
        docs_viewer_service.load_service_config(
            REPO_ROOT,
            environ={
                "DOCS_VIEWER_HOST": "127.0.0.1",
                "DOCS_VIEWER_PORT": "8776",
                "DOCS_VIEWER_BASE_URL": "http://127.0.0.1:8776",
                "SITE_PREVIEW_BASE": "javascript:alert(1)",
            },
        )


def test_load_service_config_defaults_public_preview_to_site_binding() -> None:
    config = docs_viewer_service.load_service_config(
        REPO_ROOT,
        environ={
            "DOCS_VIEWER_HOST": "127.0.0.1",
            "DOCS_VIEWER_PORT": "8776",
            "DOCS_VIEWER_BASE_URL": "http://127.0.0.1:8776",
            "SITE_HOST": "localhost",
            "SITE_PORT": "4444",
        },
    )

    assert config.public_preview_base == "http://localhost:4444"
    assert config.studio_base_url == "http://127.0.0.1:8765"


@pytest.mark.parametrize(
    ("host", "port", "message"),
    [
        ("example.com", "8765", "Studio base URL"),
        ("127.0.0.1", "70000", "STUDIO_APP_PORT"),
    ],
)
def test_load_service_config_rejects_invalid_studio_binding(
    host: str,
    port: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        docs_viewer_service.load_service_config(
            REPO_ROOT,
            environ={
                "DOCS_VIEWER_HOST": "127.0.0.1",
                "DOCS_VIEWER_PORT": "8776",
                "DOCS_VIEWER_BASE_URL": "http://127.0.0.1:8776",
                "STUDIO_APP_HOST": host,
                "STUDIO_APP_PORT": port,
            },
        )


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


def test_review_route_config_exposes_generated_reads_without_source_services() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=False,
        watch_enabled=True,
        review_enabled=True,
    )

    route_registry = docs_viewer_service.render_route_config_registry(REPO_ROOT, config)
    review_route = next(route for route in route_registry["routes"] if route["route_id"] == "docs-review")

    assert review_route["app_kind"] == "review"
    assert review_route["viewer_base_url"] == "/docs-review/"
    assert review_route["preserve_query_params"] == ["package"]
    assert review_route["features"] == []
    assert review_route["access"]["management_ui"] is False
    assert review_route["services"]["generated_data"]["base_url"] == "http://127.0.0.1:8776"
    assert review_route["services"]["source"]["base_url"] == ""
    assert review_route["services"]["management"]["base_url"] == ""

def test_apply_capability_flags_respects_local_service_flags() -> None:
    payload = {
        "ok": True,
        "capabilities": {
            "docs_management": True,
            "generated_data_reads": True,
            "source_config_settings_writes": True,
            "html_import": True,
            "docs_export": True,
            "document_packages": {
                "available": True,
                "prepare": True,
                "context": True,
                "review_returned": True,
                "atomic_return": True,
            },
            "document_delete": {
                "preview": True,
                "apply": True,
                "sub_scope_detail": True,
            },
            "scope_lifecycle": {
                "create_apply": True,
                "rename_apply": True,
                "delete_apply": True,
                "sub_scope_create_apply": True,
                "sub_scope_delete_apply": True,
            },
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
    assert capabilities["document_packages"] == {
        "available": True,
        "prepare": False,
        "context": False,
        "review_returned": False,
        "atomic_return": True,
    }
    assert capabilities["document_delete"] == {
        "preview": False,
        "apply": False,
        "sub_scope_detail": False,
    }
    assert capabilities["scope_lifecycle"]["create_apply"] is False
    assert capabilities["scope_lifecycle"]["rename_apply"] is False
    assert capabilities["scope_lifecycle"]["sub_scope_create_apply"] is False
    assert capabilities["scope_lifecycle"]["sub_scope_delete_apply"] is False
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


def test_external_sub_scope_payload_route_dispatches_as_generated_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    handler.path = "/docs/generated/external/private/projects/manage-manifest.json"
    called: list[str] = []
    monkeypatch.setattr(handler, "send_external_sub_scope_payload", called.append)

    handler.do_GET()

    assert called == [handler.path]


def test_published_media_route_respects_generated_read_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
                generated_reads_enabled=False,
                watch_enabled=True,
            ),
        },
    )()
    handler.path = "/docs/published/media/studio/img/example.png"
    sent: dict[str, object] = {}
    published_calls: list[str] = []

    def fake_send_json(payload: object, status: object = docs_viewer_service.HTTPStatus.OK) -> None:
        sent["payload"] = payload
        sent["status"] = status

    monkeypatch.setattr(handler, "send_json", fake_send_json)
    monkeypatch.setattr(handler, "send_published_docs_media", published_calls.append)

    handler.do_GET()

    assert sent == {
        "payload": {"ok": False, "error": "Published reads are disabled"},
        "status": docs_viewer_service.HTTPStatus.FORBIDDEN,
    }
    assert published_calls == []
