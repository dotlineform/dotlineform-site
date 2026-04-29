---
layout: studio
title: "Catalogue Moment Editor"
permalink: /studio/catalogue-moment/
section: catalogue-moment
studio_page_doc: /docs/?scope=studio&doc=catalogue-moment-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueMomentRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
        <label class="visually-hidden" for="catalogueMomentSearch">Find moment by id or title</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueMomentSearch"
          placeholder="find moment by id or title"
          autocomplete="off"
        >
        <div class="tagStudio__popup" id="catalogueMomentPopup" hidden>
          <div class="tagStudio__popupInner" id="catalogueMomentPopupList"></div>
        </div>
      </div>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentOpen">Open</button>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentNew">New</button>
      <span class="tagStudio__saveMode" id="catalogueMomentSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueMomentContext"></p>
    <p class="tagStudio__status" id="catalogueMomentStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueMomentWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueMomentResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">moment metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentSave">Save</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentPublication">Publish</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentDelete">Delete</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentImportPreview">Preview</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueMomentImportApply">Import</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueMomentMeta"></p>
      <div class="tagStudioForm__fields" id="catalogueMomentImportSource" hidden>
        <label class="tagStudioForm__field" for="catalogueMomentImportFile">
          <span class="tagStudioForm__label" id="catalogueMomentImportFileLabel">moment file</span>
          <input class="tagStudio__input" id="catalogueMomentImportFile" type="text" placeholder="keys.md" spellcheck="false" autocomplete="off">
          <p class="tagStudioForm__meta" id="catalogueMomentImportFileDescription"></p>
        </label>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueMomentFields"></div>
      <p class="tagStudioForm__meta" id="catalogueMomentImportSourceSummary"></p>
      <p class="tagStudioForm__meta" id="catalogueMomentImportImageGuidance"></p>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading" id="catalogueMomentSideHeading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueMomentReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueMomentRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueMomentBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueMomentSummary"></div>
      <div class="tagStudioForm__fields" id="catalogueMomentReadiness"></div>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueMomentLoading">loading catalogue moment editor...</p>
<p class="tagStudio__empty" id="catalogueMomentEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-moment-editor.js' | relative_url }}"></script>
