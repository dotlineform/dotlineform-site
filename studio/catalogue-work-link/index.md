---
layout: studio
title: Catalogue Work Link Editor
permalink: /studio/catalogue-work-link/
section: catalogue-work-link
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-link-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueWorkLinkRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">work link metadata</h2>
      <span class="tagStudio__saveMode" id="catalogueWorkLinkSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueWorkLinkContext"></p>
    <p class="tagStudio__status" id="catalogueWorkLinkStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueWorkLinkWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueWorkLinkResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">link record</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueWorkLinkSave">Save Source</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkLinkBuild">Save + Rebuild</button>
          <button type="button" class="tagStudio__button" id="catalogueWorkLinkDelete">Delete Source</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueWorkLinkMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkLinkFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueWorkLinkReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueWorkLinkRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueWorkLinkBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueWorkLinkSummary"></div>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueWorkLinkLoading">loading catalogue work link editor…</p>
<p class="tagStudio__empty" id="catalogueWorkLinkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-work-link-editor.js' | relative_url }}"></script>
