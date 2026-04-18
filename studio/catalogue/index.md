---
layout: studio
title: Catalogue Dashboard
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
          <p>Create draft records and import new source content.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-new-work/' | relative_url }}"><span class="studioLinkList__title">Create New Work</span><span class="studioLinkList__meta">Create a draft work record in the JSON catalogue pipeline.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-new-series/' | relative_url }}"><span class="studioLinkList__title">Create New Series</span><span class="studioLinkList__meta">Create a series record and establish the series-level metadata boundary.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-new-work-detail/' | relative_url }}"><span class="studioLinkList__title">Create New Detail</span><span class="studioLinkList__meta">Create a new work detail record for an existing work.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-new-work-file/' | relative_url }}"><span class="studioLinkList__title">Create New File</span><span class="studioLinkList__meta">Create a new downloadable file record for an existing work.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-new-work-link/' | relative_url }}"><span class="studioLinkList__title">Create New Link</span><span class="studioLinkList__meta">Create a new published link record for an existing work.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-moment-import/' | relative_url }}"><span class="studioLinkList__title">Import Moment</span><span class="studioLinkList__meta">Import one moment from an explicit markdown source file and publish it into the runtime.</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Edit</h4>
          <p>Open an editor route, then search for the record you need.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work/' | relative_url }}"><span class="studioLinkList__title">Edit Work</span><span class="studioLinkList__meta">Search by work id and open a single-work metadata editor.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-series/' | relative_url }}"><span class="studioLinkList__title">Edit Series</span><span class="studioLinkList__meta">Search by series title and manage metadata plus member works.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work-detail/' | relative_url }}"><span class="studioLinkList__title">Edit Work Detail</span><span class="studioLinkList__meta">Search by detail id and open a single-detail metadata editor.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work-file/' | relative_url }}"><span class="studioLinkList__title">Edit Work File</span><span class="studioLinkList__meta">Search by file id and edit one work-file record.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-work-link/' | relative_url }}"><span class="studioLinkList__title">Edit Work Link</span><span class="studioLinkList__meta">Search by link id and edit one work-link record.</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Review</h4>
          <p>Use review pages to find draft records, inspect activity, and follow rebuild effects.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-status/' | relative_url }}"><span class="studioLinkList__title">Review Catalogue Status</span><span class="studioLinkList__meta">Inspect non-published source records and jump into the matching editor routes.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/catalogue-activity/' | relative_url }}"><span class="studioLinkList__title">Review Source Activity</span><span class="studioLinkList__meta">Inspect recent source changes and follow up on affected records.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/build-activity/' | relative_url }}"><span class="studioLinkList__title">Review Build Activity</span><span class="studioLinkList__meta">Review rebuild outcomes and confirm which generated outputs changed.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/studio-works/' | relative_url }}"><span class="studioLinkList__title">Open Works View</span><span class="studioLinkList__meta">Review the current works index and jump into portfolio-specific checks.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/bulk-add-work/' | relative_url }}"><span class="studioLinkList__title">Run Bulk Add Work</span><span class="studioLinkList__meta">Stage or import batches where a single-record flow is too slow.</span></a></li>
        </ul>
      </section>
      <section class="studioLinkGroup">
        <div class="studioLinkGroup__header">
          <h4>Guidance</h4>
          <p>Docs support the workflow, but the dashboard should remain the primary entry surface.</p>
        </div>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan' | relative_url }}"><span class="studioLinkList__title">Studio Implementation Plan</span><span class="studioLinkList__meta">Current phased plan for Studio shell, Catalogue refinement, moments, and later workstreams.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=scripts-main-pipeline' | relative_url }}"><span class="studioLinkList__title">Main Pipeline</span><span class="studioLinkList__meta">Reference for the current pipeline stages and the script boundaries they rely on.</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/docs/?scope=studio&doc=studio' | relative_url }}"><span class="studioLinkList__title">Studio Docs</span><span class="studioLinkList__meta">Shared Studio runtime, UI, and implementation notes.</span></a></li>
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
        <p>Create new work records from the dedicated create flow, then use Catalogue Status to review and reopen records for editing.</p>
      </article>
      <article class="studioInfoCard">
        <h4>Series records</h4>
        <p>Create new series from the series flow, then use catalogue pages to connect works, metadata, and build actions.</p>
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
