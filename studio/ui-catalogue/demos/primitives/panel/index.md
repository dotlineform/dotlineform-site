---
layout: studio
title: "UI Demo Primitive: Panel"
permalink: /studio/ui-catalogue/demos/primitives/panel/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-panel
ui_catalogue_demo_primitive: panel
---

<link rel="stylesheet" href="{{ '/studio/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture panel_markup %}<div class="uiCatalogueDemoPanel">
  <h4 class="uiCatalogueDemoPanel__heading">Panel Heading</h4>
  <p class="uiCatalogueDemoText">Panel body content goes here.</p>
</div>
{% endcapture %}
{% capture compact_markup %}<div class="uiCatalogueDemoPanel uiCatalogueDemoPanel--compact">
  <h4 class="uiCatalogueDemoPanel__heading">Compact Panel</h4>
  <p class="uiCatalogueDemoText">Use for denser supporting content.</p>
</div>
{% endcapture %}
{% capture nested_markup %}<div class="uiCatalogueDemoPanel">
  <h4 class="uiCatalogueDemoPanel__heading">Parent Panel</h4>
  <div class="uiCatalogueDemoPanel uiCatalogueDemoPanel--compact">
    <h4 class="uiCatalogueDemoPanel__heading">Nested Panel</h4>
    <p class="uiCatalogueDemoText">The nested panel reads as a subordinate surface.</p>
  </div>
</div>
{% endcapture %}
{% capture image_markup %}<a
  class="uiCatalogueDemoPanel uiCatalogueDemoPanel--image uiCatalogueDemoPanel--imageContrast"
  href="#"
  style="--ui-demo-panel-image: url('/assets/moments/img/blue-sky-thumb-96.webp');"
>
  <h4 class="uiCatalogueDemoPanel__heading">Image Panel Link</h4>
  <p class="uiCatalogueDemoText">Use the contrast modifier when the image needs white text.</p>
</a>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoPanelRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-panel"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoPanelIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/studio/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-primitive-panel' | relative_url }}">Docs viewer: Panel Primitive</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Primitive</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoPanelIntroHeading">Panel demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates panel composition with demo-only classes. It is a reference for mapping structure into live surfaces, not a live panel CSS check.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoPanelLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoPanelLiveHeading">Demo Variants</h3>
      <p class="uiCatalogueDemoSummary">The examples cover default, compact, editor, nested, link, and image panel composition.</p>
    </div>
<div class="uiCatalogueDemoGrid">
  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Default</h3>
      <p class="uiCatalogueDemoExample__summary">Base shared surface for grouped content.</p>
    </header>
    <div class="uiCatalogueDemoPanel">
      <h4 class="uiCatalogueDemoPanel__heading">Panel Heading</h4>
      <p class="uiCatalogueDemoText">Shared surface, border, radius, and padding with no extra layout behavior.</p>
      <div class="uiCatalogueDemoActions">
        <a class="uiCatalogueDemoButton" href="#">Action</a>
      </div>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Compact</h3>
      <p class="uiCatalogueDemoExample__summary">Same shell with reduced padding.</p>
    </header>
    <div class="uiCatalogueDemoPanel uiCatalogueDemoPanel--compact">
      <h4 class="uiCatalogueDemoPanel__heading">Compact Panel</h4>
      <p class="uiCatalogueDemoText">Use when standard panel spacing is too loose but containment is still needed.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Editor</h3>
      <p class="uiCatalogueDemoExample__summary">Same shell with stacked editor rhythm.</p>
    </header>
    <div class="uiCatalogueDemoPanel uiCatalogueDemoPanel--editor">
      <h4 class="uiCatalogueDemoPanel__heading">Editor Panel</h4>
      <label class="uiCatalogueDemoField" for="uiCatalogueDemoPanelName">
        <span class="uiCatalogueDemoField__label">name</span>
        <span class="uiCatalogueDemoField__control">
          <input class="uiCatalogueDemoInput" id="uiCatalogueDemoPanelName" type="text" value="Shared panel example">
        </span>
      </label>
      <p class="uiCatalogueDemoText">The editor variant keeps the same shell and adds stacked control spacing only.</p>
      <div class="uiCatalogueDemoActions">
        <button class="uiCatalogueDemoButton" type="button">Save</button>
      </div>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Nested</h3>
      <p class="uiCatalogueDemoExample__summary">Supported self-composition for grouped subsections.</p>
    </header>
    <div class="uiCatalogueDemoPanel">
      <h4 class="uiCatalogueDemoPanel__heading">Parent Panel</h4>
      <p class="uiCatalogueDemoText">Use nested panels when a child group needs its own boundary inside a larger panel.</p>
      <div class="uiCatalogueDemoPanel uiCatalogueDemoPanel--compact">
        <h4 class="uiCatalogueDemoPanel__heading">Nested Panel</h4>
        <p class="uiCatalogueDemoText">The child panel should read as a subordinate surface without page-level compensation.</p>
      </div>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Panel Link</h3>
      <p class="uiCatalogueDemoExample__summary">Static content, whole panel clickable, fixed design-time height.</p>
    </header>
    <a class="uiCatalogueDemoPanel" href="#">
      <h4 class="uiCatalogueDemoPanel__heading">Panel Link</h4>
      <p class="uiCatalogueDemoText">Use for dashboard and landing-page navigation panels where dimensions should stay fixed.</p>
    </a>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Image Panel Link</h3>
      <p class="uiCatalogueDemoExample__summary">Base image-fill panel with dark text kept intact.</p>
    </header>
    <a
      class="uiCatalogueDemoPanel uiCatalogueDemoPanel--image"
      href="#"
      style="--ui-demo-panel-image: url('{{ '/assets/moments/img/blue-sky-thumb-96.webp' | relative_url }}');"
    >
      <h4 class="uiCatalogueDemoPanel__heading">Image Panel Link</h4>
      <p class="uiCatalogueDemoText">Choose image and overlay together at design time.</p>
    </a>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Image Panel Link: Contrast Override</h3>
      <p class="uiCatalogueDemoExample__summary">Common design-led override for darker or busier source images.</p>
    </header>
    <a
      class="uiCatalogueDemoPanel uiCatalogueDemoPanel--image uiCatalogueDemoPanel--imageContrast"
      href="#"
      style="--ui-demo-panel-image: url('{{ '/assets/moments/img/blue-sky-thumb-96.webp' | relative_url }}');"
    >
      <h4 class="uiCatalogueDemoPanel__heading">Image Panel Link: Contrast Override</h4>
      <p class="uiCatalogueDemoText">Use the contrast modifier when the chosen image needs white text.</p>
    </a>
  </section>
</div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoPanelCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoPanelCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">These examples define the demo pattern vocabulary before any production mapping.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Default</h4>
        <pre><code>{{ panel_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Compact</h4>
        <pre><code>{{ compact_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Nested</h4>
        <pre><code>{{ nested_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Image Link With Contrast</h4>
        <pre><code>{{ image_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/studio/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
