---
layout: studio
title: "Catalogue Series Editor"
permalink: /studio/catalogue-series/
section: catalogue-series
studio_page_doc: /docs/?scope=studio&doc=catalogue-series-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueSeriesRoot" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueWorkPage__searchWrap">
        <label class="visually-hidden" for="catalogueSeriesSearch">Find series by title</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueSeriesSearch"
          placeholder="find series by title"
          autocomplete="off"
        >
        <div class="tagStudio__popup" id="catalogueSeriesPopup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" id="catalogueSeriesPopupList"></div>
        </div>
      </div>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesOpen">Open</button>
      <span class="tagStudio__saveMode" id="catalogueSeriesSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="catalogueSeriesContext"></p>
    <p class="tagStudio__status" id="catalogueSeriesStatus"></p>
    <p class="tagStudio__saveWarning" id="catalogueSeriesWarning"></p>
    <p class="tagStudio__saveResult" id="catalogueSeriesResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">series metadata</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesSave">Save</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesBuild">Rebuild</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesDelete">Delete</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueSeriesMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueSeriesFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div class="tagStudioForm__fields" id="catalogueSeriesReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueSeriesRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueSeriesBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueSeriesSummary"></div>
      <div class="tagStudioForm__fields" id="catalogueSeriesReadiness"></div>
    </aside>
  </div>

  <section class="tagStudio__panel catalogueSeriesMembers">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="catalogueSeriesMembersHeading">member works</h2>
    </div>
    <div class="tagStudio__headingRow catalogueSeriesMembers__searchRow" id="catalogueSeriesMemberSearchRow" hidden>
      <div class="tagStudioForm__searchWrap catalogueSeriesMembers__searchWrap">
        <label class="visually-hidden" for="catalogueSeriesMemberSearch">Find member work by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueSeriesMemberSearch"
          placeholder="find member work by id"
          autocomplete="off"
        >
      </div>
      <span class="tagStudioForm__meta" id="catalogueSeriesMemberSearchMeta"></span>
    </div>
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <div class="tagStudioForm__searchWrap catalogueSeriesMembers__searchWrap">
        <label class="visually-hidden" for="catalogueSeriesMemberAdd">Add work by id</label>
        <input
          type="text"
          class="tagStudio__input"
          id="catalogueSeriesMemberAdd"
          placeholder="add work by id"
          autocomplete="off"
        >
      </div>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueSeriesMemberAddButton">Add</button>
      <span class="tagStudioForm__meta" id="catalogueSeriesMembersMeta"></span>
    </div>
    <p class="tagStudio__status" id="catalogueSeriesMembersStatus"></p>
    <div class="catalogueSeriesMembers__results" id="catalogueSeriesMembersResults"></div>
  </section>
</div>

<p class="tagStudio__status" id="catalogueSeriesLoading">loading catalogue series editor…</p>
<p class="tagStudio__empty" id="catalogueSeriesEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-series-editor.js' | relative_url }}"></script>
