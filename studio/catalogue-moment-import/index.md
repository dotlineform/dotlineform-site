---
layout: studio
title: "Catalogue Moment Import"
permalink: /studio/catalogue-moment-import/
section: catalogue-moment-import
studio_domain: catalogue
studio_page_doc: /docs/?scope=studio&doc=catalogue-moment-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div class="tagStudioPage catalogueWorkPage" id="catalogueMomentImportBridge">
  <section class="tagStudio__panel tagStudio__panel--editor">
    <div class="tagStudio__headingRow">
      <h2 class="tagStudio__heading">moment editor</h2>
    </div>
    <p class="tagStudio__contextHint">Moment import now lives on the Moment editor page.</p>
    <p class="tagStudio__status"><a href="{{ '/studio/catalogue-moment/' | relative_url }}" id="catalogueMomentImportBridgeLink">Open Moment editor</a></p>
  </section>
</div>

<script>
  (function () {
    var target = new URL("{{ '/studio/catalogue-moment/' | relative_url }}", window.location.href);
    var source = new URL(window.location.href);
    var file = source.searchParams.get("file");
    if (file) target.searchParams.set("file", file);
    var link = document.getElementById("catalogueMomentImportBridgeLink");
    if (link) link.href = target.toString();
    window.location.replace(target.toString());
  })();
</script>
