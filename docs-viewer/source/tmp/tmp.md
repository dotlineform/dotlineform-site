---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
sort_order: 100
---

# tmp



---


semantic [work_id]-[detail_id] link
need more



we are working on site-request-docs-viewer-app-shell-search-recent-bookmark-tasks.md, 
please proceed with the tasks.

great. please create a sibling tracker doc for the next slice, Document mount and metadata shell, using tasks-template.md as the template.

great, can you summarise those next slices in the doc and we can continue with the tasks-template.md doc approach which works well. please create a tasks doc for the next slice. combine slices if that makes more logical sense, we are not rigid in needing a slice on its own if it is too narrow.

- we need to remove migration fallbacks and compatibility layers e.g. data attributes used for routing. also, the management controller reads the shell refs after the app shell promise resolves, with direct DOM lookups kept only as fallback compatibility.
- retire docs-viewer.js?

'I removed the shell JSON approach and adjusted the tests to exercise explicit route config records through the resolver API plus current data-attribute fallback.'

---

markdown editor
- but not a conventional one, this will be focussed on converting words to semantic references.
- to do this, need an info panel to show current tags



---

Studio home page

catalogue
- drafts - `studio/catalogue-status/?mode=manage`
- series editor: `/studio/catalogue-series/`
- work editor: `/studio/catalogue-work/`
- work detail editor - `/studio/catalogue-work-detail/?mode=manage`
- bulk add work - `/studio/bulk-add-work/?mode=manage`
- moment editor - `/studio/catalogue-moment/?mode=manage`
- list of works - `/studio/studio-works/?mode=manage&sort=cat&dir=asc`
- project state - `/studio/project-state/?mode=manage`

analytics
- series tags - `/studio/analytics/series-tags/`
- tag registry - `/studio/analytics/tag-registry/`
- tag aliases - `/studio/analytics/tag-aliases/`
- tag groups - `/studio/analytics/tag-groups/`

data sharing
- prepare package - `/studio/data-sharing/prepare/?mode=manage&scope=library`
- returned package - `/studio/data-sharing/review/?mode=manage&scope=library`

admin
- studio audits - `/studio/audits/?mode=manage`
- thumbnail tests - `/studio/thumbnail-quality/?mode=manage`
- UI demos - `/studio/ui-catalogue/demos/`
- studio activity - `/studio/activity/?mode=manage`
- field registry - `/studio/catalogue-field-registry/?mode=manage`


---

servers:

- `bin/local-all` - Studio, Jekyll site, Docs Viewer, docs watcher
- `bin/local-studio` - Studio + Docs Watcher: `http://127.0.0.1:8765/studio/`
- `docs-viewer/bin/docs-viewer` - Docs Viewer: `http://127.0.0.1:8776/docs/?scope=studio&mode=manage&doc=change-requests`
- `bin/public-site-preview` - public Jekyll preview: `http://127.0.0.1:4000/series/`
- `bin/public-site-preview --livereload`

scripts:

./docs-viewer/build/build_docs.rb --scope studio
./docs-viewer/build/build_docs.rb --scope studio --write
./docs-viewer/build/build_docs.rb --scope studio --write --only-doc-ids example-doc
./docs-viewer/build/build_search.rb

./studio/services/catalogue/search/build_search.rb


---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---