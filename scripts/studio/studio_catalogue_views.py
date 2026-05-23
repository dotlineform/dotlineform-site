"""Catalogue HTML views for the local Studio app server."""

from __future__ import annotations

import html
import json
from pathlib import Path

try:
    from studio_app_config import STUDIO_MEDIA
    from studio_app_views import load_pipeline, studio_route_view
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports in tests/tools.
    from .studio_app_config import STUDIO_MEDIA
    from .studio_app_views import load_pipeline, studio_route_view


def catalogue_field_registry_view(version: str) -> str:
    body = """<div
          class="tagStudioPage fieldRegistryReviewPage"
          id="fieldRegistryReviewRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="fieldRegistryReviewHeading">catalogue field registry</h2>
            </div>
            <p class="tagStudio__contextHint" id="fieldRegistryReviewContext"></p>
            <p class="tagStudio__status" id="fieldRegistryReviewStatus"></p>
          </section>

          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <label class="visually-hidden" for="fieldRegistryReviewSearch">Search by field name</label>
              <input
                type="search"
                class="tagStudio__input"
                id="fieldRegistryReviewSearch"
                placeholder="field name"
                autocomplete="off"
              >
            </div>
            <p class="tagStudioForm__meta" id="fieldRegistryReviewMeta"></p>
            <label class="tagStudioForm__field tagStudioForm__field--topAligned fieldRegistryReviewPage__outputField" for="fieldRegistryReviewOutput">
              <span class="tagStudioForm__label" id="fieldRegistryReviewOutputLabel">registry extract</span>
              <textarea class="tagStudio__input fieldRegistryReviewPage__output" id="fieldRegistryReviewOutput" readonly spellcheck="false"></textarea>
            </label>
          </section>
        </div>

        <p class="tagStudio__status" id="fieldRegistryReviewLoading">loading catalogue field registry...</p>
        <p class="tagStudio__empty" id="fieldRegistryReviewEmpty" hidden></p>"""
    return studio_route_view(version, "catalogue_field_registry", body)


def catalogue_dashboard_view(version: str) -> str:
    body = """<div
          class="studioDashboard"
          id="studioCatalogueDashboardRoot"
          data-studio-dashboard-route="studio-catalogue"
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="studioDashboard__metrics" aria-label="Catalogue metrics">
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="series-count">--</p>
              <p class="studioMetricCard__label">series</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="works-count">--</p>
              <p class="studioMetricCard__label">works</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="work-details-count">--</p>
              <p class="studioMetricCard__label">work details</p>
            </article>
            <article class="studioMetricCard">
              <p class="studioMetricCard__value" data-studio-metric="moments-count">--</p>
              <p class="studioMetricCard__label">moments</p>
            </article>
          </section>

          <section class="catalogueDashboardRoutes" aria-label="Catalogue links">
            <section class="catalogueDashboardColumn">
              <h3>Edit</h3>
              <ul class="catalogueDashboardPills">
                <li><a href="/studio/catalogue-series/?mode=manage">series</a></li>
                <li><a href="/studio/catalogue-work/?mode=manage">works</a></li>
                <li><a href="/studio/catalogue-work-detail/?mode=manage">work details</a></li>
                <li><a href="/studio/bulk-add-work/?mode=manage">bulk add</a></li>
                <li><a href="/studio/catalogue-moment/?mode=manage">moments</a></li>
              </ul>
            </section>
            <section class="catalogueDashboardColumn">
              <h3>Review</h3>
              <ul class="catalogueDashboardPills">
                <li><a href="/studio/catalogue-status/?mode=manage">drafts</a></li>
                <li><a href="/studio/studio-works/?mode=manage">works</a></li>
                <li><a href="/studio/project-state/?mode=manage">projects</a></li>
              </ul>
            </section>
          </section>
        </div>"""
    return studio_route_view(version, "studio_catalogue", body)


def catalogue_status_view(version: str) -> str:
    body = """<div
          class="tagStudioPage catalogueStatusPage"
          id="catalogueStatusRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel">
            <div class="tagStudioFilters catalogueStatusPage__filters">
              <div class="tagStudio__key tagStudioFilters__key" id="catalogueStatusKey"></div>
              <label class="tagStudioFilters__searchWrap catalogueStatusPage__searchWrap">
                <span class="visually-hidden">Search catalogue draft rows</span>
                <input
                  type="text"
                  class="tagStudio__input tagStudioFilters__searchInput"
                  id="catalogueStatusSearch"
                  placeholder="search"
                  autocomplete="off"
                >
              </label>
            </div>

            <p class="tagStudio__status catalogueStatusPage__meta" id="catalogueStatusMeta"></p>
            <div id="catalogueStatusList"></div>
          </section>
        </div>

        <p class="tagStudio__status" id="catalogueStatusLoading">loading catalogue drafts...</p>
        <p class="tagStudio__empty" id="catalogueStatusEmpty" hidden>No draft catalogue source records.</p>"""
    return studio_route_view(version, "catalogue_status", body)


