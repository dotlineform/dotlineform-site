---
layout: studio
title: "Studio Audits"
permalink: /studio/audits/
section: studio-audits
studio_page_doc: /docs/?scope=studio&doc=studio-audits
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage studioAuditsPage"
  id="studioAuditsRoot"
  hidden
  data-studio-route="studio-audits"
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="tagStudio__panel studioAuditsPage__panel">
    <p class="studioAuditsPage__intro" id="studioAuditsIntro"></p>
    <p class="tagStudio__status" id="studioAuditsStatus"></p>
    <div class="studioAuditsPage__list" id="studioAuditsList"></div>
  </div>
</div>

<p class="tagStudio__status" id="studioAuditsBootStatus">loading Studio audits...</p>

<script type="module" src="{{ '/assets/studio/js/studio-audits.js' | relative_url }}"></script>
