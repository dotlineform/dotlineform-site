---
layout: default
title: Moments
permalink: /moments/
---

<h1 class="visually-hidden">Moments</h1>

{% assign sorted_moments = site.moments | sort: 'date' | reverse %}
<div class="moments-index">

{% for moment in sorted_moments %}
{% if moment.published == false %}{% continue %}{% endif %}
<div class="moments-index-item">
  <span class="moments-index-date">
    {% if moment.date_display %}
      {{ moment.date_display }}
    {% else %}
      {{ moment.date | date: "%-d %b %Y" }}
    {% endif %}
  </span>

  <a class="moments-index-link" href="{{ moment.url | relative_url }}">
    {{ moment.title | default: moment.slug }}
  </a>
</div>
{% endfor %}
</div>