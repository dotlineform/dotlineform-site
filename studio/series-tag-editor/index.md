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
    </figure>

    <section class="tagStudioPage__context">
      <h1 class="tagStudioPage__title" id="seriesTagEditorTitle">Series Tag Editor</h1>
      <div class="workCurator__rows" style="font-size:var(--meta-small-size);line-height:var(--meta-small-line);">
        <div class="page__row">
          cat
          <span id="seriesTagEditorCat">—</span>
        </div>
        <div class="page__row">year <span id="seriesTagEditorYear">—</span></div>
        <div class="page__row">year display <span id="seriesTagEditorYearDisplay">—</span></div>
        <div class="page__row">sort fields <span id="seriesTagEditorSortFields">—</span></div>
        <div class="page__row">primary work <span id="seriesTagEditorPrimaryWork">—</span></div>
        <div class="page__row">project folders <span id="seriesTagEditorFolders">—</span></div>
        <div class="page__row">notes <span id="seriesTagEditorNotes">—</span></div>
      </div>
    </section>
  </header>

  <section class="tagStudioPage__editor">
    <div id="tag-studio"></div>
  </section>
</article>
<p id="seriesTagEditorEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/series-tag-editor-page.js' | relative_url }}"></script>
