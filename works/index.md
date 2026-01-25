---
layout: default
title: Works
permalink: /works/
section: works
---

<h1 class="visually-hidden">Works</h1>

<h2>Recently added work</h2>

{% assign works_items = site.works %}
{% if works_items and works_items != empty %}
  {% assign sorted_works = works_items | sort: 'catalogue_date' | reverse %}
<div class="works-index">

{% for work in sorted_works %}
{% if work.published == false %}{% continue %}{% endif %}
<div class="works-index-item">
  <span class="works-index-date">{% if work.catalogue_date %}{{ work.catalogue_date | date: "%-d %b %Y" }}{% endif %}</span>
  <a class="works-index-link" href="{{ work.url | relative_url }}">{{ work.title | default: work.slug }}</a>
</div>
{% endfor %}
</div>
{% else %}
  <p>No works yet.</p>
{% endif %}
