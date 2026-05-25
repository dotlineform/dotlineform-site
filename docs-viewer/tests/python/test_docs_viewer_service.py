#!/usr/bin/env python3
"""Focused checks for the standalone Docs Viewer service shell."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICE_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICE_DIR))

import docs_viewer_service  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_service_config_reads_static_site_env() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        (repo_root / "_config.yml").write_text("title: fixture\n", encoding="utf-8")
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
        site_env = repo_root / "var/local/site.env"
        site_env.parent.mkdir(parents=True)
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


def test_manage_shell_uses_docs_viewer_service_api_base() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=True,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    rendered = docs_viewer_service.render_manage_page(REPO_ROOT, config, "test-version")

    assert "<title>Docs Viewer</title>" in rendered
    assert 'data-viewer-base-url="/docs/"' in rendered
    assert 'data-include-scope-param="true"' in rendered
    assert 'data-allow-management="true"' in rendered
    assert 'data-allow-scope-query="true"' in rendered
    assert 'data-generated-base-url="http://127.0.0.1:8776"' in rendered
    assert 'data-management-base-url="http://127.0.0.1:8776"' in rendered
    assert "/docs-viewer/runtime/js/docs-viewer.js?v=test-version" in rendered
    assert "/docs-viewer/static/css/docs-viewer-management.css?v=test-version" in rendered
    assert "/studio/api/docs" not in rendered
    assert "/studio/app/assets/css/studio.css" not in rendered
    assert "{%" not in rendered
    assert "{{" not in rendered


def test_manage_shell_can_disable_management_markup_by_capability_flag() -> None:
    config = docs_viewer_service.DocsViewerServiceConfig(
        host="127.0.0.1",
        port=8776,
        base_url="http://127.0.0.1:8776",
        management_enabled=False,
        generated_reads_enabled=True,
        watch_enabled=True,
    )

    rendered = docs_viewer_service.render_manage_page(REPO_ROOT, config, "test-version")

    assert 'data-allow-management="false"' in rendered
    assert 'data-management-base-url=""' in rendered
    assert "docs-viewer-management.css" not in rendered
    assert "docsViewerManageActionsButton" not in rendered


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


def test_static_path_policy_is_docs_viewer_scoped() -> None:
    def allowed(path: str) -> bool:
        return docs_viewer_service.DocsViewerRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/docs-viewer/runtime/js/docs-viewer.js") is True
    assert allowed("/docs-viewer/static/css/docs-viewer.css") is True
    assert allowed("/docs-viewer/config/defaults/docs-viewer-config.json") is True
    assert allowed("/docs-viewer/generated/docs/studio/index.json") is True
    assert allowed("/assets/docs/library/img/example.png") is True
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/studio/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/source/studio/docs-viewer.md") is False


def test_public_browser_config_projects_public_readonly_scope_routes() -> None:
    source_payload = json.loads((REPO_ROOT / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
    public_payload = json.loads((REPO_ROOT / "docs-viewer/config/defaults/docs-viewer-public-config.json").read_text(encoding="utf-8"))

    public_source_scopes = [
        scope
        for scope in source_payload["scopes"]
        if scope.get("include_scope_param") is False and scope.get("viewer_base_url") != "/docs/"
    ]
    public_scope_ids = [scope["scope_id"] for scope in public_source_scopes]

    assert public_payload["schema_version"] == "docs_viewer_config_v1"
    assert public_payload["default_scope_id"] == public_scope_ids[0]
    assert [scope["scope_id"] for scope in public_payload["scopes"]] == public_scope_ids
    assert [scope["viewer_base_url"] for scope in public_payload["scopes"]] == [
        scope["viewer_base_url"] for scope in public_source_scopes
    ]
    assert "studio" not in public_payload["docs_viewer"]["ui_statuses_by_scope"]
