---
layout: studio
title: "Review Returned Package"
permalink: /studio/data-sharing/review/
section: data-sharing-review
studio_domain: data-sharing
studio_page_doc: /docs/?scope=studio&doc=studio-data-sharing
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage dataSharingReviewPage"
  id="dataSharingReviewRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel dataSharingReviewPage__panel">
    <div class="dataSharingReviewPage__controls">
      <label class="tagStudioField dataSharingReviewPage__scopeField" for="dataSharingReviewScopeSelect">
        <span class="tagStudioField__label" id="dataSharingReviewScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataSharingReviewScopeSelect"></select>
        </span>
      </label>
      <label class="tagStudioField dataSharingReviewPage__field" for="dataSharingReviewFileSelect">
        <span class="tagStudioField__label" id="dataSharingReviewFileLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataSharingReviewFileSelect"></select>
        </span>
      </label>
      <div class="dataSharingReviewPage__commandButtons">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataSharingReviewRun"></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataSharingReviewUpdateSummary" disabled></button>
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataSharingReviewApplyHierarchy" disabled></button>
      </div>
    </div>

    <div class="dataSharingReviewPage__statusRow">
      <p class="tagStudio__status" id="dataSharingReviewStatus"></p>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn dataSharingReviewPage__resultButton" id="dataSharingReviewResults" hidden></button>
    </div>
    <p class="tagStudioForm__meta dataSharingReviewPage__selectionSummary" id="dataSharingReviewSelectionSummary"></p>

    <div class="dataSharingReviewPage__listActions" aria-label="Returned package review selection actions">
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataSharingReviewSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataSharingReviewClear"></button>
    </div>

    <div class="tagStudioList dataSharingReviewList" id="dataSharingReviewList"></div>

    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="dataSharingReviewBootStatus">loading Data Sharing...</p>

{% include studio_module_script.html src='/assets/studio/js/data-sharing-review.js' %}
