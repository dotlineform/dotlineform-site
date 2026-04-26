---
layout: studio
title: "Docs HTML Import"
permalink: /studio/docs-import/
section: docs-html-import
studio_page_doc: /docs/?scope=studio&doc=user-guide-docs-html-import
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage docsHtmlImportPage" id="docsHtmlImportRoot" hidden>
  <div class="tagStudio__panel docsHtmlImportPage__panel">
    <p class="docsHtmlImportPage__intro" id="docsHtmlImportIntro"></p>

    <div class="docsHtmlImportPage__controls">
      <label class="tagStudioField tagStudioField--inline docsHtmlImportPage__field">
        <span class="tagStudioField__label" id="docsHtmlImportFileLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="docsHtmlImportFileSelect"></select>
        </span>
      </label>

      <label class="tagStudioField tagStudioField--inline docsHtmlImportPage__field">
        <span class="tagStudioField__label" id="docsHtmlImportScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="docsHtmlImportScopeSelect"></select>
        </span>
      </label>
    </div>

    <label class="docsHtmlImportPage__toggle">
      <input type="checkbox" id="docsHtmlImportIncludePromptMeta">
      <span id="docsHtmlImportIncludePromptMetaLabel"></span>
    </label>
    <p class="tagStudioForm__meta docsHtmlImportPage__toggleHint" id="docsHtmlImportIncludePromptMetaHint"></p>

    <div class="docsHtmlImportPage__actions">
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="docsHtmlImportRun"></button>
      <button
        type="button"
        class="tagStudio__button tagStudio__button--defaultWidth"
        id="docsHtmlImportConfirm"
        hidden
      ></button>
      <button
        type="button"
        class="tagStudio__button tagStudio__button--defaultWidth"
        id="docsHtmlImportCancel"
        hidden
      ></button>
    </div>

    <p class="tagStudio__status" id="docsHtmlImportStatus"></p>

    <div class="docsHtmlImportPage__warning" id="docsHtmlImportWarning" hidden>
      <h3 id="docsHtmlImportCollisionHeading"></h3>
      <p id="docsHtmlImportCollisionBody"></p>
      <p class="tagStudioForm__meta" id="docsHtmlImportCollisionMeta"></p>
    </div>

    <div class="docsHtmlImportPage__result" id="docsHtmlImportResult" hidden>
      <h3 id="docsHtmlImportResultTitle"></h3>
      <dl class="docsHtmlImportPage__resultGrid">
        <div>
          <dt id="docsHtmlImportResultScopeLabel"></dt>
          <dd id="docsHtmlImportResultScope"></dd>
        </div>
        <div>
          <dt id="docsHtmlImportResultDocIdLabel"></dt>
          <dd id="docsHtmlImportResultDocId"></dd>
        </div>
        <div>
          <dt id="docsHtmlImportResultTitleLabel"></dt>
          <dd id="docsHtmlImportResultDocTitle"></dd>
        </div>
        <div>
          <dt id="docsHtmlImportResultSourceLabel"></dt>
          <dd id="docsHtmlImportResultSource"></dd>
        </div>
        <div>
          <dt id="docsHtmlImportResultViewerLabel"></dt>
          <dd id="docsHtmlImportResultViewer"></dd>
        </div>
        <div>
          <dt id="docsHtmlImportResultBackupLabel"></dt>
          <dd id="docsHtmlImportResultBackup"></dd>
        </div>
      </dl>
      <p class="tagStudioForm__meta" id="docsHtmlImportResultCounts"></p>
      <div class="docsHtmlImportPage__warnings" id="docsHtmlImportWarnings" hidden>
        <h4 id="docsHtmlImportWarningsHeading"></h4>
        <ul id="docsHtmlImportWarningsList"></ul>
      </div>
    </div>
  </div>
</div>

<p class="tagStudio__status" id="docsHtmlImportBootStatus">loading docs import…</p>

<script type="module" src="{{ '/assets/studio/js/docs-html-import.js' | relative_url }}"></script>
