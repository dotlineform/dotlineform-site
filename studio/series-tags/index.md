---
layout: studio
title: Series Tags
permalink: /studio/series-tags/
---

<link rel="stylesheet" href="{{ '/assets/css/studio.css' | relative_url }}">

{% assign studio_series_docs = site.studio_series | sort_natural: "title" %}

<div class="seriesTagsPage">
  <div class="tagStudio__panel">
    <div id="series-tags"></div>
  </div>
</div>

<script type="application/json" id="series-tags-series-data">
[
{%- for s in studio_series_docs -%}
  {
    "series_id": {{ s.series_id | default: s.slug | jsonify }},
    "title": {{ s.title | default: s.series_id | default: s.slug | jsonify }},
    "url": {{ s.url | relative_url | jsonify }}
  }{% unless forloop.last %},{% endunless %}
{%- endfor -%}
]
</script>

<script type="module" src="{{ '/assets/js/series-tags.js' | relative_url }}"></script>
