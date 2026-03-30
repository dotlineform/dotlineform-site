---
layout: default
title: Search
permalink: /search/
section: series
---

<div
  class="studioSearch"
  id="studioSearchRoot"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  hidden
>
  <div class="studioSearch__header">
    <a class="studioSearch__backLink" id="studioSearchBackLink" href="{{ '/series/' | relative_url }}">← works</a>
    <p class="studioSearch__scope" id="studioSearchScope">catalogue</p>
  </div>
  <label class="visually-hidden" for="studioSearchInput">search</label>
  <div class="studioSearch__controls">
    <input
      class="studioSearch__input"
      id="studioSearchInput"
      type="search"
      autocomplete="off"
      spellcheck="false"
    >
  </div>

  <p class="studioSearch__status" id="studioSearchStatus">loading search index…</p>
  <ol class="studioSearch__results" id="studioSearchResults"></ol>
  <div class="studioSearch__more" id="studioSearchMore"></div>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-search.js' | relative_url }}"></script>
