"""HTML views for the local Analytics app server."""

from __future__ import annotations

import html
import json
from pathlib import Path

try:
    from analytics_app_config import ANALYTICS_MEDIA, ANALYTICS_TOP_NAV_VIEW_IDS, analytics_views
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .analytics_app_config import ANALYTICS_MEDIA, ANALYTICS_TOP_NAV_VIEW_IDS, analytics_views


REPO_ROOT = Path(__file__).resolve().parents[4]


ANALYTICS_TOP_NAV_ACTIVE_VIEW_IDS: dict[str, str] = {}


ANALYTICS_HOME_LINK_COLUMNS: tuple[dict[str, object], ...] = (
    {
        "label": "tags",
        "links": (
            ("series tags", "/analytics/series-tags/"),
            ("series tag editor", "/analytics/series-tag-editor/"),
        ),
    },
    {
        "label": "registry",
        "links": (
            ("tag registry", "/analytics/tag-registry/"),
            ("tag aliases", "/analytics/tag-aliases/"),
            ("tag groups", "/analytics/tag-groups/"),
        ),
    },
    {
        "label": "data sharing",
        "links": (
            ("prepare package", "/analytics/data-sharing/prepare/?mode=manage"),
            ("returned package", "/analytics/data-sharing/review/?mode=manage"),
        ),
    },
)


def analytics_nav(active_view_id: str = "") -> str:
    items = []
    active_nav_id = ANALYTICS_TOP_NAV_ACTIVE_VIEW_IDS.get(active_view_id, active_view_id)
    views = analytics_views(REPO_ROOT)
    for view_id in ANALYTICS_TOP_NAV_VIEW_IDS:
        view = views[view_id]
        label = html.escape(view["label"])
        href = html.escape(view["path"], quote=True)
        escaped_view_id = html.escape(view_id, quote=True)
        active_class = " is-active" if view_id == active_nav_id else ""
        items.append(f'<a class="nav-item{active_class}" href="{href}" data-analytics-navigate="{escaped_view_id}">{label}</a>')
    return "\n        ".join(items)


def analytics_header(active_view_id: str = "") -> str:
    return f"""<header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/analytics/">dotlineform analytics</a></div>
      <div class="analyticsHeader__actions">
        <nav class="site-nav" aria-label="Analytics">
          {analytics_nav(active_view_id)}
        </nav>
        <button class="analyticsThemeToggle" type="button" data-analytics-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
          <svg class="analyticsThemeToggle__icon" data-analytics-theme-icon="light" viewBox="0 0 24 24" aria-hidden="true">
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
          <svg class="analyticsThemeToggle__icon" data-analytics-theme-icon="dark" viewBox="0 0 24 24" aria-hidden="true" hidden>
            <path d="M21 12.79A8.5 8.5 0 1 1 11.21 3 6.5 6.5 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </div>
  </header>"""


def analytics_theme_boot_script() -> str:
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


def analytics_home_column_links() -> str:
    columns = []
    for column in ANALYTICS_HOME_LINK_COLUMNS:
        heading = html.escape(str(column["label"]))
        links = "\n              ".join(
            '<li><a class="analyticsHomeLinks__pill" href="{href}">{label}</a></li>'.format(
                href=html.escape(href, quote=True),
                label=html.escape(label),
            )
            for label, href in column["links"]
        )
        columns.append(
            f"""<section class="analyticsHomeLinks__column">
            <h3>{heading}</h3>
            <ul class="analyticsHomeLinks__pills">
              {links}
            </ul>
          </section>"""
        )
    return "\n          ".join(columns)


