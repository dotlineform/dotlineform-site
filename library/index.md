---
layout: default
title: Library
section: library
permalink: /library/
---

{%- assign docs_index_url = '/assets/data/docs/scopes/library/index.json' | relative_url -%}
{%- assign docs_viewer_base_url = '/library/' | relative_url -%}
{%- assign docs_search_index_url = '/assets/data/search/library/index.json' | relative_url -%}
{%- assign docs_management_base_url = 'http://127.0.0.1:8789' -%}

{% include docs_viewer_shell.html
  index_url=docs_index_url
  viewer_base_url=docs_viewer_base_url
  viewer_scope='library'
  include_scope_param=false
  default_doc_id='library'
  search_index_url=docs_search_index_url
  management_base_url=docs_management_base_url
  search_placeholder='search library'
  search_aria_label='Search library'
%}
