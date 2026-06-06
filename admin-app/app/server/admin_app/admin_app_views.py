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


def admin_audits_view(version: str) -> str:
    return admin_route_view(
        version,
        title="Audits",
        route_id="admin-audits",
        script="/admin/app/frontend/js/admin-audits.js",
        body="""<div
          class="tagStudioPage studioAuditsPage"
          id="studioAuditsRoot"
          hidden
          data-admin-route="admin-audits"
          data-admin-ready="false"
          data-admin-busy="false"
        >
          <div class="tagStudio__panel studioAuditsPage__panel">
            <p class="studioAuditsPage__intro" id="studioAuditsIntro"></p>
            <p class="tagStudio__status" id="studioAuditsStatus"></p>
            <div class="studioAuditsPage__list" id="studioAuditsList"></div>
          </div>
        </div>
        <p class="tagStudio__status" id="studioAuditsBootStatus">loading Admin audits...</p>""",
    )


def admin_risk_view(version: str) -> str:
    return admin_route_view(
        version,
        title="Risk",
        route_id="admin-risk",
        script="/admin/app/frontend/js/admin-risk.js",
        body="""<div
          class="tagStudioPage studioRiskPage"
          id="studioRiskRoot"
          hidden
          data-admin-route="admin-risk"
          data-admin-ready="false"
          data-admin-busy="false"
        >
          <div class="tagStudio__panel studioRiskPage__panel">
            <p class="studioRiskPage__intro" id="studioRiskIntro"></p>
            <p class="tagStudio__status" id="studioRiskStatus"></p>
            <form class="studioRiskForm" id="studioRiskForm">
              <label class="studioRiskField">
                <span id="studioRiskAppLabel"></span>
                <select class="tagStudio__input" id="studioRiskApp" name="app"></select>
              </label>
              <label class="studioRiskField">
                <span id="studioRiskAreaLabel"></span>
                <input class="tagStudio__input" id="studioRiskArea" name="area" value="runtime" autocomplete="off">
              </label>
              <label class="studioRiskField">
                <span id="studioRiskRunIdLabel"></span>
                <input class="tagStudio__input" id="studioRiskRunId" name="run_id" autocomplete="off">
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskDryRun" name="dry_run">
                <span id="studioRiskDryRunLabel"></span>
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskRuntime" name="include_runtime">
                <span id="studioRiskRuntimeLabel"></span>
              </label>
              <label class="studioRiskCheck">
                <input type="checkbox" id="studioRiskLighthouse" name="include_lighthouse">
                <span id="studioRiskLighthouseLabel"></span>
              </label>
              <div class="studioRiskActions">
                <button type="submit" class="tagStudio__button tagStudio__button--defaultWidth" id="studioRiskRun"></button>
              </div>
            </form>
          </div>
          <section class="tagStudio__panel studioRiskPage__panel">
            <h3 id="studioRiskSummaryTitle"></h3>
            <div class="studioRiskSummary" id="studioRiskSummary"></div>
          </section>
          <section class="tagStudio__panel studioRiskPage__panel">
            <h3 id="studioRiskRunsTitle"></h3>
            <div class="studioRiskRuns" id="studioRiskRuns"></div>
          </section>
        </div>
        <p class="tagStudio__status" id="studioRiskBootStatus">loading Admin risk...</p>""",
    )


def admin_activity_view(version: str) -> str:
    return admin_route_view(
        version,
        title="Activity",
        route_id="admin-activity",
        script="/admin/app/frontend/js/admin-activity.js",
        body="""<div
          class="tagStudioPage buildActivityPage studioActivityPage"
          id="studioActivityRoot"
          hidden
          data-admin-route="admin-activity"
          data-admin-ready="false"
          data-admin-busy="false"
        >
          <div class="tagStudio__panel buildActivityPage__panel">
            <p class="buildActivityPage__meta" id="studioActivityMeta"></p>
            <div id="studioActivityList"></div>
          </div>
        </div>
        <p class="buildActivityPage__status" id="studioActivityStatus">loading Admin activity...</p>
        <p class="buildActivityPage__empty" id="studioActivityEmpty" hidden>No Admin activity yet.</p>""",
    )


def admin_testing_view(version: str) -> str:
    return admin_route_view(
        version,
        title="Testing",
        route_id="admin-testing",
        script="/admin/app/frontend/js/admin-testing.js",
        body="""<div
          class="adminTesting"
          id="adminTestingRoot"
          data-admin-route="admin-testing"
          data-admin-ready="false"
          data-admin-busy="false"
        >
          <section class="tagStudio__panel">
            <p class="tagStudio__status" id="adminTestingStatus">loading Admin test runs...</p>
            <div class="adminTestingRuns" id="adminTestingRuns"></div>
          </section>
        </div>""",
    )


def admin_route_view(version: str, *, title: str, route_id: str, script: str, body: str) -> str:
    escaped_version = html.escape(version, quote=True)
    escaped_title = html.escape(title)
    escaped_route_id = html.escape(route_id, quote=True)
    escaped_script = html.escape(script, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-admin-config-url" content="/admin/runtime-config.json">
  <title>{escaped_title} | dotlineform Admin</title>
  <link rel="stylesheet" href="/admin/app/assets/css/admin.css?v={escaped_version}">
</head>
<body class="adminApp">
  <div class="adminShell">
    {admin_header()}
    <main class="adminMain">
      <section class="adminRoute" data-admin-page="{escaped_route_id}">
        <div class="adminRoute__header">
          <h1 class="adminRoute__title">{escaped_title}</h1>
        </div>
        {body}
      </section>
    </main>
  </div>
  <script type="module" src="{escaped_script}?v={escaped_version}"></script>
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
