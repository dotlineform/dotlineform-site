---
layout: studio
title: "Library Export"
permalink: /studio/library-export/
section: library-export
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=library-export
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage libraryExportPage"
  id="libraryExportRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel libraryExportPage__panel">
    <div class="libraryExportPage__controls">
      <label class="tagStudioField libraryExportPage__field" for="libraryExportConfigSelect">
        <span class="tagStudioField__label" id="libraryExportConfigLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="libraryExportConfigSelect"></select>
        </span>
      </label>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryExportRun"></button>
      <label class="libraryExportPage__toggle" id="libraryExportMissingSummaryWrap" hidden>
        <input type="checkbox" id="libraryExportMissingSummaryOnly">
        <span id="libraryExportMissingSummaryLabel"></span>
      </label>
    </div>

    <p class="tagStudio__status" id="libraryExportStatus"></p>
    <p class="tagStudioForm__meta libraryExportPage__selectionSummary" id="libraryExportSelectionSummary"></p>

    <div class="libraryExportPage__listActions" aria-label="Library export document selection actions">
      <span class="libraryExportPage__filterPills" id="libraryExportListFilters" aria-label="Library export list filters"></span>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryExportSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryExportClear"></button>
    </div>

    <div class="tagStudioList libraryExportList" id="libraryExportList"></div>
    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="libraryExportBootStatus">loading Library export…</p>

<script type="module" src="{{ '/assets/studio/js/library-export.js' | relative_url }}"></script>
