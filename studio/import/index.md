---
layout: studio
title: "Data Import"
permalink: /studio/import/
section: data-import
studio_domain: data
studio_page_doc: /docs/?scope=studio&doc=studio-data-import
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage dataImportPage"
  id="dataImportRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel dataImportPage__panel">
    <div class="dataImportPage__controls">
      <label class="tagStudioField dataImportPage__scopeField" for="dataImportScopeSelect">
        <span class="tagStudioField__label" id="dataImportScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataImportScopeSelect"></select>
        </span>
      </label>
      <label class="tagStudioField dataImportPage__field" for="dataImportFileSelect">
        <span class="tagStudioField__label" id="dataImportFileLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataImportFileSelect"></select>
        </span>
      </label>
      <div class="dataImportPage__commandButtons">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataImportPreview"></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataImportUpdateSummary" disabled></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataImportApplyHierarchy" disabled></button>
      </div>
    </div>

    <div class="dataImportPage__statusRow">
      <p class="tagStudio__status" id="dataImportStatus"></p>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn dataImportPage__resultButton" id="dataImportResults" hidden></button>
    </div>
    <p class="tagStudioForm__meta dataImportPage__selectionSummary" id="dataImportSelectionSummary"></p>

    <div class="dataImportPage__listActions" aria-label="Import preview selection actions">
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataImportSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataImportClear"></button>
    </div>

    <div class="tagStudioList dataImportList" id="dataImportList"></div>

    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="dataImportBootStatus">loading import...</p>

<script type="module" src="{{ '/assets/studio/js/data-import.js' | relative_url }}"></script>
