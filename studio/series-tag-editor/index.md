---
layout: studio
title: Series Tag Editor
permalink: /studio/series-tag-editor/
section: works
studio_page_doc: /docs/studio/pages/tag-editor/
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<article
  class="page tagStudioPage"
  id="seriesTagEditorRoot"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  data-media-base="{{ site.media_base | default: '' | escape }}"
  data-media-prefix="{% if site.media_prefix == nil %}/assets{% else %}{{ site.media_prefix | escape }}{% endif %}"
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
          <p class="tagStudio__status" data-role="status"></p>
          <p class="tagStudio__saveWarning" data-role="save-warning"></p>
          <p class="tagStudio__saveResult" data-role="save-result"></p>
        </section>

        <section class="tagStudioEditorSection tagStudioEditorSection--groups" data-role="groups-section">
          <div data-role="groups"></div>
        </section>

        <section class="tagStudioEditorSection tagStudioEditorSection--search" data-role="search-section">
          <div class="tagStudio__inputRow tagStudio__inputRow--editor">
            <input
              class="tagStudio__input"
              data-role="tag-input"
              type="text"
              autocomplete="off"
              placeholder="tag slug or alias"
            >
            <button type="button" class="tagStudio__button" data-role="add-tag">Add</button>
            <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save">Save Tags</button>
            <span class="tagStudio__saveMode" data-role="save-mode"></span>
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
