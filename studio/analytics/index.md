---
layout: studio
title: "Analytics Dashboard"
permalink: /studio/analytics/
studio_domain: analytics
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-analytics
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="studioDashboard"
  id="studioAnalyticsDashboardRoot"
  data-studio-dashboard-route="studio-analytics"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="studioDashboard__metrics" aria-label="Analytics metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="tag-count">--</p>
      <p class="studioMetricCard__label">tags</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="tag-group-count">--</p>
      <p class="studioMetricCard__label">tag groups</p>
    </article>
  </section>

  <section class="catalogueDashboardRoutes" aria-label="Analytics links">
    <section class="catalogueDashboardColumn">
      <h3>Data</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/export/?scope=analytics' | relative_url }}">export</a></li>
        <li><a href="{{ '/studio/import/?scope=analytics' | relative_url }}">import</a></li>
        <li><a href="{{ '/docs/?scope=analysis&mode=manage&doc=analysis&import=1' | relative_url }}">docs import</a></li>
        <li><a href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-analytics' | relative_url }}">plan</a></li>
      </ul>
    </section>
    <section class="catalogueDashboardColumn">
      <h3>Tags</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/analytics/tag-registry/' | relative_url }}">registry</a></li>
        <li><a href="{{ '/studio/analytics/tag-aliases/' | relative_url }}">aliases</a></li>
        <li><a href="{{ '/studio/analytics/tag-groups/' | relative_url }}">groups</a></li>
        <li><a href="{{ '/studio/analytics/series-tags/' | relative_url }}">series tags</a></li>
      </ul>
    </section>
  </section>
</div>

{% include studio_module_script.html src='/assets/studio/js/studio-dashboard.js' %}
