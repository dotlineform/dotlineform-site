---
layout: default
title: Works
permalink: /works/
section: works
---

{% assign works_items = site.works %}
{% if works_items and works_items != empty %}

  {% assign random_works = works_items | sample: 6 %}

  <div class="index">
    <h1 class="index__heading">selected</h1>

    {% for w in random_works %}
      {% include work_index_item.html work=w %}
    {% endfor %}
  </div>

{% else %}
  <p>no works yet</p>
{% endif %}
