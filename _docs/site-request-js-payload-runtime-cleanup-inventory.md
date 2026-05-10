---
doc_id: site-request-js-payload-runtime-cleanup-inventory
title: JavaScript Payload And Runtime Cleanup Inventory
added_date: 2026-05-10
last_updated: "2026-05-10 20:55"
ui_status: draft
parent_id: site-request-js-payload-runtime-cleanup
sort_order: 10
hidden: false
---
# JavaScript Payload And Runtime Cleanup Inventory

This is the Slice C inventory for [JavaScript Payload And Runtime Cleanup Request](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup).

It is intentionally separate from the work-editor implementation plan so the Catalogue Work Editor slices can stay focused while the broader long-file priorities remain available for later cleanup.

## Policy Context

Any browser JavaScript file over 1,000 lines must be classified as one of:

- route shell
- mixed route controller
- domain module
- generated/runtime utility

Any mixed route controller over 1,000 lines must have either:

- a named extraction slice in the owning request or implementation plan
- an explicit reason to stay large for the next implementation period

Prioritize long mixed controllers that combine mutation orchestration, modal composition, generated-data reads, and rendering.

Treat transfer-size risk separately from maintenance risk.
A large file is not automatically a runtime problem unless it is eagerly loaded on a high-traffic route or brings avoidable transitive payload.

Re-run this inventory after material Studio or Docs Viewer JavaScript refactors.

## Inventory Command

```bash
find assets -type f -name '*.js' -print0 | xargs -0 wc -l | sort -nr
```

## Measured Inventory

| File | Lines | Raw | Gzip | Classification | Maintenance risk | Transfer-size risk | Disposition |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `assets/studio/js/catalogue-work-editor.js` | 1,231 | 44.0 KiB | 8.9 KiB | mixed route controller | medium | low | Extraction continues in the parent request. Slices D-G are implemented; Slice H covers search/selection. `catalogue-work-actions.js` is intentionally below the 1,000-line threshold after action workflow extraction. |
| `assets/js/docs-viewer.js` | 2,912 | 99.9 KiB | 18.8 KiB | mixed shared viewer runtime controller | high | medium | Existing Docs Viewer extraction plan remains active; render and management-UI boundaries are the next justified targets. |
| `assets/studio/js/tag-studio.js` | 1,886 | 63.2 KiB | 13.2 KiB | mixed route controller | high | low | Continue the existing Tag Editor split by moving render groups, popup behavior, and modal/save orchestration behind named route-local helpers only after current catalogue cleanup. |
| `assets/studio/js/catalogue-work-detail-editor.js` | 1,806 | 75.5 KiB | 14.0 KiB | mixed route controller | high | low | Pair with the work-editor section-renderer findings; extract detail section rendering only where the helper boundary is clearer than route-local ownership. |
| `assets/studio/js/tag-aliases.js` | 1,708 | 62.3 KiB | 11.3 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete; next slice should target modal view-models and list rendering before more alias workflow is added. |
| `assets/studio/js/tag-registry.js` | 1,625 | 58.3 KiB | 11.2 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete; next slice should target modal view-models, delete-impact rendering, and import-result rendering. |
| `assets/studio/js/catalogue-series-editor.js` | 1,625 | 68.3 KiB | 12.9 KiB | mixed route controller | medium | low | Keep route-local short term; revisit with work/detail section-renderer results because series has fewer section types and less immediate extraction pressure. |
| `assets/studio/js/catalogue-moment-editor.js` | 1,371 | 58.4 KiB | 11.2 KiB | mixed route controller | medium | low | Keep route-local short term; future extraction should focus on import/prose/media workflow helpers rather than line-count reduction. |
| `assets/studio/js/data-import.js` | 1,133 | 39.8 KiB | 7.8 KiB | mixed route controller | medium | low | Explicitly allowed to stay large for now because it is barely over threshold and still owns one coherent import workflow; split preview-list rendering or docs-management apply transport if it grows further. |

## Current Priority

1. `assets/studio/js/catalogue-work-editor.js`
2. `assets/js/docs-viewer.js`
3. `assets/studio/js/catalogue-work-detail-editor.js`
4. `assets/studio/js/tag-studio.js`
5. `assets/studio/js/tag-aliases.js` and `assets/studio/js/tag-registry.js`
6. `assets/studio/js/catalogue-series-editor.js`
7. `assets/studio/js/catalogue-moment-editor.js`
8. `assets/studio/js/data-import.js`

## Notes

- The inventory found no over-threshold pure domain modules and no over-threshold generated/runtime utilities.
- All over-threshold files are mixed route or shared viewer controllers, so the cleanup priority is maintenance-driven rather than payload-size-driven.
- The nine over-threshold files total about 569.6 KiB raw and 108.3 KiB gzip, but no route loads all nine together.
- The largest transfer-size risk is now the shared Docs Viewer controller because it is the largest remaining over-threshold JavaScript file and is eagerly loaded by docs-viewer routes.
- The work-editor measured line count reflects the post-Slice G state; the parent request records the per-slice measurements.
