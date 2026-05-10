---
layout: studio
title: "Studio Works"
permalink: /studio/studio-works/
section: works
studio_page_doc: /docs/?scope=studio&doc=studio-works
---
<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="index worksList worksList--studio tagStudioList tagStudioList--dense"
  id="worksStudioRoot"
  data-role="studio-works"
  data-baseurl="{{ site.baseurl | default: '' | escape }}"
  data-works-index-url="{{ '/assets/data/works_index.json' | relative_url }}"
  data-work-storage-index-url="{{ '/assets/studio/data/work_storage_index.json' | relative_url }}"
  data-series-index-url="{{ '/assets/data/series_index.json' | relative_url }}"
  data-series-base-href="{{ '/series/' | relative_url }}"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <h1 class="index__heading visually-hidden">studio works</h1>
  <div class="worksList__metaRow">
    <p class="worksList__count" id="worksListCount"></p>
    <div class="worksList__metaActions">
      <button class="tagStudio__button worksList__metaButton" type="button" id="worksListCopySeriesButton">copy series</button>
    </div>
  </div>

  <div class="tagStudioList__head worksList__head" role="group" aria-label="Sort studio works">
    <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="cat">
      cat <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
    </button>
    <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="year">
      year <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
    </button>
    <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="title">
      title <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
    </button>
    <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="series">
      series <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
    </button>
    <button class="tagStudioList__sortBtn" type="button" data-role="sort-button" data-sort-key="storage">
      storage <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
    </button>
  </div>

  <ul class="tagStudioList__rows" id="worksList"></ul>

  <nav class="page__nav" id="worksIndexBackNav" hidden>
    <a
      class="page__back"
      id="worksIndexBackLink"
      href="{{ '/series/' | relative_url }}"
    >← series</a>
  </nav>
</div>
<p id="worksStudioEmpty" hidden>no studio works yet</p>

{% include studio_module_script.html src='/assets/studio/js/studio-works.js' %}
