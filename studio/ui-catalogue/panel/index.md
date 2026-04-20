---
layout: studio
title: "UI Primitive: Panel"
permalink: /studio/ui-catalogue/panel/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-panel
ui_catalogue_primitive: panel
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture primitive_note_markdown %}{% include ui_catalogue_notes/panel.md %}{% endcapture %}
{% capture panel_markup %}<div class="tagStudio__panel">
  <h4>Panel Heading</h4>
  <p>Panel body content goes here.</p>
</div>
{% endcapture %}
{% capture compact_markup %}<div class="tagStudio__panel tagStudio__panel--compact">
  <h4>Compact Panel</h4>
  <p>Use for denser supporting content.</p>
</div>
{% endcapture %}
{% capture editor_markup %}<div class="tagStudio__panel tagStudio__panel--editor">
  <label class="tagStudio__label" for="examplePanelInput">Name</label>
  <input class="tagStudio__input" id="examplePanelInput" type="text">
  <button class="tagStudio__button" type="button">Save</button>
</div>
{% endcapture %}

<div class="tagStudioPage studioUiPrimitivePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow">Live Primitive</p>
    <p class="studioUiPrimitivePage__intro">This page is the code-bound reference for the shared panel shell. The examples below use the real shared Studio classes rather than a demo-only imitation.</p>
  </section>

  <section class="tagStudio__panel studioUiPrimitivePage__live" aria-labelledby="studioUiPrimitiveLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveLiveHeading">Live Variants</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Use the shared shell first. Change internal content before changing outer chrome.</p>
    </div>
    {% include studio_ui_catalogue_panel_demo.html %}
  </section>

  <section class="tagStudio__panel studioUiPrimitivePage__code" aria-labelledby="studioUiPrimitiveCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Copy these snippets as the baseline implementation rather than rebuilding the shell by hand.</p>
    </div>

    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Default</h4>
        <pre><code>{{ panel_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Compact</h4>
        <pre><code>{{ compact_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Editor</h4>
        <pre><code>{{ editor_markup | escape }}</code></pre>
      </section>
    </div>
  </section>

  <section class="tagStudio__panel studioUiPrimitivePage__notes" aria-labelledby="studioUiPrimitiveNotesHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveNotesHeading">Notes</h3>
      <p class="studioUiPrimitivePage__sectionSummary">This copy comes from the markdown note source for the primitive.</p>
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
