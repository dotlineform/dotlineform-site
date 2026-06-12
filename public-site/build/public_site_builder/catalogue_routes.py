from __future__ import annotations

import json
from html import escape
from typing import Any

from .config import PublicSiteConfig
from .render import join_url, render_page, script_tag


def render_series(config: PublicSiteConfig, pipeline: dict[str, Any]) -> str:
    thumb_sizes = _thumb_sizes(pipeline)
    thumb_suffix = _variant(pipeline, "thumb").get("suffix", "thumb")
    asset_format = _asset_format(pipeline)
    body = f"""
<h1 class="index__heading visually-hidden">works</h1>
<div
  id="seriesIndexRoot"
  data-baseurl="{_baseurl(config)}"
  data-thumb-works-base="{escape(join_url(config.thumbs['base'], config.thumbs['works']), quote=True)}"
  data-thumb-moments-base="{escape(join_url(config.thumbs['base'], config.thumbs['moments']), quote=True)}"
  data-thumb-sizes="{_json_attr(thumb_sizes)}"
  data-thumb-suffix="{escape(str(thumb_suffix), quote=True)}"
  data-asset-format="{escape(asset_format, quote=True)}"
  hidden
>
  <div class="seriesIndex__toolbar" aria-label="Works and moments view and sorting">
    <div class="seriesIndex__toolbarPrimary">
      <div class="seriesIndex__viewControls" role="group" aria-label="View">
        <button class="theme-toggle seriesIndex__viewBtn" type="button" data-role="catalog-index-view-btn" data-view="list" aria-label="Show list view" aria-pressed="true"><svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="4" y="5" width="2.5" height="2.5" rx="1"></rect><rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect><rect x="4" y="16.5" width="2.5" height="2.5" rx="1"></rect><path d="M10 6.25H20"></path><path d="M10 12H20"></path><path d="M10 17.75H20"></path></svg><span class="sr-only">list</span></button>
        <button class="theme-toggle seriesIndex__viewBtn" type="button" data-role="catalog-index-view-btn" data-view="grid" aria-label="Show grid view" aria-pressed="false"><svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="4" y="4" width="6.25" height="6.25" rx="1.5"></rect><rect x="13.75" y="4" width="6.25" height="6.25" rx="1.5"></rect><rect x="4" y="13.75" width="6.25" height="6.25" rx="1.5"></rect><rect x="13.75" y="13.75" width="6.25" height="6.25" rx="1.5"></rect></svg><span class="sr-only">grid</span></button>
      </div>
      <div class="seriesIndex__sortControls" role="group" aria-label="Sort">
        <button class="theme-toggle seriesIndex__sortBtn" type="button" data-role="catalog-index-sort-btn" data-sort-key="year" aria-pressed="true"><span class="seriesIndex__sortText">year</span><span class="seriesIndex__sortArrow" aria-hidden="true">&darr;</span></button>
        <button class="theme-toggle seriesIndex__sortBtn" type="button" data-role="catalog-index-sort-btn" data-sort-key="title" aria-pressed="false"><span class="seriesIndex__sortText">title</span><span class="seriesIndex__sortArrow" aria-hidden="true">&uarr;</span></button>
      </div>
    </div>
    <div class="seriesIndex__toolbarMiddle">
      <a id="seriesIndexRecentBtn" class="theme-toggle seriesIndex__recentBtn" data-enabled-href="/recent/" href="/recent/">recently added</a>
    </div>
    <div class="seriesIndex__toolbarSecondary">
      <div class="seriesIndex__modeControls" role="group" aria-label="Browse works or moments">
        <button class="theme-toggle seriesIndex__modeBtn" type="button" data-role="catalog-index-mode-btn" data-mode="works" aria-pressed="true"><span class="seriesIndex__modeText">works</span></button>
        <button class="theme-toggle seriesIndex__modeBtn" type="button" data-role="catalog-index-mode-btn" data-mode="moments" aria-pressed="false"><span class="seriesIndex__modeText">moments</span></button>
      </div>
      <a class="theme-toggle seriesIndex__searchBtn" href="/catalogue/search/" aria-label="Search the catalogue"><svg class="seriesIndex__searchIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="11" cy="11" r="6.5"></circle><path d="M16 16L20 20"></path></svg><span class="sr-only">search</span></a>
    </div>
  </div>
  <div class="index seriesIndex__list" id="seriesIndexList" aria-live="polite"></div>
  <div class="seriesGrid seriesIndex__grid" id="seriesIndexThumbGrid" aria-live="polite" hidden></div>
  <nav class="gridPager seriesIndex__pager" id="seriesIndexPager" aria-label="catalog index pagination" hidden>
    <span class="gridPager__status" id="seriesIndexPagerStatus"></span>
    <button class="gridPager__btn" type="button" id="seriesIndexPrev" aria-label="Previous page">&larr;</button>
    <button class="gridPager__btn" type="button" id="seriesIndexNext" aria-label="Next page">&rarr;</button>
  </nav>
</div>
<p id="seriesIndexEmpty" hidden>no works yet</p>

{script_tag('/assets/js/public-catalogue-runtime.js', config)}
{script_tag('/assets/js/series-index.js', config)}""".strip()
    return render_page(config, title="works", body=body, path="/series/", section="series")


