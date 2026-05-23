---
doc_id: site-request-js-payload-runtime-cleanup-inventory
title: JavaScript Payload And Runtime Cleanup Inventory
added_date: 2026-05-10
last_updated: "2026-05-11 00:35"
ui_status: done
parent_id: site-request-js-config-structural-review
sort_order: 7000
viewable: true
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
| `assets/js/docs-viewer.js` | 2,912 | 99.9 KiB | 18.6 KiB | mixed shared viewer runtime controller | high | medium | Existing Docs Viewer extraction plan remains active; render and management-UI boundaries are the next justified targets now that Catalogue route cleanup has reached its stop point. |
| `assets/studio/js/tag-studio.js` | 1,886 | 63.2 KiB | 13.0 KiB | mixed route controller | high | low | Continue the existing Tag Editor split later by moving render groups, popup behavior, and modal/save orchestration behind named route-local helpers. |
| `assets/studio/js/tag-aliases.js` | 1,708 | 62.3 KiB | 11.2 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete; next slice should target modal view-models and list rendering before more alias workflow is added. |
| `assets/studio/js/tag-registry.js` | 1,625 | 58.3 KiB | 11.1 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete; next slice should target modal view-models, delete-impact rendering, and import-result rendering. |
| `assets/studio/js/data-import.js` | 1,133 | 39.8 KiB | 7.8 KiB | mixed route controller | medium | low | Explicitly allowed to stay large for now because it is barely over threshold and still owns one coherent import workflow; split preview-list rendering or docs-management apply transport if it grows further. |
| `assets/studio/js/catalogue-work-editor.js` | 992 | 36.0 KiB | 7.2 KiB | route coordinator | low | low | Below the long-file threshold after Work form, section, action, and selection extractions; accepted as a Catalogue route coordinator. |
| `assets/studio/js/catalogue-work-detail-editor.js` | 642 | 25.3 KiB | 5.3 KiB | route coordinator | low | low | Below the long-file threshold after Work Detail selection, form, section, and action extractions; accepted as a Catalogue route coordinator. |
| `assets/studio/js/catalogue-series-editor.js` | 605 | 24.1 KiB | 4.8 KiB | route coordinator | low | low | Below the long-file threshold after Series membership, action workflow, selection, form, and section extractions; accepted as a Catalogue route coordinator. |
| `assets/studio/js/catalogue-moment-editor.js` | 554 | 21.6 KiB | 4.4 KiB | route coordinator | low | low | Below the long-file threshold after the Moment import, action workflow, form, section, and selection/opening extractions; accepted as a Catalogue route coordinator. |

## Current Priority

1. `assets/js/docs-viewer.js`
2. `assets/studio/js/tag-studio.js`
3. `assets/studio/js/tag-aliases.js` and `assets/studio/js/tag-registry.js`
4. `assets/studio/js/data-import.js`

## Notes

- The inventory found no over-threshold pure domain modules and no over-threshold generated/runtime utilities.
- All remaining over-threshold files are mixed route or shared viewer controllers, so the cleanup priority is maintenance-driven rather than payload-size-driven.
- The five remaining over-threshold files total about 323.5 KiB raw and 61.7 KiB gzip, but no route loads all five together.
- The largest transfer-size risk is now the shared Docs Viewer controller because it is the largest remaining over-threshold JavaScript file and is eagerly loaded by docs-viewer routes.
- Catalogue route cleanup reached its stop point: `catalogue-work-editor.js`, `catalogue-work-detail-editor.js`, `catalogue-series-editor.js`, and `catalogue-moment-editor.js` are all below the 1,000-line review threshold and accepted as route coordinators.
