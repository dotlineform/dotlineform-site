---
layout: studio
title: "UI Catalogue"
permalink: /studio/ui-catalogue/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage studioUiCataloguePage"
  id="studioUiCatalogueRoot"
  data-studio-static-route="studio-ui-catalogue"
  data-studio-mode="reference"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="tagStudioPage__context tagStudioPage__context--meta">
    <p class="studioUiCataloguePage__intro">Use the UI catalogue as the live reference surface for shared primitives. Each primitive page should show the real implementation first, link to its matching docs-viewer contract, then provide short editable notes and canonical copyable markup.</p>
  </section>

  <section class="catalogueDashboardRoutes" aria-label="UI catalogue links">
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
</div>

{% include studio_module_script.html src='/assets/studio/js/studio-static-route.js' %}
