---
layout: default
title: Themes
section: themes
permalink: /themes/
---

{% assign theme_items = site.themes | where_exp: "t", "t.published != false" %}
{% if theme_items and theme_items != empty %}
  {% assign sorted_themes = theme_items | sort: 'date' | reverse %}
  <div class="index">
    <h1 class="index__heading">themes</h1>
    {% for theme in sorted_themes %}
      <div class="index__item">
        <span class="index__date">{% if theme.date %}{{ theme.date | date: "%-d %b %Y" }}{% endif %}</span>
        <a class="index__link" href="{{ theme.url | relative_url }}">{{ theme.title | default: theme.slug }}</a>
      </div>
    {% endfor %}
  </div>
{% else %}
  <p>no themes yet</p>
{% endif %}
