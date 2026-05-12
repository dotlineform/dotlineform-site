---
layout: studio
title: "Thumbnail Quality"
permalink: /studio/thumbnail-quality/
section: thumbnail-quality
studio_domain: catalogue
studio_page_doc: /docs/?scope=studio&doc=thumbnail-quality-page
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage thumbnailQualityPage"
  id="thumbnailQualityRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="thumbnailQualityPageHeading">thumbnail quality</h2>
      <div class="catalogueWorkPage__actions">
        <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="thumbnailQualityRefreshButton">Refresh</button>
      </div>
    </div>
    <p class="tagStudio__contextHint" id="thumbnailQualityContext"></p>
    <p class="tagStudio__status" id="thumbnailQualityStatus"></p>
    <p class="tagStudio__saveResult" id="thumbnailQualityResult"></p>
  </section>

  <section class="tagStudio__panel thumbnailQualitySettings" aria-labelledby="thumbnailQualitySettingsHeading">
    <h2 class="tagStudio__heading" id="thumbnailQualitySettingsHeading">settings</h2>
    <div class="thumbnailQualitySettings__grid" id="thumbnailQualitySettingsList"></div>
  </section>

  <section class="tagStudio__panel thumbnailQualitySeriesPreview" aria-labelledby="thumbnailQualitySeriesHeading">
    <h2 class="tagStudio__heading" id="thumbnailQualitySeriesHeading">series gallery comparison</h2>
    <p class="tagStudio__contextHint" id="thumbnailQualitySeriesContext"></p>
    <div class="seriesGrid thumbnailQualitySeriesPreview__grid" id="thumbnailQualitySeriesGrid"></div>
  </section>

  <section class="thumbnailQualityRows" id="thumbnailQualityRows" aria-label="Thumbnail quality comparison rows"></section>
</div>

<p class="tagStudio__status" id="thumbnailQualityLoading">loading thumbnail quality preview...</p>
<p class="tagStudio__empty" id="thumbnailQualityEmpty" hidden></p>

{% include studio_module_script.html src='/assets/studio/js/thumbnail-quality.js' %}
