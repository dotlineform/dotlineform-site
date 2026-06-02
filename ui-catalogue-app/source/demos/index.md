---
title: "UI Catalogue Demos"
permalink: /ui-catalogue/demos/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
---

<link rel="stylesheet" href="{{ '/ui-catalogue/app/assets/css/ui-catalogue-demo.css' | relative_url }}">

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoIndexRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demos"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoIndexHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow">Demo Namespace</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoIndexHeading">Isolated UI catalogue demos</h3>
      <p class="uiCatalogueDemoIntro">These pages use demo-only markup, CSS, and JavaScript. They are a designer/developer reference for building new UI patterns, not live Studio CSS checks.</p>
    </div>
  </section>
<section class="uiCatalogueDemoNav" aria-label="Example UI catalogue links">
  <section class="uiCatalogueDemoNav__group">
    <h3 class="uiCatalogueDemoHeading">Primitives</h3>
    <ul class="uiCatalogueDemoNav__list">
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/primitives/button/' | relative_url }}">button</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/primitives/input/' | relative_url }}">input</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/primitives/list/' | relative_url }}">list</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/primitives/modal-shell/' | relative_url }}">modal shell</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/primitives/panel/' | relative_url }}">panel</a></li>
    </ul>
  </section>
  <section class="uiCatalogueDemoNav__group">
    <h3 class="uiCatalogueDemoHeading">Composition Patterns</h3>
    <ul class="uiCatalogueDemoNav__list">
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/patterns/action-menu/' | relative_url }}">action menu</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/patterns/reopenable-command-result/' | relative_url }}">reopenable command result</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/patterns/select-menu/' | relative_url }}">select menu</a></li>
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/demos/patterns/column-links/' | relative_url }}">column links</a></li>
    </ul>
  </section>
  <section class="uiCatalogueDemoNav__group">
    <h3 class="uiCatalogueDemoHeading">References</h3>
    <ul class="uiCatalogueDemoNav__list">
      <li><a class="uiCatalogueDemoNav__link" href="{{ '/ui-catalogue/palette/' | relative_url }}">palette</a></li>
    </ul>
  </section>
</section>
</div>

<script type="module" src="{{ '/ui-catalogue/app/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
