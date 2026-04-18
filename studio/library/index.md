---
layout: studio
title: Library Dashboard
permalink: /studio/library/
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-library
---

<div class="studioDashboard">
  <p class="studioDashboard__intro">Use the Library dashboard as the admin-facing entry surface for the published library, its guidance docs, and future maintenance workflows.</p>

  <section class="studioDashboard__metrics" aria-label="Library metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Library docs</p>
      <p class="studioMetricCard__value" data-studio-metric="library-doc-count">--</p>
      <p class="studioMetricCard__meta">Documents currently exposed through the public library viewer.</p>
    </article>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Current entry points</h3>
      <p>The public library remains user-facing; this dashboard is the admin-facing route into that domain.</p>
    </div>
    <div class="studioCardGrid">
      <a class="studioCardLink" href="{{ '/library/' | relative_url }}">
        <h4>Published library</h4>
        <p>Open the public library viewer in its user-facing context.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-library' | relative_url }}">
        <h4>Library plan</h4>
        <p>Parallel planning stub for the Library domain and future Studio workflows.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=library' | relative_url }}">
        <h4>Library docs</h4>
        <p>Open the public-library documentation set from the shared docs viewer.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
