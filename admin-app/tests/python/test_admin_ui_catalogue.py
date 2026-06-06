#!/usr/bin/env python3
"""Focused checks for the Admin-hosted UI Catalogue."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server" / "admin_app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from admin_app_server import AdminAppRequestHandler  # noqa: E402
from ui_catalogue_config import asset_version  # noqa: E402
from ui_catalogue_views import UI_CATALOGUE_DEMO_ROUTES, load_palette_items, ui_catalogue_demo_view, ui_catalogue_palette_view  # noqa: E402


def test_static_path_policy_serves_only_admin_ui_catalogue_assets() -> None:
    def allowed(path: str) -> bool:
        return AdminAppRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/admin/ui-catalogue/assets/css/ui-catalogue-demo.css") is True
    assert allowed("/admin/ui-catalogue/assets/css/ui-catalogue-shell.css") is True
    assert allowed("/admin/ui-catalogue/assets/js/ui-catalogue-demo.js") is True
    assert allowed("/admin/ui-catalogue/assets/js/ui-catalogue-shell.js") is True
    assert allowed("/admin/ui-catalogue/assets/img/panel-backgrounds/01007-primary-800.webp") is True
    assert allowed("/admin/ui-catalogue/assets/img/moments/blue-sky-thumb-96.webp") is True

    assert allowed("/studio/ui-catalogue/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/ui-catalogue/app/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/ui-catalogue/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/assets/ui-catalogue/js/ui-catalogue-demo.js") is False
    assert allowed("/assets/css/main.css") is False


def test_demo_routes_render_admin_hosted_shell() -> None:
    assert UI_CATALOGUE_DEMO_ROUTES["/admin/ui-catalogue/demos/"] == "ui_catalogue_demos"
    html = ui_catalogue_demo_view("test-version", REPO_ROOT, "ui_catalogue_demos")

    assert "dotlineform UI catalogue" in html
    assert 'class="uiCatalogueShellNav__item"' not in html
    assert ">demos</a>" not in html
    assert "/admin/ui-catalogue/assets/css/ui-catalogue-shell.css?v=test-version" in html
    assert "/admin/ui-catalogue/assets/css/ui-catalogue-demo.css?v=test-version" in html
    assert "/admin/ui-catalogue/assets/js/ui-catalogue-shell.js?v=test-version" in html
    assert "/admin/ui-catalogue/assets/js/ui-catalogue-demo.js?v=test-version" in html
    assert "/docs/" not in html
    assert "uiCatalogueShellDocLink" not in html
    assert "/studio/ui-catalogue/" not in html
    assert 'href="/ui-catalogue/' not in html
    assert 'src="/ui-catalogue/' not in html
    assert "/studio/app/" not in html
    assert "/assets/ui-catalogue/" not in html
    assert "/assets/css/main.css" not in html


def test_palette_route_renders_from_ui_catalogue_owned_data() -> None:
    items = load_palette_items(REPO_ROOT)
    assert items
    assert items[0]["id"] == "--text"

    html = ui_catalogue_palette_view("test-version", REPO_ROOT)

    assert "Palette | dotlineform UI Catalogue" in html
    assert "/admin/ui-catalogue/assets/css/ui-catalogue-shell.css?v=test-version" in html
    assert "/admin/ui-catalogue/assets/css/ui-catalogue-demo.css?v=test-version" in html
    assert "admin-app/ui-catalogue/source/palette/palette.yml" in html
    assert "<td class=\"uiCataloguePalette__id\">--text</td>" in html
    assert 'href="/palette/"' not in html
    assert 'href="/assets/css/main.css' not in html


def test_asset_version_tracks_ui_catalogue_assets() -> None:
    assert asset_version(REPO_ROOT).isdigit()
