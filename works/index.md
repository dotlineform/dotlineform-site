---
layout: default
title: "Works"
permalink: /works/
section: works
---

{% assign public_text = site.public_runtime_text | default: nil %}
{% assign loading_text = public_text.loading | default: "loading..." %}
{% assign unavailable_text = public_text.unavailable | default: "info not available" %}
{% assign media_base = site.media_base | default: "" %}
{% assign media_image_works = site.media_image_works | default: "/works/img" %}
{% assign media_files_works = site.media_files_works | default: "/assets/works/files" %}
{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_work_details = site.thumb_work_details | default: "/assets/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_display_width %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign works_img_base = media_base | append: media_image_works | append: "/" %}
{% assign works_files_base = media_base | append: media_files_works | append: "/" %}
{% assign details_thumb_base = thumb_base | append: thumb_work_details | append: "/" %}
{% assign works_img_base_out = works_img_base %}
{% assign works_files_base_out = works_files_base %}
{% assign details_thumb_base_out = details_thumb_base %}
{% unless works_img_base contains '://' %}
  {% assign works_img_base_out = works_img_base | relative_url %}
{% endunless %}
{% unless works_files_base contains '://' %}
  {% assign works_files_base_out = works_files_base | relative_url %}
{% endunless %}
{% unless details_thumb_base contains '://' %}
  {% assign details_thumb_base_out = details_thumb_base | relative_url %}
{% endunless %}

<article
  class="page work"
  id="selectedWorkRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-works-img-base="{{ works_img_base_out | escape }}"
  data-works-files-base="{{ works_files_base_out | escape }}"
  data-details-thumb-base="{{ details_thumb_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-detail-thumb-sizes="{{ thumb_variants.sizes | default: '96,192' | jsonify | escape }}"
  data-detail-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-loading-text="{{ loading_text | escape }}"
  data-unavailable-text="{{ unavailable_text | escape }}"
  hidden
>
  <h1 class="visually-hidden" id="selectedWorkTitleHidden">{{ loading_text }}</h1>
  <figure class="page__media">
    <a class="page__mediaLink" id="selectedWorkMediaLink" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="selectedWorkImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>
  <section class="page__meta page__media">
    <h2 class="visually-hidden">work details</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="selectedWorkTitleText">{{ loading_text }}</span></span>
        <nav class="seriesNav seriesNav--title" id="seriesNav" aria-label="Series navigation" data-work-id="" data-series="" data-baseurl="{{ site.baseurl | default: '' }}" hidden>
          <span class="navCounter" id="seriesNavCounter" hidden></span>
          <a class="seriesNav__prev" id="seriesNavPrev" href="#">←</a>
          <a class="seriesNav__next" id="seriesNavNext" href="#">→</a>
        </nav>
      </div>
      <div class="page__row" id="selectedWorkYearRow" hidden><span id="selectedWorkYearText"></span></div>
      <div class="page__row" id="selectedWorkMediumRow" hidden><span id="selectedWorkMediumText"></span></div>
      <div class="page__row" id="selectedWorkDimensionsRow" hidden><span id="selectedWorkDimensionsText"></span></div>
      <div class="page__row" id="selectedWorkCatRow">cat. <span id="selectedWorkCatText"></span> <span id="workSeriesLinkWrap" hidden>| <a id="workSeriesLink" class="work__seriesLink" href="{{ '/series/' | relative_url }}"></a></span></div>
      <div class="page__row" id="selectedWorkDownloadsRow" hidden><span id="selectedWorkDownloadsLabel"></span> <span id="selectedWorkDownloadsLinks"></span></div>
      <div class="page__row" id="selectedWorkLinksRow" hidden><span id="selectedWorkLinksLabel"></span> <span id="selectedWorkLinksLinks"></span></div>
    </div>
  </section>
  <section class="content work__prose" id="selectedWorkProseSection" hidden>
    <div id="selectedWorkProseContent"></div>
  </section>
  <section class="workDetails" id="selectedWorkDetailsSection" hidden>
    <h2 class="visually-hidden">Additional details</h2>
    <div id="selectedWorkDetailsContent"></div>
  </section>
  <nav class="page__nav">
    <a id="pageBackLink" class="page__back" href="{{ '/series/' | relative_url }}" data-baseurl="{{ site.baseurl | default: '' }}" data-series-label="series">← works</a>
  </nav>
</article>

<div class="index worksList" id="worksIndexRoot" hidden>
  <h1 class="index__heading visually-hidden">works</h1>
  <p class="worksList__count" id="worksListCount"></p>

  <div class="worksList__head" role="group" aria-label="Sort works">
    <button class="worksList__sortBtn" type="button" data-sort-key="cat">
      cat <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="year">
      year <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="title">
      title <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="series">
      series <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
  </div>

  <ul class="worksList__list" id="worksList"></ul>

  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a
      class="page__back"
      id="worksIndexBackLink"
      href="{{ '/series/' | relative_url }}"
    >← series</a>
  </nav>
</div>
<p id="worksEmpty" hidden>no works yet</p>

<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/work-page.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/work.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/works-index.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
