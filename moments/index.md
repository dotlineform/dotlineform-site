---
layout: default
title: "moments"
permalink: /moments/
section: series
---

{% assign media_base = site.media_base | default: "" %}
{% assign media_image_moments = site.media_image_moments | default: "/moments/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign img_base = media_base | append: media_image_moments | append: "/" %}
{% assign img_base_out = img_base %}
{% unless img_base contains '://' %}
  {% assign img_base_out = img_base | relative_url %}
{% endunless %}
{% assign public_text = site.public_runtime_text | default: nil %}
{% assign loading_text = public_text.loading | default: "loading..." %}
{% assign unavailable_text = public_text.unavailable | default: "info not available" %}

<article
  class="page moment"
  id="momentPageRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-img-base="{{ img_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-loading-text="{{ loading_text | escape }}"
  data-unavailable-text="{{ unavailable_text | escape }}"
>
  <header class="page__header moment-header">
    <h1 class="page__title" id="momentTitleText">{{ loading_text }}</h1>

    <p class="page__meta muted small" id="momentDateText" hidden></p>
  </header>

  <figure class="page__media moment-hero" id="momentHero" hidden>
    <img class="page__mediaImg" id="momentHeroImg"
         width="1600"
         height="1200"
         alt=""
         loading="eager" fetchpriority="high" decoding="async">
    <figcaption id="momentHeroCaption" hidden></figcaption>
  </figure>

  <div class="content moment-body" id="momentBody"></div>
  <nav class="page__nav moment__nav" id="momentBackNav" hidden>
    <a id="momentBackLink" class="page__back" href="{{ '/series/?mode=moments' | relative_url }}" aria-label="Back to moments">←</a>
  </nav>
</article>
<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/moment.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