def analytics_route_view(version: str, view_id: str, body_html: str) -> str:
    view = analytics_views(REPO_ROOT)[view_id]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    script = html.escape(view["script"], quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-analytics-config-url" content="/analytics/runtime-config.json">
  <title>{title} | dotlineform Analytics</title>
  {analytics_theme_boot_script()}
  <link rel="stylesheet" href="/analytics/app/assets/css/analytics.css?v={escaped_version}">
</head>
<body class="analytics-local-app">
  {analytics_header(view_id)}
  <main class="container">
    <div class="analyticsShell">
      <div class="analyticsShell__headerRow">
        <h2>{title}</h2>
      </div>
      <div class="analyticsShell__content">
        {body_html}
      </div>
    </div>
  </main>
  <script type="module" src="/analytics/app/frontend/js/analytics-navigation.js?v={escaped_version}"></script>
  <script type="module" src="{script}?v={escaped_version}"></script>
</body>
</html>
"""

def tag_groups_view(version: str) -> str:
    body = """<div class="analyticsPage tagGroupsPage">
          <div id="tag-groups" data-role="tag-groups" data-analytics-ready="false" data-analytics-busy="false">
            <div class="analytics__panel">
              <div data-role="content"></div>
            </div>
          </div>
        </div>"""
    return analytics_route_view(version, "tag_groups", body)


def tag_registry_view(version: str) -> str:
    body = """<div class="tagRegistryPage">
          <div id="tag-registry" data-role="tag-registry" data-analytics-ready="false" data-analytics-busy="false">
            <div class="seriesTagsActions">
              <button type="button" class="analytics__button" data-role="open-import-modal">Import</button>
              <button type="button" class="analytics__button" data-role="open-new-tag">New tag</button>
            </div>
            <section class="analytics__panel">
              <div class="analyticsFilters" data-role="filters">
                <div class="analytics__key analyticsFilters__key" data-role="key"></div>
                <label class="analyticsFilters__searchWrap">
                  <span class="visually-hidden" data-role="search-label">Search tags</span>
                  <input
                    type="text"
                    class="analytics__input analyticsFilters__searchInput"
                    data-role="search"
                    placeholder="search"
                    autocomplete="off"
                  >
                </label>
              </div>
              <div data-role="list"></div>
            </section>
            <div data-role="modal-host"></div>
          </div>
        </div>"""
    return analytics_route_view(version, "tag_registry", body)


def tag_aliases_view(version: str) -> str:
    body = """<div class="tagAliasesPage">
          <div id="tag-aliases" data-role="tag-aliases" data-analytics-ready="false" data-analytics-busy="false">
            <div class="seriesTagsActions">
              <button type="button" class="analytics__button" data-role="open-import-modal">Import</button>
              <button type="button" class="analytics__button" data-role="open-new-alias">New alias</button>
            </div>
            <section class="analytics__panel">
              <div class="analyticsFilters" data-role="filters">
                <div class="analytics__key analyticsFilters__key" data-role="key"></div>
                <label class="analyticsFilters__searchWrap">
                  <span class="visually-hidden" data-role="search-label">Search aliases</span>
                  <input
                    type="text"
                    class="analytics__input analyticsFilters__searchInput"
                    data-role="search"
                    placeholder="search"
                    autocomplete="off"
                  >
                </label>
              </div>
              <div data-role="list"></div>
            </section>
            <div data-role="modal-host"></div>
          </div>
        </div>"""
    return analytics_route_view(version, "tag_aliases", body)


def series_tags_view(version: str) -> str:
    body = """<div class="seriesTagsPage">
          <div class="seriesTagsActions" data-role="series-tags-actions">
            <button type="button" class="analytics__button" data-role="open-session-modal"></button>
            <button type="button" class="analytics__button" data-role="open-import-modal"></button>
          </div>
          <div data-role="series-tags-session-modal-host"></div>
          <div data-role="series-tags-import-modal-host"></div>
          <div class="analytics__panel">
            <div id="series-tags" data-role="series-tags" data-analytics-ready="false" data-analytics-busy="false"></div>
          </div>
        </div>"""
    return analytics_route_view(version, "series_tags", body)


def series_tag_editor_view(version: str, repo_root: Path) -> str:
    escaped_version = html.escape(version, quote=True)
    pipeline = load_pipeline(repo_root)
    variants = pipeline.get("variants") if isinstance(pipeline.get("variants"), dict) else {}
    primary_variants = variants.get("primary") if isinstance(variants.get("primary"), dict) else {}
    compatibility_variants = variants.get("compatibility") if isinstance(variants.get("compatibility"), dict) else {}
    encoding = pipeline.get("encoding") if isinstance(pipeline.get("encoding"), dict) else {}
    render_widths = compatibility_variants.get("render_widths") or primary_variants.get("widths") or [800, 1200, 1600]
    if not isinstance(render_widths, list):
        render_widths = [800, 1200, 1600]
    display_width = render_widths[-1] if render_widths else 1600
    full_width = primary_variants.get("preferred_width") or display_width
    media_config = ANALYTICS_MEDIA.get("media") if isinstance(ANALYTICS_MEDIA.get("media"), dict) else {}
    media_base = str(media_config.get("base") or "")
    media_works = str(media_config.get("works_images") or "/works/img")
    media_image_works_base = f"{media_base}{media_works}/"
    body = f"""<article
          class="page analyticsPage"
          id="seriesTagEditorRoot"
          data-baseurl=""
          data-media-image-works-base="{html.escape(media_image_works_base, quote=True)}"
          data-primary-render-widths="{html.escape(json.dumps(render_widths), quote=True)}"
          data-primary-display-width="{html.escape(str(display_width), quote=True)}"
          data-primary-full-width="{html.escape(str(full_width), quote=True)}"
          data-primary-suffix="{html.escape(str(primary_variants.get("suffix") or "primary"), quote=True)}"
          data-asset-format="{html.escape(str(encoding.get("format") or "webp"), quote=True)}"
          data-series-index-url="/assets/data/series_index.json"
          data-analytics-tag-editor-module-url="/analytics/app/frontend/js/analytics-tag-editor.js?v={escaped_version}"
          hidden
          data-analytics-ready="false"
          data-analytics-busy="false"
        >
          <header class="analyticsPage__header">
            <figure class="analyticsPage__media" id="seriesTagEditorMedia" hidden>
              <a
                class="page__mediaLink"
                id="seriesTagEditorMediaLink"
                href="#"
                target="_blank"
                rel="noopener"
                style="--work-ar: 4 / 3;"
              >
                <img
                  class="analyticsPage__mediaImg"
                  id="seriesTagEditorMediaImg"
                  src=""
                  srcset=""
                  sizes="(max-width: 900px) 100vw, 40vw"
                  alt=""
                  loading="eager"
                  fetchpriority="high"
                  decoding="async"
                >
              </a>
              <figcaption class="analyticsPage__mediaCaption" id="seriesTagEditorMediaCaption"></figcaption>
            </figure>

            <section class="analyticsPage__context analyticsPage__context--meta">
              <h1 class="analyticsPage__title" id="seriesTagEditorTitle">Series Tag Editor</h1>
              <div class="page__caption page__metaList">
                <div class="page__row"><span id="seriesTagEditorYearDisplay">-</span></div>
                <div class="page__row">
                  <span id="seriesTagEditorCat">-</span>
                </div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorYear">-</span></div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorSortFields">-</span></div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorPrimaryWork">-</span></div>
                <div class="page__row">/<span id="seriesTagEditorFolders">-</span></div>
              </div>
            </section>
          </header>

          <section class="analyticsPage__editor">
            <div id="analytics-tag-editor" class="analyticsTagEditor" data-role="series-tag-editor">
              <section class="analytics__panel analytics__panel--editor" data-role="editor-shell">
                <section class="analyticsEditorSection analyticsEditorSection--work" data-role="work-section">
                  <div class="analytics__inputRow analytics__inputRow--work">
                    <input class="analytics__input" data-role="work-input" type="text" autocomplete="off" placeholder="work_id(s) in this series">
                    <div class="analytics__workSelection" data-role="selected-work"></div>
                  </div>
                  <div class="analytics__popup analytics__popup--work" data-role="work-popup" hidden>
                    <div class="analytics__popupInner analytics__popupInner--series" data-role="work-popup-list"></div>
                  </div>
                </section>

                <section class="analyticsEditorSection analyticsEditorSection--messages" data-role="message-section">
                  <p class="analytics__contextHint" data-role="context-hint"></p>
                </section>

                <section class="analyticsEditorSection analyticsEditorSection--groups" data-role="groups-section">
                  <div data-role="groups"></div>
                </section>

                <section class="analyticsEditorSection analyticsEditorSection--search" data-role="search-section">
                  <div class="analytics__inputRow analytics__editorActionGrid">
                    <input class="analytics__input" data-role="tag-input" type="text" autocomplete="off" placeholder="tag slug or alias">
                    <button type="button" class="analytics__button analytics__button--defaultWidth" data-role="add-tag">Add</button>
                    <button type="button" class="analytics__button analytics__button--defaultWidth" data-role="save">Save</button>
                    <span class="analytics__saveMode" data-role="save-mode"></span>
                    <div class="analytics__buttonFeedback analytics__buttonFeedback--editor">
                      <p class="analytics__status" data-role="status"></p>
                      <p class="analytics__saveWarning" data-role="save-warning"></p>
                      <p class="analytics__saveResult" data-role="save-result"></p>
                    </div>
                  </div>
                  <div class="analytics__popup analytics__popup--series" data-role="popup" hidden>
                    <div class="analytics__popupInner analytics__popupInner--series" data-role="popup-list"></div>
                  </div>
                </section>
              </section>
              <div data-role="modal-host"></div>
            </div>
          </section>
        </article>
        <p id="seriesTagEditorEmpty" hidden></p>"""
    return analytics_route_view(version, "series_tag_editor", body)


def data_sharing_prepare_view(version: str) -> str:
    body = """<div
          class="analyticsPage dataSharingPreparePage"
          id="dataSharingPrepareRoot"
          hidden
          data-analytics-ready="false"
          data-analytics-busy="false"
        >
          <div class="analytics__panel dataSharingPreparePage__panel">
            <div class="dataSharingPreparePage__controls">
              <label class="analyticsField dataSharingPreparePage__appField" for="dataSharingPrepareAppSelect">
                <span class="analyticsField__label" id="dataSharingPrepareAppLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingPrepareAppSelect"></select>
                </span>
              </label>
              <label class="analyticsField dataSharingPreparePage__dataDomainField" for="dataSharingPrepareDataDomainSelect">
                <span class="analyticsField__label" id="dataSharingPrepareDataDomainLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingPrepareDataDomainSelect"></select>
                </span>
              </label>
              <label class="analyticsField dataSharingPreparePage__field" for="dataSharingPrepareConfigSelect">
                <span class="analyticsField__label" id="dataSharingPrepareConfigLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingPrepareConfigSelect"></select>
                </span>
              </label>
              <button type="button" class="analytics__button analytics__button--defaultWidth" id="dataSharingPrepareRun"></button>
              <fieldset class="dataSharingPreparePage__format" id="dataSharingPrepareFormatWrap" aria-labelledby="dataSharingPrepareFormatLabel">
                <span class="dataSharingPreparePage__formatLabel" id="dataSharingPrepareFormatLabel"></span>
                <span class="dataSharingPreparePage__formatOptions" id="dataSharingPrepareFormatOptions"></span>
              </fieldset>
              <label class="dataSharingPreparePage__toggle" id="dataSharingPrepareMissingSummaryWrap" hidden>
                <input type="checkbox" id="dataSharingPrepareMissingSummaryOnly">
                <span id="dataSharingPrepareMissingSummaryLabel"></span>
              </label>
            </div>

            <p class="analytics__status" id="dataSharingPrepareStatus"></p>
            <p class="analyticsForm__meta dataSharingPreparePage__selectionSummary" id="dataSharingPrepareSelectionSummary"></p>

            <div class="dataSharingPreparePage__listActions" aria-label="Share package document selection actions">
              <span class="dataSharingPreparePage__filterPills" id="dataSharingPrepareListFilters" aria-label="Data Sharing list filters"></span>
              <button type="button" class="analytics__keyPill analyticsFilters__groupBtn" id="dataSharingPrepareSelectAll"></button>
              <button type="button" class="analytics__keyPill analyticsFilters__groupBtn" id="dataSharingPrepareClear"></button>
            </div>

            <div class="analyticsList dataSharingPrepareList" id="dataSharingPrepareList"></div>
            <div data-analytics-modal-host="true"></div>
          </div>
        </div>

        <p class="analytics__status" id="dataSharingPrepareBootStatus">loading Data Sharing...</p>"""
    return analytics_route_view(version, "data_sharing_prepare", body)


def data_sharing_review_view(version: str) -> str:
    body = """<div
          class="analyticsPage dataSharingReviewPage"
          id="dataSharingReviewRoot"
          hidden
          data-analytics-ready="false"
          data-analytics-busy="false"
        >
          <div class="analytics__panel dataSharingReviewPage__panel">
            <div class="dataSharingReviewPage__controls">
              <label class="analyticsField dataSharingReviewPage__appField" for="dataSharingReviewAppSelect">
                <span class="analyticsField__label" id="dataSharingReviewAppLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingReviewAppSelect"></select>
                </span>
              </label>
              <label class="analyticsField dataSharingReviewPage__dataDomainField" for="dataSharingReviewDataDomainSelect">
                <span class="analyticsField__label" id="dataSharingReviewDataDomainLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingReviewDataDomainSelect"></select>
                </span>
              </label>
              <label class="analyticsField dataSharingReviewPage__field" for="dataSharingReviewFileSelect">
                <span class="analyticsField__label" id="dataSharingReviewFileLabel"></span>
                <span class="analyticsField__control">
                  <select class="analytics__input" id="dataSharingReviewFileSelect"></select>
                </span>
              </label>
              <div class="dataSharingReviewPage__commandButtons" id="dataSharingReviewApplyActions" aria-label="Returned package apply actions">
                <button type="button" class="analytics__button analytics__button--defaultWidth" id="dataSharingReviewRun"></button>
                <div class="dataSharingReviewPage__actionsMenuHost">
                  <button
                    type="button"
                    class="analytics__button analytics__button--defaultWidth"
                    id="dataSharingReviewActionsButton"
                    aria-haspopup="menu"
                    aria-expanded="false"
                    aria-controls="dataSharingReviewActionsMenu"
                  ></button>
                  <div
                    class="dataSharingReviewPage__actionsMenu"
                    id="dataSharingReviewActionsMenu"
                    role="menu"
                    hidden
                  ></div>
                </div>
              </div>
            </div>

            <div class="dataSharingReviewPage__statusRow">
              <p class="analytics__status" id="dataSharingReviewStatus"></p>
              <button type="button" class="analytics__keyPill analyticsFilters__groupBtn dataSharingReviewPage__resultButton" id="dataSharingReviewResults" hidden></button>
            </div>
            <p class="analyticsForm__meta dataSharingReviewPage__selectionSummary" id="dataSharingReviewSelectionSummary"></p>

            <div class="dataSharingReviewPage__listActions" aria-label="Returned package review selection actions">
              <button type="button" class="analytics__keyPill analyticsFilters__groupBtn" id="dataSharingReviewSelectAll"></button>
              <button type="button" class="analytics__keyPill analyticsFilters__groupBtn" id="dataSharingReviewClear"></button>
            </div>

            <div class="analyticsList dataSharingReviewList" id="dataSharingReviewList"></div>

            <div data-analytics-modal-host="true"></div>
          </div>
        </div>

        <p class="analytics__status" id="dataSharingReviewBootStatus">loading Data Sharing...</p>"""
    return analytics_route_view(version, "data_sharing_review", body)


def load_pipeline(repo_root: Path) -> dict[str, object]:
    path = repo_root / "_data" / "pipeline.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def analytics_home_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    links = analytics_home_column_links()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-analytics-config-url" content="/analytics/runtime-config.json">
  <title>dotlineform Analytics</title>
  {analytics_theme_boot_script()}
  <link rel="stylesheet" href="/analytics/app/assets/css/analytics.css?v={escaped_version}">
</head>
<body class="analytics-local-app">
  {analytics_header()}
  <main class="container">
    <div class="analyticsShell" id="analyticsHomeRoot" data-analytics-ready="true" data-analytics-busy="false">
      <div class="analyticsShell__content">
        <section class="analyticsHomeLinks" aria-label="Analytics home links">
          {links}
        </section>
      </div>
    </div>
  </main>
  <script type="module" src="/analytics/app/frontend/js/analytics-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""
