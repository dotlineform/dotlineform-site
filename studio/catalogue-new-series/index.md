---
layout: studio
title: "New Catalogue Series"
permalink: /studio/catalogue-new-series/
section: catalogue-new-series
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-series-editor
---

{% assign catalogue_series_new_url = '/studio/catalogue-series/' | relative_url | append: '?mode=new' %}

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">
<meta http-equiv="refresh" content="0; url={{ catalogue_series_new_url }}">
<script>
  window.location.replace("{{ catalogue_series_new_url }}");
</script>

<p class="tagStudio__status">
  New series creation has moved to the <a href="{{ catalogue_series_new_url }}">Catalogue Series Editor</a>.
</p>
