#!/usr/bin/env python3
"""Focused checks for the standalone UI Catalogue app server."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_DIR = REPO_ROOT / "ui-catalogue-app" / "app" / "server" / "ui_catalogue_app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from ui_catalogue_app_config import asset_version  # noqa: E402
from ui_catalogue_app_server import UiCatalogueAppRequestHandler, env_flag, parse_args  # noqa: E402
from ui_catalogue_app_views import UI_CATALOGUE_DEMO_ROUTES, load_palette_items, ui_catalogue_demo_view, ui_catalogue_palette_view  # noqa: E402


def test_static_path_policy_serves_only_ui_catalogue_app_assets() -> None:
    def allowed(path: str) -> bool:
        return UiCatalogueAppRequestHandler.is_allowed_static_path(object(), path)

    assert allowed("/ui-catalogue/app/assets/css/ui-catalogue-demo.css") is True
    assert allowed("/ui-catalogue/app/assets/css/ui-catalogue-shell.css") is True
    assert allowed("/ui-catalogue/app/assets/js/ui-catalogue-demo.js") is True
    assert allowed("/ui-catalogue/app/assets/js/ui-catalogue-shell.js") is True
    assert allowed("/ui-catalogue/app/assets/img/panel-backgrounds/01007-primary-800.webp") is True
    assert allowed("/ui-catalogue/app/assets/img/moments/blue-sky-thumb-96.webp") is True

    assert allowed("/studio/ui-catalogue/assets/js/ui-catalogue-demo.js") is False
    assert allowed("/studio/app/assets/css/studio.css") is False
    assert allowed("/assets/ui-catalogue/js/ui-catalogue-demo.js") is False
    assert allowed("/assets/css/main.css") is False


def test_demo_routes_render_standalone_shell() -> None:
    assert UI_CATALOGUE_DEMO_ROUTES["/ui-catalogue/demos/"] == "ui_catalogue_demos"
    html = ui_catalogue_demo_view("test-version", REPO_ROOT, "ui_catalogue_demos")

    assert "dotlineform UI catalogue" in html
    assert 'class="uiCatalogueShellNav__item"' not in html
    assert ">demos</a>" not in html
    assert "/ui-catalogue/app/assets/css/ui-catalogue-shell.css?v=test-version" in html
    assert "/ui-catalogue/app/assets/css/ui-catalogue-demo.css?v=test-version" in html
    assert "/ui-catalogue/app/assets/js/ui-catalogue-shell.js?v=test-version" in html
    assert "/ui-catalogue/app/assets/js/ui-catalogue-demo.js?v=test-version" in html
    assert "/docs/" not in html
    assert "uiCatalogueShellDocLink" not in html
    assert "/studio/ui-catalogue/" not in html
    assert "/studio/app/" not in html
    assert "/assets/ui-catalogue/" not in html
    assert "/assets/css/main.css" not in html


def test_palette_route_renders_from_ui_catalogue_owned_data() -> None:
    items = load_palette_items(REPO_ROOT)
    assert items
    assert items[0]["id"] == "--text"

    html = ui_catalogue_palette_view("test-version", REPO_ROOT)

    assert "Palette | dotlineform UI Catalogue" in html
    assert "/ui-catalogue/app/assets/css/ui-catalogue-shell.css?v=test-version" in html
    assert "/ui-catalogue/app/assets/css/ui-catalogue-demo.css?v=test-version" in html
    assert "ui-catalogue-app/source/palette/palette.yml" in html
    assert "<td class=\"uiCataloguePalette__id\">--text</td>" in html
    assert 'href="/palette/"' not in html
    assert 'href="/assets/css/main.css' not in html


def test_access_log_is_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("UI_CATALOGUE_APP_ACCESS_LOG", raising=False)
    assert env_flag("UI_CATALOGUE_APP_ACCESS_LOG") is False
    assert parse_args([]).access_log is False

    monkeypatch.setenv("UI_CATALOGUE_APP_ACCESS_LOG", "1")
    assert env_flag("UI_CATALOGUE_APP_ACCESS_LOG") is True
    assert parse_args([]).access_log is True
    assert parse_args(["--access-log"]).access_log is True

    monkeypatch.setenv("UI_CATALOGUE_APP_ACCESS_LOG", "0")
    assert parse_args([]).access_log is False
    assert parse_args(["--access-log"]).access_log is True


def test_asset_version_tracks_ui_catalogue_assets() -> None:
    assert asset_version(REPO_ROOT).isdigit()
