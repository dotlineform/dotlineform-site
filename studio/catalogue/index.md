---
layout: studio
title: "Catalogue Dashboard"
permalink: /studio/catalogue/
studio_domain: catalogue
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-studio-implementation-plan
---

<div class="studioDashboard">
  <p class="studioDashboard__intro">Use Catalogue to create records, review pipeline state, and move between work, series, and build tasks without relying on the docs.</p>

  <section class="studioDashboard__metrics" aria-label="Catalogue metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Works</p>
      <p class="studioMetricCard__value" data-studio-metric="works-count">--</p>
      <p class="studioMetricCard__meta">Published and draft work records in the generated index.</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Series</p>
      <p class="studioMetricCard__value" data-studio-metric="series-count">--</p>
      <p class="studioMetricCard__meta">Series records currently represented in the catalogue index.</p>
    </article>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Catalogue Routes</h3>
      <p>Use the dashboard as the normal entry point. Start with directional links rather than docs, then move into status, activity, and rebuild pages as needed.</p>
    </div>
    <div class="studioDashboard__linkGroups">
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Create</h4>
          <p>Import new source content. Create work, series, and detail records from their editor routes.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-moment-import/' | relative_url }}"><span class="studioLinkList__title">Import Moment</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Edit</h4>
          <p>Open an editor route, then search for the record you need.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work/' | relative_url }}"><span class="studioLinkList__title">Work Editor</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-series/' | relative_url }}"><span class="studioLinkList__title">Series Editor</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-moment/' | relative_url }}"><span class="studioLinkList__title">Edit Moment</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work-detail/' | relative_url }}"><span class="studioLinkList__title">Edit Work Detail</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Review</h4>
          <p>Use review pages to find draft records, inspect activity, and follow rebuild effects.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-status/' | relative_url }}"><span class="studioLinkList__title">Review Catalogue Status</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-status/' | relative_url }}?view=draft-works"><span class="studioLinkList__title">Review Draft Works</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-status/' | relative_url }}?view=draft-series"><span class="studioLinkList__title">Review Draft Series</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-activity/' | relative_url }}"><span class="studioLinkList__title">Review Source Activity</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/project-state/' | relative_url }}"><span class="studioLinkList__title">Review Project State</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/build-activity/' | relative_url }}"><span class="studioLinkList__title">Review Build Activity</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/studio-works/' | relative_url }}"><span class="studioLinkList__title">Open Works View</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/bulk-add-work/' | relative_url }}"><span class="studioLinkList__title">Run Bulk Add Work</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Guidance</h4>
          <p>Docs support the workflow, but the dashboard should remain the primary entry surface.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan' | relative_url }}"><span class="studioLinkList__title">Studio Implementation Plan</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=scripts-main-pipeline' | relative_url }}"><span class="studioLinkList__title">Main Pipeline</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=studio' | relative_url }}"><span class="studioLinkList__title">Studio Docs</span></a></li>
        </ul>
      </section>
    </div>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Workflow Summary</h3>
      <p>Normal day-to-day work should move through create or edit, validate the record, and then confirm rebuild effects.</p>
    </div>
    <div class="studioInfoGrid">
      <article class="studioInfoCard">
        <h4>Work records</h4>
        <p>Create and edit work records from the Work Editor. Work details are created from the current parent work.</p>
      </article>
      <article class="studioInfoCard">
        <h4>Series records</h4>
        <p>Create and edit series from the Series Editor, then connect works, metadata, and build actions after the draft exists.</p>
      </article>
      <article class="studioInfoCard">
        <h4>Operational checks</h4>
        <p>Use Catalogue Activity and Build Activity as the operational view once source writes or rebuild actions have run.</p>
      </article>
      <article class="studioInfoCard">
        <h4>Moments</h4>
        <p>Import existing source markdown files one at a time. Missing images are acceptable in this first phase.</p>
      </article>
    </div>
  </section>

</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