def studio_works_view(version: str) -> str:
    body = """<div
          class="index worksList worksList--studio tagStudioList tagStudioList--dense"
          id="worksStudioRoot"
          data-role="studio-works"
          data-baseurl=""
          data-works-index-url="/assets/data/works_index.json"
          data-work-storage-index-url="/assets/studio/data/work_storage_index.json"
          data-series-index-url="/assets/data/series_index.json"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <h1 class="index__heading visually-hidden">studio works</h1>
          <div class="worksList__metaRow">
            <p class="worksList__count" id="worksListCount"></p>
            <div class="worksList__metaActions">
              <button class="tagStudio__button worksList__metaButton" type="button" id="worksListCopySeriesButton">copy series</button>
            </div>
          </div>

          <div class="tagStudioList__head worksList__head" role="group" aria-label="Sort studio works">
            <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="cat">
              cat <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
            </button>
            <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="year">
              year <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
            </button>
            <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="title">
              title <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
            </button>
            <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="series">
              series <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
            </button>
            <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="storage">
              storage <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
            </button>
          </div>

          <ul class="tagStudioList__rows" id="worksList"></ul>

          <nav class="page__nav" id="worksIndexBackNav" hidden>
            <a class="page__back" id="worksIndexBackLink" href="#">series</a>
          </nav>
        </div>
        <p id="worksStudioEmpty" hidden>no studio works yet</p>"""
    return studio_route_view(version, "studio_works", body)


def catalogue_media_attrs(repo_root: Path) -> dict[str, object]:
    pipeline = load_pipeline(repo_root)
    variants = pipeline.get("variants") if isinstance(pipeline.get("variants"), dict) else {}
    primary_variants = variants.get("primary") if isinstance(variants.get("primary"), dict) else {}
    compatibility_variants = variants.get("compatibility") if isinstance(variants.get("compatibility"), dict) else {}
    thumb_variants = variants.get("thumb") if isinstance(variants.get("thumb"), dict) else {}
    encoding = pipeline.get("encoding") if isinstance(pipeline.get("encoding"), dict) else {}
    render_widths = compatibility_variants.get("render_widths") or primary_variants.get("widths") or [800, 1200, 1600]
    if not isinstance(render_widths, list):
        render_widths = [800, 1200, 1600]
    thumb_sizes = thumb_variants.get("sizes") or [96, 192]
    if not isinstance(thumb_sizes, list):
        thumb_sizes = [96, 192]
    media_config = STUDIO_MEDIA.get("media") if isinstance(STUDIO_MEDIA.get("media"), dict) else {}
    thumbs_config = STUDIO_MEDIA.get("thumbs") if isinstance(STUDIO_MEDIA.get("thumbs"), dict) else {}
    media_base = str(media_config.get("base") or "")
    works_images = str(media_config.get("works_images") or "/works/img")
    thumb_base = str(thumbs_config.get("base") or "")
    thumb_works = str(thumbs_config.get("works") or "/assets/works/img")
    thumb_work_details = str(thumbs_config.get("work_details") or "/assets/work_details/img")
    return {
        "works_primary_base": f"{media_base}{works_images}/",
        "thumb_works_base": f"{thumb_base}{thumb_works}/",
        "thumb_work_details_base": f"{thumb_base}{thumb_work_details}/",
        "primary_display_width": render_widths[0] if render_widths else 800,
        "primary_full_width": primary_variants.get("preferred_width") or (render_widths[-1] if render_widths else 1600),
        "primary_suffix": primary_variants.get("suffix") or "primary",
        "thumb_sizes": thumb_sizes,
        "thumb_suffix": thumb_variants.get("suffix") or "thumb",
        "asset_format": encoding.get("format") or "webp",
    }


