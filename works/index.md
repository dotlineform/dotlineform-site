---
layout: default
title: Works
permalink: /works/
---

<h1 class="visually-hidden">Works</h1>

{% assign sorted_works = site.works | sort: 'date' | reverse %}
<div class="works-index">

{% for work in sorted_works %}
{% if work.published == false %}{% continue %}{% endif %}
<div class="works-index-item">
  <span class="works-index-date">{{ work.date | date: "%-d %b %Y" }}</span>
  <a class="works-index-link" href="{{ work.url | relative_url }}">{{ work.title | default: work.slug }}</a>
</div>
{% endfor %}
</div>

<p><a href="/works/">Browse all works</a></p>