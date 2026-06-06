"""HTML views for the local Admin app server."""

from __future__ import annotations

import html
from pathlib import Path

try:
    from admin_app_config import admin_views, load_admin_home_ui_text
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .admin_app_config import admin_views, load_admin_home_ui_text


REPO_ROOT = Path(__file__).resolve().parents[4]


def admin_header() -> str:
    return """<header class="adminHeader">
    <div class="adminHeader__inner">
      <a class="adminHeader__brand" href="/admin/">dotlineform admin</a>
      <nav class="adminHeader__nav" aria-label="Admin">
        <a href="/admin/audits/">audits</a>
        <a href="/admin/risk/">risk</a>
        <a href="/admin/activity/">activity</a>
        <a href="/admin/testing/">testing</a>
      </nav>
    </div>
  </header>"""


def admin_home_view(version: str, repo_root: Path) -> str:
    escaped_version = html.escape(version, quote=True)
    route_map = admin_views(repo_root)
    ui_text = load_admin_home_ui_text(repo_root)
    link_groups = render_home_groups(route_map, ui_text)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-admin-config-url" content="/admin/runtime-config.json">
  <title>Admin | dotlineform</title>
  <link rel="stylesheet" href="/admin/app/assets/css/admin.css?v={escaped_version}">
</head>
<body class="adminApp">
  <div class="adminShell">
    {admin_header()}
    <main class="adminMain">
      <section class="adminHome" data-admin-home data-admin-ready="false" data-admin-busy="false">
        <div class="adminHome__header">
          <h1 class="adminHome__title">Admin</h1>
          <p class="adminHome__summary">Operational review, testing, risk, activity, and reference surfaces for local development.</p>
        </div>
        <div class="adminHome__grid">
          {link_groups}
        </div>
      </section>
    </main>
  </div>
  <script type="module" src="/admin/app/frontend/js/admin-home.js?v={escaped_version}"></script>
</body>
</html>
"""


def render_home_groups(route_map: dict[str, dict[str, object]], ui_text: dict[str, object]) -> str:
    raw_groups = ui_text.get("groups")
    if not isinstance(raw_groups, list):
        return ""

    groups: list[str] = []
    sibling_paths = {
        "studio": "/studio/",
        "analytics": "/analytics/",
        "docs_viewer": "/docs/",
    }
    for group in raw_groups:
        if not isinstance(group, dict):
            continue
        label = html.escape(str(group.get("label") or "links"))
        links = []
        raw_links = group.get("links")
        if isinstance(raw_links, list):
            for item in raw_links:
                if not isinstance(item, dict):
                    continue
                route_id = str(item.get("route_id") or "")
                path = sibling_paths.get(route_id)
                if path is None:
                    route = route_map.get(route_id, {})
                    raw_path = route.get("path") if isinstance(route, dict) else None
                    path = raw_path if isinstance(raw_path, str) else "#"
                link_label = html.escape(str(item.get("label") or route_id))
                links.append(
                    '<li><a class="adminLinkList__item" href="{href}">{label}</a></li>'.format(
                        href=html.escape(path, quote=True),
                        label=link_label,
                    )
                )
        groups.append(
            f"""<section class="adminHome__section">
            <h2>{label}</h2>
            <ul class="adminLinkList">
              {"".join(links)}
            </ul>
          </section>"""
        )
    return "\n          ".join(groups)
