"""HTML views for the local Studio app server."""

from __future__ import annotations

import html
import json
from pathlib import Path

try:
    from studio_app_config import studio_top_nav_view_ids, studio_views
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .studio_app_config import studio_top_nav_view_ids, studio_views


REPO_ROOT = Path(__file__).resolve().parents[4]


STUDIO_TOP_NAV_ACTIVE_VIEW_IDS: dict[str, str] = {}


STUDIO_HOME_LINK_COLUMNS: tuple[dict[str, object], ...] = (
    {
        "label": "catalogue",
        "links": (
            ("drafts", "/studio/catalogue-status/?mode=manage"),
            ("series editor", "/studio/catalogue-series/"),
            ("work editor", "/studio/catalogue-work/"),
            ("work detail editor", "/studio/catalogue-work-detail/?mode=manage"),
            ("bulk add work", "/studio/bulk-add-work/?mode=manage"),
            ("moment editor", "/studio/catalogue-moment/?mode=manage"),
            ("list of works", "/studio/studio-works/?mode=manage&sort=cat&dir=asc"),
            ("project state", "/studio/project-state/?mode=manage"),
        ),
    },
    {
        "label": "admin",
        "links": (
            ("studio audits", "/studio/audits/?mode=manage"),
            ("studio activity", "/studio/activity/?mode=manage"),
            ("field registry", "/studio/catalogue-field-registry/?mode=manage"),
        ),
    },
)


def studio_nav(active_view_id: str = "") -> str:
    items = []
    active_nav_id = STUDIO_TOP_NAV_ACTIVE_VIEW_IDS.get(active_view_id, active_view_id)
    views = studio_views(REPO_ROOT)
    for view_id in studio_top_nav_view_ids(REPO_ROOT):
        view = views[view_id]
        label = html.escape(view["label"])
        href = html.escape(view["path"], quote=True)
        escaped_view_id = html.escape(view_id, quote=True)
        active_class = " is-active" if view_id == active_nav_id else ""
        items.append(f'<a class="nav-item{active_class}" href="{href}" data-studio-navigate="{escaped_view_id}">{label}</a>')
    return "\n        ".join(items)


def studio_header(active_view_id: str = "") -> str:
    return f"""<header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform studio</a></div>
      <div class="studioHeader__actions">
        <nav class="site-nav" aria-label="Studio">
          {studio_nav(active_view_id)}
        </nav>
        <button class="studioThemeToggle" type="button" data-studio-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
          <svg class="studioThemeToggle__icon" data-studio-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
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
          <svg class="studioThemeToggle__icon" data-studio-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
            <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </div>
  </header>"""


def studio_theme_boot_script() -> str:
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


def studio_home_column_links() -> str:
    columns = []
    for column in STUDIO_HOME_LINK_COLUMNS:
        heading = html.escape(str(column["label"]))
        links = "\n              ".join(
            '<li><a class="studioHomeLinks__pill studioLinkList__item" href="{href}">{label}</a></li>'.format(
                href=html.escape(href, quote=True),
                label=html.escape(label),
            )
            for label, href in column["links"]
        )
        columns.append(
            f"""<section class="studioHomeLinks__column">
            <h3>{heading}</h3>
            <ul class="studioHomeLinks__pills">
              {links}
            </ul>
          </section>"""
        )
    return "\n          ".join(columns)


