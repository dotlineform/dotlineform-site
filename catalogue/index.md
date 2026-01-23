---
layout: default
title: Catalogue
permalink: /catalogue/
---
<!-- Initial behaviour: list catalogue notes.

Implementation (Liquid loop) conceptually:
	•	Loop over site.catalogue_notes
	•	Sort by date or a front matter order
	•	Render each as a card/list item linking to the note page. -->

<ul>
  {% assign notes = site.catalogue_notes | sort: 'date' | reverse %}
  {% for n in notes %}
    <li>
      <a href="{{ n.url }}">{{ n.title }}</a>
      {% if n.description_short %}<div>{{ n.description_short }}</div>{% endif %}
    </li>
  {% endfor %}
</ul>

<p><a href="/catalogue/works/">Browse all works</a></p>