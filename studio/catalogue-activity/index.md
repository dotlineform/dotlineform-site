---
layout: studio
title: Catalogue Activity
permalink: /studio/catalogue-activity/
section: catalogue-activity
studio_page_doc: /docs/?scope=studio&doc=catalogue-activity
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage buildActivityPage catalogueActivityPage" id="catalogueActivityRoot" hidden>
  <div class="tagStudio__panel buildActivityPage__panel">
    <p class="buildActivityPage__meta" id="catalogueActivityMeta"></p>
    <div id="catalogueActivityList"></div>
  </div>
</div>

<p class="buildActivityPage__status" id="catalogueActivityStatus">loading catalogue activity…</p>
<p class="buildActivityPage__empty" id="catalogueActivityEmpty" hidden>No catalogue activity yet.</p>

<script type="module" src="{{ '/assets/studio/js/catalogue-activity.js' | relative_url }}"></script>
