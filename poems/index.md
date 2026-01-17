---
layout: default
title: Poems
permalink: /poems/
---

<h1 class="visually-hidden">Notes</h1>

<!-- reuses note classes - can introduce parallel classes later -->
{% assign sorted_poems = site.poems | sort: 'date' | reverse %}
<div class="note-index">

{% for poem in sorted_poems %}
{% if note.published == false %}{% continue %}{% endif %}
<div class="note-index-item">
  <span class="note-index-date">{{ poem.date | date: "%-d %b %Y" }}</span>
  <a class="note-index-link" href="{{ poem.url | relative_url }}">{{ poem.title | default: poem.slug }}</a>
</div>
{% endfor %}
</div>