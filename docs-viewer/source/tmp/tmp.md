---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
sort_order: 100
---

# tmp

docs viewer config:

how to update config through manage-mode
equivalent to an app's 'settings' UI


---


semantic [work_id]-[detail_id] link
need more

---

we are working on site-request-testing-framework-review.md,
please proceed with the tasks.






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

> great. my initial reading is that lots of actions are needed which implies that the previous work wasn't thorough enough. but perhaps the reason is rather that the migration targetted functional areas, which was the only way to tackle it, and accept that gaps will remain. if we were to do a similar app/shell rewrite for studio, would we keep the same basic approach and follow up cleanup as we are doing here?

Yes. I would keep the same basic approach for a Studio app/shell rewrite: migrate by functional area, make ownership better with each slice, and then run a deliberate cleanup/classification pass like this one.

The important distinction is that the cleanup findings do not automatically mean the prior work was poor. In a live app, the alternative to functional slices is usually a risky “big rewrite” where you try to make the architecture perfect before behavior is safely moved. The Docs Viewer work seems to have chosen the safer path: extract boot, app context, service context, generated-data runtime, state domains, hosted views, route workflow, search/bookmarks, management lazy loading, etc., while leaving compatibility bridges where complete controller families still depended on broad state or callbacks.

That is a valid migration strategy if three things are true:

1. The temporary bridges are named honestly.
2. The public API is narrowed as soon as possible.
3. A follow-up cleanup pass classifies each remaining bridge as remove, track, or rename as current architecture.

That is exactly what this cleanup tracker is doing now.

For Studio, I would use the same migration shape, but I would be stricter up front about the cleanup ledger because Studio has more write surfaces and operational routes. I would expect each slice to record:

- the functional area moved,
- the new owner module,
- the compatibility bridge left behind,
- why it could not be removed yet,
- the test that guards current behavior,
- the exact follow-up task that removes or narrows it.

So the lesson is not “avoid compatibility gaps.” The lesson is “make compatibility gaps explicit, bounded, and scheduled.” For a Studio shell rewrite, that is probably the only pragmatic way to reduce risk while keeping the app working.

---