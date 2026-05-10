---
layout: studio
title: "Catalogue Field Registry"
permalink: /studio/catalogue-field-registry/
section: catalogue-field-registry
studio_page_doc: /docs/?scope=studio&doc=catalogue-field-registry-review
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage fieldRegistryReviewPage"
  id="fieldRegistryReviewRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading" id="fieldRegistryReviewHeading">catalogue field registry</h2>
    </div>
    <p class="tagStudio__contextHint" id="fieldRegistryReviewContext"></p>
    <p class="tagStudio__status" id="fieldRegistryReviewStatus"></p>
  </section>

  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__inputRow tagStudio__inputRow--editor">
      <label class="visually-hidden" for="fieldRegistryReviewSearch">Search by field name</label>
      <input
        type="search"
        class="tagStudio__input"
        id="fieldRegistryReviewSearch"
        placeholder="field name"
        autocomplete="off"
      >
    </div>
    <p class="tagStudioForm__meta" id="fieldRegistryReviewMeta"></p>
    <label class="tagStudioForm__field tagStudioForm__field--topAligned fieldRegistryReviewPage__outputField" for="fieldRegistryReviewOutput">
      <span class="tagStudioForm__label" id="fieldRegistryReviewOutputLabel">registry extract</span>
      <textarea class="tagStudio__input fieldRegistryReviewPage__output" id="fieldRegistryReviewOutput" readonly spellcheck="false"></textarea>
    </label>
  </section>
</div>

<p class="tagStudio__status" id="fieldRegistryReviewLoading">loading catalogue field registry...</p>
<p class="tagStudio__empty" id="fieldRegistryReviewEmpty" hidden></p>

{% include studio_module_script.html src='/assets/studio/js/catalogue-field-registry-review.js' %}