def render_recent(config: PublicSiteConfig, pipeline: dict[str, Any]) -> str:
    body = f"""
<div
  class="index recentIndex"
  id="recentIndexRoot"
  data-baseurl="{_baseurl(config)}"
  data-thumb-works-base="{escape(join_url(config.thumbs['base'], config.thumbs['works']), quote=True)}"
  data-thumb-sizes="{_json_attr(_thumb_sizes(pipeline))}"
  data-thumb-suffix="{escape(str(_variant(pipeline, 'thumb').get('suffix', 'thumb')), quote=True)}"
  data-asset-format="{escape(_asset_format(pipeline), quote=True)}"
  hidden
>
  <h1 class="index__heading">recently added</h1>
  <ul class="recentIndex__list" id="recentIndexList"></ul>
  <nav class="page__nav">
    <a class="page__back" href="/series/">&larr; works</a>
  </nav>
</div>
<p id="recentIndexEmpty" hidden>nothing recently added yet</p>

{script_tag('/assets/js/public-catalogue-runtime.js', config)}
{script_tag('/assets/js/recent-index.js', config)}""".strip()
    return render_page(config, title="recently added", body=body, path="/recent/", section="works")


def render_works(config: PublicSiteConfig, pipeline: dict[str, Any]) -> str:
    primary_render_widths = _primary_render_widths(pipeline)
    primary_display_width = primary_render_widths[-1]
    primary_variant = _variant(pipeline, "primary")
    thumb_variant = _variant(pipeline, "thumb")
    body = f"""
<article
  class="page work"
  id="selectedWorkRoot"
  data-baseurl="{_baseurl(config)}"
  data-works-img-base="{escape(join_url(config.media['base'], config.media['image_works']), quote=True)}"
  data-works-files-base="{escape(join_url(config.media['base'], config.media['files_works']), quote=True)}"
  data-details-thumb-base="{escape(join_url(config.thumbs['base'], config.thumbs['work_details']), quote=True)}"
  data-primary-render-widths="{_json_attr(primary_render_widths)}"
  data-primary-display-width="{primary_display_width}"
  data-primary-full-width="{primary_variant.get('preferred_width', primary_display_width)}"
  data-primary-suffix="{escape(str(primary_variant.get('suffix', 'primary')), quote=True)}"
  data-detail-thumb-sizes="{_json_attr(_thumb_sizes(pipeline))}"
  data-detail-thumb-suffix="{escape(str(thumb_variant.get('suffix', 'thumb')), quote=True)}"
  data-asset-format="{escape(_asset_format(pipeline), quote=True)}"
  data-loading-text="{escape(config.runtime_text['loading'], quote=True)}"
  data-unavailable-text="{escape(config.runtime_text['unavailable'], quote=True)}"
  hidden
>
  <h1 class="visually-hidden" id="selectedWorkTitleHidden">{escape(config.runtime_text['loading'])}</h1>
  <figure class="page__media">
    <a class="page__mediaLink" id="selectedWorkMediaLink" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="selectedWorkImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>
  <section class="page__meta page__media">
    <h2 class="visually-hidden">work details</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="selectedWorkTitleText">{escape(config.runtime_text['loading'])}</span></span>
        <nav class="seriesNav seriesNav--title" id="seriesNav" aria-label="Series navigation" data-work-id="" data-series="" data-baseurl="{_baseurl(config)}" hidden>
          <span class="navCounter" id="seriesNavCounter" hidden></span>
          <a class="seriesNav__prev" id="seriesNavPrev" href="#">&larr;</a>
          <a class="seriesNav__next" id="seriesNavNext" href="#">&rarr;</a>
        </nav>
      </div>
      <div class="page__row" id="selectedWorkYearRow" hidden><span id="selectedWorkYearText"></span></div>
      <div class="page__row" id="selectedWorkMediumRow" hidden><span id="selectedWorkMediumText"></span></div>
      <div class="page__row" id="selectedWorkDimensionsRow" hidden><span id="selectedWorkDimensionsText"></span></div>
      <div class="page__row" id="selectedWorkCatRow">cat. <span id="selectedWorkCatText"></span> <span id="workSeriesLinkWrap" hidden>| <a id="workSeriesLink" class="work__seriesLink" href="/series/"></a></span></div>
      <div class="page__row" id="selectedWorkDownloadsRow" hidden><span id="selectedWorkDownloadsLabel"></span> <span id="selectedWorkDownloadsLinks"></span></div>
      <div class="page__row" id="selectedWorkLinksRow" hidden><span id="selectedWorkLinksLabel"></span> <span id="selectedWorkLinksLinks"></span></div>
    </div>
  </section>
  <section class="content work__prose" id="selectedWorkProseSection" hidden><div id="selectedWorkProseContent"></div></section>
  <section class="workDetails" id="selectedWorkDetailsSection" hidden><h2 class="visually-hidden">Additional details</h2><div id="selectedWorkDetailsContent"></div></section>
  <nav class="page__nav">
    <a id="pageBackLink" class="page__back" href="/series/" data-baseurl="{_baseurl(config)}" data-series-label="series">&larr; works</a>
  </nav>
</article>

<div class="index worksList" id="worksIndexRoot" hidden>
  <h1 class="index__heading visually-hidden">works</h1>
  <p class="worksList__count" id="worksListCount"></p>
  <div class="worksList__head" role="group" aria-label="Sort works">
    <button class="worksList__sortBtn" type="button" data-sort-key="cat">cat <span class="worksList__sortIcon" aria-hidden="true"></span></button>
    <button class="worksList__sortBtn" type="button" data-sort-key="year">year <span class="worksList__sortIcon" aria-hidden="true"></span></button>
    <button class="worksList__sortBtn" type="button" data-sort-key="title">title <span class="worksList__sortIcon" aria-hidden="true"></span></button>
    <button class="worksList__sortBtn" type="button" data-sort-key="series">series <span class="worksList__sortIcon" aria-hidden="true"></span></button>
  </div>
  <ul class="worksList__list" id="worksList"></ul>
  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a class="page__back" id="worksIndexBackLink" href="/series/">&larr; series</a>
  </nav>
</div>
<p id="worksEmpty" hidden>no works yet</p>

{script_tag('/assets/js/public-catalogue-runtime.js', config)}
{script_tag('/assets/js/work-page.js', config)}
{script_tag('/assets/js/work.js', config)}
{script_tag('/assets/js/works-index.js', config)}""".strip()
    return render_page(config, title="Works", body=body, path="/works/", section="works")


