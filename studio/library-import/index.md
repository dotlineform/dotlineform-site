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
      <label class="tagStudioField libraryImportPage__field" for="libraryImportFileSelect">
        <span class="tagStudioField__label" id="libraryImportFileLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="libraryImportFileSelect"></select>
        </span>
      </label>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportPreview"></button>
    </div>

    <dl class="libraryImportPage__fileMeta" id="libraryImportFileMeta" hidden>
      <div>
        <dt id="libraryImportFilePathLabel"></dt>
        <dd id="libraryImportFilePath"></dd>
      </div>
      <div>
        <dt id="libraryImportFileFormatLabel"></dt>
        <dd id="libraryImportFileFormat"></dd>
      </div>
      <div>
        <dt id="libraryImportFileSizeLabel"></dt>
        <dd id="libraryImportFileSize"></dd>
      </div>
      <div>
        <dt id="libraryImportFileModifiedLabel"></dt>
        <dd id="libraryImportFileModified"></dd>
      </div>
    </dl>

    <p class="tagStudio__status" id="libraryImportStatus"></p>
    <p class="tagStudioForm__meta libraryImportPage__selectionSummary" id="libraryImportSelectionSummary"></p>

    <div class="libraryImportPage__listActions" aria-label="Library import preview selection actions">
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryImportSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="libraryImportClear"></button>
    </div>

    <div class="tagStudioList libraryImportList" id="libraryImportList"></div>

    <div class="libraryImportPage__applyActions" aria-label="Library import apply actions">
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportUpdateSummary" disabled></button>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="libraryImportApplyHierarchy" disabled></button>
    </div>

    <div class="libraryImportPage__resultMeta" id="libraryImportResult" hidden>
      <p class="tagStudioForm__meta libraryImportPage__summary" id="libraryImportSummary"></p>
      <dl class="libraryImportPage__resultGrid">
        <div>
          <dt id="libraryImportResultTypeLabel"></dt>
          <dd id="libraryImportResultType"></dd>
        </div>
        <div>
          <dt id="libraryImportResultExportLabel"></dt>
          <dd id="libraryImportResultExport"></dd>
        </div>
        <div>
          <dt id="libraryImportResultGeneratedLabel"></dt>
          <dd id="libraryImportResultGenerated"></dd>
        </div>
        <div>
          <dt id="libraryImportResultCountsLabel"></dt>
          <dd id="libraryImportResultCounts"></dd>
        </div>
      </dl>

      <div class="libraryImportPage__issues" id="libraryImportIssues" hidden>
        <h4 id="libraryImportIssuesHeading"></h4>
        <ul id="libraryImportIssuesList"></ul>
      </div>

      <div class="libraryImportPage__previews" id="libraryImportPreviews" hidden>
        <h4 id="libraryImportPreviewsHeading"></h4>
        <p class="tagStudioForm__meta" id="libraryImportPreviewList"></p>
      </div>
    </div>
  </div>
</div>

<p class="tagStudio__status" id="libraryImportBootStatus">loading Library import...</p>

<script type="module" src="{{ '/assets/studio/js/library-import.js' | relative_url }}"></script>
