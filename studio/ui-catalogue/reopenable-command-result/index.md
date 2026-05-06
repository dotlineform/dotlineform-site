---
layout: studio
title: "UI Pattern: Reopenable Command Result"
permalink: /studio/ui-catalogue/reopenable-command-result/
studio_page_doc: /docs/?scope=studio&doc=ui-pattern-reopenable-command-result
ui_catalogue_pattern: reopenable-command-result
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

{% capture status_markup %}<div class="dataImportPage__statusRow">
  <p class="tagStudio__status" data-state="success">Generated 6 Library import preview files.</p>
  <button class="tagStudio__button dataImportPage__resultButton" type="button">results</button>
</div>
{% endcapture %}

{% capture modal_markup %}<div class="tagStudioModal" data-role="studio-modal">
  <div class="tagStudioModal__backdrop" data-role="modal-cancel"></div>
  <div class="tagStudioModal__dialog dataImportResultModal" role="dialog" aria-modal="true" aria-labelledby="studioPatternResultTitle">
    <h3 id="studioPatternResultTitle">Import preview</h3>
    <p>Generated 6 Library import preview files.</p>
    <dl class="dataImportResultModal__counts">
      <dt>records</dt>
      <dd>5</dd>
      <dt>parsed</dt>
      <dd>5</dd>
      <dt>warnings</dt>
      <dd>1</dd>
      <dt>errors</dt>
      <dd>0</dd>
    </dl>
    <div class="tagStudioModal__actions">
      <button class="tagStudio__button" type="button">Close</button>
    </div>
  </div>
</div>
{% endcapture %}

<div
  class="tagStudioPage studioUiPrimitivePage studioUiPatternPage"
  id="studioUiCatalogueReopenableCommandResultRoot"
  data-studio-static-route="studio-ui-catalogue-reopenable-command-result"
  data-studio-mode="reference"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="tagStudioPage__context tagStudioPage__context--meta studioUiPrimitivePage__context">
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/studio/ui-catalogue/' | relative_url }}">&larr; ui catalogue</a></p>
    <p class="studioUiPrimitivePage__eyebrow"><a href="{{ '/docs/?scope=studio&doc=ui-pattern-reopenable-command-result' | relative_url }}">Docs viewer: Reopenable Command Result Pattern</a></p>
    <p class="studioUiPrimitivePage__eyebrow">Live Composition Pattern</p>
    <p class="studioUiPrimitivePage__intro">This page is the visual reference for command results that open in a modal and remain reopenable while the current status still describes the same result.</p>
  </section>

  <section class="studioUiPrimitivePage__live" aria-labelledby="studioPatternLiveHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioPatternLiveHeading">Live Composition</h3>
      <p class="studioUiPrimitivePage__sectionSummary">The status-adjacent action is intentionally small. It is a recovery affordance for the current result, not a second primary command.</p>
    </div>
    <div class="studioUiPatternExample">
      {{ status_markup }}
    </div>
  </section>

  <section class="studioUiPrimitivePage__code" aria-labelledby="studioPatternCodeHeading">
    <div class="studioUiPrimitivePage__sectionHeader">
      <h3 class="tagStudio__heading" id="studioPatternCodeHeading">Canonical Markup</h3>
      <p class="studioUiPrimitivePage__sectionSummary">The route owns the lifecycle: store the successful result payload, show the action only while the status remains current, and clear it when the input context changes.</p>
    </div>
    <div class="studioUiPrimitiveCodeList">
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Status Row</h4>
        <pre><code>{{ status_markup | escape }}</code></pre>
      </section>
      <section class="studioUiPrimitiveCodeList__item">
        <h4 class="studioUiPrimitiveCodeList__title">Result Modal Shape</h4>
        <pre><code>{{ modal_markup | escape }}</code></pre>
      </section>
    </div>
  </section>
</div>

<script type="module" src="{{ '/assets/studio/js/studio-static-route.js' | relative_url }}"></script>