def catalogue_work_view(version: str, repo_root: Path) -> str:
    media = catalogue_media_attrs(repo_root)
    body = f"""<div
          class="tagStudioPage catalogueWorkPage"
          id="catalogueWorkRoot"
          hidden
          data-studio-route="catalogue-work"
          data-studio-ready="false"
          data-studio-busy="false"
          data-works-primary-base="{html.escape(str(media["works_primary_base"]), quote=True)}"
          data-thumb-works-base="{html.escape(str(media["thumb_works_base"]), quote=True)}"
          data-thumb-work-details-base="{html.escape(str(media["thumb_work_details_base"]), quote=True)}"
          data-primary-display-width="{html.escape(str(media["primary_display_width"]), quote=True)}"
          data-primary-full-width="{html.escape(str(media["primary_full_width"]), quote=True)}"
          data-primary-suffix="{html.escape(str(media["primary_suffix"]), quote=True)}"
          data-thumb-sizes="{html.escape(json.dumps(media["thumb_sizes"]), quote=True)}"
          data-thumb-suffix="{html.escape(str(media["thumb_suffix"]), quote=True)}"
          data-asset-format="{html.escape(str(media["asset_format"]), quote=True)}"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueWorkSearch">Find work by id</label>
                <input type="text" class="tagStudio__input" id="catalogueWorkSearch" placeholder="find work by id" autocomplete="off">
                <div class="tagStudio__popup" id="catalogueWorkPopup" hidden>
                  <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkPopupList"></div>
                </div>
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkOpen">Open</button>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkNew">New</button>
              <span class="tagStudio__saveMode" id="catalogueWorkSaveMode"></span>
            </div>
            <p class="tagStudio__contextHint" id="catalogueWorkContext"></p>
            <p class="tagStudio__status" id="catalogueWorkStatus"></p>
            <p class="tagStudio__saveWarning" id="catalogueWorkWarning"></p>
            <p class="tagStudio__saveResult" id="catalogueWorkResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading">work metadata</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkSave">Save</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkPublication">Publish</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDelete">Delete</button>
                </div>
              </div>
              <p class="tagStudioForm__meta" id="catalogueWorkMeta"></p>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkFields"></div>
            </section>

            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading">current record</h2>
              <div id="catalogueWorkPreview"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkReadonly"></div>
              <p class="tagStudioForm__impact" id="catalogueWorkRuntimeState"></p>
              <p class="tagStudioForm__impact" id="catalogueWorkBuildImpact"></p>
              <div class="tagStudioForm__fields" id="catalogueWorkSummary"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkReadiness"></div>
            </aside>
          </div>

          <section class="tagStudio__panel catalogueWorkDetails">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="catalogueWorkDetailsHeading">work details</h2>
              <a class="catalogueWorkDetails__newLink" id="catalogueWorkNewDetailLink" href="/studio/catalogue-work-detail/?mode=manage">new work detail -></a>
            </div>
            <div class="catalogueWorkDetails__searchRow" id="catalogueWorkDetailsSearchRow" hidden>
              <div class="tagStudioForm__searchWrap catalogueWorkDetails__searchWrap">
                <label class="visually-hidden" for="catalogueWorkDetailSearch">Find detail by id</label>
                <input type="text" class="tagStudio__input" id="catalogueWorkDetailSearch" placeholder="find detail by id" autocomplete="off">
              </div>
            </div>
            <p class="tagStudioForm__meta" id="catalogueWorkDetailsMeta"></p>
            <div class="catalogueWorkDetails__results" id="catalogueWorkDetailsResults"></div>
          </section>

          <section class="tagStudio__panel catalogueWorkDetails">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="catalogueWorkFilesHeading">work files</h2>
              <button type="button" class="tagStudio__button" id="catalogueWorkNewFileLink">Add file</button>
            </div>
            <p class="tagStudioForm__meta" id="catalogueWorkFilesMeta"></p>
            <div class="catalogueWorkDetails__results" id="catalogueWorkFilesResults"></div>
          </section>

          <section class="tagStudio__panel catalogueWorkDetails">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="catalogueWorkLinksHeading">work links</h2>
              <button type="button" class="tagStudio__button" id="catalogueWorkNewLinkLink">Add link</button>
            </div>
            <p class="tagStudioForm__meta" id="catalogueWorkLinksMeta"></p>
            <div class="catalogueWorkDetails__results" id="catalogueWorkLinksResults"></div>
          </section>
        </div>
        <p class="tagStudio__status" id="catalogueWorkLoading">loading catalogue work editor...</p>
        <p class="tagStudio__empty" id="catalogueWorkEmpty" hidden></p>"""
    return studio_route_view(version, "catalogue_work_editor", body)


