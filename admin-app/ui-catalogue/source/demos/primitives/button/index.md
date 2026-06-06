---
title: "UI Demo Primitive: Button"
permalink: /admin/ui-catalogue/demos/primitives/button/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-button
ui_catalogue_demo_primitive: button
---

<link rel="stylesheet" href="{{ '/admin/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture field_markup %}<div class="uiCatalogueDemoFieldGroup">
  <div class="uiCatalogueDemoFieldGrid">
    <input class="uiCatalogueDemoInput" type="text" value="Shared field example">
    <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Save</button>
  </div>
  <p class="uiCatalogueDemoStatus" data-state="success">Saved.</p>
</div>
{% endcapture %}
{% capture command_markup %}<button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Save</button>
{% endcapture %}
{% capture modal_markup %}<div class="uiCatalogueDemoModal__actions">
  <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Cancel</button>
  <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button">OK</button>
</div>
{% endcapture %}
{% capture disabled_markup %}<button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" disabled>Save</button>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoButtonRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-button"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoButtonIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/admin/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-primitive-button' | relative_url }}">Docs viewer: Button Primitive</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Primitive</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoButtonIntroHeading">Button demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates command-button patterns with <code>uiCatalogueDemo*</code> classes only. New live UI should map these examples into the owning production namespace deliberately.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoButtonLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoButtonLiveHeading">Demo Variants</h3>
      <p class="uiCatalogueDemoSummary">The rendered examples are isolated from live Studio button CSS.</p>
    </div>
<div class="uiCatalogueDemoGrid">
  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Button Next To A Field</h3>
      <p class="uiCatalogueDemoExample__summary">A command aligns with a neighbouring field and keeps feedback beside the command area.</p>
    </header>
    <div class="uiCatalogueDemoFieldGroup">
      <div class="uiCatalogueDemoFieldGrid">
        <input class="uiCatalogueDemoInput" type="text" value="Shared field example">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Save</button>
      </div>
      <p class="uiCatalogueDemoStatus" data-state="success">Saved.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Command Button</h3>
      <p class="uiCatalogueDemoExample__summary">All shared command buttons use the same compact height and optional default width.</p>
    </header>
    <div class="uiCatalogueDemoActions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Save</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Default Width Pair</h3>
      <p class="uiCatalogueDemoExample__summary">Short and long labels share a predictable width inside the same action row.</p>
    </header>
    <div class="uiCatalogueDemoButtonPair">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">OK</button>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Cancel</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Modal Action Row</h3>
      <p class="uiCatalogueDemoExample__summary">The modal shell owns alignment; the button namespace only owns button geometry and visual weight.</p>
    </header>
    <div class="uiCatalogueDemoModal__actions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Cancel</button>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button">OK</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Destructive Command</h3>
      <p class="uiCatalogueDemoExample__summary">Destructive meaning belongs to the flow and confirmation copy, not a special default button color.</p>
    </header>
    <div class="uiCatalogueDemoActions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Delete</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Disabled</h3>
      <p class="uiCatalogueDemoExample__summary">Disabled state keeps geometry stable.</p>
    </header>
    <div class="uiCatalogueDemoActions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" disabled>Save</button>
    </div>
  </section>
</div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoButtonCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoButtonCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Copy these snippets as demo patterns, then map the classes into live implementation code when building a real route.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Small Button Next To A Field</h4>
        <pre><code>{{ field_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Command Button</h4>
        <pre><code>{{ command_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Modal Action Row</h4>
        <pre><code>{{ modal_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Disabled</h4>
        <pre><code>{{ disabled_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/admin/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
