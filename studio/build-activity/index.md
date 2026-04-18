---
layout: studio
title: Build Activity
permalink: /studio/build-activity/
section: build-activity
studio_page_doc: /docs/?scope=studio&doc=build-activity
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage buildActivityPage" id="buildActivityRoot" hidden>
  <div class="tagStudio__panel buildActivityPage__panel">
    <p class="buildActivityPage__meta" id="buildActivityMeta"></p>
    <div id="buildActivityList"></div>
  </div>
</div>

<p class="buildActivityPage__status" id="buildActivityStatus">loading build activity…</p>
<p class="buildActivityPage__empty" id="buildActivityEmpty" hidden>No build activity yet.</p>

<script type="module" src="{{ '/assets/studio/js/build-activity.js' | relative_url }}"></script>
