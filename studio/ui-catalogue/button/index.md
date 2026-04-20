---
layout: studio
title: "UI Primitive: Button"
permalink: /studio/ui-catalogue/button/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
ui_catalogue_primitive: button
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture primitive_note_markdown %}{% include ui_catalogue_notes/button.md %}{% endcapture %}
{% capture default_markup %}<button class="tagStudio__button" type="button">Save</button>
{% endcapture %}
{% capture anchor_markup %}<a class="tagStudio__button" href="#">New Detail</a>
{% endcapture %}
{% capture disabled_markup %}<button class="tagStudio__button" type="button" disabled>Save</button>
{% endcapture %}
{% capture modal_markup %}<div class="tagStudioModal__actions">
  <button class="tagStudio__button" type="button">Cancel</button>
  <button class="tagStudio__button" type="button">Save</button>
</div>
{% endcapture %}
{% capture toolbar_markup %}<div class="tagStudioToolbar__row">
  <button class="tagStudio__button" type="button">Import</button>
  <button class="tagStudio__button" type="button">New</button>
</div>
{% endcapture %}

<div class="tagStudioPage studioUiPrimitivePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-catalogue' | relative_url }}">Docs viewer: UI Catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Primitive</p>
    <p class="studioUiPrimitivePage__intro">This page is the code-bound reference for shared command buttons. It excludes clickable pills and captures current button drift before richer emphasis variants are defined.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioUiPrimitiveLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveLiveHeading">Live Variants</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Each example shows current shared command-button usage, including modal and toolbar subsets.</p>
    </div>
    {% include studio_ui_catalogue_button_demo.html %}
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioUiPrimitiveCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Copy these snippets as the current shared baseline while the button emphasis system is still being defined.</p>
    </div>

    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Default Command Button</h4>
        <pre><code>{{ default_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Anchor Command</h4>
        <pre><code>{{ anchor_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Disabled</h4>
        <pre><code>{{ disabled_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Modal Action Row</h4>
        <pre><code>{{ modal_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Toolbar Subset</h4>
        <pre><code>{{ toolbar_markup | escape }}</code></pre>
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
