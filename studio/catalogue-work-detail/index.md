---
layout: studio
title: "Catalogue Work Detail Editor"
permalink: /studio/catalogue-work-detail/
section: catalogue-work-detail
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-detail-editor
---

{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_work_details = site.thumb_work_details | default: "/assets/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign thumb_sizes = thumb_variants.sizes | default: "96,192" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign details_thumb_base = thumb_base | append: thumb_work_details | append: "/" %}
{%- assign details_thumb_base_out = details_thumb_base -%}
{%- unless details_thumb_base contains '://' -%}
  {%- assign details_thumb_base_out = details_thumb_base | relative_url -%}
{%- endunless -%}

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage catalogueWorkPage"
  id="catalogueWorkDetailRoot"
  hidden
  data-thumb-work-details-base="{{ details_thumb_base_out | escape }}"
  data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}"
  data-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
>
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
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailOpen">Open</button>
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
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailSave">Save</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailBuild">Rebuild</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDetailDelete">Delete</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkDetailFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div id="catalogueWorkDetailPreview"></div>
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
