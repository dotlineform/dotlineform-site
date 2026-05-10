---
layout: studio
title: "Library Documents"
permalink: /studio/library-documents/
section: library-documents
studio_domain: library
studio_page_doc: /docs/?scope=studio&doc=library-documents
---

<link rel="stylesheet" href="{{ '/assets/studio/css/studio.css' | relative_url }}">

<div
  class="tagStudioPage libraryDocumentsPage"
  id="libraryDocumentsRoot"
  hidden
  data-studio-ready="false"
  data-studio-busy="false"
>
  <div class="libraryDocumentsPage__toolbar">
    <div class="libraryDocumentsPage__filters" id="libraryDocumentsFilters" aria-label="Library document filters"></div>
    <p class="tagStudio__status libraryDocumentsPage__status" id="libraryDocumentsStatus"></p>
  </div>

  <div class="tagStudioList tagStudioList--dense libraryDocumentsList">
    <div class="tagStudioList__head libraryDocumentsList__head" role="group" aria-label="Sort Library documents">
      <button class="tagStudioList__sortBtn" type="button" data-library-documents-sort="doc_id">
        doc_id <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
      </button>
      <button class="tagStudioList__sortBtn" type="button" data-library-documents-sort="added_date">
        added date <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
      </button>
      <span class="tagStudioList__headLabel">parent</span>
      <span class="tagStudioList__headLabel">viewable</span>
      <button class="tagStudioList__sortBtn" type="button" data-library-documents-sort="title">
        title <span class="tagStudioList__sortIndicator" aria-hidden="true"></span>
      </button>
    </div>
    <ul class="tagStudioList__rows" id="libraryDocumentsRows"></ul>
  </div>
</div>

<p class="tagStudio__status" id="libraryDocumentsBootStatus">loading Library documents...</p>

{% include studio_module_script.html src='/assets/studio/js/library-documents.js' %}
