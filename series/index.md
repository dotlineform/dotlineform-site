---
layout: default
title: Series
section: series
permalink: /series/
---

{% assign series = site.series %}
{% if series and series != empty %}
  {% assign sorted_series = series | sort: 'year' | reverse %}
  <div class="index">
    <h1 class="index__heading">series</h1>
    {% for s in sorted_series %}
      <div class="index__item">
        <span class="index__date">
          {% if s.year_display %}{{ s.year_display }}{% elsif s.year %}{{ s.year }}{% endif %}
        </span>
        <a class="index__link" href="{{ s.url | relative_url }}">{{ s.title | default: s.series_id }}</a>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>no series yet</p>
{% endif %}