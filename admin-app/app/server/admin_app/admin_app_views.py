"""HTML views for the local Admin app server."""

from __future__ import annotations

import html
from pathlib import Path

try:
    from admin_app_config import admin_views, load_admin_home_ui_text
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .admin_app_config import admin_views, load_admin_home_ui_text


REPO_ROOT = Path(__file__).resolve().parents[4]


def admin_theme_boot_script() -> str:
    return """<script>
    (function () {
      try {
        var theme = localStorage.getItem("theme");
        document.documentElement.setAttribute("data-theme", theme === "dark" ? "dark" : "light");
      } catch (error) {
        document.documentElement.setAttribute("data-theme", "light");
      }
    })();
  </script>"""


def admin_header() -> str:
    return """<header class="adminHeader">
    <div class="adminHeader__inner">
      <a class="adminHeader__brand" href="/admin/">dotlineform admin</a>
      <div class="adminHeader__actions">
        <button class="studioThemeToggle" type="button" data-admin-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
          <svg class="studioThemeToggle__icon" data-admin-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4"></circle>
            <path d="M12 2v2"></path>
            <path d="M12 20v2"></path>
            <path d="M4.93 4.93l1.41 1.41"></path>
            <path d="M17.66 17.66l1.41 1.41"></path>
            <path d="M2 12h2"></path>
            <path d="M20 12h2"></path>
            <path d="M4.93 19.07l1.41-1.41"></path>
            <path d="M17.66 6.34l1.41-1.41"></path>
          </svg>
          <svg class="studioThemeToggle__icon" data-admin-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
            <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
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
  {admin_theme_boot_script()}
  <link rel="stylesheet" href="/admin/app/assets/css/admin.css?v={escaped_version}">
</head>
<body class="adminApp">
  <div class="adminShell">
    {admin_header()}
    <main class="adminMain">
      <section class="adminHome" data-admin-home data-admin-ready="false" data-admin-busy="false">
        <section class="studioHomeLinks" aria-label="Admin home links">
          {link_groups}
        </section>
      </section>
    </main>
  </div>
  <script type="module" src="/admin/app/frontend/js/admin-theme.js?v={escaped_version}"></script>
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


def admin_checks_view(version: str) -> str:
    return admin_route_view(
        version,
        title="Checks",
        route_id="admin-checks",
        script="/admin/app/frontend/js/admin-checks.js",
        body="""<div
          class="tagStudioPage studioChecksPage"
          id="studioChecksRoot"
          hidden
          data-admin-route="admin-checks"
          data-admin-ready="false"
          data-admin-busy="false"
        >
          <div class="studioChecksTop">
            <section class="tagStudio__panel studioChecksPanel studioChecksControlsPanel">
              <p class="tagStudio__status" id="studioChecksStatus"></p>
              <form class="studioChecksForm" id="studioChecksForm">
                <label class="studioChecksField">
                  <span id="studioChecksReportLabel"></span>
                  <select class="tagStudio__input" id="studioChecksReport" name="report"></select>
                </label>
                <label class="studioChecksField">
                  <span id="studioChecksScopeLabel"></span>
                  <select class="tagStudio__input" id="studioChecksScope" name="scope"></select>
                </label>
                <label class="studioChecksField">
                  <span id="studioChecksFamilyLabel"></span>
                  <select class="tagStudio__input" id="studioChecksFamily" name="family"></select>
                </label>
                <label class="studioChecksField">
                  <span id="studioChecksAreaLabel"></span>
                  <select class="tagStudio__input" id="studioChecksArea" name="area"></select>
                </label>
                <label class="studioChecksField">
                  <span id="studioChecksRouteLabel"></span>
                  <select class="tagStudio__input" id="studioChecksRoute" name="route"></select>
                </label>
                <div class="studioChecksOptions" id="studioChecksOptions"></div>
                <div class="studioChecksActions">
                  <button type="submit" class="tagStudio__button tagStudio__button--defaultWidth" id="studioChecksRun"></button>
                </div>
              </form>
            </section>
            <section class="tagStudio__panel studioChecksPanel studioChecksRunsPanel">
              <div class="studioChecksPanelHead">
                <h3 id="studioChecksRunsTitle"></h3>
                <button type="button" class="tagStudio__button" id="studioChecksDelete"></button>
              </div>
              <select class="tagStudio__input studioChecksRunList" id="studioChecksRuns" size="8"></select>
            </section>
          </div>
          <section class="tagStudio__panel studioChecksOutputPanel">
            <div class="studioChecksArtifactPath" id="studioChecksArtifactPath"></div>
            <pre class="studioChecksMarkdown" id="studioChecksMarkdown"></pre>
          </section>
        </div>
        <p class="tagStudio__status" id="studioChecksBootStatus">loading Admin checks...</p>""",
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
  {admin_theme_boot_script()}
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
  <script type="module" src="/admin/app/frontend/js/admin-theme.js?v={escaped_version}"></script>
  <script type="module" src="{escaped_script}?v={escaped_version}"></script>
</body>
</html>
"""


def render_home_groups(route_map: dict[str, dict[str, object]], ui_text: dict[str, object]) -> str:
    raw_groups = ui_text.get("groups")
    if not isinstance(raw_groups, list):
        return ""

    groups: list[str] = []
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
                route = route_map.get(route_id, {})
                raw_path = route.get("path") if isinstance(route, dict) else None
                path = raw_path if isinstance(raw_path, str) else "#"
                link_label = html.escape(str(item.get("label") or route_id))
                links.append(
                    '<li><a class="studioHomeLinks__pill" href="{href}">{label}</a></li>'.format(
                        href=html.escape(path, quote=True),
                        label=link_label,
                    )
                )
        groups.append(
            f"""<section class="studioHomeLinks__column">
            <h3>{label}</h3>
            <ul class="studioHomeLinks__pills">
              {"".join(links)}
            </ul>
          </section>"""
        )
    return "\n          ".join(groups)
