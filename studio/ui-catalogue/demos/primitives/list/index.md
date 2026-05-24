---
layout: studio
title: "UI Demo Primitive: List"
permalink: /studio/ui-catalogue/demos/primitives/list/
studio_page_doc: /docs/?scope=studio&doc=ui-primitive-list
ui_catalogue_demo_primitive: list
---

<link rel="stylesheet" href="{{ '/assets/ui-catalogue/css/ui-catalogue-demo.css' | relative_url }}">

{% capture simple_markup %}<div class="uiCatalogueDemoList uiCatalogueDemoList--simple">
  <ul class="uiCatalogueDemoList__rows">
    <li class="uiCatalogueDemoList__row uiCatalogueDemoList__row--center">
      <a class="uiCatalogueDemoList__link" href="#">source.md</a>
      <a class="uiCatalogueDemoList__link" href="#">ready</a>
    </li>
  </ul>
</div>
{% endcapture %}
{% capture sortable_markup %}<div class="uiCatalogueDemoList uiCatalogueDemoList--sortable">
  <div class="uiCatalogueDemoList__head">
    <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="id" data-state="active" aria-pressed="true">id <span aria-hidden="true">&uarr;</span></button>
    <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="title" aria-pressed="false">title</button>
    <span class="uiCatalogueDemoList__label">next</span>
  </div>
  <ol class="uiCatalogueDemoList__rows">
    <li class="uiCatalogueDemoList__row">
      <a class="uiCatalogueDemoList__link" href="#">01007</a>
      <span class="uiCatalogueDemoList__cell">
        <a class="uiCatalogueDemoList__link" href="#">Soft geometry study</a>
        <span class="uiCatalogueDemoList__meta">three related details</span>
      </span>
      <button class="uiCatalogueDemoList__sort" type="button">Open modal</button>
    </li>
  </ol>
</div>
{% endcapture %}
{% capture thumbnail_markup %}<div class="uiCatalogueDemoList uiCatalogueDemoList--thumbnail">
  <div class="uiCatalogueDemoListSortControls" aria-label="Thumbnail list sort controls">
    <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Newest</button>
    <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Title</button>
  </div>
  <div class="uiCatalogueDemoList__head">
    <span class="uiCatalogueDemoList__label">image</span>
    <span class="uiCatalogueDemoList__label">work</span>
    <span class="uiCatalogueDemoList__label">status</span>
  </div>
</div>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoListRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-list"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoListIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/studio/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-primitive-list' | relative_url }}">Docs viewer: List Primitive</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Primitive</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoListIntroHeading">List demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates repeated-row patterns with demo-only list classes. Production pages should map these structures into the live list shell or a route-owned variant.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoListLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoListLiveHeading">Demo Variants</h3>
      <p class="uiCatalogueDemoSummary">The examples cover simple, sortable, dense, and thumbnail list composition without importing live Studio list CSS.</p>
    </div>
