---
layout: studio
title: Studio Works
permalink: /studio/studio-works/
section: works
studio_page_doc: /docs/?scope=studio&doc=studio-works
---
<div
  class="index worksList worksList--studio"
  id="worksStudioRoot"
  data-role="studio-works"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  data-works-index-url="{{ '/assets/data/works_index.json' | relative_url }}"
  data-series-index-url="{{ '/assets/data/series_index.json' | relative_url }}"
  data-series-base-href="{{ '/series/' | relative_url }}"
  hidden
>
  <h1 class="index__heading visually-hidden">studio works</h1>
  <div class="worksList__metaRow">
    <p class="worksList__count" id="worksListCount"></p>
    <div class="worksList__metaActions">
      <button class="tagStudio__button worksList__metaButton" type="button" id="worksListCopySeriesButton">copy series</button>
      <a class="worksList__metaLink" href="{{ '/site_map/' | relative_url }}">site map</a>
    </div>
  </div>

  <div class="worksList__head" role="group" aria-label="Sort studio works">
    <button class="worksList__sortBtn" type="button" data-role="sort-button" data-sort-key="cat">
      cat <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-role="sort-button" data-sort-key="year">
      year <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-role="sort-button" data-sort-key="title">
      title <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-role="sort-button" data-sort-key="series">
      series <span class="worksList__sortIcon" aria-hidden="true"></span>
    </button>
    <button class="worksList__sortBtn" type="button" data-role="sort-button" data-sort-key="storage">
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
<p id="worksStudioEmpty" hidden>no studio works yet</p>

<script type="module" src="{{ '/assets/studio/js/studio-works.js' | relative_url }}"></script>
