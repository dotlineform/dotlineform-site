---
layout: studio
title: "Data Sharing"
permalink: /studio/data-sharing/
section: data-sharing
studio_domain: data-sharing
studio_page_doc: /docs/?scope=studio&doc=studio-data-sharing
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="studioDashboard"
  id="studioDataSharingDashboardRoot"
  data-studio-static-route="studio-data-sharing"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="catalogueDashboardRoutes" aria-label="Data Sharing links">
    <section class="catalogueDashboardColumn">
      <h3>Share</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/data-sharing/prepare/?scope=library' | relative_url }}">prepare package</a></li>
        <li><a href="{{ '/studio/data-sharing/review/?scope=library' | relative_url }}">review returned package</a></li>
      </ul>
    </section>
  </section>
</div>

{% include studio_module_script.html src='/assets/studio/js/studio-static-route.js' %}