<div class="uiCatalogueDemoGrid">
  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Simple List</h3>
      <p class="uiCatalogueDemoExample__summary">Minimal rows without column headers.</p>
    </header>
    <div class="uiCatalogueDemoList uiCatalogueDemoList--simple">
      <ul class="uiCatalogueDemoList__rows">
        <li class="uiCatalogueDemoList__row uiCatalogueDemoList__row--center">
          <a class="uiCatalogueDemoList__link" href="#">source.md</a>
          <a class="uiCatalogueDemoList__link" href="#">updated today</a>
        </li>
        <li class="uiCatalogueDemoList__row uiCatalogueDemoList__row--center">
          <a class="uiCatalogueDemoList__link" href="#">detail-001.jpg</a>
          <a class="uiCatalogueDemoList__link" href="#">ready</a>
        </li>
        <li class="uiCatalogueDemoList__row uiCatalogueDemoList__row--center">
          <a class="uiCatalogueDemoList__link" href="#">notes.txt</a>
          <a class="uiCatalogueDemoList__link" href="#">draft</a>
        </li>
      </ul>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Sortable List</h3>
      <p class="uiCatalogueDemoExample__summary">Column headers are command buttons when the list owns sorting.</p>
    </header>
    <div class="uiCatalogueDemoList uiCatalogueDemoList--sortable">
      <div class="uiCatalogueDemoList__head">
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="id" data-state="active" aria-pressed="true">id <span aria-hidden="true">&uarr;</span></button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="title" aria-pressed="false">title</button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="status" aria-pressed="false">status</button>
      </div>
      <ol class="uiCatalogueDemoList__rows">
        <li class="uiCatalogueDemoList__row">
          <a class="uiCatalogueDemoList__link" href="#">01007</a>
          <span class="uiCatalogueDemoList__cell">
            <a class="uiCatalogueDemoList__link" href="#">Soft geometry study</a>
            <span class="uiCatalogueDemoList__meta">three related details</span>
          </span>
          <a class="uiCatalogueDemoList__link" href="#">published</a>
        </li>
        <li class="uiCatalogueDemoList__row">
          <a class="uiCatalogueDemoList__link" href="#">01008</a>
          <span class="uiCatalogueDemoList__cell">
            <a class="uiCatalogueDemoList__link" href="#">Line weight test</a>
            <span class="uiCatalogueDemoList__meta">needs source prose</span>
          </span>
          <a class="uiCatalogueDemoList__link" href="#">draft</a>
        </li>
      </ol>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Dense List</h3>
      <p class="uiCatalogueDemoExample__summary">High-density rows use compact spacing and a bold title column.</p>
    </header>
    <div class="uiCatalogueDemoList uiCatalogueDemoList--dense">
      <div class="uiCatalogueDemoList__head" role="group" aria-label="Dense list sort controls">
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="cat" data-state="active" aria-pressed="true">cat <span aria-hidden="true">&uarr;</span></button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="year" aria-pressed="false">year</button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="title" aria-pressed="false">title</button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="series" aria-pressed="false">series</button>
        <button class="uiCatalogueDemoList__sort" type="button" data-sort-key="storage" aria-pressed="false">storage</button>
      </div>
      <ul class="uiCatalogueDemoList__rows">
        <li class="uiCatalogueDemoList__row">
          <a class="uiCatalogueDemoList__link" href="#">01007</a>
          <span class="uiCatalogueDemoList__meta">2024</span>
          <a class="uiCatalogueDemoList__link uiCatalogueDemoList__title" href="#">Soft geometry study</a>
          <a class="uiCatalogueDemoList__link" href="#">drawing systems</a>
          <span class="uiCatalogueDemoList__meta">flat file</span>
        </li>
        <li class="uiCatalogueDemoList__row">
          <a class="uiCatalogueDemoList__link" href="#">01008</a>
          <span class="uiCatalogueDemoList__meta">2025</span>
          <a class="uiCatalogueDemoList__link uiCatalogueDemoList__title" href="#">Line weight test</a>
          <a class="uiCatalogueDemoList__link" href="#">draft set</a>
          <span class="uiCatalogueDemoList__meta">archive box</span>
        </li>
      </ul>
    </div>
  </section>

  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Thumbnail List</h3>
      <p class="uiCatalogueDemoExample__summary">The first column is media. Sorting can live outside the list when needed.</p>
    </header>
    <div class="uiCatalogueDemoList uiCatalogueDemoList--thumbnail">
      <div class="uiCatalogueDemoListSortControls" aria-label="Thumbnail list sort controls">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Newest</button>
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button">Title</button>
      </div>
      <div class="uiCatalogueDemoList__head">
        <span class="uiCatalogueDemoList__label">image</span>
        <span class="uiCatalogueDemoList__label">work</span>
        <span class="uiCatalogueDemoList__label">status</span>
      </div>
      <ul class="uiCatalogueDemoList__rows">
        <li class="uiCatalogueDemoList__row uiCatalogueDemoList__row--center">
          <span class="uiCatalogueDemoList__thumb">
            <img class="uiCatalogueDemoList__thumbImage" src="{{ '/studio/app/assets/img/panel-backgrounds/01007-primary-800.webp' | relative_url }}" alt="" loading="lazy" decoding="async">
          </span>
          <span class="uiCatalogueDemoList__cell">
            <a class="uiCatalogueDemoList__link" href="#">Soft geometry study</a>
            <span class="uiCatalogueDemoList__meta">01007</span>
          </span>
          <a class="uiCatalogueDemoList__link" href="#">published</a>
        </li>
      </ul>
    </div>
  </section>
</div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoListCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoListCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Use these snippets to discuss structure, then map class names intentionally in live work.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Simple List</h4>
        <pre><code>{{ simple_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Sortable List</h4>
        <pre><code>{{ sortable_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Thumbnail List Header</h4>
        <pre><code>{{ thumbnail_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/ui-catalogue/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