def render_work_details(config: PublicSiteConfig, pipeline: dict[str, Any]) -> str:
    primary_render_widths = _primary_render_widths(pipeline)
    primary_display_width = primary_render_widths[-1]
    primary_variant = _variant(pipeline, "primary")
    body = f"""
<article
  class="page work"
  id="detailPageRoot"
  data-baseurl="{_baseurl(config)}"
  data-img-base="{escape(join_url(config.media['base'], config.media['image_work_details']), quote=True)}"
  data-primary-render-widths="{_json_attr(primary_render_widths)}"
  data-primary-display-width="{primary_display_width}"
  data-primary-full-width="{primary_variant.get('preferred_width', primary_display_width)}"
  data-primary-suffix="{escape(str(primary_variant.get('suffix', 'primary')), quote=True)}"
  data-asset-format="{escape(_asset_format(pipeline), quote=True)}"
  data-loading-text="{escape(config.runtime_text['loading'], quote=True)}"
  data-unavailable-text="{escape(config.runtime_text['unavailable'], quote=True)}"
  hidden
>
  <h1 class="visually-hidden" id="detailHiddenTitle">{escape(config.runtime_text['loading'])}</h1>
  <figure class="page__media">
    <a class="page__mediaLink" id="detailMediaLink" data-swipe-nav-zone="detail-media" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="detailPrimaryImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>
  <section class="page__meta page__media">
    <h2 class="visually-hidden">work detail metadata</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="detailTitleText">{escape(config.runtime_text['loading'])}</span></span>
        <nav class="seriesNav seriesNav--title" id="detailNav" aria-label="Detail navigation" data-detail-uid="" data-work-id="" data-work-title="" data-baseurl="{_baseurl(config)}" data-default-section="" hidden>
          <span class="navCounter" id="detailTitleCounter" hidden></span>
          <a class="seriesNav__prev" id="detailNavPrev" href="#">&larr;</a>
          <a class="seriesNav__next" id="detailNavNext" href="#">&rarr;</a>
        </nav>
      </div>
      <div class="page__row">cat. <span id="detailCatText"></span></div>
    </div>
  </section>
  <nav class="page__nav"><a id="detailBackLink" class="page__back" href="/series/">&larr; work</a></nav>
</article>
<p id="detailPageEmpty" hidden>{escape(config.runtime_text['unavailable'])}</p>

{script_tag('/assets/js/swipe-nav.js', config)}
{script_tag('/assets/js/public-catalogue-runtime.js', config)}
{script_tag('/assets/js/work-detail-page.js', config)}
{script_tag('/assets/js/work.js', config)}""".strip()
    return render_page(config, title="Work Detail", body=body, path="/work-details/", section="works")


