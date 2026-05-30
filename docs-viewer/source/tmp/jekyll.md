---
doc_id: jekyll
title: jekyll
added_date: 2026-05-30
last_updated: 2026-05-30
parent_id: ""
---

Ruby/Jekyll retirement is important, but I would not start by removing it. It is broader than the Studio shell: Jekyll currently owns public site build/preview, Docs Viewer Markdown rendering, docs rebuild/watch flows, import validation, and publish parity. Treat that as a separate inventory + target-contract request before implementation.

Then write the Ruby/Jekyll retirement plan

Inventory current Ruby/Jekyll responsibilities and decide replacement targets. Likely separate tracks:

- public site generator replacement or static build strategy
- Docs Markdown renderer replacement
- docs search/docs payload builder migration
- import validation replacement
- CI/local parity changes

Only then implement Ruby/Jekyll retirement in slices

Start with the least public-risk surface, probably Docs Viewer builder/rendering, before touching public site generation.