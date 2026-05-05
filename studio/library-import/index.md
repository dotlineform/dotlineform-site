---
layout: studio
title: "Library Import"
permalink: /studio/library-import/
section: library-import
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=library-import
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage libraryImportPage"
  id="libraryImportRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel libraryImportPage__panel">
    <div class="libraryImportPage__controls">
      <label class="tagStudioField libraryImportPage__scopeField" for="libraryImportScopeSelect">
        <span class="tagStudioField__label" id="libraryImportScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="libraryImportScopeSelect"></select>
        </span>
      </label>
      <label class="tagStudioField libraryImportPage__field" for="libraryImportFileSelect">
        <span class="tagStudioField__label" id="libraryImportFileLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="libraryImportFileSelect"></select>
        </span>
      </label>
      <div class="libraryImportPage__commandButtons">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportPreview"></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportUpdateSummary" disabled></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportApplyHierarchy" disabled></button>
      </div>
    </div>

    <div class="libraryImportPage__statusRow">
      <p class="tagStudio__status" id="libraryImportStatus"></p>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn libraryImportPage__resultButton" id="libraryImportResults" hidden></button>
    </div>
    <p class="tagStudioForm__meta libraryImportPage__selectionSummary" id="libraryImportSelectionSummary"></p>

    <div class="libraryImportPage__listActions" aria-label="Import preview selection actions">
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryImportSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryImportClear"></button>
    </div>

    <div class="tagStudioList libraryImportList" id="libraryImportList"></div>

    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="libraryImportBootStatus">loading import...</p>

<script type="module" src="{{ '/assets/studio/js/library-import.js' | relative_url }}"></script>
