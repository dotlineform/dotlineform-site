---
layout: default
title: Works
permalink: /works/
section: works
---

<!-- when the cataloguing is complete, use 'recent work' and sort by work.date -->

{% assign works_items = site.works %}
{% if works_items and works_items != empty %}
  {% assign sorted_works = works_items | sort: 'catalogue_date' | reverse %}
<div class="index">
  <h1 class="index__heading">recently added work</h1>
  {% for work in sorted_works %}
  {% if work.published == false %}{% continue %}{% endif %}
  <div class="index__item">
    <span class="index__date">{% if work.catalogue_date %}{{ work.catalogue_date | date: "%-d %b %Y" }}{% endif %}</span>
    <a class="index__link" href="{{ work.url | relative_url }}">{{ work.title | default: work.slug }}</a>
  </div>
  {% endfor %}
</div>
{% else %}
  <p>No works yet.</p>
{% endif %}
