---
layout: studio
title: "Series Tags"
permalink: /studio/analytics/series-tags/
studio_domain: analytics
studio_page_doc: /docs/?scope=studio&doc=series-tags
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="seriesTagsPage">
  <div class="seriesTagsActions" data-role="series-tags-actions">
    <button type="button" class="tagStudio__button" data-role="open-session-modal"></button>
    <button type="button" class="tagStudio__button" data-role="open-import-modal"></button>
  </div>
  <div data-role="series-tags-session-modal-host"></div>
  <div data-role="series-tags-import-modal-host"></div>
  <div class="tagStudio__panel">
    <div id="series-tags" data-role="series-tags" data-studio-ready="false" data-studio-busy="false"></div>
  </div>
</div>

<script type="module" src="{{ '/assets/studio/js/series-tags.js' | relative_url }}"></script>
