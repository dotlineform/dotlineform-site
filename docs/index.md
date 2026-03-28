---
title: Docs
permalink: /docs/
section: studio-docs
---

<section
  class="docsViewer"
  id="docsViewerRoot"
  data-index-url="{{ '/assets/data/docs/index.json' | relative_url }}"
  data-viewer-base-url="{{ '/docs/' | relative_url }}"
>
  <aside class="docsViewer__sidebar" aria-label="Docs index">
    <div class="docsViewer__sidebarInner">
      <nav class="docsViewer__nav" id="docsViewerNav" aria-label="Docs tree"></nav>
    </div>
  </aside>

  <article class="docsViewer__main" aria-live="polite">
    <p class="docsViewer__status muted small" id="docsViewerStatus">Loading docs...</p>
    <div class="docsViewer__meta" id="docsViewerMeta" hidden>
      <p class="docsViewer__path small" id="docsViewerPath"></p>
      <p class="docsViewer__updated muted small" id="docsViewerUpdated"></p>
    </div>
    <div class="docsViewer__content content" id="docsViewerContent">
      <noscript>This docs viewer requires JavaScript to load the generated docs index.</noscript>
    </div>
  </article>
</section>

<script src="{{ '/assets/js/docs-viewer.js' | relative_url }}"></script>
