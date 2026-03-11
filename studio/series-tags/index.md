---
layout: studio
title: Series Tags
permalink: /studio/series-tags/
studio_page_doc: /docs/studio/pages/series-tags/
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="seriesTagsPage">
  <div class="tagStudio__panel">
    <section class="tagStudioToolbar seriesTagsSession" data-role="series-tags-session">
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="series-tags-session-summary"></div>
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="series-tags-session-actions"></div>
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="series-tags-session-import"></div>
      <div class="seriesTagsSession__review" data-role="series-tags-session-review"></div>
      <p class="tagStudioToolbar__result" data-role="series-tags-session-result"></p>
    </section>
    <div id="series-tags" data-role="series-tags"></div>
  </div>
</div>

<script type="module" src="{{ '/assets/studio/js/series-tags.js' | relative_url }}"></script>
