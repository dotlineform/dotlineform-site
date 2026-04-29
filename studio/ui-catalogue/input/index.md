---
layout: studio
title: "UI Primitive: Input"
permalink: /studio/ui-catalogue/input/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
ui_catalogue_primitive: input
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture primitive_note_markdown %}{% include ui_catalogue_notes/input.md %}{% endcapture %}
{% capture default_markup %}<div class="tagStudioField">
  <div class="tagStudioField__control">
    <input class="tagStudio__input" type="text" placeholder="80%">
  </div>
</div>
{% endcapture %}
{% capture stacked_markup %}<label class="tagStudioField" for="exampleInputStacked">
  <span class="tagStudioField__label">alpha</span>
  <span class="tagStudioField__control">
    <input class="tagStudio__input" id="exampleInputStacked" type="text" placeholder="80%">
  </span>
</label>
{% endcapture %}
{% capture inline_markup %}<label class="tagStudioField tagStudioField--inline" for="exampleInputInline">
  <span class="tagStudioField__label">alpha</span>
  <span class="tagStudioField__control">
    <input class="tagStudio__input" id="exampleInputInline" type="text" placeholder="80%">
  </span>
</label>
{% endcapture %}
{% capture width_markup %}<label class="tagStudioField" for="exampleInputWidth" style="--field-width: 11rem;">
  <span class="tagStudioField__label">alpha</span>
  <span class="tagStudioField__control">
    <input class="tagStudio__input" id="exampleInputWidth" type="text" placeholder="80%">
  </span>
</label>
{% endcapture %}
{% capture fill_markup %}<div class="tagStudioField tagStudioField--fill">
  <div class="tagStudioField__control">
    <input class="tagStudio__input" type="text" placeholder="Opacity for the current layer">
  </div>
</div>
{% endcapture %}
{% capture select_markup %}<label class="tagStudioField tagStudioField--split" for="exampleInputSelect">
  <span class="tagStudioField__label">preset</span>
  <span class="tagStudioField__control">
    <select class="tagStudio__input tagStudio__input--defaultValue" id="exampleInputSelect">
      <option selected>Alpha 80%</option>
      <option>Alpha 100%</option>
      <option>Alpha 60%</option>
    </select>
  </span>
</label>
{% endcapture %}
{% capture increment_markup %}<div class="tagStudioField tagStudioField--inline">
  <label class="tagStudioField__label" for="exampleInputStep">alpha</label>
  <div class="tagStudioField__control">
    <button class="tagStudio__button tagStudioField__stepButton" type="button" aria-label="Decrease alpha">-</button>
    <input class="tagStudio__input tagStudioField__incrementValue" id="exampleInputStep" type="text" placeholder="80" inputmode="numeric">
    <button class="tagStudio__button tagStudioField__stepButton" type="button" aria-label="Increase alpha">+</button>
  </div>
</div>
{% endcapture %}
{% capture disabled_markup %}<label class="tagStudioField" for="exampleInputDisabled">
  <span class="tagStudioField__label">alpha</span>
  <span class="tagStudioField__control">
    <input class="tagStudio__input" id="exampleInputDisabled" type="text" placeholder="Available after selecting a layer" disabled>
  </span>
</label>
{% endcapture %}
{% capture readonly_markup %}<div class="tagStudioField tagStudioField--split">
  <span class="tagStudioField__label">source alpha</span>
  <div class="tagStudioField__control">
    <span class="tagStudio__input tagStudio__input--readonlyDisplay" id="exampleInputReadonly">80%</span>
  </div>
</div>
{% endcapture %}

<div class="tagStudioPage studioUiPrimitivePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-catalogue' | relative_url }}">Docs viewer: UI Catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Primitive</p>
    <p class="studioUiPrimitivePage__intro">This page is the code-bound reference for shared field-entry controls. It keeps text entry, dropdowns, stepped numeric assignment, and readonly field display in one primitive family because the user intent is assigning one field value.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioUiPrimitiveLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveLiveHeading">Live Variants</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Each example keeps the shared control height and uses the same field wrapper for width and label placement. Numeric data should still default to plain input boxes unless step controls are part of the explicit UI requirement.</p>
    </div>
    {% include studio_ui_catalogue_input_demo.html %}
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioUiPrimitiveCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Copy these snippets as the current baseline for one-value field controls. Use the field wrapper for layout, and keep the base input class focused on the shared shell.</p>
    </div>

    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Default Width</h4>
        <pre><code>{{ default_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Label Above</h4>
        <pre><code>{{ stacked_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Label Left</h4>
        <pre><code>{{ inline_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Specified Width</h4>
        <pre><code>{{ width_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Fill Width</h4>
        <pre><code>{{ fill_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Two Columns With Dropdown</h4>
        <pre><code>{{ select_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Increment Control</h4>
        <pre><code>{{ increment_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Disabled</h4>
        <pre><code>{{ disabled_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Readonly Display</h4>
        <pre><code>{{ readonly_markup | escape }}</code></pre>
      </section>
    </div>
  </section>

  <section class="studioUiPrimitivePage__notes" aria-labelledby="studioUiPrimitiveNotesHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveNotesHeading">Notes</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Implementation points only.</p>
    </div>
    <div class="studioUiPrimitivePage__notesBody">
      {% if primitive_note_markdown and primitive_note_markdown != "" %}
        {{ primitive_note_markdown | markdownify }}
      {% else %}
        <p>No notes found for this primitive.</p>
      {% endif %}
    </div>
  </section>
</div>