def render_moments(config: PublicSiteConfig, pipeline: dict[str, Any]) -> str:
    primary_render_widths = _primary_render_widths(pipeline)
    primary_display_width = primary_render_widths[-1]
    primary_variant = _variant(pipeline, "primary")
    body = f"""
<article
  class="page moment"
  id="momentPageRoot"
  data-baseurl="{_baseurl(config)}"
  data-img-base="{escape(join_url(config.media['base'], config.media['image_moments']), quote=True)}"
  data-primary-render-widths="{_json_attr(primary_render_widths)}"
  data-primary-display-width="{primary_display_width}"
  data-primary-suffix="{escape(str(primary_variant.get('suffix', 'primary')), quote=True)}"
  data-asset-format="{escape(_asset_format(pipeline), quote=True)}"
  data-loading-text="{escape(config.runtime_text['loading'], quote=True)}"
  data-unavailable-text="{escape(config.runtime_text['unavailable'], quote=True)}"
>
  <header class="page__header moment-header">
    <h1 class="page__title" id="momentTitleText">{escape(config.runtime_text['loading'])}</h1>
    <p class="page__meta muted small" id="momentDateText" hidden></p>
  </header>
  <figure class="page__media moment-hero" id="momentHero" hidden>
    <img class="page__mediaImg" id="momentHeroImg" width="1600" height="1200" alt="" loading="eager" fetchpriority="high" decoding="async">
    <figcaption id="momentHeroCaption" hidden></figcaption>
  </figure>
  <div class="content moment-body" id="momentBody"></div>
  <nav class="page__nav moment__nav" id="momentBackNav" hidden>
    <a id="momentBackLink" class="page__back" href="/series/?mode=moments" aria-label="Back to moments">&larr;</a>
  </nav>
</article>
{script_tag('/assets/js/public-catalogue-runtime.js', config)}
{script_tag('/assets/js/moment.js', config)}""".strip()
    return render_page(config, title="moments", body=body, path="/moments/", section="series")


def render_catalogue_search(config: PublicSiteConfig) -> str:
    body = f"""
<div class="studioSearch" id="studioSearchRoot" data-baseurl="{_baseurl(config)}" hidden>
  <div class="studioSearch__header">
    <a class="studioSearch__backLink" id="studioSearchBackLink" href="/series/">&larr; works</a>
    <p class="studioSearch__scope" id="studioSearchScope">catalogue</p>
  </div>
  <label class="visually-hidden" for="studioSearchInput">search</label>
  <div class="studioSearch__controls">
    <input class="studioSearch__input" id="studioSearchInput" type="search" autocomplete="off" spellcheck="false">
  </div>
  <p class="studioSearch__status" id="studioSearchStatus">loading search index...</p>
  <details class="studioSearch__performance" id="studioSearchPerformance" hidden>
    <summary class="studioSearch__performanceSummary" id="studioSearchPerformanceSummary">Search performance</summary>
    <pre class="studioSearch__performanceReport" id="studioSearchPerformanceReport"></pre>
  </details>
  <ol class="studioSearch__results" id="studioSearchResults"></ol>
  <div class="studioSearch__more" id="studioSearchMore"></div>
</div>

{script_tag('/assets/js/catalogue-search.js', config, module=True)}""".strip()
    return render_page(config, title="Catalogue Search", body=body, path="/catalogue/search/", section="catalogue")


def _variant(pipeline: dict[str, Any], name: str) -> dict[str, Any]:
    value = pipeline.get("variants", {}).get(name, {})
    return value if isinstance(value, dict) else {}


def _primary_render_widths(pipeline: dict[str, Any]) -> list[int]:
    compatibility = _variant(pipeline, "compatibility")
    primary = _variant(pipeline, "primary")
    widths = compatibility.get("render_widths") or primary.get("widths") or [800, 1200, 1600]
    return [int(width) for width in widths]


def _thumb_sizes(pipeline: dict[str, Any]) -> list[int]:
    sizes = _variant(pipeline, "thumb").get("sizes") or [96, 192]
    return [int(size) for size in sizes]


def _asset_format(pipeline: dict[str, Any]) -> str:
    return str(pipeline.get("encoding", {}).get("format", "webp"))


def _json_attr(value: Any) -> str:
    return escape(json.dumps(value), quote=True)


def _baseurl(config: PublicSiteConfig) -> str:
    return escape(config.site.get("baseurl", ""), quote=True)
