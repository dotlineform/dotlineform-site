---
layout: studio
title: "Library Dashboard"
permalink: /studio/library/
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-library
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

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
      <a class="tagStudio__panel tagStudio__panelLink" href="{{ '/library/?mode=manage' | relative_url }}">
        <h4>Manage library</h4>
        <p>Open the Library viewer with local management controls enabled.</p>
      </a>
      <a class="tagStudio__panel tagStudio__panelLink" href="{{ '/studio/library-import/' | relative_url }}">
        <h4>Import</h4>
        <p>Import staged HTML into the published Library docs source, with optional Studio scope selection.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
