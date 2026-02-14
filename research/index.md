---
layout: default
title: Research
section: research
permalink: /research/
---

{% assign research_items = site.research | where_exp: "n", "n.published != false" %}
{% if research_items and research_items != empty %}
  {% assign sorted_research = research_items | sort: 'date' | reverse %}
  <div class="index">
    <h1 class="index__heading visually-hidden">research notes</h1>
    {% for note in sorted_research %}
      {% include research_index_item.html note=note %}
    {% endfor %}
  </div>
{% else %}
  <p>no research notes yet</p>
{% endif %}
