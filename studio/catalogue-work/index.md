---
layout: studio
title: Catalogue Work Editor
permalink: /studio/catalogue-work/
section: catalogue-work
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueWorkRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
        <label class="visually-hidden" for="catalogueWorkSearch">Find work by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueWorkSearch"
          placeholder="find work by id"
          autocomplete="off"
        >
        <div class="tagStudio__popup" id="catalogueWorkPopup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueWorkPopupList"></div>
        </div>
      </div>
      <button type="button" class="tagStudio__button" id="catalogueWorkOpen">Open</button>
      <span class="tagStudio__saveMode" id="catalogueWorkSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueWorkContext"></p>
    <p class="tagStudio__status" id="catalogueWorkStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueWorkWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueWorkResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">work metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueWorkSave">Save Source</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkBuild">Save + Rebuild</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueWorkMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueWorkReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueWorkRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueWorkBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueWorkSummary"></div>
    </aside>
  </div>

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="catalogueWorkDetailsHeading">work details</h2>
      <a class="tagStudio__button" id="catalogueWorkNewDetailLink" href="{{ '/studio/catalogue-new-work-detail/' | relative_url }}">New Detail</a>
      <div class="tagStudioForm__searchWrap catalogueWorkDetails__searchWrap">
        <label class="visually-hidden" for="catalogueWorkDetailSearch">Find detail by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueWorkDetailSearch"
          placeholder="find detail by id"
          autocomplete="off"
        >
      </div>
    </div>
    <p class="tagStudioForm__meta" id="catalogueWorkDetailsMeta"></p>
    <div class="catalogueWorkDetails__results" id="catalogueWorkDetailsResults"></div>
  </section>
</div>

<p class="tagStudio__status" id="catalogueWorkLoading">loading catalogue work editor…</p>
<p class="tagStudio__empty" id="catalogueWorkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-work-editor.js' | relative_url }}"></script>
