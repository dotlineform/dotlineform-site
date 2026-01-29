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
    {% for theme in sorted_series %}
      <div class="index__item">
        <span class="index__date">{% if series.year_display %}{{ series.year_display }}{% endif %}</span>
        <a class="index__link" href="{{ series.url | relative_url }}">{{ series.title | default: series.slug }}</a>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>no series yet</p>
{% endif %}