---
layout: studio
title: "Tag Aliases"
permalink: /studio/analytics/tag-aliases/
studio_domain: analytics
studio_page_doc: /docs/?scope=studio&doc=tag-aliases
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagAliasesPage">
  <div id="tag-aliases" data-role="tag-aliases" data-studio-ready="false" data-studio-busy="false">
    <div class="seriesTagsActions">
      <button type="button" class="tagStudio__button" data-role="open-import-modal">Import</button>
      <button type="button" class="tagStudio__button" data-role="open-new-alias">New alias</button>
    </div>
    <section class="tagStudio__panel">
      <div class="tagStudioFilters" data-role="filters">
        <div class="tagStudio__key tagStudioFilters__key" data-role="key"></div>
        <label class="tagStudioFilters__searchWrap">
          <span class="visually-hidden" data-role="search-label">Search aliases</span>
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

{% include studio_module_script.html src='/assets/studio/js/tag-aliases.js' %}
