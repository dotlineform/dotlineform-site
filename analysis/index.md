---
layout: default
title: "Analysis"
section: analysis
permalink: /analysis/
---

{%- assign docs_index_url = '/assets/data/docs/scopes/analysis/index.json' | relative_url -%}
{%- assign docs_viewer_base_url = '/analysis/' | relative_url -%}
{%- assign docs_search_index_url = '/assets/data/search/analysis/index.json' | relative_url -%}
{%- assign docs_management_base_url = 'http://127.0.0.1:8789' -%}

{% include docs_viewer_shell.html
  index_url=docs_index_url
  viewer_base_url=docs_viewer_base_url
  viewer_scope='analysis'
  include_scope_param=false
  default_doc_id='analysis'
  search_index_url=docs_search_index_url
  management_base_url=docs_management_base_url
  search_placeholder='search analysis'
  search_aria_label='Search analysis'
%}
