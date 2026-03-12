---
layout: studio
title: Tag Aliases
permalink: /studio/tag-aliases/
studio_page_doc: /docs/studio/pages/tag-aliases/
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagAliasesPage">
  <div id="tag-aliases" data-role="tag-aliases">
    <section class="tagStudio__panel">
      <div class="tagStudioToolbar" data-role="toolbar">
        <div class="tagStudioToolbar__row">
          <label class="tagStudioToolbar__field">
            <span class="tagStudioToolbar__label" data-role="import-file-label">import file</span>
            <button type="button" class="tagStudio__button" data-role="choose-file">Choose file</button>
            <input type="file" data-role="import-file" accept=".json,application/json" hidden>
          </label>
          <label class="tagStudioToolbar__field">
            <span class="tagStudioToolbar__label" data-role="import-mode-label">mode</span>
            <select class="tagStudioToolbar__select" data-role="import-mode">
              <option value="add">add (no overwrite)</option>
              <option value="merge">add + overwrite</option>
              <option value="replace">replace entire aliases</option>
            </select>
          </label>
          <button type="button" class="tagStudio__button" data-role="import-btn">Import</button>
          <span class="tagStudioToolbar__mode" data-role="save-mode"></span>
          <button type="button" class="tagStudio__button tagStudioToolbar__action" data-role="open-new-alias">New alias</button>
        </div>
        <p class="tagStudioToolbar__selected" data-role="selected-file"></p>
        <p class="tagStudioToolbar__result" data-role="import-result"></p>
      </div>

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

<script type="module" src="{{ '/assets/studio/js/tag-aliases.js' | relative_url }}"></script>
