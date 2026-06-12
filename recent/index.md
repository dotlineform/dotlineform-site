---
layout: default
title: "recently added"
permalink: /recent/
section: works
---

{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_works = site.thumb_works | default: "/assets/works/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign thumb_sizes = thumb_variants.sizes | default: "96,192" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign thumb_works_base = thumb_base | append: thumb_works | append: "/" %}
{%- assign thumb_works_base_out = thumb_works_base -%}
{%- unless thumb_works_base contains '://' -%}
  {%- assign thumb_works_base_out = thumb_works_base | relative_url -%}
{%- endunless -%}

<div
  class="index recentIndex"
  id="recentIndexRoot"
  data-baseurl="{{ site.baseurl | default: '' }}"
  data-thumb-works-base="{{ thumb_works_base_out | escape }}"
  data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}"
  data-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  hidden
>
  <h1 class="index__heading">recently added</h1>
  <ul class="recentIndex__list" id="recentIndexList"></ul>
  <nav class="page__nav">
    <a class="page__back" href="{{ '/series/' | relative_url }}">← works</a>
  </nav>
</div>
<p id="recentIndexEmpty" hidden>nothing recently added yet</p>

<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script src="{{ '/assets/js/recent-index.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
