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
    <p class="libraryExportPage__intro" id="libraryExportIntro"></p>

    <div class="libraryExportPage__controls">
      <label class="tagStudioField tagStudioField--inline libraryExportPage__field">
        <span class="tagStudioField__label" id="libraryExportConfigLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="libraryExportConfigSelect"></select>
        </span>
      </label>
      <label class="libraryExportPage__toggle" id="libraryExportMissingSummaryWrap" hidden>
        <input type="checkbox" id="libraryExportMissingSummaryOnly">
        <span id="libraryExportMissingSummaryLabel"></span>
      </label>
    </div>

    <div class="libraryExportPage__actions" aria-label="Library export document selection actions">
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryExportSelectAll"></button>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryExportClear"></button>
    </div>

    <p class="tagStudio__status" id="libraryExportStatus"></p>
    <p class="tagStudioForm__meta libraryExportPage__selectionSummary" id="libraryExportSelectionSummary"></p>

    <div class="tagStudioList libraryExportList" id="libraryExportList"></div>

    <div class="libraryExportPage__actions libraryExportPage__run">
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryExportRun" disabled></button>
    </div>
  </div>
</div>

<p class="tagStudio__status" id="libraryExportBootStatus">loading Library export…</p>

<script type="module" src="{{ '/assets/studio/js/library-export.js' | relative_url }}"></script>
