---
title: Docs
permalink: /docs/
section: studio-docs
---

{%- assign docs_index_url = '/assets/data/docs/scopes/studio/index.json' | relative_url -%}
{%- assign docs_viewer_base_url = '/docs/' | relative_url -%}
{%- assign docs_search_index_url = '/assets/data/search/studio/index.json' | relative_url -%}
{%- assign docs_management_base_url = 'http://127.0.0.1:8789' -%}

{% include docs_viewer_shell.html
  index_url=docs_index_url
  viewer_base_url=docs_viewer_base_url
  viewer_scope='studio'
  include_scope_param=true
  default_doc_id='site-docs'
  search_index_url=docs_search_index_url
  management_base_url=docs_management_base_url
  search_placeholder='search studio docs'
  search_aria_label='Search Studio docs'
  show_rebuild_button=true
  rebuild_button_label='Rebuild docs'
%}

<script type="module" src="{{ '/assets/studio/js/docs-rebuild-button.js' | relative_url }}"></script>
