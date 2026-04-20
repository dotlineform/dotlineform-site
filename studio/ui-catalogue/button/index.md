---
layout: studio
title: "UI Primitive: Button"
permalink: /studio/ui-catalogue/button/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
ui_catalogue_primitive: button
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture primitive_note_markdown %}{% include ui_catalogue_notes/button.md %}{% endcapture %}
{% capture small_markup %}<div class="studioUiPrimitiveButtonDemo__fieldGroup">
  <div class="studioUiPrimitiveButtonDemo__fieldGrid">
    <input class="tagStudio__input" type="text" value="Shared field example">
    <button class="tagStudio__button tagStudio__button--defaultWidth" type="button">Save</button>
  </div>
  <div class="tagStudio__buttonFeedback studioUiPrimitiveButtonDemo__fieldFeedback">
    <p class="tagStudio__status" data-state="success">Saved.</p>
  </div>
</div>
{% endcapture %}
{% capture medium_markup %}<button class="tagStudio__button tagStudio__button--md tagStudio__button--defaultWidth" type="button">Save</button>
{% endcapture %}
{% capture width_pair_markup %}<div>
  <button class="tagStudio__button tagStudio__button--md tagStudio__button--defaultWidth" type="button">OK</button>
  <button class="tagStudio__button tagStudio__button--md tagStudio__button--defaultWidth" type="button">Cancel</button>
</div>
{% endcapture %}
{% capture modal_markup %}<div class="tagStudioModal__actions">
  <button class="tagStudio__button tagStudio__button--md tagStudio__button--defaultWidth" type="button">Cancel</button>
  <button class="tagStudio__button tagStudio__button--md tagStudio__button--defaultWidth tagStudio__button--defaultAction" type="button">OK</button>
</div>
{% endcapture %}
{% capture destructive_markup %}<button class="tagStudio__button tagStudio__button--defaultWidth" type="button">Delete</button>
{% endcapture %}
{% capture disabled_markup %}<button class="tagStudio__button tagStudio__button--defaultWidth" type="button" disabled>Save</button>
{% endcapture %}

<div class="tagStudioPage studioUiPrimitivePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-catalogue' | relative_url }}">Docs viewer: UI Catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Primitive</p>
    <p class="studioUiPrimitivePage__intro">This page is the code-bound reference for shared command buttons. It excludes clickable pills and navigation links, and captures the minimal size/width contract before a broader page sweep.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioUiPrimitiveLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveLiveHeading">Live Variants</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Each example shows the intended command-button contract without pulling in link or toolbar behavior.</p>
    </div>
    {% include studio_ui_catalogue_button_demo.html %}
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioUiPrimitiveCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Copy these snippets as the current shared baseline for command buttons. Navigation actions such as <code>New Detail -&gt;</code> belong to a separate link pattern, and button feedback should stay local to the same command area.</p>
    </div>

    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Small Button Next To A Field</h4>
        <pre><code>{{ small_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Medium Command Button</h4>
        <pre><code>{{ medium_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Default Width Pair</h4>
        <pre><code>{{ width_pair_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Modal Action Row</h4>
        <pre><code>{{ modal_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Destructive Command</h4>
        <pre><code>{{ destructive_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Disabled</h4>
        <pre><code>{{ disabled_markup | escape }}</code></pre>
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
