---
layout: default
title: Moments
section: moments
permalink: /moments/
---

<h1 class="index__heading">moments</h1>

{% assign moments_items = site.moments %}

{% if moments_items and moments_items != empty %}
  {% assign sorted_moments = moments_items | sort: 'date' | reverse %}
  <div class="index">

{% for moment in sorted_moments %}
{% if moment.published == false %}{% continue %}{% endif %}
<div class="index__item">
  <span class="index__date">
    {% if moment.date_display %}
      {{ moment.date_display }}
    {% else %}
      {{ moment.date | date: "%-d %b %Y" }}
    {% endif %}
  </span>

  <a class="index__link" href="{{ moment.url | relative_url }}">
    {{ moment.title | default: moment.slug }}
  </a>
</div>
{% endfor %}
</div>
{% else %}
  <p>No moments yet.</p>
{% endif %}