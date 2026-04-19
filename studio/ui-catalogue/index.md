---
layout: studio
title: UI Catalogue
permalink: /studio/ui-catalogue/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage studioUiCataloguePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta">
    <p class="studioUiCataloguePage__intro">Use the UI catalogue as the live reference surface for shared primitives. Each primitive page should show the real implementation first, then short editable notes and canonical copyable markup.</p>
  </section>

  <section class="tagStudio__panel studioUiCatalogueIndex" aria-labelledby="studioUiCatalogueListHeading">
    <div class="studioUiCatalogueIndex__header">
      <h3 class="tagStudio__heading" id="studioUiCatalogueListHeading">First Primitive Pages</h3>
      <p class="studioUiCatalogueIndex__summary">Start with live pages rather than long framework docs. Add new primitives here as soon as they become repeated shared elements.</p>
    </div>
    <ul class="studioUiCatalogueIndex__list">
      <li>
        <a class="studioUiCatalogueIndex__item" href="{{ '/studio/ui-catalogue/panel/' | relative_url }}">
          <span class="studioUiCatalogueIndex__title">Panel</span>
          <span class="studioUiCatalogueIndex__meta">Live primitive page with shared shell variants and markdown-backed notes.</span>
        </a>
      </li>
    </ul>
  </section>
</div>