def studio_route_view(version: str, view_id: str, body_html: str) -> str:
    view = studio_views(REPO_ROOT)[view_id]
    escaped_version = html.escape(version, quote=True)
    escaped_view_id = html.escape(view_id, quote=True)
    title = html.escape(view["title"])
    script = html.escape(view["script"], quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>{title} | dotlineform Studio</title>
  {studio_theme_boot_script()}
  <link rel="stylesheet" href="/studio/app/assets/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  {studio_header(view_id)}
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow">
        <h2>{title}</h2>
        <a
          class="studioLayout__docLink"
          href="/docs/"
          data-studio-doc-view="{escaped_view_id}"
          target="_blank"
          rel="noopener noreferrer"
          title="Open Studio page implementation notes"
          aria-label="Open Studio page implementation notes"
        >
          <em>i</em>
        </a>
      </div>
      <div class="studio__content">
        {body_html}
      </div>
    </div>
  </main>
  <script type="module" src="/studio/app/frontend/js/studio-navigation.js?v={escaped_version}"></script>
  <script type="module" src="{script}?v={escaped_version}"></script>
</body>
</html>
"""


def studio_app_bootstrap_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>dotlineform Studio</title>
  {studio_theme_boot_script()}
  <link rel="stylesheet" href="/studio/app/assets/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <div id="studioApp" data-studio-app-root="true"></div>
  <script type="module" src="/studio/app/frontend/js/studio-app.js?v={escaped_version}"></script>
</body>
</html>
"""


def studio_audits_view(version: str) -> str:
    body = """<div
          class="tagStudioPage studioAuditsPage"
          id="studioAuditsRoot"
          hidden
          data-studio-route="studio-audits"
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <div class="tagStudio__panel studioAuditsPage__panel">
            <p class="studioAuditsPage__intro" id="studioAuditsIntro"></p>
            <p class="tagStudio__status" id="studioAuditsStatus"></p>
            <div class="studioAuditsPage__list" id="studioAuditsList"></div>
          </div>
        </div>

        <p class="tagStudio__status" id="studioAuditsBootStatus">loading Studio audits...</p>"""
    return studio_route_view(version, "studio_audits", body)


def bulk_add_work_view(version: str, repo_root: Path) -> str:
    pipeline = load_pipeline(repo_root)
    paths = pipeline.get("paths") if isinstance(pipeline.get("paths"), dict) else {}
    workbooks = paths.get("workbooks") if isinstance(paths.get("workbooks"), dict) else {}
    workbook_path = str(workbooks.get("bulk_import") or "data/works_bulk_import.xlsx")
    escaped_workbook_path = html.escape(workbook_path, quote=True)
    body = f"""<div
          class="tagStudioPage catalogueWorkPage"
          id="bulkAddWorkRoot"
          data-workbook-path="{escaped_workbook_path}"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="bulkAddWorkPageHeading">bulk add work</h2>
              <span class="tagStudio__saveMode" id="bulkAddWorkSaveMode"></span>
            </div>

            <p class="tagStudio__contextHint" id="bulkAddWorkContext"></p>
            <p class="tagStudio__status" id="bulkAddWorkStatus"></p>
            <p class="tagStudio__saveWarning" id="bulkAddWorkWarning"></p>
            <p class="tagStudio__saveResult" id="bulkAddWorkResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading" id="bulkAddWorkImportHeading">import</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="bulkAddWorkPreview">Preview</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="bulkAddWorkApply">Import</button>
                </div>
              </div>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="bulkAddWorkFields">
                <label class="tagStudioForm__field catalogueWorkForm__field" for="bulkAddWorkMode">
                  <span class="tagStudioForm__label" id="bulkAddWorkModeLabel">mode</span>
                  <select class="tagStudio__input" id="bulkAddWorkMode">
                    <option value="works" id="bulkAddWorkModeWorks">works</option>
                    <option value="work_details" id="bulkAddWorkModeWorkDetails">work details</option>
                  </select>
                </label>
                <div class="tagStudioForm__field">
                  <span class="tagStudioForm__label" id="bulkAddWorkWorkbookLabel">workbook</span>
                  <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="bulkAddWorkWorkbook">{html.escape(workbook_path)}</span>
                </div>
              </div>
            </section>

            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading" id="bulkAddWorkSummaryHeading">preview summary</h2>
              <div class="tagStudioForm__fields" id="bulkAddWorkSummary"></div>
            </aside>
          </div>

          <section class="tagStudio__panel catalogueWorkDetails">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="bulkAddWorkDetailsHeading">preview details</h2>
            </div>
            <div class="catalogueWorkDetails__results" id="bulkAddWorkPreviewDetails"></div>
          </section>
        </div>

        <p class="tagStudio__status" id="bulkAddWorkLoading">loading bulk add work...</p>
        <p class="tagStudio__empty" id="bulkAddWorkEmpty" hidden></p>"""
    return studio_route_view(version, "bulk_add_work", body)


def activity_view(version: str) -> str:
    body = """<div
          class="tagStudioPage buildActivityPage studioActivityPage"
          id="studioActivityRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <div class="tagStudio__panel buildActivityPage__panel">
            <p class="buildActivityPage__meta" id="studioActivityMeta"></p>
            <div id="studioActivityList"></div>
          </div>
        </div>

        <p class="buildActivityPage__status" id="studioActivityStatus">loading Studio activity...</p>
        <p class="buildActivityPage__empty" id="studioActivityEmpty" hidden>No Studio activity yet.</p>"""
    return studio_route_view(version, "activity", body)


def load_pipeline(repo_root: Path) -> dict[str, object]:
    path = repo_root / "_data" / "pipeline.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def studio_home_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    links = studio_home_column_links()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>dotlineform Studio</title>
  {studio_theme_boot_script()}
  <link rel="stylesheet" href="/studio/app/assets/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  {studio_header()}
  <main class="container">
    <div class="studio" id="studioHomeRoot" data-studio-ready="true" data-studio-busy="false">
      <div class="studio__content">
        <section class="studioHomeLinks" aria-label="Studio home links">
          {links}
        </section>
      </div>
    </div>
  </main>
  <script type="module" src="/studio/app/frontend/js/studio-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""
