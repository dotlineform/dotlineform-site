---
layout: studio
title: "Analytics Dashboard"
permalink: /studio/analytics/
studio_domain: analytics
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-analytics
---

<div class="studioDashboard">
  <p class="studioDashboard__intro">Analytics groups together the analytical and contextual tools around the portfolio. Current tag tooling remains live here while the wider Analytics plan is developed.</p>

  <section class="studioDashboard__metrics" aria-label="Analytics metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Tags</p>
      <p class="studioMetricCard__value" data-studio-metric="tag-count">--</p>
      <p class="studioMetricCard__meta">Current tag registry entries available to analytical workflows.</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Tag groups</p>
      <p class="studioMetricCard__value" data-studio-metric="tag-group-count">--</p>
      <p class="studioMetricCard__meta">Allowed tag groups currently defined in the registry policy.</p>
    </article>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Current tools</h3>
      <p>These routes stay available while the broader Analytics dashboard definition is refined.</p>
    </div>
    <div class="studioCardGrid">
      <a class="studioCardLink" href="{{ '/studio/tag-registry/' | relative_url }}">
        <h4>Tag registry</h4>
        <p>Maintain the canonical registry of analytical tags.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/tag-aliases/' | relative_url }}">
        <h4>Tag aliases</h4>
        <p>Manage alias mappings and promotion flows for analytical terms.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/tag-groups/' | relative_url }}">
        <h4>Tag groups</h4>
        <p>Review and maintain the grouping structure used by tagging workflows.</p>
      </a>
      <a class="studioCardLink" href="{{ '/studio/series-tags/' | relative_url }}">
        <h4>Series tags</h4>
        <p>Review tag assignments across series and move into record-level editing.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-analytics' | relative_url }}">
        <h4>Analytics plan</h4>
        <p>Parallel planning stub for the wider Analytics domain.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
