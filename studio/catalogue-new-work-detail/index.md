---
layout: studio
title: "New Catalogue Work Detail"
permalink: /studio/catalogue-new-work-detail/
section: catalogue-new-work-detail
studio_page_doc: /docs/?scope=studio&doc=catalogue-new-work-detail-editor
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<p class="tagStudio__status" id="catalogueNewWorkDetailRedirect">
  New work detail creation has moved to the Catalogue Work Detail Editor.
</p>

<script>
  (function () {
    var params = new URLSearchParams(window.location.search);
    var workId = String(params.get("work") || "").trim();
    var target = "{{ '/studio/catalogue-work-detail/' | relative_url }}";
    if (workId) {
      target += "?work=" + encodeURIComponent(workId) + "&mode=new";
    } else {
      target = "{{ '/studio/catalogue-work/' | relative_url }}";
    }
    var link = document.createElement("a");
    link.href = target;
    link.textContent = "Open redirected route";
    var node = document.getElementById("catalogueNewWorkDetailRedirect");
    if (node) {
      node.textContent = "New work detail creation has moved. ";
      node.appendChild(link);
    }
    window.location.replace(target);
  }());
</script>
