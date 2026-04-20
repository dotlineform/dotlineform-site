---
layout: studio
title: "Tag Registry"
permalink: /studio/tag-registry/
studio_page_doc: /docs/?scope=studio&doc=tag-registry
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagRegistryPage">
  <div id="tag-registry" data-role="tag-registry">
    <div class="seriesTagsActions">
      <button type="button" class="tagStudio__button" data-role="open-import-modal">Import</button>
      <button type="button" class="tagStudio__button" data-role="open-new-tag">New tag</button>
    </div>
    <section class="tagStudio__panel">
      <div class="tagStudioFilters" data-role="filters">
        <div class="tagStudio__key tagStudioFilters__key" data-role="key"></div>
        <label class="tagStudioFilters__searchWrap">
          <span class="visually-hidden" data-role="search-label">Search tags</span>
          <input
            type="text"
            class="tagStudio__input tagStudioFilters__searchInput"
            data-role="search"
            placeholder="search"
            autocomplete="off"
          >
        </label>
      </div>

      <div data-role="list"></div>
    </section>

    <div data-role="modal-host"></div>
  </div>
</div>

<script type="module" src="{{ '/assets/studio/js/tag-registry.js' | relative_url }}"></script>
