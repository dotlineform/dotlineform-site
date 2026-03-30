---
title: Docs
permalink: /docs/
section: studio-docs
---

{%- assign docs_index_url = '/assets/data/docs/scopes/studio/index.json' | relative_url -%}
{%- assign docs_viewer_base_url = '/docs/' | relative_url -%}
{%- assign docs_search_href = '/search/?scope=studio' | relative_url -%}

{% include docs_viewer_shell.html
  index_url=docs_index_url
  viewer_base_url=docs_viewer_base_url
  viewer_scope='studio'
  include_scope_param=true
  default_doc_id='studio'
  search_href=docs_search_href
  search_aria_label='Search Studio docs'
%}
