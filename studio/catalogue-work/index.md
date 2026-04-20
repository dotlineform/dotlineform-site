---
layout: studio
title: "Catalogue Work Editor"
permalink: /studio/catalogue-work/
section: catalogue-work
studio_page_doc: /docs/?scope=studio&doc=catalogue-work-editor
---

{% assign media_base = site.media_base | default: "" %}
{% assign media_image_works = site.media_image_works | default: "/works/img" %}
{% assign thumb_base = site.thumb_base | default: "" %}
{% assign thumb_works = site.thumb_works | default: "/assets/works/img" %}
{% assign thumb_work_details = site.thumb_work_details | default: "/assets/work_details/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign thumb_variants = pipeline.variants.thumb %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | first %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_render_widths | last %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign thumb_sizes = thumb_variants.sizes | default: "96,192" %}
{% assign thumb_suffix = thumb_variants.suffix | default: "thumb" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign works_primary_base = media_base | append: media_image_works | append: "/" %}
{% assign works_thumb_base = thumb_base | append: thumb_works | append: "/" %}
{% assign details_thumb_base = thumb_base | append: thumb_work_details | append: "/" %}
{%- assign works_primary_base_out = works_primary_base -%}
{%- assign works_thumb_base_out = works_thumb_base -%}
{%- assign details_thumb_base_out = details_thumb_base -%}
{%- unless works_primary_base contains '://' -%}
  {%- assign works_primary_base_out = works_primary_base | relative_url -%}
{%- endunless -%}
{%- unless works_thumb_base contains '://' -%}
  {%- assign works_thumb_base_out = works_thumb_base | relative_url -%}
{%- endunless -%}
{%- unless details_thumb_base contains '://' -%}
  {%- assign details_thumb_base_out = details_thumb_base | relative_url -%}
{%- endunless -%}

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage catalogueWorkPage"
  id="catalogueWorkRoot"
  hidden
  data-works-primary-base="{{ works_primary_base_out | escape }}"
  data-thumb-works-base="{{ works_thumb_base_out | escape }}"
  data-thumb-work-details-base="{{ details_thumb_base_out | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-thumb-sizes="{{ thumb_sizes | jsonify | escape }}"
  data-thumb-suffix="{{ thumb_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
>
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
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkOpen">Open</button>
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
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkSave">Save</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkBuild">Rebuild</button>
          <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="catalogueWorkDelete">Delete</button>
        </div>
      </div>
      <p class="tagStudioForm__meta" id="catalogueWorkMeta"></p>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="catalogueWorkFields"></div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">current record</h2>
      <div id="catalogueWorkPreview"></div>
      <div class="tagStudioForm__fields" id="catalogueWorkReadonly"></div>
      <p class="tagStudioForm__impact" id="catalogueWorkRuntimeState"></p>
      <p class="tagStudioForm__impact" id="catalogueWorkBuildImpact"></p>
      <div class="tagStudioForm__fields" id="catalogueWorkSummary"></div>
      <div class="tagStudioForm__fields" id="catalogueWorkReadiness"></div>
    </aside>
  </div>

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="catalogueWorkDetailsHeading">work details</h2>
      <a class="catalogueWorkDetails__newLink" id="catalogueWorkNewDetailLink" href="{{ '/studio/catalogue-new-work-detail/' | relative_url }}">new work detail →</a>
    </div>
    <div class="catalogueWorkDetails__searchRow" id="catalogueWorkDetailsSearchRow" hidden>
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

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="catalogueWorkFilesHeading">work files</h2>
      <a class="catalogueWorkDetails__newLink" id="catalogueWorkNewFileLink" href="{{ '/studio/catalogue-new-work-file/' | relative_url }}">new file →</a>
    </div>
    <p class="tagStudioForm__meta" id="catalogueWorkFilesMeta"></p>
    <div class="catalogueWorkDetails__results" id="catalogueWorkFilesResults"></div>
  </section>

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="catalogueWorkLinksHeading">work links</h2>
      <a class="catalogueWorkDetails__newLink" id="catalogueWorkNewLinkLink" href="{{ '/studio/catalogue-new-work-link/' | relative_url }}">new link →</a>
    </div>
    <p class="tagStudioForm__meta" id="catalogueWorkLinksMeta"></p>
    <div class="catalogueWorkDetails__results" id="catalogueWorkLinksResults"></div>
  </section>
</div>

<p class="tagStudio__status" id="catalogueWorkLoading">loading catalogue work editor…</p>
<p class="tagStudio__empty" id="catalogueWorkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/catalogue-work-editor.js' | relative_url }}"></script>
