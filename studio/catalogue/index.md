---
layout: studio
title: "Catalogue Dashboard"
permalink: /studio/catalogue/
studio_domain: catalogue
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-studio-implementation-plan
---

<div class="studioDashboard">
  <section class="studioDashboard__metrics" aria-label="Catalogue metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="series-count">--</p>
      <p class="studioMetricCard__label">series</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="works-count">--</p>
      <p class="studioMetricCard__label">works</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="work-details-count">--</p>
      <p class="studioMetricCard__label">work details</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__value" data-studio-metric="moments-count">--</p>
      <p class="studioMetricCard__label">moments</p>
    </article>
  </section>

  <section class="catalogueDashboardRoutes" aria-label="Catalogue links">
    <section class="catalogueDashboardColumn">
      <h3>Edit</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/catalogue-series/' | relative_url }}">series</a></li>
        <li><a href="{{ '/studio/catalogue-work/' | relative_url }}">works</a></li>
        <li><a href="{{ '/studio/catalogue-work-detail/' | relative_url }}">work details</a></li>
        <li><a href="{{ '/studio/bulk-add-work/' | relative_url }}">bulk add</a></li>
        <li><a href="{{ '/studio/catalogue-moment/' | relative_url }}">moments</a></li>
      </ul>
    </section>
    <section class="catalogueDashboardColumn">
      <h3>Review</h3>
      <ul class="catalogueDashboardPills">
        <li><a href="{{ '/studio/catalogue-status/' | relative_url }}">drafts</a></li>
        <li><a href="{{ '/studio/studio-works/' | relative_url }}">works</a></li>
        <li><a href="{{ '/studio/project-state/' | relative_url }}">projects</a></li>
      </ul>
    </section>
  </section>

  <section aria-labelledby="catalogueAdminHeading">
    <h3 id="catalogueAdminHeading">Admin</h3>
    <p><a href="{{ '/studio/catalogue-activity/' | relative_url }}">catalogue activity</a></p>
    <p><a href="{{ '/studio/build-activity/' | relative_url }}">build activity</a></p>
  </section>

</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
