---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
---

# tmp


the risk categories defined in studio-javascript-payload-inventory.md and studio-python-ruby-script-inventory.md are useful but the current analysis is too complicated and it is hard to see what the priorities for improvement are. there are a few issues:

- the risk categories are all contained in single tables, which makes prioritising difficult because it is dealing with multiple risks at once. separating risk categories into separate reports might be easier to comprehend?
- there is a mix of analysis across single files and 'file families'. both are relevant but not necessarily in the same report.
- the summaries of the findings are too scattered across the documents.
- the documents are too long to easily extract the key messages
- we need to be able to extract concrete actions from the analysis.

please provide recommendations for improving this risk analysis.


docs viewer config:

how to update config through manage-mode
equivalent to an app's 'settings' UI

---

semantic [work_id]-[detail_id] link
need more

---

we are working on site-request-studio-javascript-app-shell-slice-1.md,
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

----------

# risks

I recommend turning the inventories into a small reporting system rather than longer single documents.

**Recommended Structure**

Keep the current scoring definitions, but split the analysis into four document types:

1. **Risk Policy**
   - Keep `studio-javascript-payload-inventory.md` mostly as policy.
   - Define categories, scoring rules, bands, and rescore rules.
   - Avoid putting current findings here.

2. **Current Risk Dashboard**
   - One short priority document for humans.
   - Purpose: answer “what should we improve next?”
   - Include:
     - top 5 priorities
     - why each matters
     - recommended next action
     - expected evidence of improvement
     - owner area
     - whether it is file-level, family-level, or cross-cutting

3. **Raw Inventories**
   - Keep long tables here only.
   - Separate by unit:
     - JavaScript file inventory
     - JavaScript family rollup
     - Python/Ruby script-family inventory
     - largest-file watch list as an appendix or separate report
   - These are evidence, not the main reading path.

4. **Risk Category Reports**
   - One report per risk type:
     - Maintenance risk
     - Structural/ownership risk
     - Performance risk
     - Architectural drift risk
   - Each report should rank only that risk, across relevant files/families.
   - This avoids one table asking the reader to compare maintenance, performance, and architecture at the same time.

**Main Change**

Separate “what is risky?” from “what should we do?”

For each priority, use a compact action card like:

```md
## Catalogue Save/Build Path

Priority: 1
Risk type: performance + maintenance
Unit: script family
Evidence: broad save path touches source writes, generated artifacts, lookup refreshes, search, media, and activity rows.
Recommended action: add save/build diagnostics before further structural splitting.
Expected improvement: identify repeated broad rebuilds and slow media/search/generated steps.
Concrete next slice: catalogue diagnostics for elapsed time, counts, fallback reasons.
Verification: local save response/log includes per-step counts and timings.
```

**Specific Recommendations**

- Do not make the big inventory tables the main artifact. They should support decisions, not be the decision surface.
- Add a short “Current Priorities” dashboard that is no more than 1-2 screens.
- Split file-level and family-level analysis. They answer different questions:
  - file-level: “where should future edits slow down?”
  - family-level: “where should improvement work be scheduled?”
- Keep largest-file analysis separate from risk priority. Large files are useful watch items, but size is not the same as risk.
- Convert “Recommended improvements” bullets into explicit actions with owner, evidence, verification, and expected score/class movement.
- For JavaScript, add family rollups so `Catalogue editors`, `Docs Viewer`, `Analytics tag routes`, and `Public runtime` can be prioritized without scanning 190 rows.
- For Python/Ruby, keep the family matrix but move the detailed prose into separate family notes or category reports.
- Add a “Do not prioritize now” section. This is useful where something is large but currently acceptable, or where diagnostics should come before refactoring.

**Best Next Step**

Create a new concise dashboard first, probably something like:

`docs-viewer/source/studio/studio-risk-priority-dashboard.md`

Then gradually move detailed category-specific analysis out of the long inventories as they are refreshed. The immediate priority list should probably start with catalogue diagnostics, because the current Python/Ruby analysis already says visibility should come before another broad split.