---
layout: studio
title: "Data Export"
permalink: /studio/export/
section: data-export
studio_domain: data
studio_page_doc: /docs/?scope=studio&doc=studio-data-export
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage dataExportPage"
  id="dataExportRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel dataExportPage__panel">
    <div class="dataExportPage__controls">
      <label class="tagStudioField dataExportPage__scopeField" for="dataExportScopeSelect">
        <span class="tagStudioField__label" id="dataExportScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataExportScopeSelect"></select>
        </span>
      </label>
      <label class="tagStudioField dataExportPage__field" for="dataExportConfigSelect">
        <span class="tagStudioField__label" id="dataExportConfigLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataExportConfigSelect"></select>
        </span>
      </label>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataExportRun"></button>
      <fieldset class="dataExportPage__format" id="dataExportFormatWrap">
        <legend id="dataExportFormatLabel"></legend>
        <span class="dataExportPage__formatOptions" id="dataExportFormatOptions"></span>
      </fieldset>
      <label class="dataExportPage__toggle" id="dataExportMissingSummaryWrap" hidden>
        <input type="checkbox" id="dataExportMissingSummaryOnly">
        <span id="dataExportMissingSummaryLabel"></span>
      </label>
    </div>

    <p class="tagStudio__status" id="dataExportStatus"></p>
    <p class="tagStudioForm__meta dataExportPage__selectionSummary" id="dataExportSelectionSummary"></p>

    <div class="dataExportPage__listActions" aria-label="Export document selection actions">
      <span class="dataExportPage__filterPills" id="dataExportListFilters" aria-label="Data export list filters"></span>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataExportSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataExportClear"></button>
    </div>

    <div class="tagStudioList dataExportList" id="dataExportList"></div>
    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="dataExportBootStatus">loading export...</p>

{% include studio_module_script.html src='/assets/studio/js/data-export.js' %}
