---
layout: studio
title: "Catalogue Moment Import"
permalink: /studio/catalogue-moment-import/
section: catalogue-moment-import
studio_domain: catalogue
studio_page_doc: /docs/?scope=studio&doc=catalogue-moment-import
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueMomentImportRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">moment import</h2>
      <span class="tagStudio__saveMode" id="catalogueMomentImportSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueMomentImportContext"></p>
    <p class="tagStudio__status" id="catalogueMomentImportStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueMomentImportWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueMomentImportResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">source file</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueMomentImportPreview">Preview Source File</button>
          <button type="button" class="tagStudio__button" id="catalogueMomentImportApply">Import + Publish Moment</button>
        </div>
      </div>
      <div class="tagStudioForm__fields">
        <label class="tagStudioForm__field" for="catalogueMomentImportFile">
          <span class="tagStudioForm__label" id="catalogueMomentImportFileLabel">moment file</span>
          <input class="tagStudio__input" id="catalogueMomentImportFile" type="text" placeholder="keys.md" spellcheck="false" autocomplete="off">
          <p class="tagStudioForm__meta" id="catalogueMomentImportFileDescription"></p>
        </label>
      </div>
      <p class="tagStudioForm__meta" id="catalogueMomentImportSourceSummary"></p>
      <p class="tagStudioForm__meta" id="catalogueMomentImportImageGuidance"></p>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">preview summary</h2>
      <div class="tagStudioForm__fields" id="catalogueMomentImportSummary"></div>
    </aside>
  </div>

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">preview details</h2>
    </div>
    <div class="catalogueWorkDetails__results" id="catalogueMomentImportDetails"></div>
  </section>
</div>

<p class="tagStudio__status" id="catalogueMomentImportLoading">loading moment import…</p>
<p class="tagStudio__empty" id="catalogueMomentImportEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-moment-import.js' | relative_url }}"></script>
