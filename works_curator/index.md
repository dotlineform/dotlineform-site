---
layout: default
title: Works Curator Index
permalink: /works_curator/
section: works
---

{% assign curator_items = site.works_curator | sort_natural: "work_id" %}

<h1>works curator index</h1>

{% if curator_items and curator_items != empty %}
<ul>
  {% for w in curator_items %}
  <li>
    <a href="{{ w.url | relative_url }}">{{ w.work_id }}</a>
    {% if w.title %} — {{ w.title }}{% endif %}
  </li>
  {% endfor %}
</ul>
{% else %}
<p>no curator pages yet</p>
{% endif %}

