---
layout: studio
title: "UI Pattern: Column Links"
permalink: /studio/ui-catalogue/column-links/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-column-links
ui_catalogue_pattern: column-links
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture column_links_markup %}<section class="catalogueDashboardRoutes" aria-label="Example links">
  <section class="catalogueDashboardColumn">
    <h3>Primitives</h3>
    <ul class="catalogueDashboardPills">
      <li><a href="{{ '/studio/ui-catalogue/button/' | relative_url }}">button</a></li>
      <li><a href="{{ '/studio/ui-catalogue/input/' | relative_url }}">input</a></li>
      <li><a href="{{ '/studio/ui-catalogue/list/' | relative_url }}">list</a></li>
      <li><a href="{{ '/studio/ui-catalogue/panel/' | relative_url }}">panel</a></li>
    </ul>
  </section>
  <section class="catalogueDashboardColumn">
    <h3>Composition Patterns</h3>
    <ul class="catalogueDashboardPills">
      <li><a href="{{ '/studio/ui-catalogue/reopenable-command-result/' | relative_url }}">reopenable command result</a></li>
      <li><a href="{{ '/studio/ui-catalogue/column-links/' | relative_url }}">column links</a></li>
    </ul>
  </section>
</section>
{% endcapture %}

<div
  class="tagStudioPage studioUiPrimitivePage studioUiPatternPage"
  id="studioUiCatalogueColumnLinksRoot"
  data-studio-static-route="studio-ui-catalogue-column-links"
  data-studio-mode="reference"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-column-links' | relative_url }}">Docs viewer: Column Links Pattern</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Composition Pattern</p>
    <p class="studioUiPrimitivePage__intro">This page is the visual reference for compact two-column link groups used by Studio dashboard and catalogue entry pages.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioColumnLinksLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioColumnLinksLiveHeading">Live Composition</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Use this for small sets of repeated route links where categories matter more than descriptions.</p>
    </div>
    {{ column_links_markup }}
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioColumnLinksCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioColumnLinksCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Keep labels short enough to fit pill buttons without turning the layout into a card grid.</p>
    </div>
    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Two Column Link Group</h4>
        <pre><code>{{ column_links_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-static-route.js' | relative_url }}"></script>
