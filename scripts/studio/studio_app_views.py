"""HTML views for the local Studio app server."""

from __future__ import annotations

import html
import json
from pathlib import Path

try:
    from studio_app_config import STUDIO_MEDIA, STUDIO_VIEWS
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .studio_app_config import STUDIO_MEDIA, STUDIO_VIEWS


def studio_nav(active_view_id: str = "") -> str:
    items = []
    for view_id, view in STUDIO_VIEWS.items():
        if view.get("nav", "true") == "false":
            continue
        label = html.escape(view["label"])
        href = html.escape(view["path"], quote=True)
        escaped_view_id = html.escape(view_id, quote=True)
        active_class = " is-active" if view_id == active_view_id else ""
        items.append(f'<a class="nav-item{active_class}" href="{href}" data-studio-navigate="{escaped_view_id}">{label}</a>')
    return "\n        ".join(items)


def studio_route_view(version: str, view_id: str, body_html: str) -> str:
    view = STUDIO_VIEWS[view_id]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    doc_href = html.escape(view["doc_href"], quote=True)
    script = html.escape(view["script"], quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>{title} | dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform Studio</a></div>
      <nav class="site-nav" aria-label="Studio">
        {studio_nav(view_id)}
      </nav>
    </div>
  </header>
  <main class="container">
    <div class="studio">
      <div class="studio__headerRow">
        <h2>{title}</h2>
        <a
          class="studioLayout__docLink"
          href="{doc_href}"
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
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
  <script type="module" src="{script}?v={escaped_version}"></script>
</body>
</html>
"""


def studio_analytics_view(version: str) -> str:
    body = """<div
          class="studioDashboard"
          id="studioAnalyticsDashboardRoot"
          data-studio-dashboard-route="studio-analytics"
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="studioDashboard__metrics" aria-label="Analytics metrics">
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="tag-count">--</p>
              <p class="studioMetricCard__label">tags</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="tag-group-count">--</p>
              <p class="studioMetricCard__label">groups</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="series-count">--</p>
              <p class="studioMetricCard__label">series</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="works-count">--</p>
              <p class="studioMetricCard__label">works</p>
            </article>
          </section>

          <section class="catalogueDashboardRoutes" aria-label="Analytics links">
            <section class="catalogueDashboardColumn">
              <h3>Tags</h3>
              <ul class="catalogueDashboardPills">
                <li><a href="/studio/analytics/tag-groups/">tag groups</a></li>
                <li><a href="/studio/analytics/tag-registry/">registry</a></li>
                <li><a href="/studio/analytics/tag-aliases/">aliases</a></li>
              </ul>
            </section>
            <section class="catalogueDashboardColumn">
              <h3>Assignments</h3>
              <ul class="catalogueDashboardPills">
                <li><a href="/studio/analytics/series-tags/">series tags</a></li>
                <li><a href="/studio/analytics/series-tag-editor/">tag editor</a></li>
              </ul>
            </section>
          </section>
        </div>"""
    return studio_route_view(version, "studio_analytics", body)


def tag_groups_view(version: str) -> str:
    body = """<div class="tagStudioPage tagGroupsPage">
          <div id="tag-groups" data-role="tag-groups" data-studio-ready="false" data-studio-busy="false">
            <div class="tagStudio__panel">
              <div data-role="content"></div>
            </div>
          </div>
        </div>"""
    return studio_route_view(version, "tag_groups", body)


def tag_registry_view(version: str) -> str:
    body = """<div class="tagRegistryPage">
          <div id="tag-registry" data-role="tag-registry" data-studio-ready="false" data-studio-busy="false">
            <div class="seriesTagsActions">
              <button type="button" class="tagStudio__button" data-role="open-import-modal">Import</button>
              <button type="button" class="tagStudio__button" data-role="open-new-tag">New tag</button>
            </div>
            <section class="tagStudio__panel">
              <div class="tagStudioFilters" data-role="filters">
                <div class="tagStudio__key tagStudioFilters__key" data-role="key"></div>
                <label class="tagStudioFilters__searchWrap">
                  <span class="visually-hidden" data-role="search-label">Search tags</span>
                  <input
                    type="text"
                    class="tagStudio__input tagStudioFilters__searchInput"
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
    return studio_route_view(version, "tag_registry", body)


def tag_aliases_view(version: str) -> str:
    body = """<div class="tagAliasesPage">
          <div id="tag-aliases" data-role="tag-aliases" data-studio-ready="false" data-studio-busy="false">
            <div class="seriesTagsActions">
              <button type="button" class="tagStudio__button" data-role="open-import-modal">Import</button>
              <button type="button" class="tagStudio__button" data-role="open-new-alias">New alias</button>
            </div>
            <section class="tagStudio__panel">
              <div class="tagStudioFilters" data-role="filters">
                <div class="tagStudio__key tagStudioFilters__key" data-role="key"></div>
                <label class="tagStudioFilters__searchWrap">
                  <span class="visually-hidden" data-role="search-label">Search aliases</span>
                  <input
                    type="text"
                    class="tagStudio__input tagStudioFilters__searchInput"
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
    return studio_route_view(version, "tag_aliases", body)


def series_tags_view(version: str) -> str:
    body = """<div class="seriesTagsPage">
          <div class="seriesTagsActions" data-role="series-tags-actions">
            <button type="button" class="tagStudio__button" data-role="open-session-modal"></button>
            <button type="button" class="tagStudio__button" data-role="open-import-modal"></button>
          </div>
          <div data-role="series-tags-session-modal-host"></div>
          <div data-role="series-tags-import-modal-host"></div>
          <div class="tagStudio__panel">
            <div id="series-tags" data-role="series-tags" data-studio-ready="false" data-studio-busy="false"></div>
          </div>
        </div>"""
    return studio_route_view(version, "series_tags", body)


def series_tag_editor_view(version: str, repo_root: Path) -> str:
    view = STUDIO_VIEWS["series_tag_editor"]
    escaped_version = html.escape(version, quote=True)
    title = html.escape(view["title"])
    doc_href = html.escape(view["doc_href"], quote=True)
    script = html.escape(view["script"], quote=True)
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
    media_config = STUDIO_MEDIA.get("media") if isinstance(STUDIO_MEDIA.get("media"), dict) else {}
    media_base = str(media_config.get("base") or "")
    media_works = str(media_config.get("works_images") or "/works/img")
    media_image_works_base = f"{media_base}{media_works}/"
    body = f"""<article
          class="page tagStudioPage"
          id="seriesTagEditorRoot"
          data-baseurl=""
          data-media-image-works-base="{html.escape(media_image_works_base, quote=True)}"
          data-primary-render-widths="{html.escape(json.dumps(render_widths), quote=True)}"
          data-primary-display-width="{html.escape(str(display_width), quote=True)}"
          data-primary-full-width="{html.escape(str(full_width), quote=True)}"
          data-primary-suffix="{html.escape(str(primary_variants.get("suffix") or "primary"), quote=True)}"
          data-asset-format="{html.escape(str(encoding.get("format") or "webp"), quote=True)}"
          data-series-index-url="/assets/data/series_index.json"
          data-tag-studio-module-url="/assets/studio/js/tag-studio.js?v={escaped_version}"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <header class="tagStudioPage__header">
            <figure class="tagStudioPage__media" id="seriesTagEditorMedia" hidden>
              <a
                class="page__mediaLink"
                id="seriesTagEditorMediaLink"
                href="#"
                target="_blank"
                rel="noopener"
                style="--work-ar: 4 / 3;"
              >
                <img
                  class="tagStudioPage__mediaImg"
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
              <figcaption class="tagStudioPage__mediaCaption" id="seriesTagEditorMediaCaption"></figcaption>
            </figure>

            <section class="tagStudioPage__context tagStudioPage__context--meta">
              <h1 class="tagStudioPage__title" id="seriesTagEditorTitle">Series Tag Editor</h1>
              <div class="page__caption page__metaList">
                <div class="page__row"><span id="seriesTagEditorYearDisplay">-</span></div>
                <div class="page__row">
                  <span id="seriesTagEditorCat">-</span>
                </div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorYear">-</span></div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorSortFields">-</span></div>
                <div class="page__row" style="display:none;"><span id="seriesTagEditorPrimaryWork">-</span></div>
                <div class="page__row">/<span id="seriesTagEditorFolders">-</span></div>
                <div class="page__row"><span id="seriesTagEditorNotes">-</span></div>
              </div>
            </section>
          </header>

          <section class="tagStudioPage__editor">
            <div id="tag-studio" class="tagStudio" data-role="series-tag-editor">
              <section class="tagStudio__panel tagStudio__panel--editor" data-role="editor-shell">
                <section class="tagStudioEditorSection tagStudioEditorSection--work" data-role="work-section">
                  <div class="tagStudio__inputRow tagStudio__inputRow--work">
                    <input class="tagStudio__input" data-role="work-input" type="text" autocomplete="off" placeholder="work_id(s) in this series">
                    <div class="tagStudio__workSelection" data-role="selected-work"></div>
                  </div>
                  <div class="tagStudio__popup tagStudio__popup--work" data-role="work-popup" hidden>
                    <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="work-popup-list"></div>
                  </div>
                </section>

                <section class="tagStudioEditorSection tagStudioEditorSection--messages" data-role="message-section">
                  <p class="tagStudio__contextHint" data-role="context-hint"></p>
                </section>

                <section class="tagStudioEditorSection tagStudioEditorSection--groups" data-role="groups-section">
                  <div data-role="groups"></div>
                </section>

                <section class="tagStudioEditorSection tagStudioEditorSection--search" data-role="search-section">
                  <div class="tagStudio__inputRow tagStudio__editorActionGrid">
                    <input class="tagStudio__input" data-role="tag-input" type="text" autocomplete="off" placeholder="tag slug or alias">
                    <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="add-tag">Add</button>
                    <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="save">Save</button>
                    <span class="tagStudio__saveMode" data-role="save-mode"></span>
                    <div class="tagStudio__buttonFeedback tagStudio__buttonFeedback--editor">
                      <p class="tagStudio__status" data-role="status"></p>
                      <p class="tagStudio__saveWarning" data-role="save-warning"></p>
                      <p class="tagStudio__saveResult" data-role="save-result"></p>
                    </div>
                  </div>
                  <div class="tagStudio__popup tagStudio__popup--series" data-role="popup" hidden>
                    <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="popup-list"></div>
                  </div>
                </section>
              </section>
              <div data-role="modal-host"></div>
            </div>
          </section>
        </article>
        <p id="seriesTagEditorEmpty" hidden></p>"""
    return studio_route_view(version, "series_tag_editor", body)


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


def project_state_view(version: str) -> str:
    body = """<div
          class="tagStudioPage catalogueWorkPage"
          id="projectStateRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="projectStatePageHeading">project state</h2>
              <span class="tagStudio__saveMode" id="projectStateSaveMode"></span>
            </div>
            <p class="tagStudio__contextHint" id="projectStateContext"></p>
            <p class="tagStudio__status" id="projectStateStatus"></p>
            <p class="tagStudio__saveWarning" id="projectStateWarning"></p>
            <p class="tagStudio__saveResult" id="projectStateResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading" id="projectStateRunHeading">report</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="projectStateRunButton">Run</button>
                </div>
              </div>
              <div class="tagStudioForm__fields catalogueWorkForm__fields">
                <div class="tagStudioForm__field">
                  <span class="tagStudioForm__label" id="projectStateOutputLabel">output</span>
                  <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="projectStateOutputPath">_docs/project-state.md</span>
                </div>
                <div class="tagStudioForm__field">
                  <span class="tagStudioForm__label" id="projectStateSourceLabel">source</span>
                  <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="projectStateSourceRoot">$DOTLINEFORM_PROJECTS_BASE_DIR/projects</span>
                </div>
                <label class="catalogueWorkPage__updateToggle" for="projectStateIncludeSubfolders">
                  <input type="checkbox" id="projectStateIncludeSubfolders">
                  <span id="projectStateIncludeSubfoldersLabel">include sub-folders</span>
                </label>
              </div>
            </section>

            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading" id="projectStateSummaryHeading">summary</h2>
              <div class="tagStudioForm__fields" id="projectStateSummary"></div>
              <div class="catalogueWorkPage__actions">
                <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="projectStateOpenButton">Open file</button>
              </div>
            </aside>
          </div>
        </div>

        <p class="tagStudio__status" id="projectStateLoading">loading project state...</p>
        <p class="tagStudio__empty" id="projectStateEmpty" hidden></p>"""
    return studio_route_view(version, "project_state", body)


def thumbnail_quality_view(version: str) -> str:
    body = """<div
          class="tagStudioPage thumbnailQualityPage"
          id="thumbnailQualityRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="thumbnailQualityPageHeading">thumbnail quality</h2>
              <div class="catalogueWorkPage__actions">
                <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="thumbnailQualityRefreshButton">Refresh</button>
              </div>
            </div>
            <p class="tagStudio__contextHint" id="thumbnailQualityContext"></p>
            <p class="tagStudio__status" id="thumbnailQualityStatus"></p>
            <p class="tagStudio__saveResult" id="thumbnailQualityResult"></p>
          </section>

          <section class="tagStudio__panel thumbnailQualitySettings" aria-labelledby="thumbnailQualitySettingsHeading">
            <h2 class="tagStudio__heading" id="thumbnailQualitySettingsHeading">settings</h2>
            <div class="thumbnailQualitySettings__grid" id="thumbnailQualitySettingsList"></div>
          </section>

          <section class="tagStudio__panel thumbnailQualitySeriesPreview" aria-labelledby="thumbnailQualitySeriesHeading">
            <h2 class="tagStudio__heading" id="thumbnailQualitySeriesHeading">series gallery comparison</h2>
            <p class="tagStudio__contextHint" id="thumbnailQualitySeriesContext"></p>
            <div class="seriesGrid thumbnailQualitySeriesPreview__grid" id="thumbnailQualitySeriesGrid"></div>
          </section>

          <section class="thumbnailQualityRows" id="thumbnailQualityRows" aria-label="Thumbnail quality comparison rows"></section>
        </div>

        <p class="tagStudio__status" id="thumbnailQualityLoading">loading thumbnail quality preview...</p>
        <p class="tagStudio__empty" id="thumbnailQualityEmpty" hidden></p>"""
    return studio_route_view(version, "thumbnail_quality", body)


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


def docs_viewer_shell(version: str, repo_root: Path) -> str:
    template_path = repo_root / "_includes" / "docs_viewer_shell.html"
    text = template_path.read_text(encoding="utf-8")
    lines = []
    active_stack = [True]
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("{%- assign "):
            continue
        if stripped == "{%- if include.allow_management -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- if include.allow_scope_query -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- unless include.enable_search == false -%}":
            active_stack.append(active_stack[-1])
            continue
        if stripped == "{%- if include.allow_scope_query and include.enable_search == false -%}":
            active_stack.append(False)
            continue
        if stripped in {"{%- endif -%}", "{%- endunless -%}"}:
            active_stack.pop()
            continue
        if active_stack[-1]:
            lines.append(raw_line)

    shell = "\n".join(lines)
    replacements = {
        "{{ '/assets/docs-viewer/css/docs-viewer.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer.css",
        "{{ '/assets/docs-viewer/css/docs-viewer-reports.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer-reports.css",
        "{{ '/assets/docs-viewer/css/docs-viewer-management.css' | relative_url }}": "/assets/docs-viewer/css/docs-viewer-management.css",
        "{{ '/assets/docs-viewer/js/docs-viewer.js' | relative_url }}": "/assets/docs-viewer/js/docs-viewer.js",
        "{{ site.time | date: '%s' }}": html.escape(version, quote=True),
        "{{ include.index_url }}": "",
        "{{ include.viewer_base_url }}": "/docs/",
        "{{ include.viewer_scope | default: '' }}": "",
        "{{ include.include_scope_param | default: false }}": "true",
        "{{ include.allow_management | default: false }}": "true",
        "{{ include.allow_scope_query | default: false }}": "true",
        "{{ include.default_doc_id | default: '' }}": "",
        "{{ include.search_index_url | default: '' }}": "",
        "{{ docs_viewer_config_url | relative_url }}": "/assets/docs-viewer/data/docs-viewer-config.json",
        "{{ include.ui_text_url | default: '/assets/docs-viewer/data/ui-text.json' | relative_url }}": "/assets/docs-viewer/data/ui-text.json",
        "{{ include.report_registry_url | default: '/assets/data/docs/reports.json' | relative_url }}": "/assets/data/docs/reports.json",
        "{{ docs_viewer_generated_base_url }}": "/studio/api/docs",
        "{{ include.management_base_url | default: '' }}": "/studio/api/docs",
        "{{ include.search_aria_label | default: 'Search docs' }}": "Search Studio docs",
        "{{ include.search_placeholder | default: 'search docs' }}": "search studio docs",
    }
    for token, value in replacements.items():
        shell = shell.replace(token, value)
    return shell


def docs_viewer_manage_view(version: str, repo_root: Path) -> str:
    escaped_version = html.escape(version, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>Docs | dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <header class="site-header">
    <div class="container">
      <div class="site-title"><a href="/studio/">dotlineform Studio</a></div>
      <nav class="site-nav" aria-label="Studio">
        {studio_nav("docs")}
      </nav>
    </div>
  </header>
  <main class="container studio-local-docs">
    {docs_viewer_shell(version, repo_root)}
  </main>
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""


def studio_home_view(version: str) -> str:
    escaped_version = html.escape(version, quote=True)
    links = "\n          ".join(
        '<li><a class="studioLinkList__item" href="{href}" data-studio-navigate="{view_id}">{label}</a></li>'.format(
            href=html.escape(view["path"], quote=True),
            view_id=html.escape(view_id, quote=True),
            label=html.escape(view["title"]),
        )
        for view_id, view in STUDIO_VIEWS.items()
        if view.get("nav", "true") != "false"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="dlf-asset-version" content="{escaped_version}">
  <meta name="dlf-studio-config-url" content="/studio/runtime-config.json">
  <title>dotlineform Studio</title>
  <link rel="stylesheet" href="/assets/css/main.css?v={escaped_version}">
  <link rel="stylesheet" href="/assets/studio/css/studio.css?v={escaped_version}">
</head>
<body class="studio-local-app">
  <main class="container">
    <div class="studio" id="studioHomeRoot" data-studio-ready="true" data-studio-busy="false">
      <div class="studio__headerRow"><h2>Studio</h2></div>
      <div class="studio__content">
        <ul class="studioLinkList">
          {links}
        </ul>
      </div>
    </div>
  </main>
  <script type="module" src="/assets/studio/js/studio-navigation.js?v={escaped_version}"></script>
</body>
</html>
"""