def catalogue_work_detail_view(version: str, repo_root: Path) -> str:
    media = catalogue_media_attrs(repo_root)
    body = f"""<div
          class="tagStudioPage catalogueWorkPage"
          id="catalogueWorkDetailRoot"
          hidden
          data-thumb-work-details-base="{html.escape(str(media["thumb_work_details_base"]), quote=True)}"
          data-thumb-sizes="{html.escape(json.dumps(media["thumb_sizes"]), quote=True)}"
          data-thumb-suffix="{html.escape(str(media["thumb_suffix"]), quote=True)}"
          data-asset-format="{html.escape(str(media["asset_format"]), quote=True)}"
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueWorkDetailSearchGlobal">Find detail by id</label>
                <input type="text" class="tagStudio__input" id="catalogueWorkDetailSearchGlobal" placeholder="find detail by id" autocomplete="off">
                <div class="tagStudio__popup" id="catalogueWorkDetailPopup" hidden>
                  <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkDetailPopupList"></div>
                </div>
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailOpen">Open</button>
              <span class="tagStudio__saveMode" id="catalogueWorkDetailSaveMode"></span>
            </div>
            <p class="tagStudio__contextHint" id="catalogueWorkDetailContext"></p>
            <p class="tagStudio__status" id="catalogueWorkDetailStatus"></p>
            <p class="tagStudio__saveWarning" id="catalogueWorkDetailWarning"></p>
            <p class="tagStudio__saveResult" id="catalogueWorkDetailResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading">work detail metadata</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailSave">Save</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailPublication">Publish</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailDelete">Delete</button>
                </div>
              </div>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkDetailFields"></div>
            </section>
            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading">current record</h2>
              <div id="catalogueWorkDetailPreview"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailReadonly"></div>
              <p class="tagStudioForm__impact" id="catalogueWorkDetailRuntimeState"></p>
              <p class="tagStudioForm__impact" id="catalogueWorkDetailBuildImpact"></p>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailSummary"></div>
              <div class="tagStudioForm__fields" id="catalogueWorkDetailReadiness"></div>
            </aside>
          </div>
        </div>
        <p class="tagStudio__status" id="catalogueWorkDetailLoading">loading catalogue work detail editor...</p>
        <p class="tagStudio__empty" id="catalogueWorkDetailEmpty" hidden></p>"""
    return studio_route_view(version, "catalogue_work_detail_editor", body)


def catalogue_series_view(version: str) -> str:
    body = """<div
          class="tagStudioPage catalogueWorkPage"
          id="catalogueSeriesRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueSeriesSearch">Find series by title</label>
                <input type="text" class="tagStudio__input" id="catalogueSeriesSearch" placeholder="find series by title" autocomplete="off">
                <div class="tagStudio__popup" id="catalogueSeriesPopup" hidden>
                  <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueSeriesPopupList"></div>
                </div>
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesOpen">Open</button>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesNew">New</button>
              <span class="tagStudio__saveMode" id="catalogueSeriesSaveMode"></span>
            </div>
            <p class="tagStudio__contextHint" id="catalogueSeriesContext"></p>
            <p class="tagStudio__status" id="catalogueSeriesStatus"></p>
            <p class="tagStudio__saveWarning" id="catalogueSeriesWarning"></p>
            <p class="tagStudio__saveResult" id="catalogueSeriesResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading">series metadata</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesSave">Save</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesPublication">Publish</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesDelete">Delete</button>
                </div>
              </div>
              <p class="tagStudioForm__meta" id="catalogueSeriesMeta"></p>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueSeriesFields"></div>
            </section>
            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading">current record</h2>
              <div class="tagStudioForm__fields" id="catalogueSeriesReadonly"></div>
              <p class="tagStudioForm__impact" id="catalogueSeriesRuntimeState"></p>
              <p class="tagStudioForm__impact" id="catalogueSeriesBuildImpact"></p>
              <div class="tagStudioForm__fields" id="catalogueSeriesSummary"></div>
              <div class="tagStudioForm__fields" id="catalogueSeriesReadiness"></div>
            </aside>
          </div>

          <section class="tagStudio__panel catalogueSeriesMembers">
            <div class="tagStudio__headingRow">
              <h2 class="tagStudio__heading" id="catalogueSeriesMembersHeading">member works</h2>
            </div>
            <div class="tagStudio__headingRow catalogueSeriesMembers__searchRow" id="catalogueSeriesMemberSearchRow" hidden>
              <div class="tagStudioForm__searchWrap catalogueSeriesMembers__searchWrap">
                <label class="visually-hidden" for="catalogueSeriesMemberSearch">Find member work by id</label>
                <input type="text" class="tagStudio__input" id="catalogueSeriesMemberSearch" placeholder="find member work by id" autocomplete="off">
              </div>
              <span class="tagStudioForm__meta" id="catalogueSeriesMemberSearchMeta"></span>
            </div>
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueSeriesMembers__searchWrap">
                <label class="visually-hidden" for="catalogueSeriesMemberAdd">Add work by id</label>
                <input type="text" class="tagStudio__input" id="catalogueSeriesMemberAdd" placeholder="add work by id" autocomplete="off">
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesMemberAddButton">Add</button>
              <span class="tagStudioForm__meta" id="catalogueSeriesMembersMeta"></span>
            </div>
            <p class="tagStudio__status" id="catalogueSeriesMembersStatus"></p>
            <div class="catalogueSeriesMembers__results" id="catalogueSeriesMembersResults"></div>
          </section>
        </div>
        <p class="tagStudio__status" id="catalogueSeriesLoading">loading catalogue series editor...</p>
        <p class="tagStudio__empty" id="catalogueSeriesEmpty" hidden></p>"""
    return studio_route_view(version, "catalogue_series_editor", body)


