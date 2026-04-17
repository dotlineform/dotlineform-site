---
layout: studio
title: Catalogue Status
permalink: /studio/catalogue-status/
section: catalogue-status
studio_page_doc: /docs/?scope=studio&doc=catalogue-status
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueStatusPage" id="catalogueStatusRoot" hidden>
  <section class="tagStudio__panel">
    <div class="tagStudioFilters catalogueStatusPage__filters">
      <div class="tagStudio__key tagStudioFilters__key" id="catalogueStatusKey"></div>
      <label class="tagStudioFilters__searchWrap catalogueStatusPage__searchWrap">
        <span class="visually-hidden">Search catalogue source status rows</span>
        <input
          type="text"
          class="tagStudio__input tagStudioFilters__searchInput"
          id="catalogueStatusSearch"
          placeholder="search"
          autocomplete="off"
        >
      </label>
    </div>

    <p class="tagStudio__status catalogueStatusPage__meta" id="catalogueStatusMeta"></p>
    <div id="catalogueStatusList"></div>
  </section>
</div>

<p class="tagStudio__status" id="catalogueStatusLoading">loading catalogue status…</p>
<p class="tagStudio__empty" id="catalogueStatusEmpty" hidden>No non-published catalogue source records.</p>

<script type="module" src="{{ '/assets/studio/js/catalogue-status.js' | relative_url }}"></script>
