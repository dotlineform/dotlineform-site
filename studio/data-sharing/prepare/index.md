---
layout: studio
title: "Prepare Share Package"
permalink: /studio/data-sharing/prepare/
section: data-sharing-prepare
studio_domain: data-sharing
studio_page_doc: /docs/?scope=studio&doc=studio-data-sharing
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage dataSharingPreparePage"
  id="dataSharingPrepareRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel dataSharingPreparePage__panel">
    <div class="dataSharingPreparePage__controls">
      <label class="tagStudioField dataSharingPreparePage__scopeField" for="dataSharingPrepareScopeSelect">
        <span class="tagStudioField__label" id="dataSharingPrepareScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataSharingPrepareScopeSelect"></select>
        </span>
      </label>
      <label class="tagStudioField dataSharingPreparePage__field" for="dataSharingPrepareConfigSelect">
        <span class="tagStudioField__label" id="dataSharingPrepareConfigLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="dataSharingPrepareConfigSelect"></select>
        </span>
      </label>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="dataSharingPrepareRun"></button>
      <fieldset class="dataSharingPreparePage__format" id="dataSharingPrepareFormatWrap">
        <legend id="dataSharingPrepareFormatLabel"></legend>
        <span class="dataSharingPreparePage__formatOptions" id="dataSharingPrepareFormatOptions"></span>
      </fieldset>
      <label class="dataSharingPreparePage__toggle" id="dataSharingPrepareMissingSummaryWrap" hidden>
        <input type="checkbox" id="dataSharingPrepareMissingSummaryOnly">
        <span id="dataSharingPrepareMissingSummaryLabel"></span>
      </label>
    </div>

    <p class="tagStudio__status" id="dataSharingPrepareStatus"></p>
    <p class="tagStudioForm__meta dataSharingPreparePage__selectionSummary" id="dataSharingPrepareSelectionSummary"></p>

    <div class="dataSharingPreparePage__listActions" aria-label="Share package document selection actions">
      <span class="dataSharingPreparePage__filterPills" id="dataSharingPrepareListFilters" aria-label="Data Sharing list filters"></span>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataSharingPrepareSelectAll"></button>
      <button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" id="dataSharingPrepareClear"></button>
    </div>

    <div class="tagStudioList dataSharingPrepareList" id="dataSharingPrepareList"></div>
    <div data-studio-modal-host="true"></div>
  </div>
</div>

<p class="tagStudio__status" id="dataSharingPrepareBootStatus">loading Data Sharing...</p>

{% include studio_module_script.html src='/assets/studio/js/data-sharing-prepare.js' %}
