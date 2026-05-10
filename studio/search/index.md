---
layout: studio
title: "Search Dashboard"
permalink: /studio/search/
studio_domain: search
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-search
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="studioDashboard"
  id="studioSearchDashboardRoot"
  data-studio-dashboard-route="studio-search"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="studioDashboard__metrics" aria-label="Search metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="catalogue-search-count">--</p>
      <p class="studioMetricCard__label">catalogue search entries</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="library-search-count">--</p>
      <p class="studioMetricCard__label">library search entries</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="studio-search-count">--</p>
      <p class="studioMetricCard__label">studio docs search entries</p>
    </article>
  </section>

  <section class="catalogueDashboardRoutes" aria-label="Search links">
    <section class="catalogueDashboardColumn">
      <h3>interface</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/search/' | relative_url }}">public search</a></li>
      </ul>
    </section>
    <section class="catalogueDashboardColumn">
      <h3>documents</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-search' | relative_url }}">plan</a></li>
        <li><a href="{{ '/docs/?scope=studio&doc=search-change-log' | relative_url }}">change log</a></li>
      </ul>
    </section>
  </section>
</div>

{% include studio_module_script.html src='/assets/studio/js/studio-dashboard.js' %}
