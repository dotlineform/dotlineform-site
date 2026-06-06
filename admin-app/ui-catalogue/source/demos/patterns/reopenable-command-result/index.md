---
title: "UI Demo Pattern: Reopenable Command Result"
permalink: /admin/ui-catalogue/demos/patterns/reopenable-command-result/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-reopenable-command-result
ui_catalogue_demo_pattern: reopenable-command-result
---

<link rel="stylesheet" href="{{ '/admin/ui-catalogue/assets/css/ui-catalogue-demo.css' | relative_url }}">

{% capture status_markup %}<div class="uiCatalogueDemoResultRow">
  <p class="uiCatalogueDemoStatus" data-state="success">Generated 6 Library import preview files.</p>
  <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoResultModal">results</button>
</div>
{% endcapture %}

{% capture modal_markup %}<div class="uiCatalogueDemoModal" id="uiCatalogueDemoResultModal" data-ui-demo-modal data-open="false" aria-hidden="true">
  <button class="uiCatalogueDemoModal__backdrop" type="button" data-ui-demo-modal-close aria-label="Close result modal"></button>
  <section class="uiCatalogueDemoModal__dialog" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoResultTitle" tabindex="-1">
    <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoResultTitle">Import preview</h3>
    <p class="uiCatalogueDemoModal__body">Generated 6 Library import preview files.</p>
    <div class="uiCatalogueDemoModal__actions">
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-close data-ui-demo-modal-initial-focus>Close</button>
    </div>
  </section>
</div>
{% endcapture %}

<div
  class="uiCatalogueDemoRoot uiCatalogueDemoPage"
  id="uiCatalogueDemoReopenableCommandResultRoot"
  data-ui-catalogue-demo-route="ui-catalogue-demo-reopenable-command-result"
  data-ui-catalogue-demo-ready="false"
  data-ui-catalogue-demo-busy="false"
>
  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoReopenableIntroHeading">
    <div class="uiCatalogueDemoSection__header">
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/admin/ui-catalogue/demos/' | relative_url }}">&larr; UI catalogue demos</a></p>
      <p class="uiCatalogueDemoEyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-reopenable-command-result' | relative_url }}">Docs viewer: Reopenable Command Result Pattern</a></p>
      <p class="uiCatalogueDemoEyebrow">Demo Composition Pattern</p>
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoReopenableIntroHeading">Reopenable result demo namespace</h3>
      <p class="uiCatalogueDemoIntro">This page demonstrates a status-adjacent result action and modal shell with demo-only classes and demo-owned JavaScript.</p>
    </div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoReopenableLiveHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoReopenableLiveHeading">Demo Composition</h3>
      <p class="uiCatalogueDemoSummary">The result action remains available while the current status is still valid.</p>
    </div>
<div class="uiCatalogueDemoGrid">
  <section class="uiCatalogueDemoExample">
    <header class="uiCatalogueDemoExample__header">
      <h3 class="uiCatalogueDemoExample__title">Status With Reopenable Result</h3>
      <p class="uiCatalogueDemoExample__summary">The result action stays available while the status still describes the same completed command.</p>
    </header>
    <div class="uiCatalogueDemoResultRow">
      <p class="uiCatalogueDemoStatus" data-state="success">Generated 6 Library import preview files.</p>
      <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed" type="button" data-ui-demo-modal-open="uiCatalogueDemoResultModal">results</button>
    </div>
  </section>

  <div class="uiCatalogueDemoModal" id="uiCatalogueDemoResultModal" data-ui-demo-modal data-open="false" aria-hidden="true">
    <button class="uiCatalogueDemoModal__backdrop" type="button" data-ui-demo-modal-close aria-label="Close result modal"></button>
    <section class="uiCatalogueDemoModal__dialog" role="dialog" aria-modal="true" aria-labelledby="uiCatalogueDemoResultTitle" tabindex="-1">
      <h3 class="uiCatalogueDemoModal__title" id="uiCatalogueDemoResultTitle">Import preview</h3>
      <p class="uiCatalogueDemoModal__body">Generated 6 Library import preview files.</p>
      <dl class="uiCatalogueDemoList uiCatalogueDemoList--simple">
        <div class="uiCatalogueDemoList__row">
          <dt class="uiCatalogueDemoList__meta">records</dt>
          <dd>5</dd>
        </div>
        <div class="uiCatalogueDemoList__row">
          <dt class="uiCatalogueDemoList__meta">warnings</dt>
          <dd>1</dd>
        </div>
      </dl>
      <div class="uiCatalogueDemoModal__actions">
        <button class="uiCatalogueDemoButton uiCatalogueDemoButton--fixed uiCatalogueDemoButton--primary" type="button" data-ui-demo-modal-close data-ui-demo-modal-initial-focus>Close</button>
      </div>
    </section>
  </div>
</div>
  </section>

  <section class="uiCatalogueDemoSection" aria-labelledby="uiCatalogueDemoReopenableCodeHeading">
    <div class="uiCatalogueDemoSection__header">
      <h3 class="uiCatalogueDemoHeading" id="uiCatalogueDemoReopenableCodeHeading">Demo Markup</h3>
      <p class="uiCatalogueDemoSummary">Live routes should map this structure into their own result lifecycle and modal helper.</p>
    </div>
    <div class="uiCatalogueDemoCode">
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Status Row</h4>
        <pre><code>{{ status_markup | escape }}</code></pre>
      </section>
      <section class="uiCatalogueDemoCode__item">
        <h4 class="uiCatalogueDemoCode__title">Result Modal Shell</h4>
        <pre><code>{{ modal_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/admin/ui-catalogue/assets/js/ui-catalogue-demo.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
