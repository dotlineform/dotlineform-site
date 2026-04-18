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
      <h3>Workflow Entry Points</h3>
      <p>Start with creation flows, then move into status and activity pages to validate and rebuild.</p>
    </div>
    <div class="studioCardGrid">
      <a class="studioCardLink" href="{{ '/studio/catalogue-new-work/' | relative_url }}">
        <h4>New work</h4>
        <p>Create a new work record in the JSON catalogue pipeline.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/catalogue-new-series/' | relative_url }}">
        <h4>New series</h4>
        <p>Create a series record and establish the series-level metadata boundary.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/catalogue-status/' | relative_url }}">
        <h4>Catalogue status</h4>
        <p>Review catalogue state, locate records, and move into editing flows.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/studio-works/' | relative_url }}">
        <h4>Works view</h4>
        <p>Review the current works index and jump into portfolio-specific checks.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/bulk-add-work/' | relative_url }}">
        <h4>Bulk add work</h4>
        <p>Stage or import batches where a single-record flow is too slow.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/catalogue-activity/' | relative_url }}">
        <h4>Catalogue activity</h4>
        <p>Inspect recent source changes and follow up on affected records.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/build-activity/' | relative_url }}">
        <h4>Build activity</h4>
        <p>Review rebuild outcomes and confirm which generated outputs changed.</p>
      </a>
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
    </div>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Guidance</h3>
      <p>Documentation remains available for implementation context, but the dashboard is intended to be the main entry surface.</p>
    </div>
    <div class="studioCardGrid">
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan' | relative_url }}">
        <h4>Studio implementation plan</h4>
        <p>Current phased plan for Studio shell, Catalogue refinement, moments, and later workstreams.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=scripts-main-pipeline' | relative_url }}">
        <h4>Main pipeline</h4>
        <p>Reference for the current pipeline stages and the script boundaries they rely on.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=studio' | relative_url }}">
        <h4>Studio docs</h4>
        <p>Shared Studio runtime, UI, and implementation notes.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
