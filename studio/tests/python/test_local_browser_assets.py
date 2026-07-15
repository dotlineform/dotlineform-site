"""Shared local browser icon contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from studio.shared.python.local_browser_assets import (
    LOCAL_BROWSER_ASSET_PATHS,
    LOCAL_BROWSER_ICON_LINKS_TOKEN,
    render_local_browser_icon_links,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_SHELLS = (
    "admin-app/app/frontend/admin-shell.html",
    "analytics-app/app/frontend/analytics-shell.html",
    "studio/app/frontend/studio-shell.html",
    "docs-viewer/shell/docs-viewer-manage.html",
    "docs-viewer/shell/docs-viewer-review.html",
)


def test_local_browser_asset_paths_include_apple_discovery_variants() -> None:
    assert "/apple-touch-icon.png" in LOCAL_BROWSER_ASSET_PATHS
    assert "/apple-touch-icon-precomposed.png" in LOCAL_BROWSER_ASSET_PATHS


def test_local_browser_asset_paths_resolve_to_repo_root_files() -> None:
    missing = [
        path
        for path in LOCAL_BROWSER_ASSET_PATHS
        if not (REPO_ROOT / path.lstrip("/")).is_file()
    ]

    assert missing == []


@pytest.mark.parametrize("relative_path", LOCAL_SHELLS)
def test_local_shell_uses_shared_browser_icon_declarations(relative_path: str) -> None:
    source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    rendered = render_local_browser_icon_links(source)

    assert LOCAL_BROWSER_ICON_LINKS_TOKEN not in rendered
    assert 'rel="icon" href="/favicon.ico"' in rendered
    assert 'rel="apple-touch-icon"' in rendered
    assert 'href="/site.webmanifest"' in rendered
    assert 'rel="mask-icon"' in rendered


def test_local_shell_requires_exactly_one_browser_icon_token() -> None:
    with pytest.raises(ValueError, match="exactly once; found 0"):
        render_local_browser_icon_links("<head></head>")
