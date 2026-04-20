---
layout: studio
title: "New Catalogue Work File"
permalink: /studio/catalogue-new-work-file/
section: catalogue-new-work-file
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-file-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueNewWorkFileRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">new work file</h2>
      <span class="tagStudio__saveMode" id="catalogueNewWorkFileSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueNewWorkFileContext"></p>
    <p class="tagStudio__status" id="catalogueNewWorkFileStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueNewWorkFileWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueNewWorkFileResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">draft metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueNewWorkFileCreate">Create</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueNewWorkFileFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">next step</h2>
      <p class="tagStudioForm__impact" id="catalogueNewWorkFileSummary"></p>
      <p class="tagStudioForm__impact" id="catalogueNewWorkFileGuidance"></p>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueNewWorkFileLoading">loading new work file editor…</p>
<p class="tagStudio__empty" id="catalogueNewWorkFileEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-new-work-file-editor.js' | relative_url }}"></script>
