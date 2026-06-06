"""Runtime config for Admin-hosted UI Catalogue routes."""

from __future__ import annotations

from pathlib import Path


UI_CATALOGUE_DEMO_VIEWS: dict[str, dict[str, str]] = {
    "ui_catalogue_demos": {
        "label": "ui catalogue",
        "title": "UI Catalogue Demos",
        "path": "/admin/ui-catalogue/demos/",
        "source": "admin-app/ui-catalogue/source/demos/index.md",
    },
    "ui_catalogue_demo_button": {
        "label": "button",
        "title": "UI Demo Primitive: Button",
        "path": "/admin/ui-catalogue/demos/primitives/button/",
        "source": "admin-app/ui-catalogue/source/demos/primitives/button/index.md",
    },
    "ui_catalogue_demo_input": {
        "label": "input",
        "title": "UI Demo Primitive: Input",
        "path": "/admin/ui-catalogue/demos/primitives/input/",
        "source": "admin-app/ui-catalogue/source/demos/primitives/input/index.md",
    },
    "ui_catalogue_demo_list": {
        "label": "list",
        "title": "UI Demo Primitive: List",
        "path": "/admin/ui-catalogue/demos/primitives/list/",
        "source": "admin-app/ui-catalogue/source/demos/primitives/list/index.md",
    },
    "ui_catalogue_demo_modal_shell": {
        "label": "modal shell",
        "title": "UI Demo Primitive: Modal Shell",
        "path": "/admin/ui-catalogue/demos/primitives/modal-shell/",
        "source": "admin-app/ui-catalogue/source/demos/primitives/modal-shell/index.md",
    },
    "ui_catalogue_demo_panel": {
        "label": "panel",
        "title": "UI Demo Primitive: Panel",
        "path": "/admin/ui-catalogue/demos/primitives/panel/",
        "source": "admin-app/ui-catalogue/source/demos/primitives/panel/index.md",
    },
    "ui_catalogue_demo_action_menu": {
        "label": "action menu",
        "title": "UI Demo Pattern: Action Menu",
        "path": "/admin/ui-catalogue/demos/patterns/action-menu/",
        "source": "admin-app/ui-catalogue/source/demos/patterns/action-menu/index.md",
    },
    "ui_catalogue_demo_reopenable_command_result": {
        "label": "reopenable result",
        "title": "UI Demo Pattern: Reopenable Command Result",
        "path": "/admin/ui-catalogue/demos/patterns/reopenable-command-result/",
        "source": "admin-app/ui-catalogue/source/demos/patterns/reopenable-command-result/index.md",
    },
    "ui_catalogue_demo_select_menu": {
        "label": "select menu",
        "title": "UI Demo Pattern: Select Menu",
        "path": "/admin/ui-catalogue/demos/patterns/select-menu/",
        "source": "admin-app/ui-catalogue/source/demos/patterns/select-menu/index.md",
    },
    "ui_catalogue_demo_column_links": {
        "label": "column links",
        "title": "UI Demo Pattern: Column Links",
        "path": "/admin/ui-catalogue/demos/patterns/column-links/",
        "source": "admin-app/ui-catalogue/source/demos/patterns/column-links/index.md",
    },
}


def ui_catalogue_demo_views(_repo_root: Path) -> dict[str, dict[str, str]]:
    return {view_id: dict(view) for view_id, view in UI_CATALOGUE_DEMO_VIEWS.items()}


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "css" / "ui-catalogue-demo.css",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "css" / "ui-catalogue-shell.css",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "js" / "ui-catalogue-demo.js",
        repo_root / "admin-app" / "ui-catalogue" / "assets" / "js" / "ui-catalogue-shell.js",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"
