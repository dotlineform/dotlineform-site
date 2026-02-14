---
layout: default
title: works
section: series
permalink: /series/
---

{% assign series = site.series %}
{% if series and series != empty %}
  {% assign sorted_series = series | sort: 'year' | reverse %}
  <div class="index">
    <h1 class="index__heading visually-hidden">works</h1>
    {% for s in sorted_series %}
      {% include series_index_item.html series=s %}
    {% endfor %}
  </div>
{% else %}
  <p>no series yet</p>
{% endif %}
