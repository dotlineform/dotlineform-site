---
layout: default
title: Studio Works
permalink: /studio/studio-works/
section: works
---
<div
  class="index worksList worksList--curator"
  id="worksCuratorRoot"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  data-works-index-url="{{ '/assets/data/works_index.json' | relative_url }}"
  data-series-index-url="{{ '/assets/data/series_index.json' | relative_url }}"
  data-series-base-href="{{ '/series/' | relative_url }}"
  hidden
>
  <h1 class="index__heading visually-hidden">works curator</h1>
  <div class="worksList__metaRow">
    <p class="worksList__count" id="worksListCount"></p>
    <a class="worksList__metaLink" href="{{ '/site_map/' | relative_url }}">site map</a>
  </div>

  <div class="worksList__head" role="group" aria-label="Sort works curator">
    <button class="worksList__sortBtn" type="button" data-sort-key="cat">
      cat <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="year">
      year <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="title">
      title <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="series">
      series <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-sort-key="storage">
      storage <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
  </div>

  <ul class="worksList__list" id="worksList"></ul>

  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a
      class="page__back"
      id="worksIndexBackLink"
      href="{{ '/series/' | relative_url }}"
    >← series</a>
  </nav>
</div>
<p id="worksCuratorEmpty" hidden>no curator works yet</p>

<script type="module" src="{{ '/assets/studio/js/studio-works.js' | relative_url }}"></script>
