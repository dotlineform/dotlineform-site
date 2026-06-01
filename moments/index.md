---
layout: default
title: "Moments"
permalink: /moments/
section: series
---

<article class="page">
  <header class="page__header">
    <h1 class="page__title">moments</h1>
  </header>
  <p>Moments are now browsed from the works index.</p>
  <p><a id="momentsRecoveryLink" href="{{ '/series/' | relative_url }}?mode=moments">open moments</a></p>
</article>

<script src="{{ '/assets/js/public-catalogue-runtime.js' | relative_url }}?v={{ site.time | date: '%s' }}"></script>
<script>
  (function () {
    var runtime = window.__dlfPublicCatalogueRuntime;
    var link = document.getElementById('momentsRecoveryLink');
    if (!runtime || !link) return;
    var href = runtime.momentsRecoveryUrl({{ site.baseurl | default: '' | jsonify }});
    link.setAttribute('href', href);
    window.location.replace(href);
  })();
</script>
