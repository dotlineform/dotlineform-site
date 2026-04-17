---
layout: studio
title: New Catalogue Series
permalink: /studio/catalogue-new-series/
section: catalogue-new-series
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-series-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueNewSeriesRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">new series</h2>
      <span class="tagStudio__saveMode" id="catalogueNewSeriesSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueNewSeriesContext"></p>
    <p class="tagStudio__status" id="catalogueNewSeriesStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueNewSeriesWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueNewSeriesResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">draft metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="catalogueNewSeriesCreate">Create Draft Series</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueNewSeriesFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">next step</h2>
      <p class="tagStudioForm__impact" id="catalogueNewSeriesSummary"></p>
    </aside>
  </div>
</div>

<p class="tagStudio__status" id="catalogueNewSeriesLoading">loading new series editor…</p>
<p class="tagStudio__empty" id="catalogueNewSeriesEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-new-series-editor.js' | relative_url }}"></script>
