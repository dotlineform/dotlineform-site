---
layout: studio
title: Search
permalink: /studio/search/
section: search
studio_page_doc: /docs/?doc=studio-search-v1
---
<div
  class="studioSearch"
  id="studioSearchRoot"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  hidden
>
  <label class="visually-hidden" for="studioSearchInput">search</label>
  <div class="studioSearch__controls">
    <input
      class="studioSearch__input"
      id="studioSearchInput"
      type="search"
      autocomplete="off"
      spellcheck="false"
    >
    <div class="studioSearch__filters" id="studioSearchFilters" aria-label="Search result filter"></div>
  </div>

  <p class="studioSearch__status" id="studioSearchStatus">loading search index…</p>
  <ol class="studioSearch__results" id="studioSearchResults"></ol>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-search.js' | relative_url }}"></script>
