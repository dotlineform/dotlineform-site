#!/usr/bin/env python3
"""Docs Viewer static asset route tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from docs_viewer_service_test_support import REPO_ROOT, docs_viewer_service

def test_asset_version_uses_canonical_site_css() -> None:
    for filename in (
        "docs-viewer.css",
        "docs-viewer-reports.css",
        "docs-viewer-moments.css",
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            shared_css = repo_root / "site/docs-viewer/static/css" / filename
            shared_css.parent.mkdir(parents=True)
            shared_css.write_text("/* shared css */\n", encoding="utf-8")

            assert docs_viewer_service.asset_version(repo_root) != "1"


def test_manage_shell_loads_feature_owned_css_after_shared_management_css() -> None:
    shell = (REPO_ROOT / "docs-viewer/shell/docs-viewer-manage.html").read_text(encoding="utf-8")
    stylesheets = [
        "docs-viewer-manage.css",
        "docs-viewer-source-editor.css",
        "docs-viewer-import.css",
    ]

    assert [shell.index(stylesheet) for stylesheet in stylesheets] == sorted(
        shell.index(stylesheet) for stylesheet in stylesheets
    )


def test_document_package_browser_assets_are_docs_viewer_owned() -> None:
    returned_shell = (
        REPO_ROOT / "docs-viewer/shell/docs-viewer-package-returned.html"
    ).read_text(encoding="utf-8")
    management_runtime = "\n".join(
        (
            REPO_ROOT / "docs-viewer/runtime/js/management" / filename
        ).read_text(encoding="utf-8")
        for filename in (
            "docs-viewer-management-actions-renderer.js",
            "docs-viewer-management.js",
        )
    )
    runtime_root = REPO_ROOT / "docs-viewer/runtime/js/packages"
    runtime = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(runtime_root.glob("*.js"))
    )

    assert "docs-viewer-packages.css" in returned_shell
    assert "document-package-returned.js" in returned_shell
    assert not (REPO_ROOT / "docs-viewer/shell/docs-viewer-package-prepare.html").exists()
    assert not (runtime_root / "document-package-prepare.js").exists()
    assert "/docs/packages/prepare/" not in returned_shell
    assert "docsViewerManagePreparePackageButton" in management_runtime
    assert 'page_id: "docs-manage"' in management_runtime
    assert "data-domain" not in returned_shell.lower()
    assert "record_indices" not in runtime
    assert "/analytics/" not in runtime
    assert "data-sharing" not in runtime.lower()
    assert 'page_id: "docs-package-returned"' in runtime
    assert 'actionId: "apply-returned-summaries"' in runtime
    assert 'actionId: "apply-returned-hierarchy"' in runtime
    assert 'type="checkbox"' not in returned_shell
    assert 'id="documentPackageReturnedScope"' not in returned_shell
    assert 'data-package-scope-link="/docs/' in returned_shell
    assert "syncPackageScopeLinks" in runtime
    assert "unassigned_files" in runtime


def test_moments_css_is_loaded_by_public_and_manage_shells() -> None:
    public_shell = (REPO_ROOT / "site/moments/index.html").read_text(encoding="utf-8")
    manage_shell = (REPO_ROOT / "docs-viewer/shell/docs-viewer-manage.html").read_text(
        encoding="utf-8"
    )

    assert "docs-viewer-moments.css" in public_shell
    assert "docs-viewer-moments.css" in manage_shell


def test_static_path_policy_is_docs_viewer_scoped() -> None:
    def allowed(path: str) -> bool:
        return docs_viewer_service.DocsViewerRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/docs-viewer/runtime/js/public/docs-viewer-public.js") is True
    assert allowed("/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js") is True
    assert allowed("/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js") is True
    assert allowed("/docs-viewer/runtime/vendor/mermaid/11.16.0/LICENSE") is True
    assert allowed("/docs-viewer/runtime/js/management/docs-viewer-manage.js") is True
    assert allowed("/docs-viewer/runtime/js/import/docs-html-import.js") is True
    assert allowed("/docs-viewer/runtime/js/packages/document-package-client.js") is True
    assert allowed("/docs-viewer/runtime/js/reports/docs-viewer-reports.js") is True
    assert allowed("/docs-viewer/runtime/js/docs-viewer-public.js") is False
    assert allowed("/docs-viewer/runtime/js/docs-viewer-manage.js") is False
    assert allowed("/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/static/css/docs-viewer.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-reports.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-moments.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-manage.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-source-editor.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-import.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-review.css") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-packages.css") is True
    assert allowed("/apple-touch-icon-precomposed.png") is True
    assert allowed("/docs-viewer/static/css/docs-viewer-base.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-management.css") is False
    assert allowed("/docs-viewer/static/css/docs-viewer-public.css") is False
    assert allowed("/docs-viewer/config/defaults/docs-viewer-config.json") is True
    assert allowed("/docs-viewer/config/routes/docs-viewer-public-routes.json") is True
    assert allowed("/docs-viewer/config/reports/reports.json") is True
    assert allowed("/docs-viewer/scopes/studio/published/documents/index-tree.json") is True
    assert allowed("/docs-viewer/generated/docs/studio/index-tree.json") is False
    assert allowed("/assets/docs/library/img/example.png") is True
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/studio/docs-viewer/runtime/js/docs-viewer.js") is False
    assert allowed("/docs-viewer/scopes/studio/source/documents/docs-viewer.md") is False

def test_runtime_static_route_prefixes_resolve_to_owning_roots() -> None:
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js"
    ) == Path("docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/public/docs-viewer-public.js"
    ) == Path("site/docs-viewer/runtime/js/public/docs-viewer-public.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js"
    ) == Path("site/docs-viewer/runtime/js/shared/docs-viewer-app-boot.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/management/docs-viewer-manage.js"
    ) == Path("docs-viewer/runtime/js/management/docs-viewer-manage.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/import/docs-html-import.js"
    ) == Path("docs-viewer/runtime/js/import/docs-html-import.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/packages/document-package-client.js"
    ) == Path("docs-viewer/runtime/js/packages/document-package-client.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ) == Path("docs-viewer/runtime/js/reports/docs-viewer-reports.js")
    assert docs_viewer_service.runtime_static_relative_path(
        "/docs-viewer/runtime/js/docs-viewer-public.js"
    ) is None

def test_shared_static_routes_resolve_to_owning_roots() -> None:
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer.css"
    ) == Path("site/docs-viewer/static/css/docs-viewer.css")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-reports.css"
    ) == Path("site/docs-viewer/static/css/docs-viewer-reports.css")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-moments.css"
    ) == Path("site/docs-viewer/static/css/docs-viewer-moments.css")
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-manage.css"
    ) is None
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-source-editor.css"
    ) is None
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/static/css/docs-viewer-import.css"
    ) is None
    assert docs_viewer_service.shared_static_relative_path(
        "/docs-viewer/config/routes/docs-viewer-public-routes.json"
    ) == Path("site/docs-viewer/config/routes/docs-viewer-public-routes.json")
