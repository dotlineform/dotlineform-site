---
layout: studio
title: "New Catalogue Work"
permalink: /studio/catalogue-new-work/
section: catalogue-new-work
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueNewWorkRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">new work</h2>
      <span class="tagStudio__saveMode" id="catalogueNewWorkSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueNewWorkContext"></p>
    <p class="tagStudio__status" id="catalogueNewWorkStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueNewWorkWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueNewWorkResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">draft metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueNewWorkCreate">Create</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueNewWorkFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">next step</h2>
      <p class="tagStudioForm__impact" id="catalogueNewWorkSummary"></p>
      <p class="tagStudioForm__impact" id="catalogueNewWorkMediaGuidance"></p>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueNewWorkLoading">loading new work editor…</p>
<p class="tagStudio__empty" id="catalogueNewWorkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-new-work-editor.js' | relative_url }}"></script>
