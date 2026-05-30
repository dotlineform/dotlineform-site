---
title: "UI Demo Pattern: Column Links"
permalink: /studio/ui-catalogue/demos/patterns/column-links/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-column-links
ui_catalogue_demo_pattern: column-links
---

<link rel="stylesheet" href="{{ '/studio/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture column_links_markup %}<section class="uiCatalogueDemoColumnLinks" aria-label="Example dashboard links">
  <section class="uiCatalogueDemoColumnLinks__column">
    <h3 class="uiCatalogueDemoHeading">Edit</h3>
    <ul class="uiCatalogueDemoColumnLinks__pills">
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">series</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">works</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">work details</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">bulk add</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">moments</a></li>
    </ul>
  </section>
  <section class="uiCatalogueDemoColumnLinks__column">
    <h3 class="uiCatalogueDemoHeading">Review</h3>
    <ul class="uiCatalogueDemoColumnLinks__pills">
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">drafts</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">works</a></li>
      <li><a class="uiCatalogueDemoColumnLinks__pill" href="#">projects</a></li>
    </ul>
  </section>
</section>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoColumnLinksRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-column-links"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoColumnLinksIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/studio/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-column-links' | relative_url }}">Docs viewer: Column Links Pattern</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Composition Pattern</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoColumnLinksIntroHeading">Column links demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This pattern combines labeled columns with vertically stacked pill links. It maps to dashboard route groups such as the Catalogue dashboard Edit and Review columns.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoColumnLinksLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoColumnLinksLiveHeading">Demo Composition</h3>
      <p class="uiCatalogueDemoSummary">Use the column count to fit the route groups; each column keeps its own heading and stacked pills.</p>
    </div>
    {{ column_links_markup }}
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoColumnLinksCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoColumnLinksCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Map this demo structure into the live dashboard namespace when implementing production routes.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Two Column Pill Links</h4>
        <pre><code>{{ column_links_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/studio/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
