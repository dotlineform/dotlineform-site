---
layout: default
title: "Work Detail"
permalink: /work-details/
section: works
---

{% assign public_text = site.public_runtime_text | default: nil %}
{% assign loading_text = public_text.loading | default: "loading..." %}
{% assign unavailable_text = public_text.unavailable | default: "info not available" %}
{% assign media_base = site.media_base | default: "" %}
{% assign media_image_work_details = site.media_image_work_details | default: "/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_display_width %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign img_base = media_base | append: media_image_work_details | append: "/" %}
{% assign img_base_out = img_base %}
{% unless img_base contains '://' %}
  {% assign img_base_out = img_base | relative_url %}
{% endunless %}

<article
  class="page work"
  id="detailPageRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-img-base="{{ img_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-loading-text="{{ loading_text | escape }}"
  data-unavailable-text="{{ unavailable_text | escape }}"
  hidden
>
  <h1 class="visually-hidden" id="detailHiddenTitle">{{ loading_text }}</h1>

  <figure class="page__media">
    <a class="page__mediaLink" id="detailMediaLink" data-swipe-nav-zone="detail-media" target="_blank" rel="noopener" style="--work-ar: 4 / 3;">
      <img class="page__mediaImg" id="detailPrimaryImg" sizes="(max-width: 800px) 100vw, 72ch" alt="" loading="eager" fetchpriority="high" decoding="async" style="width:100%;height:auto;display:block;">
    </a>
  </figure>

  <section class="page__meta page__media">
    <h2 class="visually-hidden">work detail metadata</h2>
    <div class="page__caption page__metaList">
      <div class="page__row work__titleRow">
        <span class="work__titleMain"><span id="detailTitleText">{{ loading_text }}</span></span>
        <nav class="seriesNav seriesNav--title" id="detailNav" aria-label="Detail navigation" data-detail-uid="" data-work-id="" data-work-title="" data-baseurl="{{ site.baseurl | default: '' }}" data-default-section="" hidden>
          <span class="navCounter" id="detailTitleCounter" hidden></span>
          <a class="seriesNav__prev" id="detailNavPrev" href="#">←</a>
          <a class="seriesNav__next" id="detailNavNext" href="#">→</a>
        </nav>
      </div>
      <div class="page__row">cat. <span id="detailCatText"></span></div>
    </div>
  </section>

  <nav class="page__nav">
    <a id="detailBackLink" class="page__back" href="{{ '/series/' | relative_url }}">← work</a>
  </nav>
</article>

<p id="detailPageEmpty" hidden>{{ unavailable_text }}</p>

<script src="{{ '/assets/js/swipe-nav.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/work-detail-page.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/work.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
