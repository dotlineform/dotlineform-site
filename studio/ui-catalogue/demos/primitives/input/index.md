---
layout: studio
title: "UI Demo Primitive: Input"
permalink: /studio/ui-catalogue/demos/primitives/input/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-input
ui_catalogue_demo_primitive: input
---

<link rel="stylesheet" href="{{ '/assets/ui-catalogue/css/ui-catalogue-demo.css' | relative_url }}">

{% capture default_markup %}<div class="uiCatalogueDemoField">
  <div class="uiCatalogueDemoField__control">
    <input class="uiCatalogueDemoInput" type="text" placeholder="80%">
  </div>
</div>
{% endcapture %}
{% capture stacked_markup %}<label class="uiCatalogueDemoField" for="exampleInputStacked">
  <span class="uiCatalogueDemoField__label">alpha</span>
  <span class="uiCatalogueDemoField__control">
    <input class="uiCatalogueDemoInput" id="exampleInputStacked" type="text" placeholder="80%">
  </span>
</label>
{% endcapture %}
{% capture fill_markup %}<div class="uiCatalogueDemoField uiCatalogueDemoField--fill">
  <div class="uiCatalogueDemoField__control">
    <input class="uiCatalogueDemoInput" type="text" placeholder="Opacity for the current layer">
  </div>
</div>
{% endcapture %}
{% capture readonly_markup %}<div class="uiCatalogueDemoField uiCatalogueDemoField--split">
  <span class="uiCatalogueDemoField__label">source alpha</span>
  <div class="uiCatalogueDemoField__control">
    <span class="uiCatalogueDemoInput uiCatalogueDemoInput--readonly">80%</span>
  </div>
</div>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoInputRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-input"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoInputIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/studio/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-primitive-input' | relative_url }}">Docs viewer: Input Primitive</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Primitive</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoInputIntroHeading">Input demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates field-entry patterns with demo-only classes. Live routes should map the pattern into their production namespace and config-backed copy.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoInputLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoInputLiveHeading">Demo Variants</h3>
      <p class="uiCatalogueDemoSummary">The rendered examples isolate input shape, field label placement, disabled state, and readonly display.</p>
    </div>
<div class="uiCatalogueDemoGrid">
  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Default Width</h3>
      <p class="uiCatalogueDemoExample__summary">The default field width fits compact command rows.</p>
    </header>
    <div class="uiCatalogueDemoInputRow">
      <div class="uiCatalogueDemoField">
        <div class="uiCatalogueDemoField__control">
          <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputDefault" type="text" placeholder="80%">
        </div>
      </div>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Save</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Fill Width</h3>
      <p class="uiCatalogueDemoExample__summary">Use fill width when the field is the main editable surface in the row.</p>
    </header>
    <div class="uiCatalogueDemoFillRow">
      <div class="uiCatalogueDemoField uiCatalogueDemoField--fill">
        <div class="uiCatalogueDemoField__control">
          <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputFill" type="text" placeholder="Opacity for the current layer">
        </div>
      </div>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Apply</button>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Label Above</h3>
      <p class="uiCatalogueDemoExample__summary">Default labelled form pattern for one field.</p>
    </header>
    <label class="uiCatalogueDemoField" for="uiCatalogueDemoInputAbove">
      <span class="uiCatalogueDemoField__label">alpha</span>
      <span class="uiCatalogueDemoField__control">
        <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputAbove" type="text" placeholder="80%">
      </span>
    </label>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Label Left</h3>
      <p class="uiCatalogueDemoExample__summary">Compact inline label when the row reads as one control group.</p>
    </header>
    <label class="uiCatalogueDemoField uiCatalogueDemoField--inline" for="uiCatalogueDemoInputInline">
      <span class="uiCatalogueDemoField__label">alpha</span>
      <span class="uiCatalogueDemoField__control">
        <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputInline" type="text" placeholder="80%">
      </span>
    </label>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Two Columns With Dropdown</h3>
      <p class="uiCatalogueDemoExample__summary">Use a stronger label column when related controls need aligned names.</p>
    </header>
    <label class="uiCatalogueDemoField uiCatalogueDemoField--split" for="uiCatalogueDemoInputSelect">
      <span class="uiCatalogueDemoField__label">preset</span>
      <span class="uiCatalogueDemoField__control">
        <select class="uiCatalogueDemoInput" id="uiCatalogueDemoInputSelect">
          <option selected>Alpha 80%</option>
          <option>Alpha 100%</option>
          <option>Alpha 60%</option>
        </select>
      </span>
    </label>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Increment Control</h3>
      <p class="uiCatalogueDemoExample__summary">Use step controls only when explicit increments are part of the task.</p>
    </header>
    <div class="uiCatalogueDemoField uiCatalogueDemoField--inline">
      <label class="uiCatalogueDemoField__label" for="uiCatalogueDemoInputStep">alpha</label>
      <div class="uiCatalogueDemoField__control">
        <button class="uiCatalogueDemoButton uiCatalogueDemoStepButton" type="button" aria-label="Decrease alpha">-</button>
        <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputStep" type="text" placeholder="80" inputmode="numeric">
        <button class="uiCatalogueDemoButton uiCatalogueDemoStepButton" type="button" aria-label="Increase alpha">+</button>
      </div>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Disabled</h3>
      <p class="uiCatalogueDemoExample__summary">Disabled means temporarily unavailable because another page state is incomplete.</p>
    </header>
    <label class="uiCatalogueDemoField" for="uiCatalogueDemoInputDisabled">
      <span class="uiCatalogueDemoField__label">alpha</span>
      <span class="uiCatalogueDemoField__control">
        <input class="uiCatalogueDemoInput" id="uiCatalogueDemoInputDisabled" type="text" placeholder="Available after selecting a layer" disabled>
      </span>
    </label>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Readonly Display</h3>
      <p class="uiCatalogueDemoExample__summary">Always-readonly values keep normal text and lose the filled background.</p>
    </header>
    <div class="uiCatalogueDemoField uiCatalogueDemoField--split">
      <span class="uiCatalogueDemoField__label">source alpha</span>
      <div class="uiCatalogueDemoField__control">
        <span class="uiCatalogueDemoInput uiCatalogueDemoInput--readonly" id="uiCatalogueDemoInputReadonly">80%</span>
      </div>
    </div>
  </section>
</div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoInputCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoInputCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">These snippets are pattern examples in the demo namespace, not production class names.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Default Width</h4>
        <pre><code>{{ default_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Label Above</h4>
        <pre><code>{{ stacked_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Fill Width</h4>
        <pre><code>{{ fill_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Readonly Display</h4>
        <pre><code>{{ readonly_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/ui-catalogue/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