def catalogue_moment_view(version: str) -> str:
    body = """<div
          class="tagStudioPage catalogueWorkPage"
          id="catalogueMomentRoot"
          hidden
          data-studio-ready="false"
          data-studio-busy="false"
        >
          <section class="tagStudio__panel tagStudio__panel--editor">
            <div class="tagStudio__inputRow tagStudio__inputRow--editor">
              <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
                <label class="visually-hidden" for="catalogueMomentSearch">Find moment by id or title</label>
                <input type="text" class="tagStudio__input" id="catalogueMomentSearch" placeholder="find moment by id or title" autocomplete="off">
                <div class="tagStudio__popup" id="catalogueMomentPopup" hidden>
                  <div class="tagStudio__popupInner" id="catalogueMomentPopupList"></div>
                </div>
              </div>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentOpen">Open</button>
              <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentNew">New</button>
              <span class="tagStudio__saveMode" id="catalogueMomentSaveMode"></span>
            </div>
            <p class="tagStudio__contextHint" id="catalogueMomentContext"></p>
            <p class="tagStudio__status" id="catalogueMomentStatus"></p>
            <p class="tagStudio__saveWarning" id="catalogueMomentWarning"></p>
            <p class="tagStudio__saveResult" id="catalogueMomentResult"></p>
          </section>

          <div class="tagStudio__grid catalogueWorkPage__grid">
            <section class="tagStudio__panel tagStudio__panel--editor">
              <div class="tagStudio__headingRow">
                <h2 class="tagStudio__heading">moment metadata</h2>
                <div class="catalogueWorkPage__actions">
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentSave">Save</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentPublication">Publish</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentDelete">Delete</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentImportPreview">Preview</button>
                  <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentImportApply">Import</button>
                </div>
              </div>
              <p class="tagStudioForm__meta" id="catalogueMomentMeta"></p>
              <div class="tagStudioForm__fields" id="catalogueMomentImportSource" hidden>
                <label class="tagStudioForm__field" for="catalogueMomentImportFile">
                  <span class="tagStudioForm__label" id="catalogueMomentImportFileLabel">moment file</span>
                  <input class="tagStudio__input" id="catalogueMomentImportFile" type="text" placeholder="keys.md" spellcheck="false" autocomplete="off">
                  <p class="tagStudioForm__meta" id="catalogueMomentImportFileDescription"></p>
                </label>
              </div>
              <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueMomentFields"></div>
              <p class="tagStudioForm__meta" id="catalogueMomentImportSourceSummary"></p>
              <p class="tagStudioForm__meta" id="catalogueMomentImportImageGuidance"></p>
            </section>
            <aside class="tagStudio__panel catalogueWorkSummary">
              <h2 class="tagStudio__heading" id="catalogueMomentSideHeading">current record</h2>
              <div class="tagStudioForm__fields" id="catalogueMomentReadonly"></div>
              <p class="tagStudioForm__impact" id="catalogueMomentRuntimeState"></p>
              <p class="tagStudioForm__impact" id="catalogueMomentBuildImpact"></p>
              <div class="tagStudioForm__fields" id="catalogueMomentSummary"></div>
              <div class="tagStudioForm__fields" id="catalogueMomentReadiness"></div>
            </aside>
          </div>
        </div>
        <p class="tagStudio__status" id="catalogueMomentLoading">loading catalogue moment editor...</p>
        <p class="tagStudio__empty" id="catalogueMomentEmpty" hidden></p>"""
    return studio_route_view(version, "catalogue_moment_editor", body)
