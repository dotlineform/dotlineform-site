---
layout: studio
title: Search Dashboard
permalink: /studio/search/
studio_domain: search
studio_page_doc: /docs/?scope=studio&doc=new-pipeline-refine-search
---

<div class="studioDashboard">
  <p class="studioDashboard__intro">Search is the admin-facing dashboard for the indexed search layers used across catalogue, library, and Studio docs.</p>

  <section class="studioDashboard__metrics" aria-label="Search metrics">
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Catalogue search entries</p>
      <p class="studioMetricCard__value" data-studio-metric="catalogue-search-count">--</p>
      <p class="studioMetricCard__meta">Indexed catalogue and moments entries available to public search.</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Library search entries</p>
      <p class="studioMetricCard__value" data-studio-metric="library-search-count">--</p>
      <p class="studioMetricCard__meta">Indexed library entries currently available in the library viewer.</p>
    </article>
    <article class="studioMetricCard">
      <p class="studioMetricCard__label">Studio docs search entries</p>
      <p class="studioMetricCard__value" data-studio-metric="studio-search-count">--</p>
      <p class="studioMetricCard__meta">Indexed Studio documentation entries available from the shared docs viewer.</p>
    </article>
  </section>

  <section class="studioDashboard__section">
    <div class="studioDashboard__sectionHeader">
      <h3>Current entry points</h3>
      <p>Search planning and validation can now start from a dedicated Studio surface rather than from scattered docs links.</p>
    </div>
    <div class="studioCardGrid">
      <a class="studioCardLink" href="{{ '/search/' | relative_url }}">
        <h4>Public search</h4>
        <p>Open the user-facing search runtime.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=new-pipeline-refine-search' | relative_url }}">
        <h4>Search plan</h4>
        <p>Parallel planning stub for Search administration and validation workflows.</p>
      </a>
      <a class="studioCardLink" href="{{ '/docs/?scope=studio&doc=search-change-log' | relative_url }}">
        <h4>Search change log</h4>
        <p>Review recent search implementation notes and historical changes.</p>
      </a>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-dashboard.js' | relative_url }}"></script>
