---
layout: studio
title: "Bulk Add Work"
permalink: /studio/bulk-add-work/
section: bulk-add-work
studio_page_doc: /docs/?scope=studio&doc=bulk-add-work
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">
{% assign bulk_import_workbook = site.data.pipeline.paths.workbooks.bulk_import | default: 'data/works_bulk_import.xlsx' %}

<div class="tagStudioPage catalogueWorkPage" id="bulkAddWorkRoot" data-workbook-path="{{ bulk_import_workbook | escape }}" hidden>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">bulk add work</h2>
      <span class="tagStudio__saveMode" id="bulkAddWorkSaveMode"></span>
    </div>

    <p class="tagStudio__contextHint" id="bulkAddWorkContext"></p>
    <p class="tagStudio__status" id="bulkAddWorkStatus"></p>
    <p class="tagStudio__saveWarning" id="bulkAddWorkWarning"></p>
    <p class="tagStudio__saveResult" id="bulkAddWorkResult"></p>
  </section>

  <div class="tagStudio__grid catalogueWorkPage__grid">
    <section class="tagStudio__panel tagStudio__panel--editor">
      <div class="tagStudio__headingRow">
        <h2 class="tagStudio__heading">import</h2>
        <div class="catalogueWorkPage__actions">
          <button type="button" class="tagStudio__button" id="bulkAddWorkPreview">Preview Import</button>
          <button type="button" class="tagStudio__button" id="bulkAddWorkApply">Apply Import</button>
        </div>
      </div>
      <div class="tagStudioForm__fields catalogueWorkForm__fields" id="bulkAddWorkFields">
        <label class="tagStudioForm__field catalogueWorkForm__field" for="bulkAddWorkMode">
          <span class="tagStudioForm__label">mode</span>
          <select class="tagStudio__input" id="bulkAddWorkMode">
            <option value="works">works</option>
            <option value="work_details">work details</option>
          </select>
        </label>
        <div class="tagStudioForm__field">
          <span class="tagStudioForm__label">workbook</span>
          <span class="tagStudio__input tagStudioForm__readonly" id="bulkAddWorkWorkbook">{{ bulk_import_workbook }}</span>
        </div>
      </div>
    </section>

    <aside class="tagStudio__panel catalogueWorkSummary">
      <h2 class="tagStudio__heading">preview summary</h2>
      <div class="tagStudioForm__fields" id="bulkAddWorkSummary"></div>
    </aside>
  </div>

  <section class="tagStudio__panel catalogueWorkDetails">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">preview details</h2>
    </div>
    <div class="catalogueWorkDetails__results" id="bulkAddWorkPreviewDetails"></div>
  </section>
</div>

<p class="tagStudio__status" id="bulkAddWorkLoading">loading bulk add work…</p>
<p class="tagStudio__empty" id="bulkAddWorkEmpty" hidden></p>

<script type="module" src="{{ '/assets/studio/js/bulk-add-work.js' | relative_url }}"></script>
