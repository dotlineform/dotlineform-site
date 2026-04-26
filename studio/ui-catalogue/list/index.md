---
layout: studio
title: "UI Primitive: List"
permalink: /studio/ui-catalogue/list/
studio_page_doc: /docs/?scope=studio&doc=ui-catalogue
ui_catalogue_primitive: list
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture primitive_note_markdown %}{% include ui_catalogue_notes/list.md %}{% endcapture %}
{% capture simple_markup %}<div class="tagStudioList exampleList__list" style="--studio-list-width: 28rem;">
  <ul class="tagStudioList__rows">
    <li class="tagStudioList__row tagStudioList__row--center exampleList__row">
      <a class="tagStudioList__cellLink" href="#">source.md</a>
      <a class="tagStudioList__cellLink" href="#">ready</a>
    </li>
  </ul>
</div>
{% endcapture %}
{% capture sortable_markup %}<div class="tagStudioList exampleList__list" style="--studio-list-width: 72%;">
  <div class="tagStudioList__head exampleList__head">
    <button class="tagStudioList__sortBtn" type="button" data-sort-key="id" data-state="active" aria-pressed="true">
      id <span class="tagStudioList__sortIndicator" aria-hidden="true">&uarr;</span>
    </button>
    <button class="tagStudioList__sortBtn" type="button" data-sort-key="title" aria-pressed="false">title</button>
    <span class="tagStudioList__headLabel">next</span>
  </div>
  <ol class="tagStudioList__rows">
    <li class="tagStudioList__row tagStudioList__row--start exampleList__row">
      <a class="tagStudioList__cellLink" href="#">01007</a>
      <span class="tagStudioList__cell">
        <a class="tagStudioList__cellLink" href="#">Soft geometry study</a>
        <span class="tagStudioList__cellMeta">three related details</span>
      </span>
      <button class="tagStudioList__cellLink" type="button">Open modal</button>
    </li>
  </ol>
</div>
{% endcapture %}
{% capture thumbnail_markup %}<div class="tagStudioList exampleList__list" style="--studio-list-width: 38rem;">
  <div class="exampleList__sortControls" aria-label="Thumbnail list sort controls">
    <button class="tagStudio__button tagStudio__button--defaultWidth" type="button">Newest</button>
    <button class="tagStudio__button tagStudio__button--defaultWidth" type="button">Title</button>
  </div>
  <div class="tagStudioList__head exampleList__head">
    <span class="tagStudioList__headLabel">image</span>
    <span class="tagStudioList__headLabel">work</span>
    <span class="tagStudioList__headLabel">status</span>
  </div>
  <ul class="tagStudioList__rows">
    <li class="tagStudioList__row tagStudioList__row--center exampleList__row">
      <span class="tagStudioList__thumb">
        <img class="tagStudioList__thumbImage" src="/assets/studio/img/panel-backgrounds/01007-primary-800.webp" alt="" loading="lazy" decoding="async">
      </span>
      <span class="tagStudioList__cell">
        <a class="tagStudioList__cellLink" href="#">Soft geometry study</a>
        <span class="tagStudioList__cellMeta">01007</span>
      </span>
      <a class="tagStudioList__cellLink" href="#">published</a>
    </li>
  </ul>
</div>
{% endcapture %}

<div class="tagStudioPage studioUiPrimitivePage">
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-catalogue' | relative_url }}">Docs viewer: UI Catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Primitive</p>
    <p class="studioUiPrimitivePage__intro">This page is the code-bound reference for shared Studio list primitives. It defines the row/header contract, width wrapper, row alignment, sortable-header treatment, and thumbnail-row baseline while leaving page-specific columns and actions in page namespaces.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioUiPrimitiveLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveLiveHeading">Live Variants</h3>
      <p class="studioUiPrimitivePage__sectionSummary">These examples show the three baseline list versions before mapping them across existing list-like Studio pages.</p>
    </div>
    {% include studio_ui_catalogue_list_demo.html %}
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioUiPrimitiveCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioUiPrimitiveCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">Copy the shared primitive classes first, then add page-specific classes for columns, links, row actions, and responsive labels.</p>
    </div>

    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Simple List</h4>
        <pre><code>{{ simple_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Sortable List</h4>
        <pre><code>{{ sortable_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Thumbnail List With External Sort Controls</h4>
        <pre><code>{{ thumbnail_markup | escape }}</code></pre>
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
