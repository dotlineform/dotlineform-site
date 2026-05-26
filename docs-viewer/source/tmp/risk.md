---
doc_id: "risk"
title: risk mitigation
added_date: 2026-05-21
last_updated: "2026-05-21"
parent_id: ""
sort_order: 100
viewable: false
---

The target is achievable, but not by working down `javascript-inventory.md` linearly. The best path is a staged risk-reduction campaign, grouped by route family and responsibility boundary.

Key finding: [javascript-inventory.md](docs-viewer/source/studio/javascript-inventory.md) is already stale. It lists 129 files, while `assets/` currently has 143 JS files. The missing files are mostly newly extracted mitigation modules such as `tag-registry-render.js`, `tag-registry-workflow.js`, `data-sharing-prepare-workflow.js`, `series-tags-render.js`, and `docs-html-import-workflow.js`. So the first move should be a rescore, not another extraction pass.

**Recommended Approach**

1. Rescore first, with category breakdowns.
   Add `maintenance / structural / performance / architectural` columns or an internal notes table. A hard score of 4 means every category is low risk, so we need to know which category is holding each file above 4.

2. Treat “score 4” as a boundary-quality target, not a file-size target.
   A score-4 file should have one clear role, explicit inputs, low boot/input cost, and no tendency to absorb future unrelated work. Splitting code without changing ownership will not really get us there.

3. Batch by family:
   - **Already-mitigated/rescore batch:** `data-sharing-prepare.js`, `tag-registry.js`, `docs-html-import.js`, `series-tags.js`, probably `tag-aliases.js`. These may already be below their listed scores.
   - **Catalogue editor batch:** `catalogue-work-editor.js`, `catalogue-work-detail-editor.js`, `catalogue-series-editor.js`, `catalogue-moment-editor.js`, plus their `*-actions`, `*-sections`, `*-selection`, and form modules. This is the biggest remaining structural risk area.
   - **Tag Studio batch:** `tag-studio.js`, `tag-studio-modals.js`, `tag-studio-render.js`, `tag-studio-save-controller.js`, `series-tag-editor-page.js`.
   - **Docs Viewer non-entry batch:** keep separate from `docs-viewer.js`, but use [docs-viewer-javascript-inventory.md](docs-viewer/source/studio/docs-viewer-javascript-inventory.md) for `docs-html-import.js`, management modules, reports, search, bookmarks, and scope lifecycle.
   - **Public runtime batch:** `catalogue-search.js`, `work.js`, `moment.js`, `swipe-nav.js`. These deserve attention because public-route exposure makes performance risk more meaningful than in Studio-only routes.

4. For each implementation slice, extract only complete responsibilities:
   domain/normalization, render, modal lifecycle, service/write orchestration, route-state projection, import/export workflow, selection state, or generated-data loading. Avoid cosmetic helper splitting.

5. Add focused module smoke tests as the exit criterion.
   A file should not be rescored to 4 just because code moved. It should have a focused owner and enough direct verification that future changes do not require full route boot to reason about the behavior.

**Is The Existing Approach Still Appropriate?**

Yes, the model in [studio-javascript-payload-inventory.md](docs-viewer/source/studio/studio-javascript-payload-inventory.md) is still the right scoring model: four risk categories, complete-responsibility extraction, and focused verification.

But the document is no longer sufficient as the implementation plan. It currently says the detail set floor is 8 and still shows several “done” mitigations with unchanged scores. For a target of 4 across the listed inventory, it should be revised into a broader tracker:

- refresh file count and include newly extracted modules
- rescore completed mitigation work
- record per-category scores
- define “score 4” acceptance criteria
- group the work by JS family instead of only top-ranked files
- keep `docs-viewer.js` explicitly out of scope

The practical first change request should be: “refresh and rescore the JavaScript inventory against a target score of 4, excluding `docs-viewer.js`, then produce grouped implementation batches.” That prevents us from spending time reducing risk that has already been reduced.