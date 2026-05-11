---
title: "Docs"
permalink: /docs/
section: studio-docs
---

{%- assign docs_viewer_base_url = '/docs/' | relative_url -%}
{%- assign docs_management_base_url = 'http://127.0.0.1:8789' -%}

{% include docs_viewer_shell.html
  viewer_base_url=docs_viewer_base_url
  allow_scope_query=true
  allow_management=true
  management_base_url=docs_management_base_url
  search_placeholder='search studio docs'
  search_aria_label='Search Studio docs'
%}
