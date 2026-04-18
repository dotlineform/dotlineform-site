---
layout: studio
title: Catalogue Work Detail Editor
permalink: /studio/catalogue-work-detail/
section: catalogue-work-detail
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-detail-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueWorkDetailRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
        <label class="visually-hidden" for="catalogueWorkDetailSearchGlobal">Find detail by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueWorkDetailSearchGlobal"
          placeholder="find detail by id"
          autocomplete="off"
        >
        <div class="tagStudio__popup" id="catalogueWorkDetailPopup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkDetailPopupList"></div>
        </div>
      </div>
      <button type="button" class="tagStudio__button" id="catalogueWorkDetailOpen">Open</button>
      <span class="tagStudio__saveMode" id="catalogueWorkDetailSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueWorkDetailContext"></p>
    <p class="tagStudio__status" id="catalogueWorkDetailStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueWorkDetailWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueWorkDetailResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">work detail metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueWorkDetailSave">Save Source</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkDetailBuild">Save + Rebuild</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkDetailDelete">Delete Source</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueWorkDetailMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkDetailFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueWorkDetailReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueWorkDetailRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueWorkDetailBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueWorkDetailSummary"></div>
      <div class="tagStudioForm__fields" id="catalogueWorkDetailReadiness"></div>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueWorkDetailLoading">loading catalogue work detail editor…</p>
<p class="tagStudio__empty" id="catalogueWorkDetailEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-work-detail-editor.js' | relative_url }}"></script>
