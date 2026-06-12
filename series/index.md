---
layout: default
title: "works"
section: series
permalink: /series/
---

<h1 class="index__heading visually-hidden">works</h1>
{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_works = site.thumb_works | default: "/assets/works/img" %}
{% assign thumb_moments = site.thumb_moments | default: "/assets/moments/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign thumb_sizes = thumb_variants.sizes | default: "96,192" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign thumb_works_base = thumb_base | append: thumb_works | append: "/" %}
{% assign thumb_moments_base = thumb_base | append: thumb_moments | append: "/" %}
{%- assign thumb_works_base_out = thumb_works_base -%}
{%- assign thumb_moments_base_out = thumb_moments_base -%}
{%- unless thumb_works_base contains '://' -%}
  {%- assign thumb_works_base_out = thumb_works_base | relative_url -%}
{%- endunless -%}
{%- unless thumb_moments_base contains '://' -%}
  {%- assign thumb_moments_base_out = thumb_moments_base | relative_url -%}
{%- endunless -%}

<div
  id="seriesIndexRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-thumb-works-base="{{ thumb_works_base_out | escape }}"
  data-thumb-moments-base="{{ thumb_moments_base_out | escape }}"
  data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}"
  data-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  hidden
>
  <div class="seriesIndex__toolbar" aria-label="Works and moments view and sorting">
    <div class="seriesIndex__toolbarPrimary">
      <div class="seriesIndex__viewControls" role="group" aria-label="View">
        <button
          class="theme-toggle seriesIndex__viewBtn"
          type="button"
          data-role="catalog-index-view-btn"
          data-view="list"
          aria-label="Show list view"
          aria-pressed="true"
        >
          <svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="4" y="5" width="2.5" height="2.5" rx="1"></rect>
            <rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect>
            <rect x="4" y="16.5" width="2.5" height="2.5" rx="1"></rect>
            <path d="M10 6.25H20"></path>
            <path d="M10 12H20"></path>
            <path d="M10 17.75H20"></path>
          </svg>
          <span class="sr-only">list</span>
        </button>
        <button
          class="theme-toggle seriesIndex__viewBtn"
          type="button"
          data-role="catalog-index-view-btn"
          data-view="grid"
          aria-label="Show grid view"
          aria-pressed="false"
        >
          <svg class="seriesIndex__viewIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <rect x="4" y="4" width="6.25" height="6.25" rx="1.5"></rect>
            <rect x="13.75" y="4" width="6.25" height="6.25" rx="1.5"></rect>
            <rect x="4" y="13.75" width="6.25" height="6.25" rx="1.5"></rect>
            <rect x="13.75" y="13.75" width="6.25" height="6.25" rx="1.5"></rect>
          </svg>
          <span class="sr-only">grid</span>
        </button>
      </div>
      <div class="seriesIndex__sortControls" role="group" aria-label="Sort">
        <button
          class="theme-toggle seriesIndex__sortBtn"
          type="button"
          data-role="catalog-index-sort-btn"
          data-sort-key="year"
          aria-pressed="true"
        >
          <span class="seriesIndex__sortText">year</span>
          <span class="seriesIndex__sortArrow" aria-hidden="true">↓</span>
        </button>
        <button
          class="theme-toggle seriesIndex__sortBtn"
          type="button"
          data-role="catalog-index-sort-btn"
          data-sort-key="title"
          aria-pressed="false"
        >
          <span class="seriesIndex__sortText">title</span>
          <span class="seriesIndex__sortArrow" aria-hidden="true">↑</span>
        </button>
      </div>
    </div>
    <div class="seriesIndex__toolbarMiddle">
      <a
        id="seriesIndexRecentBtn"
        class="theme-toggle seriesIndex__recentBtn"
        data-enabled-href="{{ '/recent/' | relative_url }}"
        href="{{ '/recent/' | relative_url }}"
      >recently added</a>
    </div>
    <div class="seriesIndex__toolbarSecondary">
      <div class="seriesIndex__modeControls" role="group" aria-label="Browse works or moments">
        <button
          class="theme-toggle seriesIndex__modeBtn"
          type="button"
          data-role="catalog-index-mode-btn"
          data-mode="works"
          aria-pressed="true"
        >
          <span class="seriesIndex__modeText">works</span>
        </button>
        <button
          class="theme-toggle seriesIndex__modeBtn"
          type="button"
          data-role="catalog-index-mode-btn"
          data-mode="moments"
          aria-pressed="false"
        >
          <span class="seriesIndex__modeText">moments</span>
        </button>
      </div>
      <a
        class="theme-toggle seriesIndex__searchBtn"
        href="{{ '/catalogue/search/' | relative_url }}"
        aria-label="Search the catalogue"
      >
        <svg class="seriesIndex__searchIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <circle cx="11" cy="11" r="6.5"></circle>
          <path d="M16 16L20 20"></path>
        </svg>
        <span class="sr-only">search</span>
      </a>
    </div>
  </div>
  <div class="index seriesIndex__list" id="seriesIndexList" aria-live="polite"></div>
  <div class="seriesGrid seriesIndex__grid" id="seriesIndexThumbGrid" aria-live="polite" hidden></div>
  <nav class="gridPager seriesIndex__pager" id="seriesIndexPager" aria-label="catalog index pagination" hidden>
    <span class="gridPager__status" id="seriesIndexPagerStatus"></span>
    <button class="gridPager__btn" type="button" id="seriesIndexPrev" aria-label="Previous page">←</button>
    <button class="gridPager__btn" type="button" id="seriesIndexNext" aria-label="Next page">→</button>
  </nav>
</div>
<p id="seriesIndexEmpty" hidden>no works yet</p>

<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/series-index.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
