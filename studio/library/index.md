---
layout: studio
title: "Library Dashboard"
permalink: /studio/library/
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-library
---

<div
  class="studioDashboard"
  id="studioLibraryDashboardRoot"
  data-studio-dashboard-route="studio-library"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="studioDashboard__metrics" aria-label="Library metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="library-doc-count">--</p>
      <p class="studioMetricCard__label">library docs</p>
    </article>
  </section>

  <section class="catalogueDashboardRoutes" aria-label="Library links">
    <section class="catalogueDashboardColumn">
      <h3>Manage</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/docs/?scope=library&mode=manage&doc=library' | relative_url }}">Library</a></li>
        <li><a href="{{ '/docs/?scope=library&mode=manage&doc=library&import=1' | relative_url }}">Docs Import</a></li>
        <li><a href="{{ '/docs/?scope=studio&mode=manage&doc=library-documents' | relative_url }}">Documents</a></li>
      </ul>
    </section>
    <section class="catalogueDashboardColumn">
      <h3>Data</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/export/?scope=library' | relative_url }}">export</a></li>
        <li><a href="{{ '/studio/import/?scope=library' | relative_url }}">import</a></li>
      </ul>
    </section>
  </section>
</div>

{% include studio_module_script.html src='/assets/studio/js/studio-dashboard.js' %}
