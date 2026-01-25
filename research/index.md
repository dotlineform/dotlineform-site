---
layout: default
title: Research
permalink: /research/
---

<h1 class="visually-hidden">Notes</h1>

{% assign sorted_notes = site.research | sort: 'date' | reverse %}
<div class="research-index">

{% for research-note in sorted_notes %}
{% if note.published == false %}{% continue %}{% endif %}
<div class="research-index-item">
  <span class="research-index-date">{{ research-note.date | date: "%-d %b %Y" }}</span>
  <a class="research-index-link" href="{{ note.url | relative_url }}">{{ research-note.title | default: research-note.slug }}</a>
</div>
{% endfor %}
</div>