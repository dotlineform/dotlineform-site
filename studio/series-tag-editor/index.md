---
layout: studio
title: "Series Tag Editor"
permalink: /studio/series-tag-editor/
section: works
studio_page_doc: /docs/?scope=studio&doc=tag-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% assign media_base = site.media_base | default: "" %}
{% assign media_image_works = site.media_image_works | default: "/works/img" %}
{% assign pipeline = site.data.pipeline %}
{% assign primary_variants = pipeline.variants.primary %}
{% assign compatibility_variants = pipeline.variants.compatibility %}
{% assign primary_render_widths = compatibility_variants.render_widths | default: primary_variants.widths %}
{% assign primary_display_width = primary_render_widths | last %}
{% assign primary_full_width = primary_variants.preferred_width | default: primary_display_width %}
{% assign primary_suffix = primary_variants.suffix | default: "primary" %}
{% assign asset_format = pipeline.encoding.format | default: "webp" %}
{% assign media_image_works_base = media_base | append: media_image_works | append: "/" %}
{%- assign media_image_works_base_out = media_image_works_base -%}
{%- unless media_image_works_base contains '://' -%}
  {%- assign media_image_works_base_out = media_image_works_base | relative_url -%}
{%- endunless -%}

<article
  class="page tagStudioPage"
  id="seriesTagEditorRoot"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  data-media-image-works-base="{{ media_image_works_base_out | escape }}"
  data-primary-render-widths="{{ primary_render_widths | jsonify | escape }}"
  data-primary-display-width="{{ primary_display_width | escape }}"
  data-primary-full-width="{{ primary_full_width | escape }}"
  data-primary-suffix="{{ primary_suffix | escape }}"
  data-asset-format="{{ asset_format | escape }}"
  data-series-index-url="{{ '/assets/data/series_index.json' | relative_url }}"
  data-tag-studio-module-url="{{ '/assets/studio/js/tag-studio.js' | relative_url }}"
  hidden
>
  <header class="tagStudioPage__header">
    <figure class="tagStudioPage__media" id="seriesTagEditorMedia" hidden>
      <a
        class="page__mediaLink"
        id="seriesTagEditorMediaLink"
        href="#"
        target="_blank"
        rel="noopener"
        style="--work-ar: 4 / 3;"
      >
        <img
          class="tagStudioPage__mediaImg"
          id="seriesTagEditorMediaImg"
          src=""
          srcset=""
          sizes="(max-width: 900px) 100vw, 40vw"
          alt=""
          loading="eager"
          fetchpriority="high"
          decoding="async"
        >
      </a>
      <figcaption class="tagStudioPage__mediaCaption" id="seriesTagEditorMediaCaption"></figcaption>
    </figure>

    <section class="tagStudioPage__context tagStudioPage__context--meta">
      <h1 class="tagStudioPage__title" id="seriesTagEditorTitle">Series Tag Editor</h1>
      <div class="page__caption page__metaList">
        <div class="page__row"><span id="seriesTagEditorYearDisplay">—</span></div>
        <div class="page__row">
          <!-- cat. -->
          <span id="seriesTagEditorCat">—</span>
        </div>
        <div class="page__row" style="display:none;"><span id="seriesTagEditorYear">—</span></div>
        <div class="page__row" style="display:none;"><span id="seriesTagEditorSortFields">—</span></div>
        <div class="page__row" style="display:none;"><span id="seriesTagEditorPrimaryWork">—</span></div>
        <div class="page__row">/<span id="seriesTagEditorFolders">—</span></div>
        <div class="page__row"><span id="seriesTagEditorNotes">—</span></div>
      </div>
    </section>
  </header>

  <section class="tagStudioPage__editor">
    <div id="tag-studio" class="tagStudio" data-role="series-tag-editor">
      <section class="tagStudio__panel tagStudio__panel--editor" data-role="editor-shell">
        <section class="tagStudioEditorSection tagStudioEditorSection--work" data-role="work-section">
          <div class="tagStudio__inputRow tagStudio__inputRow--work">
            <input
              class="tagStudio__input"
              data-role="work-input"
              type="text"
              autocomplete="off"
              placeholder="work_id(s) in this series"
            >
            <div class="tagStudio__workSelection" data-role="selected-work"></div>
          </div>
          <div class="tagStudio__popup tagStudio__popup--work" data-role="work-popup" hidden>
            <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="work-popup-list"></div>
          </div>
        </section>

        <section class="tagStudioEditorSection tagStudioEditorSection--messages" data-role="message-section">
          <p class="tagStudio__contextHint" data-role="context-hint"></p>
        </section>

        <section class="tagStudioEditorSection tagStudioEditorSection--groups" data-role="groups-section">
          <div data-role="groups"></div>
        </section>

        <section class="tagStudioEditorSection tagStudioEditorSection--search" data-role="search-section">
          <div class="tagStudio__inputRow tagStudio__editorActionGrid">
            <input
              class="tagStudio__input"
              data-role="tag-input"
              type="text"
              autocomplete="off"
              placeholder="tag slug or alias"
            >
            <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="add-tag">Add</button>
            <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" data-role="save">Save</button>
            <span class="tagStudio__saveMode" data-role="save-mode"></span>
            <div class="tagStudio__buttonFeedback tagStudio__buttonFeedback--editor">
              <p class="tagStudio__status" data-role="status"></p>
              <p class="tagStudio__saveWarning" data-role="save-warning"></p>
              <p class="tagStudio__saveResult" data-role="save-result"></p>
            </div>
          </div>
          <div class="tagStudio__popup tagStudio__popup--series" data-role="popup" hidden>
            <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="popup-list"></div>
          </div>
        </section>
      </section>

      <div data-role="modal-host"></div>
    </div>
  </section>
</article>
<p id="seriesTagEditorEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/series-tag-editor-page.js' | relative_url }}"></script>
