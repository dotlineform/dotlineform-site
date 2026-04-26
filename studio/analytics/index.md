---
layout: studio
title: "Analytics Dashboard"
permalink: /studio/analytics/
studio_domain: analytics
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-analytics
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

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
      <a class="tagStudio__panel tagStudio__panelLink" href="{{ '/studio/docs-import/?scope=analysis' | relative_url }}">
        <h4>Import analysis doc</h4>
        <p>Import staged HTML into the Analysis docs source for manage-mode review.</p>
      </a>
      <div class="tagStudio__panel">
        <h4>Tag tools</h4>
        <p>Maintain analytical tags, aliases, groups, and series assignments.</p>
        <ul class="studioLinkList">
          <li><a class="studioLinkList__item" href="{{ '/studio/tag-registry/' | relative_url }}"><span class="studioLinkList__title">Tag registry</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/tag-aliases/' | relative_url }}"><span class="studioLinkList__title">Tag aliases</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/tag-groups/' | relative_url }}"><span class="studioLinkList__title">Tag groups</span></a></li>
          <li><a class="studioLinkList__item" href="{{ '/studio/series-tags/' | relative_url }}"><span class="studioLinkList__title">Series tags</span></a></li>
        </ul>
      </div>
      <a class="tagStudio__panel tagStudio__panelLink" href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-analytics' | relative_url }}">
        <h4>Analytics plan</h4>
        <p>Parallel planning stub for the wider Analytics domain.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
