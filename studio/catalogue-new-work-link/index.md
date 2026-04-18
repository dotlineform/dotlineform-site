---
layout: studio
title: New Catalogue Work Link
permalink: /studio/catalogue-new-work-link/
section: catalogue-new-work-link
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-link-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueNewWorkLinkRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">new work link</h2>
      <span class="tagStudio__saveMode" id="catalogueNewWorkLinkSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueNewWorkLinkContext"></p>
    <p class="tagStudio__status" id="catalogueNewWorkLinkStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueNewWorkLinkWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueNewWorkLinkResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">draft metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueNewWorkLinkCreate">Create Draft Link</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueNewWorkLinkFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">next step</h2>
      <p class="tagStudioForm__impact" id="catalogueNewWorkLinkSummary"></p>
      <p class="tagStudioForm__impact" id="catalogueNewWorkLinkGuidance"></p>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueNewWorkLinkLoading">loading new work link editor…</p>
<p class="tagStudio__empty" id="catalogueNewWorkLinkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-new-work-link-editor.js' | relative_url }}"></script>
