---
doc_id: "_tmp"
title: tmp
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
sort_order: 40000
viewable: false
---
# tmp

we are working on site-request-committed-manage-mode-scope-storage.md
please start with task 1




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

