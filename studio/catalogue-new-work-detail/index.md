---
layout: studio
title: New Catalogue Work Detail
permalink: /studio/catalogue-new-work-detail/
section: catalogue-new-work-detail
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-detail-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueNewWorkDetailRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">new work detail</h2>
      <span class="tagStudio__saveMode" id="catalogueNewWorkDetailSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueNewWorkDetailContext"></p>
    <p class="tagStudio__status" id="catalogueNewWorkDetailStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueNewWorkDetailWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueNewWorkDetailResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">draft metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueNewWorkDetailCreate">Create Draft Detail</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueNewWorkDetailFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">next step</h2>
      <p class="tagStudioForm__impact" id="catalogueNewWorkDetailSummary"></p>
      <p class="tagStudioForm__impact" id="catalogueNewWorkDetailMediaGuidance"></p>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueNewWorkDetailLoading">loading new work detail editor…</p>
<p class="tagStudio__empty" id="catalogueNewWorkDetailEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-new-work-detail-editor.js' | relative_url }}"></script>
