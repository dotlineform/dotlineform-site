---
layout: studio
title: "Catalogue Work File Editor"
permalink: /studio/catalogue-work-file/
section: catalogue-work-file
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-file-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueWorkFileRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
        <label class="visually-hidden" for="catalogueWorkFileSearch">Find work file by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueWorkFileSearch"
          placeholder="find work file by id"
          autocomplete="off"
        >
        <div class="tagStudio__popup" id="catalogueWorkFilePopup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkFilePopupList"></div>
        </div>
      </div>
      <button type="button" class="tagStudio__button" id="catalogueWorkFileOpen">Open</button>
      <span class="tagStudio__saveMode" id="catalogueWorkFileSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueWorkFileContext"></p>
    <p class="tagStudio__status" id="catalogueWorkFileStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueWorkFileWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueWorkFileResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">file record</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueWorkFileSave">Save Source</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkFileBuild">Save + Rebuild</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkFileDelete">Delete Source</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueWorkFileMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkFileFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueWorkFileReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueWorkFileRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueWorkFileBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueWorkFileSummary"></div>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueWorkFileLoading">loading catalogue work file editor…</p>
<p class="tagStudio__empty" id="catalogueWorkFileEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-work-file-editor.js' | relative_url }}"></script>
