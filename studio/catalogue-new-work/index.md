---
layout: studio
title: "New Catalogue Work"
permalink: /studio/catalogue-new-work/
section: catalogue-new-work
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-editor
---

{% assign catalogue_work_new_url = '/studio/catalogue-work/' | relative_url | append: '?mode=new' %}

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">
<meta http-equiv="refresh" content="0; url={{ catalogue_work_new_url }}">
<script>
  window.location.replace("{{ catalogue_work_new_url }}");
</script>

<p class="tagStudio__status">
  New work creation has moved to the <a href="{{ catalogue_work_new_url }}">Catalogue Work Editor</a>.
</p>
