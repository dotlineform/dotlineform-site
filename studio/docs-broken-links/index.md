---
layout: studio
title: "Docs Broken Links"
permalink: /studio/docs-broken-links/
section: docs-broken-links
studio_page_doc: /docs/?scope=studio&doc=docs-broken-links
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage docsBrokenLinksPage" id="docsBrokenLinksRoot" hidden>
  <div class="tagStudio__panel docsBrokenLinksPage__panel">
    <p class="docsBrokenLinksPage__intro" id="docsBrokenLinksIntro"></p>
    <div class="docsBrokenLinksPage__controls">
      <label class="tagStudioField tagStudioField--inline docsBrokenLinksPage__scopeField">
        <span class="tagStudioField__label" id="docsBrokenLinksScopeLabel"></span>
        <span class="tagStudioField__control">
          <select class="tagStudio__input" id="docsBrokenLinksScope"></select>
        </span>
      </label>
      <button type="button" class="tagStudio__button tagStudio__button--defaultWidth" id="docsBrokenLinksRun"></button>
    </div>
    <p class="tagStudio__status" id="docsBrokenLinksStatus"></p>
    <p class="tagStudioForm__meta" id="docsBrokenLinksMeta"></p>
    <div id="docsBrokenLinksListWrap" hidden></div>
    <p class="docsBrokenLinksPage__empty" id="docsBrokenLinksEmpty" hidden></p>
  </div>
</div>

<p class="tagStudio__status" id="docsBrokenLinksBootStatus">loading docs broken links…</p>

<script type="module" src="{{ '/assets/studio/js/docs-broken-links.js' | relative_url }}"></script>
